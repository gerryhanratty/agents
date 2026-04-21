#!/usr/bin/env python3
import asyncio
import os
import sys
from datetime import datetime

# Add Playwright to path
sys.path.insert(0, "/Users/gerry/Library/Python/3.9/lib/python/site-packages")
from playwright.async_api import async_playwright
import resend

EVENTS = [
    {
        "name": "Angine de Poitrine (16 Oct 2026)",
        "url": "https://www.ticketmaster.ie/angine-de-poitrine-16-10-2026/event/18006481B129DEEC",
    },
    {
        "name": "Big Thief Dublin (29 Apr 2026)",
        "url": "https://www.ticketmaster.ie/big-thief-dublin-29-04-2026/event/1800631581826F5D",
    },
]

TO_EMAIL = "ghanratty@gmail.com"
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
LOG_FILE = os.path.expanduser("~/ticketmaster_monitor.log")


def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


async def check_tickets(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle", timeout=45000)
        await page.wait_for_timeout(6000)

        content = await page.content()

        # Try to grab any price/ticket info text
        ticket_info = []
        for selector in ["[data-testid*='ticket']", ".ticket", "[class*='ticket']", "[class*='price']"]:
            try:
                elements = await page.query_selector_all(selector)
                for el in elements[:5]:
                    text = (await el.inner_text()).strip()
                    if text and len(text) < 200:
                        ticket_info.append(text)
            except Exception:
                pass

        ticket_info = list(set(ticket_info))[:10]

        # Resale tickets with prices are available even if sold-out text is present
        has_priced_tickets = any("€" in t or "$" in t or "£" in t for t in ticket_info)
        has_resale = any("resale" in t.lower() for t in ticket_info) or "resale" in content.lower()

        sold_out_keywords = ["sold out", "soldout", "no tickets available", "not available"]
        is_sold_out = any(kw.lower() in content.lower() for kw in sold_out_keywords)

        # Only truly sold out if no priced tickets found
        truly_sold_out = is_sold_out and not has_priced_tickets

        resale_keywords = [
            "resale", "fan-to-fan", "buy tickets", "tickets from",
            "add to cart", "select tickets", "ticket prices"
        ]
        found_keywords = [kw for kw in resale_keywords if kw.lower() in content.lower()]

        await browser.close()
        return {
            "sold_out": truly_sold_out,
            "has_resale": has_resale,
            "found_keywords": found_keywords,
            "ticket_info": ticket_info,
            "has_tickets": has_priced_tickets or (bool(found_keywords) and not truly_sold_out),
        }


def send_email(event, result):
    if not RESEND_API_KEY:
        log("ERROR: RESEND_API_KEY env var not set — cannot send email.")
        return

    resend.api_key = RESEND_API_KEY

    ticket_type = "resale tickets" if result["has_resale"] else "tickets"
    body = f"Possible {ticket_type} detected for {event['name']}.\n\n"
    body += f"Event page: {event['url']}\n\n"
    if result["ticket_info"]:
        body += "Detected info:\n" + "\n".join(f"  - {t}" for t in result["ticket_info"])
    body += "\n\nCheck the link above to confirm and buy."

    try:
        resend.Emails.send({
            "from": "Ticket Monitor <onboarding@resend.dev>",
            "to": TO_EMAIL,
            "subject": f"Ticketmaster Alert: {event['name']} tickets may be available!",
            "text": body,
        })
        log(f"Alert email sent for {event['name']}.")
    except Exception as e:
        log(f"Failed to send email: {e}")


async def main():
    for event in EVENTS:
        log(f"Checking {event['name']}...")
        try:
            result = await check_tickets(event["url"])
            if result["sold_out"]:
                log(f"  Sold out — no tickets.")
            elif result["has_tickets"]:
                ticket_type = "resale tickets" if result["has_resale"] else "tickets"
                log(f"  Possible {ticket_type} available! Keywords: {result['found_keywords']}")
                send_email(event, result)
            else:
                log(f"  No clear ticket availability. Keywords: {result['found_keywords']}")
        except Exception as e:
            log(f"  Error checking {event['name']}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
