# Granola Export Skill

Export Granola meeting notes to markdown and push them to the gerryhanratty/agents GitHub repo.

## What this skill does

Runs `granola_export.py` to:
1. Fetch new meeting notes from the Granola API (or use mock data)
2. Write each note as a markdown file with YAML frontmatter and transcript into `notes/granola/` in the repo
3. Commit and push new notes to `github.com/gerryhanratty/agents`

## Usage

When the user invokes `/granola`, run the export script:

```bash
python3 ~/agents/skills/granola_skill/granola_export.py --repo ~/agents
```

### Options

- Add `--mock` to run with synthetic test data (no API key needed):
  ```bash
  python3 ~/agents/skills/granola_skill/granola_export.py --repo ~/agents --mock
  ```

- Add `--notes-dir <path>` to change the output subdirectory (default: `notes/granola`)

## API key setup

The script reads the Granola API key from the macOS Keychain:

```bash
security add-generic-password \
  -s granola-api \
  -a ghanratty@gmail.com \
  -w YOUR_GRANOLA_API_KEY
```

Or via environment variable (less secure): `export GRANOLA_API_KEY=your-key-here`

## After running

Report:
- How many notes were exported
- Which files were written
- Whether the push to GitHub succeeded
- Any notes skipped (already exported or not yet summarised)
