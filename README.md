<div align="center">

# AI Tool Atlas

**Every AI tool, sorted by what it does. Free and paid kept apart, with monthly prices.**

[**Open the live site**](https://sabyasachi-kashyap.github.io/ai-tool-atlas/) · [About the Atlas](https://sabyasachi-kashyap.github.io/ai-tool-atlas/about.html)

![Tools](https://img.shields.io/badge/tools-60-1f6f54)
![Categories](https://img.shields.io/badge/categories-8-a8480a)
![No build step](https://img.shields.io/badge/build-none-12161b)
![Frontend dependencies](https://img.shields.io/badge/frontend%20deps-0-12161b)

</div>

---

## What it is

A searchable directory of AI tools for writing, images, video, voice, music, coding, productivity and meetings. For each tool it shows what the tool is good for, what the free plan includes, and what each paid plan costs per month.

Prices change often, so every card is meant to be checked against the vendor's own pricing page. The site shows the date of the last refresh.

## Features

- **Free and paid are separated.** A *Free tools* section and a *Paid-only tools* section, with All / Free / Paid switches.
- **Monthly prices.** Every paid plan is listed in USD. Free cards state the actual limits.
- **8 categories** with live counts: Chat assistants, Images, Video & avatars, Voice, Music, Coding, Writing & productivity, Research & meetings.
- **Search** across tool names, descriptions and categories.
- **Sort** by category or by lowest paid price.
- **Category links.** Categories on the About page open the directory already filtered.
- **No build step.** One HTML page reads one JSON file. No framework, no dependencies.
- **Accessible and responsive.** Real buttons and links, visible focus styles, works at phone width, respects reduced-motion settings.

## Repository layout

```
.
├── index.html                  # the directory (HTML, CSS and JS in one file)
├── about.html                  # the About page
├── prices.json                 # all tools, plans and prices
├── README.md
├── requirements.txt            # Python packages for the optional updater
├── updater/
│   └── update_prices.py        # optional: reads pricing pages and refreshes prices.json
└── .github/workflows/
    └── update.yml              # optional: runs the updater every 2 days
```

## How prices are kept current

There are two ways to update `prices.json`:

1. **By hand.** Edit the tool's entry (plan names, `"p"` prices, `"from"` lowest monthly price, `"free"` text), set `"updated"` at the top of the file, and commit.
2. **Automatically (optional).** The updater script visits each tool's `pricing_url`, asks an AI model to read the plans and limits, and writes the changes. It runs every 2 days through GitHub Actions. It needs an `ANTHROPIC_API_KEY` repository secret. Until that secret is added, the scheduled run is disabled or will fail, and prices are updated by hand.

The updater never overwrites a price it cannot read, and it keeps any change that moves a lowest price by more than 3x for review. Every change is a Git commit, so any update can be undone from the history.

## Data format

Each tool in `prices.json`:

```json
{
  "name": "Example Tool",
  "cat": "image",
  "url": "https://example.com",
  "pricing_url": "https://example.com/pricing",
  "does": "One sentence on what the tool is good for.",
  "free": "What the free plan includes. Empty text means no free plan.",
  "plans": [
    { "n": "Pro", "p": "$20/mo" },
    { "n": "Max", "p": "$60/mo" }
  ],
  "from": 20,
  "last_checked": "2026-10-29"
}
```

| Field | Meaning |
|---|---|
| `cat` | One of the keys in `categories` at the top of the file |
| `free` | Free-plan limits. Empty text means the tool is shown as paid-only |
| `plans` | Paid plans as shown on the vendor's pricing page |
| `from` | Lowest paid monthly price in USD, or `null` if there is none |
| `pricing_url` | The page the updater reads for this tool |
| `last_checked` | The date the entry was last checked against the vendor |

## Run it locally

Opening `index.html` by double-clicking works, because the page includes a built-in copy of the data. For the live data, serve the folder:

```bash
python -m http.server 8000
```

Then open <http://localhost:8000>.

## Run the updater (optional)

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key-here

python updater/update_prices.py --dry-run        # preview changes, write nothing
python updater/update_prices.py --only Claude    # test a single tool
python updater/update_prices.py                  # update everything
```

| Setting | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | none, required | Lets the updater read pricing pages with an AI model |
| `ATLAS_MODEL` | `claude-haiku-5-5` | Which model reads the pages |

## Deploy your own copy

1. Copy this repository to your own GitHub account. Use a public repository for free GitHub Pages.
2. Turn on the site: **Settings > Pages > Source: Deploy from a branch**, branch `main`, folder `/ (root)`.
3. Optional: add `ANTHROPIC_API_KEY` under **Settings > Secrets and variables > Actions**, then run **Actions > Update prices > Run workflow**.

## Adding or fixing a tool

- **Add a tool:** add an entry to `prices.json` in the format above. Add a built-in copy only if you also regenerate it; the page still reads the live file when it is served.
- **Fix a price:** edit the entry, check it on the vendor's page, and set `last_checked`.
- **A vendor loads prices with JavaScript:** a simple download can't read those prices, so check them by hand and set `pricing_url` to the page that shows plain text.

## Limitations

- Prices are checked against vendor pages. Some are promotional, yearly-only, or set per seat, and the site shows what each page states.
- Prices are in USD per month unless a plan says otherwise. Taxes, regional prices and promotions vary.
- A tool is shown as paid-only when no free plan was found. It may still offer a trial.
- Open-source coding tools are free to install, but you pay your chosen AI provider for usage.
- The list is a curated snapshot. New tools and shutdowns are added by hand.

## Disclaimer

This is an independent directory. It is not affiliated with, endorsed by, or sponsored by any of the listed tools or companies. Product names belong to their owners. Always confirm current prices on the vendor's own website before you pay.
