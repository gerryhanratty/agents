#!/usr/bin/env python3
"""
granola_export.py
-----------------
Export Granola meeting notes to markdown files and push to a GitHub repo.

Key security
------------
Store your API key in the macOS Keychain (recommended):

    security add-generic-password \
        -s granola-api \
        -a ghanratty@gmail.com \
        -w YOUR_GRANOLA_API_KEY

Or export it as an environment variable (less secure):

    export GRANOLA_API_KEY="your-key-here"

Usage
-----
    # Live mode (real API) — point --repo at your local clone of gerryhanratty/agents
    python3 granola_export.py --repo ~/code/agents

    # Mock mode (synthetic data, no API key needed)
    python3 granola_export.py --repo ~/code/agents --mock

    # Custom notes subdirectory (default: notes/granola)
    python3 granola_export.py --repo ~/code/agents --notes-dir notes/granola
"""

import os
import sys
import json
import subprocess
import re
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────

KEYCHAIN_SERVICE  = "granola-api"
KEYCHAIN_ACCOUNT  = "ghanratty@gmail.com"
GRANOLA_API_BASE  = "https://public-api.granola.ai/v1"
EXPORTED_IDS_FILE = ".exported_ids"          # lives inside the notes subdir
GITHUB_REPO_URL   = "https://github.com/gerryhanratty/agents.git"
GITHUB_BRANCH     = "main"
DEFAULT_NOTES_DIR = "notes/granola"          # relative to repo root

# ── Synthetic test data ────────────────────────────────────────────────────────

MOCK_NOTES_LIST = [
    {
        "id": "not_mock0000000001",
        "object": "note",
        "title": "Q2 Planning Kickoff",
        "owner": {"name": "Gerry Hanratty", "email": "ghanratty@gmail.com"},
        "created_at": "2026-05-05T09:00:00Z",
        "updated_at": "2026-05-05T10:15:00Z",
    },
    {
        "id": "not_mock0000000002",
        "object": "note",
        "title": "1:1 with Sarah — Product Roadmap",
        "owner": {"name": "Gerry Hanratty", "email": "ghanratty@gmail.com"},
        "created_at": "2026-05-07T14:00:00Z",
        "updated_at": "2026-05-07T14:45:00Z",
    },
    {
        "id": "not_mock0000000003",
        "object": "note",
        "title": "Design Review: Mobile Onboarding",
        "owner": {"name": "Gerry Hanratty", "email": "ghanratty@gmail.com"},
        "created_at": "2026-05-09T11:00:00Z",
        "updated_at": "2026-05-09T12:00:00Z",
    },
]

MOCK_NOTES_DETAIL = {
    "not_mock0000000001": {
        "id": "not_mock0000000001",
        "object": "note",
        "title": "Q2 Planning Kickoff",
        "owner": {"name": "Gerry Hanratty", "email": "ghanratty@gmail.com"},
        "created_at": "2026-05-05T09:00:00Z",
        "updated_at": "2026-05-05T10:15:00Z",
        "calendar_event": {
            "event_title": "Q2 Planning Kickoff",
            "organiser": "ghanratty@gmail.com",
            "scheduled_start_time": "2026-05-05T09:00:00Z",
            "scheduled_end_time": "2026-05-05T10:00:00Z",
            "invitees": [
                {"email": "sarah@example.com"},
                {"email": "tom@example.com"},
            ],
        },
        "attendees": [
            {"name": "Gerry Hanratty", "email": "ghanratty@gmail.com"},
            {"name": "Sarah Chen",     "email": "sarah@example.com"},
            {"name": "Tom Reilly",     "email": "tom@example.com"},
        ],
        "folder_membership": [],
        "summary_text": "Agreed on three Q2 priorities: ship mobile onboarding by end of May, close two enterprise pilots, and reduce infra costs by 15%.",
        "summary_markdown": (
            "## Q2 Planning Kickoff\n\n"
            "### Decisions\n"
            "- Ship mobile onboarding by **31 May**\n"
            "- Close two enterprise pilots (Acme, Globex)\n"
            "- Reduce infra costs by **15%** via rightsizing\n\n"
            "### Action Items\n"
            "- **Gerry**: Share updated roadmap doc by EOD Friday\n"
            "- **Sarah**: Confirm Acme pilot timeline\n"
            "- **Tom**: Pull current infra cost breakdown\n"
        ),
        "transcript": [
            {
                "speaker": {"source": "microphone"},
                "text": "Let's lock down the three big bets for Q2.",
                "start_time": "2026-05-05T09:01:00Z",
                "end_time":   "2026-05-05T09:01:10Z",
            },
            {
                "speaker": {"source": "speaker"},
                "text": "Mobile onboarding has to be the top priority — it's blocking the pilots.",
                "start_time": "2026-05-05T09:01:15Z",
                "end_time":   "2026-05-05T09:01:30Z",
            },
            {
                "speaker": {"source": "microphone"},
                "text": "Agreed. And we need to get serious about the infra costs before the board meeting.",
                "start_time": "2026-05-05T09:02:00Z",
                "end_time":   "2026-05-05T09:02:12Z",
            },
        ],
    },
    "not_mock0000000002": {
        "id": "not_mock0000000002",
        "object": "note",
        "title": "1:1 with Sarah — Product Roadmap",
        "owner": {"name": "Gerry Hanratty", "email": "ghanratty@gmail.com"},
        "created_at": "2026-05-07T14:00:00Z",
        "updated_at": "2026-05-07T14:45:00Z",
        "calendar_event": {
            "event_title": "1:1 Gerry / Sarah",
            "organiser": "sarah@example.com",
            "scheduled_start_time": "2026-05-07T14:00:00Z",
            "scheduled_end_time":   "2026-05-07T14:30:00Z",
            "invitees": [{"email": "ghanratty@gmail.com"}],
        },
        "attendees": [
            {"name": "Gerry Hanratty", "email": "ghanratty@gmail.com"},
            {"name": "Sarah Chen",     "email": "sarah@example.com"},
        ],
        "folder_membership": [],
        "summary_text": "Sarah flagged a scope risk on the onboarding flow. Agreed to cut the social sign-in step for the initial release.",
        "summary_markdown": (
            "## 1:1 with Sarah — Product Roadmap\n\n"
            "### Key points\n"
            "- Social sign-in is too risky to ship by 31 May — cutting it from v1\n"
            "- Email + password flow will launch first; social sign-in moves to v1.1\n"
            "- Sarah to update the spec and re-share with design by Thursday\n\n"
            "### Follow-ups\n"
            "- **Sarah**: Update spec (by Thu 9 May)\n"
            "- **Gerry**: Communicate scope change to Tom and engineering\n"
        ),
        "transcript": [
            {
                "speaker": {"source": "speaker"},
                "text": "I've been looking at the social sign-in work and I don't think we can make it by the 31st.",
                "start_time": "2026-05-07T14:02:00Z",
                "end_time":   "2026-05-07T14:02:20Z",
            },
            {
                "speaker": {"source": "microphone"},
                "text": "What's the blocker?",
                "start_time": "2026-05-07T14:02:22Z",
                "end_time":   "2026-05-07T14:02:25Z",
            },
            {
                "speaker": {"source": "speaker"},
                "text": "OAuth callback handling in the mobile app — it's more edge cases than we thought.",
                "start_time": "2026-05-07T14:02:28Z",
                "end_time":   "2026-05-07T14:02:45Z",
            },
        ],
    },
    "not_mock0000000003": {
        "id": "not_mock0000000003",
        "object": "note",
        "title": "Design Review: Mobile Onboarding",
        "owner": {"name": "Gerry Hanratty", "email": "ghanratty@gmail.com"},
        "created_at": "2026-05-09T11:00:00Z",
        "updated_at": "2026-05-09T12:00:00Z",
        "calendar_event": {
            "event_title": "Design Review: Mobile Onboarding",
            "organiser": "ghanratty@gmail.com",
            "scheduled_start_time": "2026-05-09T11:00:00Z",
            "scheduled_end_time":   "2026-05-09T12:00:00Z",
            "invitees": [
                {"email": "sarah@example.com"},
                {"email": "mei@example.com"},
            ],
        },
        "attendees": [
            {"name": "Gerry Hanratty", "email": "ghanratty@gmail.com"},
            {"name": "Sarah Chen",     "email": "sarah@example.com"},
            {"name": "Mei Liu",        "email": "mei@example.com"},
        ],
        "folder_membership": [],
        "summary_text": "Reviewed three onboarding screens. Approved the welcome and permissions screens; the profile setup screen needs a second pass before sign-off.",
        "summary_markdown": (
            "## Design Review: Mobile Onboarding\n\n"
            "### Screens reviewed\n"
            "| Screen           | Status       | Notes |\n"
            "|------------------|--------------|-------|\n"
            "| Welcome          | ✅ Approved  | — |\n"
            "| Permissions      | ✅ Approved  | Add copy explaining why notifications are needed |\n"
            "| Profile setup    | 🔄 Needs work | Simplify to name + avatar only for v1 |\n\n"
            "### Next steps\n"
            "- **Mei**: Revise profile setup screen and reshare by Mon 12 May\n"
            "- **Sarah**: Update spec to reflect permissions copy change\n"
        ),
        "transcript": [
            {
                "speaker": {"source": "microphone"},
                "text": "The welcome screen looks great — I think we can approve that one.",
                "start_time": "2026-05-09T11:05:00Z",
                "end_time":   "2026-05-09T11:05:12Z",
            },
            {
                "speaker": {"source": "speaker"},
                "text": "Agreed. The profile screen though — it's asking for too much upfront.",
                "start_time": "2026-05-09T11:08:00Z",
                "end_time":   "2026-05-09T11:08:15Z",
            },
            {
                "speaker": {"source": "microphone"},
                "text": "Let's cut it down to just name and avatar for v1. Everything else can come later.",
                "start_time": "2026-05-09T11:08:20Z",
                "end_time":   "2026-05-09T11:08:35Z",
            },
        ],
    },
}

# ── Key retrieval ──────────────────────────────────────────────────────────────

def get_api_key() -> str:
    """Read the Granola API key from macOS Keychain, then env var fallback."""

    # 1. macOS Keychain
    try:
        result = subprocess.run(
            [
                "security", "find-generic-password",
                "-s", KEYCHAIN_SERVICE,
                "-a", KEYCHAIN_ACCOUNT,
                "-w",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            key = result.stdout.strip()
            if key:
                return key
    except FileNotFoundError:
        pass  # not on macOS — fall through

    # 2. Environment variable
    key = os.environ.get("GRANOLA_API_KEY", "").strip()
    if key:
        return key

    print(
        "Error: No Granola API key found.\n\n"
        "Store it securely in the macOS Keychain:\n"
        f"  security add-generic-password \\\n"
        f"    -s {KEYCHAIN_SERVICE} \\\n"
        f"    -a {KEYCHAIN_ACCOUNT} \\\n"
        f"    -w YOUR_API_KEY\n\n"
        "Or export it as an environment variable (less secure):\n"
        "  export GRANOLA_API_KEY=your-key-here"
    )
    sys.exit(1)


# ── API helpers ────────────────────────────────────────────────────────────────

def _get(url: str, api_key: str) -> dict:
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {api_key}"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def fetch_all_notes(api_key: str) -> list[dict]:
    """Fetch every note from the Granola API, handling pagination."""
    notes = []
    cursor = None
    while True:
        url = f"{GRANOLA_API_BASE}/notes?page_size=30"
        if cursor:
            url += f"&cursor={cursor}"
        data = _get(url, api_key)
        notes.extend(data.get("notes", []))
        if not data.get("hasMore"):
            break
        cursor = data.get("cursor")
    return notes


def fetch_note_detail(api_key: str, note_id: str) -> dict:
    """Fetch a single note's full content including transcript."""
    url = f"{GRANOLA_API_BASE}/notes/{note_id}?include=transcript"
    return _get(url, api_key)


# ── Markdown conversion ────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    """Convert a title to a filename-safe slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:80]  # cap length


def format_timestamp(iso: str) -> str:
    """Format an ISO timestamp to HH:MM."""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%H:%M")
    except Exception:
        return iso


def note_to_markdown(note: dict) -> tuple[str, str]:
    """
    Convert a Granola note dict to a (filename, markdown_content) pair.
    """
    note_id    = note.get("id", "unknown")
    title      = note.get("title") or "Untitled Meeting"
    created_at = note.get("created_at", "")
    attendees  = note.get("attendees", [])
    cal        = note.get("calendar_event", {})
    summary_md = note.get("summary_markdown") or note.get("summary_text", "")
    transcript = note.get("transcript") or []

    # Date for frontmatter and filename
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M")
    except Exception:
        date_str = "0000-00-00"
        time_str = ""

    filename = f"{date_str}-{slugify(title)}.md"

    # Attendee list
    attendee_lines = "\n".join(
        f"  - {a.get('name', '')} <{a.get('email', '')}>".strip()
        for a in attendees
    ) or "  - (none recorded)"

    # Scheduled times
    start = cal.get("scheduled_start_time", "")
    end   = cal.get("scheduled_end_time", "")
    duration = ""
    if start and end:
        duration = f"{format_timestamp(start)} – {format_timestamp(end)}"

    # YAML frontmatter
    frontmatter = (
        f"---\n"
        f"id: {note_id}\n"
        f"title: \"{title}\"\n"
        f"date: {date_str}\n"
        f"time: {time_str}\n"
        f"duration: \"{duration}\"\n"
        f"attendees:\n{attendee_lines}\n"
        f"---\n\n"
    )

    # Transcript section
    if transcript:
        transcript_lines = []
        for entry in transcript:
            source = entry.get("speaker", {}).get("source", "unknown")
            label  = "You" if source == "microphone" else "Them"
            ts     = format_timestamp(entry.get("start_time", ""))
            text   = entry.get("text", "").strip()
            transcript_lines.append(f"**{label}** {ts} — {text}")
        transcript_section = "\n\n## Transcript\n\n" + "\n\n".join(transcript_lines)
    else:
        transcript_section = ""

    body = frontmatter + summary_md + transcript_section + "\n"
    return filename, body


# ── Exported IDs tracking ──────────────────────────────────────────────────────

def load_exported_ids(repo_dir: Path) -> set[str]:
    path = repo_dir / EXPORTED_IDS_FILE
    if not path.exists():
        return set()
    return set(path.read_text().splitlines())


def save_exported_ids(repo_dir: Path, ids: set[str]) -> None:
    path = repo_dir / EXPORTED_IDS_FILE
    path.write_text("\n".join(sorted(ids)) + "\n")


# ── Git operations ─────────────────────────────────────────────────────────────

def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def git_push(repo_dir: Path, new_count: int) -> None:
    """Stage all changes, commit, and push to origin/main."""
    run_git(["add", "."], repo_dir)

    # Check if there's anything to commit
    status = run_git(["status", "--porcelain"], repo_dir)
    if not status.stdout.strip():
        print("Nothing new to commit — all notes already exported.")
        return

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    msg = f"granola: export {new_count} note(s) [{now}]"
    run_git(["commit", "-m", msg], repo_dir)

    result = run_git(["push", "origin", GITHUB_BRANCH], repo_dir)
    if result.returncode != 0:
        print(f"Git push failed:\n{result.stderr}")
        sys.exit(1)
    print(f"Pushed {new_count} note(s) → github.com/gerryhanratty/agents ({GITHUB_BRANCH})")


def ensure_repo(repo_dir: Path) -> None:
    """Initialise the repo and set remote if it doesn't exist yet."""
    if not (repo_dir / ".git").exists():
        print(f"Initialising git repo at {repo_dir}")
        repo_dir.mkdir(parents=True, exist_ok=True)
        run_git(["init", "-b", GITHUB_BRANCH], repo_dir)
        run_git(["remote", "add", "origin", GITHUB_REPO_URL], repo_dir)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export Granola meeting notes to markdown and push to GitHub."
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Path to your local clone of gerryhanratty/agents",
    )
    parser.add_argument(
        "--notes-dir",
        default=DEFAULT_NOTES_DIR,
        help=f"Subdirectory inside --repo where notes are written (default: {DEFAULT_NOTES_DIR})",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use synthetic test data instead of calling the real API",
    )
    args = parser.parse_args()

    repo_dir  = Path(args.repo).expanduser().resolve()
    notes_dir = repo_dir / args.notes_dir
    notes_dir.mkdir(parents=True, exist_ok=True)

    ensure_repo(repo_dir)

    # ── Fetch notes ────────────────────────────────────────────────────────────
    if args.mock:
        print("Running in MOCK mode — using synthetic test data.")
        notes_list = MOCK_NOTES_LIST
        detail_map = MOCK_NOTES_DETAIL
    else:
        api_key = get_api_key()
        print("Fetching note list from Granola API…")
        notes_list = fetch_all_notes(api_key)
        detail_map = None  # fetched individually below

    # ── Export ─────────────────────────────────────────────────────────────────
    exported_ids = load_exported_ids(notes_dir)
    new_ids      = set()
    new_count    = 0

    for stub in notes_list:
        note_id = stub["id"]
        title   = stub.get("title") or "Untitled"

        if note_id in exported_ids:
            print(f"  skip  {title} (already exported)")
            continue

        # Fetch detail
        if args.mock:
            note = detail_map.get(note_id)
            if not note:
                print(f"  skip  {title} (no mock detail)")
                continue
        else:
            try:
                note = fetch_note_detail(api_key, note_id)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    print(f"  skip  {title} (note not yet summarised)")
                    continue
                raise

        filename, content = note_to_markdown(note)
        dest = notes_dir / filename
        dest.write_text(content, encoding="utf-8")
        print(f"  write {args.notes_dir}/{filename}")
        new_ids.add(note_id)
        new_count += 1

    if new_count == 0:
        print("No new notes to export.")
        return

    # Update tracking file
    save_exported_ids(notes_dir, exported_ids | new_ids)

    # Push to GitHub
    git_push(repo_dir, new_count)


if __name__ == "__main__":
    main()
