# Ticketmaster Monitor

A local event monitoring tool that watches Ticketmaster event pages for ticket availability and sends email alerts when tickets are found.

## Execution notes

The monitor runs **headless by default** and works fine that way — verified
against a live ticketmaster.ie event page, which renders the real ticket list
under headless Chromium. (An earlier version of this README claimed a visible
browser was mandatory; that is not the case.)

Ticketmaster returns an HTTP 401 on the event page while still serving the full
rendered page, so status codes are not used as a health signal.

If you ever do hit a bot challenge, force a visible browser with:

```bash
TICKETMASTER_HEADLESS=0 python ticketmaster_monitor.py
```

## Requirements

- Python 3.7+
- Playwright browser automation library
- Resend account (free) for email alerts
- `python-dotenv` (optional — only needed if you use a `.env` file)

## Setup

### 1. Clone and Install Dependencies

```bash
git clone https://github.com/gerryhanratty/agents.git
cd agents
pip install playwright resend python-dotenv
playwright install chromium
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:
```
TICKETMASTER_ALERT_EMAIL=your-email@example.com
RESEND_API_KEY=re_xxxxxxxxxxxxx
```

- **TICKETMASTER_ALERT_EMAIL**: The email address to receive alerts
- **RESEND_API_KEY**: Get a free API key from [Resend](https://resend.com)
- **TICKETMASTER_LOG_FILE** (optional): Custom log file location

### 3. Add Events to Monitor

Edit `ticketmaster_monitor.py` and update the `EVENTS` list with the Ticketmaster event URLs you want to monitor:

```python
EVENTS = [
    {
        "name": "Your Event Name (Date)",
        "url": "https://www.ticketmaster.ie/your-event-url",
    },
]
```

## Usage

### Run Once

```bash
python ticketmaster_monitor.py
```

The browser will open, navigate to each event page, and check for ticket availability. A visible browser window is required - do not minimize or close it while the script runs.

### Schedule with Cron (macOS/Linux)

Run the monitor periodically by adding to your crontab:

```bash
crontab -e
```

Add a single line to check every hour:

```cron
0 * * * * . $HOME/.ticketmaster.env && /usr/bin/python3 /path/to/agents/2026/ticketmaster_monitor.py >> $HOME/ticketmaster_monitor.log 2>&1
```

Notes:

- Use `.` rather than `source` — cron runs `/bin/sh`, where `source` is not portable.
- Keep it to **one line ending in a newline**. A crontab whose lines get joined
  produces a command ending `2>&10 * * * * ...`, where `2>&10` redirects stderr
  to file descriptor 10; that fd is not open, so the shell aborts before running
  anything and the job silently never executes.
- Use absolute paths; cron has a minimal environment.

## How It Works

1. Opens a headless browser to each event URL
2. Waits for the page to render (falls back to `domcontentloaded` if
   `networkidle` times out on ad/analytics traffic)
3. Reads the **rendered ticket list** (`#list-view` / `#quickpicks`), not raw HTML
4. Classifies the event into one status:
   - **available** — priced listings are showing in the ticket list
   - **none** — the list renders "no results"
   - **dead** — the event page 404s/410s (event removed or past)
   - **cancelled** — JSON-LD `eventStatus` says cancelled
   - **unclear** — the list could not be read (never alerts)
5. Sends an email **only when an event transitions into `available`**

### Why not raw-HTML keyword matching

Every Ticketmaster page embeds a complete UI translations dictionary in
`<script id="__NEXT_DATA__">`, which contains the literal strings "Sold Out",
"resale", "buy tickets", "Limited Availability" and so on. Searching the raw
HTML for those keywords therefore matches on **every** page — including on a
410 "page not found" page. The previous version of this script did exactly that
and emailed a false "tickets available!" alert every hour.

Detection now reads only text that is actually rendered to the user, and
filters out delivery copy such as "Gift Wrap + Post out IE and UK €5.99" so a
postage price is never mistaken for ticket inventory.

## State / alert de-duplication

The last known status per event is stored in `~/.ticketmaster_state.json`
(override with `TICKETMASTER_STATE_FILE`). Alerts are edge-triggered: going
`none → available` emails once; staying `available` on later runs does not
re-email. Delete the state file to reset.

## Logs

All activity is logged to `~/ticketmaster_monitor.log` (or custom location via `TICKETMASTER_LOG_FILE`).

View logs:
```bash
tail -f ~/ticketmaster_monitor.log
```

## Troubleshooting

**Browser won't open / "Failed to launch chromium"**
- Ensure Playwright is installed: `playwright install chromium`
- Ensure you're running on a machine with a display (not SSH/headless)

**No email alerts being sent**
- Check your `RESEND_API_KEY` is set correctly
- Check your `TICKETMASTER_ALERT_EMAIL` is set
- Look at logs for error messages

**Status is always `unclear`**
- Ticketmaster may have changed its ticket-list markup; check the `#list-view`
  and `#quickpicks` selectors still exist on the page
- Or you hit a bot challenge — try `TICKETMASTER_HEADLESS=0`

**Status is `dead`**
- The event has been removed from Ticketmaster (past or cancelled). Delete it
  from the `EVENTS` list.

**Cron job never runs**
- Check `crontab -l | wc -l` matches the number of jobs you expect; joined
  lines silently break the whole crontab
- On macOS, `cron` may need Full Disk Access under System Settings →
  Privacy & Security

**Connection timeouts**
- Ticketmaster pages can take a while to load
- The script waits up to 45 seconds by default - consider adjusting if needed

## Security

- `.env` file is excluded from version control (see `.gitignore`)
- Never commit your actual `.env` file
- API keys are stored locally only
- No sensitive data is logged

## License

MIT
