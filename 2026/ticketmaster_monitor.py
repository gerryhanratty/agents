#!/usr/bin/env python3
"""
Ticketmaster Event Monitor

Monitors Ticketmaster event pages for ticket / resale availability and emails
an alert via Resend when availability appears.

Detection reads the *rendered ticket list*, not raw HTML. Ticketmaster ships a
full translations dictionary inside `<script id="__NEXT_DATA__">` on every page,
so raw-HTML keyword matching ("sold out", "resale", "buy tickets") matches on
every page regardless of real availability — including on dead event pages.

Alerts are edge-triggered: an email is sent when an event's state *changes*
into an available state, not on every run that finds tickets.
"""
import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone

from playwright.async_api import async_playwright
import resend

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

EVENTS = [
    {
        "name": "Angine de Poitrine (16 Oct 2026)",
        "url": "https://www.ticketmaster.ie/angine-de-poitrine-16-10-2026/event/18006481B129DEEC",
    },
]

TO_EMAIL = os.environ.get("TICKETMASTER_ALERT_EMAIL", "")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
FROM_EMAIL = os.environ.get("TICKETMASTER_FROM_EMAIL", "Ticket Monitor <onboarding@resend.dev>")
LOG_FILE = os.path.expanduser(
    os.environ.get("TICKETMASTER_LOG_FILE", "~/ticketmaster_monitor.log")
)
STATE_FILE = os.path.expanduser(
    os.environ.get("TICKETMASTER_STATE_FILE", "~/.ticketmaster_state.json")
)

# Headless works: verified rendering the real event page and ticket list.
HEADLESS = os.environ.get("TICKETMASTER_HEADLESS", "1") != "0"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Visible-text markers that Ticketmaster renders when the list is empty.
EMPTY_LIST_MARKERS = [
    "couldn't find any results",
    "couldn`t find any results",
    "could not find any results",
    "no results",
]

PRICE_RE = re.compile(r"[€$£]\s?\d")
DEAD_PAGE_MARKERS = ["page not found", "server error", "410:", "404:"]


def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except OSError as e:
        print(f"(could not write log: {e})", flush=True)


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except OSError as e:
        log(f"WARN: could not write state file: {e}")


async def check_tickets(url):
    """Return a dict describing the event's current availability state."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context(user_agent=USER_AGENT, locale="en-IE")
        page = await context.new_page()
        result = {"status": "unknown", "prices": [], "detail": ""}
        try:
            try:
                await page.goto(url, wait_until="networkidle", timeout=45000)
            except Exception:
                # networkidle can time out on ad/analytics chatter; the DOM is
                # usually complete well before that.
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(6000)

            title = (await page.title()) or ""

            # --- dead / removed event page -------------------------------
            if any(m in title.lower() for m in DEAD_PAGE_MARKERS):
                result["status"] = "dead"
                result["detail"] = f"Event page returns: {title.strip()}"
                return result

            # --- structured event metadata (JSON-LD) ---------------------
            event_status, start_date = None, None
            try:
                blocks = await page.eval_on_selector_all(
                    "script[type='application/ld+json']", "els => els.map(e => e.textContent)"
                )
                for raw in blocks:
                    try:
                        data = json.loads(raw)
                    except ValueError:
                        continue
                    if isinstance(data, dict) and "Event" in str(data.get("@type", "")):
                        event_status = data.get("eventStatus", "") or ""
                        start_date = data.get("startDate")
                        break
            except Exception:
                pass
            result["event_status"] = event_status
            result["start_date"] = start_date

            if event_status and "cancelled" in event_status.lower():
                result["status"] = "cancelled"
                result["detail"] = "Event is marked cancelled."
                return result

            # --- rendered ticket list ------------------------------------
            list_text = ""
            for selector in ["#list-view", "#quickpicks", "#main-content", "body"]:
                try:
                    el = await page.query_selector(selector)
                    if el:
                        list_text = await el.inner_text()
                        if list_text.strip():
                            break
                except Exception:
                    continue

            low = list_text.lower()
            prices = PRICE_RE.findall(list_text)
            price_lines = [
                ln.strip()
                for ln in list_text.splitlines()
                if PRICE_RE.search(ln) and len(ln.strip()) < 160
            ]
            # Delivery/fee copy ("Gift Wrap + Post out IE and UK €5.99") is not
            # ticket inventory.
            price_lines = [
                ln for ln in price_lines
                if not any(w in ln.lower() for w in ("post out", "gift wrap", "etickets", "delivery"))
            ]
            is_empty = any(m in low for m in EMPTY_LIST_MARKERS)

            result["prices"] = price_lines[:10]
            if price_lines and not is_empty:
                result["status"] = "available"
                result["detail"] = "Ticket listings with prices are showing."
            elif is_empty:
                result["status"] = "none"
                result["detail"] = "Ticket list shows no results."
            else:
                result["status"] = "unclear"
                result["detail"] = (
                    "Could not read the ticket list (layout change or bot challenge)."
                )
            return result
        finally:
            await browser.close()


def send_email(event, result):
    if not RESEND_API_KEY:
        log("ERROR: RESEND_API_KEY not set — cannot send email.")
        return False
    if not TO_EMAIL:
        log("ERROR: TICKETMASTER_ALERT_EMAIL not set — cannot send email.")
        return False

    resend.api_key = RESEND_API_KEY
    body = f"Tickets appear to be available for {event['name']}.\n\n"
    body += f"Event page: {event['url']}\n\n"
    if result["prices"]:
        body += "Listings detected:\n" + "\n".join(f"  - {t}" for t in result["prices"])
        body += "\n\n"
    body += "Check the link above to confirm and buy."

    try:
        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": TO_EMAIL,
            "subject": f"Ticketmaster Alert: {event['name']} tickets may be available!",
            "text": body,
        })
        log(f"  Alert email sent for {event['name']}.")
        return True
    except Exception as e:
        log(f"  Failed to send email: {e}")
        return False


async def main():
    if not EVENTS:
        log("No events configured — nothing to check.")
        return

    state = load_state()
    now = datetime.now(timezone.utc).isoformat()

    for event in EVENTS:
        name = event["name"]
        log(f"Checking {name}...")
        try:
            result = await check_tickets(event["url"])
        except Exception as e:
            log(f"  Error checking {name}: {type(e).__name__}: {e}")
            continue

        status = result["status"]
        prev = state.get(name, {}).get("status")
        log(f"  status={status} ({result['detail']})")
        if result["prices"]:
            log(f"  listings: {result['prices']}")

        if status == "dead":
            if prev != "dead":
                log(f"  NOTE: {name} no longer resolves — remove it from EVENTS.")
        elif status == "available":
            # Edge-triggered: only alert on transition into availability.
            if prev != "available":
                send_email(event, result)
            else:
                log("  Already alerted for this availability window — no email.")
        elif status == "unclear":
            log("  WARN: detection inconclusive; not alerting.")

        state[name] = {"status": status, "checked_at": now, "detail": result["detail"]}

    save_state(state)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
