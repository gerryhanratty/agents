# Ticketmaster Monitor

A local event monitoring tool that watches Ticketmaster event pages for ticket availability and sends email alerts when tickets are found.

## ⚠️ Important: Local Execution Required

**This script MUST run locally on your machine with a visible browser window.** Ticketmaster blocks headless and automated access, so the browser window will open and remain visible during ticket checks.

This is NOT suitable for running on remote servers or in cloud environments.

## Requirements

- Python 3.7+
- Playwright browser automation library
- Resend account (free) for email alerts
- A visible desktop (not SSH/headless environment)

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

Add this line to check every 30 minutes:

```cron
*/30 * * * * cd /path/to/agents && python ticketmaster_monitor.py >> /var/log/ticketmaster.log 2>&1
```

Or check every hour:

```cron
0 * * * * cd /path/to/agents && python ticketmaster_monitor.py >> /var/log/ticketmaster.log 2>&1
```

Make sure the cron job runs in a session where a display is available (this typically works on local macOS/Linux machines).

## How It Works

1. Opens a browser to each event URL
2. Waits for page to load (network idle)
3. Scrapes the page for:
   - Price indicators (€, $, £)
   - Ticket-related text elements
   - Keywords like "resale", "buy tickets", "add to cart"
4. Determines ticket availability status:
   - **Sold out**: No price indicators found
   - **Available**: Price indicators or purchase keywords found
   - **Resale**: Resale-specific keywords found
5. Sends email alert if tickets are found

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

**Ticketmaster returns "Access Denied"**
- You're likely running in headless mode - this script requires a visible browser
- Ensure the browser window stays open during execution
- If running via cron, ensure cron has access to a display

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
