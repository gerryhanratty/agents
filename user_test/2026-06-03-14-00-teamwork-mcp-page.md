---
date: 2026-06-03 14:00
task: "Explore and document the Teamwork.com MCP server page"
url: https://www.teamwork.com/ai/mcp/
result: pass
---

## Task
Review and document the TeamworkAI MCP server landing page — content, structure, CTAs, and notable UX observations.

## Steps taken
1. Navigated to https://www.teamwork.com/ai/mcp/
2. Took above-fold and full-page screenshots at 1440×900 (desktop)
3. Extracted page text for copy and structure analysis

## Observations

### Page purpose
Dedicated landing page for the Teamwork.com MCP (Model Context Protocol) server. Positioned as a way for users to connect Claude, ChatGPT, Gemini, Copilot, or Cursor to their Teamwork account so AI agents can read and write across projects, tasks, Desk tickets, and milestones.

### Above the fold
- Hero headline: **"Put your AI to work with the Teamwork.com MCP server"** — clear and direct. No ambiguity about what this page is for.
- Sub-copy names Claude, ChatGPT, and Gemini explicitly — immediately signals compatibility for AI-tool users.
- Two CTAs: **"Start your free trial"** (purple, filled) and **"Book a demo"** (outlined). Both visible without scrolling.
- "30 DAY TRIAL. NO CREDIT CARD REQUIRED" under the primary CTA — good friction-reducer.
- A live chat widget fires immediately in the bottom-right corner: *"Hi there 👋 Need help deciding if Teamwork.com is right for your team?"* with options to start free, book a demo, or chat with sales. This is useful but competes visually with the CTAs.
- Cookie consent banner at the bottom — fires before the user has scrolled.

### How it works section
Three-step flow, clearly laid out:
1. **Enable the MCP** — set up in settings, choose workspaces
2. **Connect your AI tool** — add the MCP URL, authenticate
3. **Let AI do the work** — ask in plain English, AI reads/writes across projects

Simple and scannable. No jargon beyond "MCP" itself, which the page does not define inline (assumes the reader already knows what MCP is).

### Supported AI tools
Icons + descriptions for: ChatGPT, Claude, Copilot, Gemini, Cursor. Each has a one-sentence description of that tool's general purpose. Practical and reassuring for users checking compatibility.

### Security section (3 panels visible in full-page screenshot)
- **OAuth 2.0 secure connection** — named explicitly, screenshot of auth flow
- **Scoped to your permissions** — AI only accesses what the user's account can access
- **MCP 2.0 + zero training** — data is not used to train AI models

These are well-chosen trust signals for a technical/business audience evaluating an AI integration.

### FAQ section
Accordion-style. Questions visible in page text include:
- What is MCP?
- Why use the Teamwork.com MCP server?
- What AI tools are compatible?
- What data can AI access?
- How does the Teamwork.com MCP server use my permissions?
- Is there a limit to how many Teamwork.com MCP servers you can have?
- Does AI have MCP 2.0 + zero training?

The FAQ anticipates both beginner questions (what is MCP?) and security-conscious ones (permissions, data use) — a good range.

### Footer CTA
"Ready to profit from every client demand with Teamwork.com?" with a "Start now" button.

### Navigation
Standard Teamwork.com global nav: Product / Solutions / Why Teamwork.com / Resources / Pricing / TeamworkAI — plus Contact Sales / Log in / Try for free. The page sits within the broader Teamwork marketing site; the MCP page is discoverable but not top-level.

## Outcome
The page loaded cleanly at desktop resolution. All content rendered correctly. The page does a solid job of explaining what the MCP server is, how to set it up in three steps, which AI tools it supports, and how security is handled. No broken elements or missing assets observed.

## Issues found
| # | Severity | Description |
|---|----------|-------------|
| 1 | Medium | "MCP" is never defined on the page — users unfamiliar with the Model Context Protocol standard will not understand what it means without prior knowledge. A one-line definition would help. |
| 2 | Medium | Live chat widget fires immediately and overlaps the hero area at 1440px — competes with the CTAs before the user has had time to form intent. |
| 3 | Low | Cookie consent banner fires on load, before any interaction — standard pattern but adds visual noise on arrival. |
| 4 | Low | The three security panels (OAuth, Scoped permissions, MCP 2.0) are visible in the full-page screenshot but their copy is too small to read without zooming — may be a density issue on wider viewports. |

## Suggested follow-up tests
- Test the MCP setup flow end-to-end from the "Enable the MCP" step in settings — does the URL + auth process match what the page describes?
- Check how the page renders on mobile (375px) — the hero copy is long and the chat widget may be more intrusive
- Test the FAQ accordion — do all items expand/collapse correctly?
- Verify the "Start your free trial" CTA destination and whether it pre-selects a plan or drops the user at a generic signup
