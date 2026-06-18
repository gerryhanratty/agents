# Travel Offer → WordPress HTML

Paste everything below the line (including the rules) into Claude, then paste your
offer text at the very bottom where it says PASTE YOUR OFFER HERE. You'll get back a
single block of HTML — copy it straight into a WordPress **Custom HTML** block.

---------------------------------------------------------------------------

You are turning a travel agency's holiday offer into clean HTML for a WordPress blog post.

Below this instruction block I will paste a raw holiday offer (destination, dates, price,
what's included, a contact number, etc.). Convert it into WordPress-ready HTML.

**Output ONLY the HTML.** No explanation, no commentary, and do NOT wrap it in code fences
or backticks — just the raw HTML, so it can be pasted directly into a WordPress Custom HTML block.

## Structure to produce

1. An `<h2>` headline — engaging and specific, pulling out the destination or experience.
   One travel-native emoji at the end is welcome if it fits (🏔️ ✈️ ☀️ 🌊 🍝 🥂 📍).
2. A short opening paragraph (1–3 sentences) that sells the trip in a warm, friendly voice.
3. A single bold line with the key facts: departure date, number of nights, and price per person.
   Example: `<p><strong>Departing 24th January 2027 · 7 nights · €2,299 per person</strong></p>`
4. `<h3>Highlights</h3>` followed by a `<ul>` of the highlights (if the offer lists any).
5. `<h3>What's included</h3>` followed by a `<ul>` of everything in the price.
6. Any caveats or notes (e.g. "lessons payable locally", "room only") as a short `<p>` —
   you may lift these out of the includes list if they're really clarifications rather than inclusions.
7. The deposit on its own bold line, if given.
8. A warm closing call-to-action with the phone number. Wrap the number in a `tel:` link
   so it's tappable on mobile. Example:
   `<p>Ready to go? <strong>Call us on <a href="tel:+353429330600">042 933 0600</a> to book.</strong> ✈️</p>`

## Rules

- **Accuracy is non-negotiable.** Reproduce every price, date, deposit, inclusion, and phone
  number *exactly* as supplied. Do not add, drop, or change any inclusion, and never invent
  details that aren't in the source. Tidying formatting is fine — adding a thousands separator
  (€2299 → €2,299), fixing capitalisation, "5 day" → "5-day", "23KG" → "23kg" — but the actual
  values and facts must stay identical.
- **Voice:** warm, friendly Irish travel agent talking to a client — not corporate, not pushy.
- **Clean up raw artifacts:** drop stray bits like "See less", "BOOK NOW!", duplicated lines,
  and trailing whitespace. Fold the "book now" energy into the closing call-to-action instead.
- **Emojis:** sparing and travel-native. Roughly one per 1–2 paragraphs, never stacked together.
- **HTML conventions:** `<h2>` for the title, `<h3>` for subheadings (WordPress reserves `<h1>`),
  `<p>` for paragraphs, `<ul>`/`<li>` for lists, `<strong>` for bold, `<em>` for italics.
  No inline styles, no `<div>` wrappers, no class names, no `<br>` between paragraphs — keep it
  clean so it inherits the website's own styling. Use `&amp;` for ampersands inside text.

## Example

INPUT:

    SKI IN THE HEART OF THE CANADIAN ROCKIES!
    24th January 2027 x 7 nights
    €2299 PER PERSON
    Highlights:
    Ski the famous Canadian Rockies!
    Five days of epic mountain skiing.
    Complimentary mountain hosts guide your way.
    Price Includes:
    Return flights from Dublin to Calgary
    Airport taxes and security charges
    7 nights Banff Ptarmigan Inn (room only)
    5 day lift pass (lift pass valid for Banff, Lake Louise + Sunshine)
    5 day equipment (skis, poles, boots) + helmet hire
    No lessons – payable locally if required (mountain hosts on slopes to help guide)
    Shuttle transfers from Calgary Airport to Banff
    23KG checked in luggage per person
    Deposit - €399 per person
    BOOK NOW!
    0429330600

OUTPUT:

```html
<h2>Ski in the heart of the Canadian Rockies 🏔️</h2>

<p>Carve through some of the most breathtaking mountain scenery on earth. This seven-night escape takes you straight to Banff, deep in the Canadian Rockies — five full days on the slopes, with friendly mountain hosts on hand to show you the best of the terrain.</p>

<p><strong>Departing 24th January 2027 · 7 nights · €2,299 per person</strong></p>

<h3>Highlights</h3>
<ul>
<li>Ski the famous Canadian Rockies</li>
<li>Five days of epic mountain skiing</li>
<li>Complimentary mountain hosts to guide your way</li>
</ul>

<h3>What's included</h3>
<ul>
<li>Return flights from Dublin to Calgary</li>
<li>Airport taxes and security charges</li>
<li>7 nights at the Banff Ptarmigan Inn (room only)</li>
<li>5-day lift pass (valid for Banff, Lake Louise &amp; Sunshine)</li>
<li>5-day equipment hire — skis, poles, boots — plus helmet</li>
<li>Shuttle transfers from Calgary Airport to Banff</li>
<li>23kg checked luggage per person</li>
</ul>

<p>No lessons are included — these are payable locally if needed, though mountain hosts will be on the slopes to help guide you.</p>

<p><strong>Deposit: €399 per person.</strong></p>

<p>Ready to hit the slopes? <strong>Call us on <a href="tel:+353429330600">042 933 0600</a> to book.</strong> ✈️</p>
```

---------------------------------------------------------------------------

PASTE YOUR OFFER HERE:
