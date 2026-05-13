# User Testing Skill — yety.ie

Perform user testing tasks on yety.ie using Playwright. The user will describe a task in plain English and you will automate it in a real browser.

## Invocation

`/user_testing <task description>`

Examples:
- `/user_testing log in`
- `/user_testing log out`
- `/user_testing create a new yety`

## Setup check

Before running, verify Playwright is installed:

```bash
npx playwright --version 2>/dev/null || pip show playwright 2>/dev/null || echo "not installed"
```

If not installed, prompt the user to run:
```bash
pip install playwright && playwright install chromium
```

## Credentials

Read login credentials from the macOS Keychain:

```bash
# Email
security find-generic-password -s yety-login -a email -w

# Password
security find-generic-password -s yety-login -a password -w
```

If credentials are not found, instruct the user to store them:
```bash
security add-generic-password -s yety-login -a email -w their@email.com
security add-generic-password -s yety-login -a password -w theirpassword
```

## How to run tasks

Write a short Python Playwright script tailored to the requested task and run it with `python3`. Use headed mode (`headless=False`) so the user can watch. Always navigate from `https://yety.ie`.

### Login task

```python
from playwright.sync_api import sync_playwright
import subprocess

def get_secret(account):
    result = subprocess.run(
        ["security", "find-generic-password", "-s", "yety-login", "-a", account, "-w"],
        capture_output=True, text=True
    )
    return result.stdout.strip()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://yety.ie")
    # Fill in login form — adapt selectors to match the actual site
    page.fill('[name="email"]', get_secret("email"))
    page.fill('[name="password"]', get_secret("password"))
    page.click('[type="submit"]')
    page.wait_for_load_state("networkidle")
    print("Done:", page.url)
    browser.close()
```

### General approach

1. Inspect the page structure to identify the correct selectors
2. Write the minimal Playwright script for the task
3. Run it and report what happened (URL reached, any errors, screenshots if useful)
4. If a step fails, pause and describe the blocker to the user

## After running

### 1. Write an observations report

Save a markdown report to `~/agents/notes/user_testing/YYYY-MM-DD-HH-MM-<slug>.md` where `<slug>` is a kebab-case version of the task (e.g. `log-in`, `create-new-yety`).

Report format:

```markdown
---
date: YYYY-MM-DD HH:MM
task: "<task description as given>"
url: https://yety.ie
result: pass | fail | partial
---

## Task
<restate the task in one sentence>

## Steps taken
1. Navigated to https://yety.ie
2. ...

## Observations
- <anything notable about the UI, flow, errors, or unexpected behaviour>
- <include selector issues, missing elements, confusing copy, etc.>

## Outcome
<one paragraph summary — did the task succeed? what was the final state?>

## Issues found
| # | Severity | Description |
|---|----------|-------------|
| 1 | High / Medium / Low | ... |

## Suggested follow-up tests
- ...
```

Create the `~/agents/notes/user_testing/` directory if it doesn't exist.

### 2. Confirm to the user

Tell the user the full path to the report file and give a one-line summary of the outcome.
