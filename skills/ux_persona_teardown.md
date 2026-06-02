---
description: "Synthesise a user persona from guided questions, then run a structured UX teardown of a web page from that persona's perspective"
argument-hint: "<URL to test>"
---

# UX Persona Teardown Skill

Run a structured front-end UX teardown of any web page through the eyes of a synthesised user persona.

---

## Step 1 — Build the persona

Ask the user the following five questions. You may ask them all at once.

1. **Who is this user?** One sentence — role, background, or life situation.  
   *e.g. "a 50-year-old nurse who occasionally books things online"*
2. **Tech comfort level** — Novice / Comfortable / Power user?
3. **Primary goal** — What is this user trying to accomplish on the page?
4. **Device** — Mobile, Desktop, or Tablet?
5. **Mindset / context** — e.g. first-time visitor, in a hurry, sceptical, referred by a friend, comparison-shopping.

## Step 2 — Synthesise and confirm the persona

From the answers, create a named persona card and show it to the user:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Persona:     "<Name, Age>"
Background:  ...
Tech level:  Novice / Comfortable / Power user
Goal:        ...
Device:      Mobile / Desktop / Tablet
Mindset:     ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Ask: "Does this persona look right, or would you like to adjust anything?"

Do not proceed until the user confirms.

---

## Step 3 — Fetch and screenshot the page

If a URL was passed as an argument, use it. Otherwise ask for the URL now.

### Take a screenshot

Set the viewport based on the persona's device:
- Mobile → width 390, height 844
- Tablet → width 768, height 1024
- Desktop → width 1440, height 900

```python
from playwright.sync_api import sync_playwright

device = "<device from persona>"  # Mobile / Tablet / Desktop
viewports = {
    "Mobile":  {"width": 390,  "height": 844},
    "Tablet":  {"width": 768,  "height": 1024},
    "Desktop": {"width": 1440, "height": 900},
}
vp = viewports.get(device, viewports["Desktop"])

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport=vp)
    page.goto("<URL>", wait_until="networkidle", timeout=15000)
    page.screenshot(path="/tmp/ux-teardown-above-fold.png", full_page=False)
    page.screenshot(path="/tmp/ux-teardown-full.png", full_page=True)
    title = page.title()
    browser.close()

print(f"Title: {title}")
print("Screenshots saved.")
```

After running, use the Read tool to view both screenshots:
- `/tmp/ux-teardown-above-fold.png` — what the user sees first
- `/tmp/ux-teardown-full.png` — the full page

### Also fetch the page text (for copy analysis)

```bash
curl -sL "<URL>" \
  | python3 -c "
import sys, re, html as h
src = sys.stdin.read()
src = re.sub(r'<script[^>]*>.*?</script>', '', src, flags=re.DOTALL|re.IGNORECASE)
src = re.sub(r'<style[^>]*>.*?</style>', '', src, flags=re.DOTALL|re.IGNORECASE)
src = re.sub(r'<[^>]+>', ' ', src)
src = h.unescape(src)
src = re.sub(r'\s+', ' ', src).strip()
print(src[:6000])
"
```

If Playwright is not installed, tell the user:
```
pip install playwright && playwright install chromium
```
and fall back to the curl text fetch only.

---

## Step 4 — Run the teardown

Analyse the page entirely through the lens of the confirmed persona. Work through each dimension below. Be specific — quote actual copy, describe real elements, flag exact friction points.

### Dimensions

**1. First impression (0–5 seconds)**  
What does this user see and feel in the first glance? Does it immediately signal relevance to their goal? Is the value proposition clear at their reading level?

**2. Navigation & wayfinding**  
Can they find what they came for? Is the menu labelled in plain language? Are there too many choices or not enough?

**3. Copy and language**  
Is the writing pitched at the right level for this user's background and tech comfort? Any jargon, assumptions, or missing explanation that would trip them up?

**4. Calls to action**  
Are the key next steps visible without scrolling? Are labels unambiguous for this persona? Is there too much choice or unclear hierarchy?

**5. Trust signals**  
Would this user feel safe and confident? Consider: social proof, contact info, pricing transparency, privacy cues, brand credibility.

**6. Friction points**  
List anything that would confuse, frustrate, or cause this user to leave. Forms, logins, unclear steps, slow load, broken elements.

**7. Device fit**  
Does the layout and interaction model suit the persona's device? Touch targets on mobile, information density on desktop, etc.

**8. Cognitive load**  
How much is being asked of this user at once? Is the page overwhelming or does it guide them clearly toward their goal?

---

## Step 5 — Write and save the report

Read the report template:

```bash
cat ~/.claude/skills/ux_persona_teardown_template.md
```

If the file is missing, tell the user and stop — do not fall back to a hardcoded format.

Write the completed report to:
```
/tmp/YYYY-MM-DD-<slug>.md
```
where `<slug>` is a kebab-case label for the URL or task (e.g. `yety-homepage`, `checkout-flow`).

Then ask the user: "Would you like me to push this report to GitHub, and if so, which repo and path?"

If they confirm a destination, push via the GitHub API:

```bash
FILENAME="<filename>"
CONTENT=$(base64 -i "/tmp/${FILENAME}")
gh api --method PUT \
  "repos/<owner>/<repo>/contents/<path>/${FILENAME}" \
  --field message="Add UX persona teardown: <URL> (<date>)" \
  --field content="${CONTENT}" \
  --field branch="main" \
  --jq '.content.html_url'
```

Return the GitHub URL (or local file path) and a one-line verdict.
