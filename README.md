# AI Tool Atlas: self-updating

A directory of AI tools (free vs paid, with monthly prices) that refreshes itself every 2 days.

| File | What it is |
|---|---|
| `index.html` | The website. Reads `prices.json` when a visitor opens it. |
| `prices.json` | All tools, plans and prices. This is the only file the robot changes. |
| `updater/update_prices.py` | Visits each tool's pricing page and updates `prices.json`. |
| `.github/workflows/update.yml` | The schedule: runs the updater every 2 days, free on GitHub. |
| `changes.md` | Written on every run: what changed and what needs your eyes. |

## One-time setup (about 10 minutes)

1. **Create a GitHub account** (free) and a new **public repository**, for example `ai-tool-atlas`.
2. **Upload everything in this folder** to the repository (drag and drop on the repo page works). Keep the `.github` folder.
3. **Get an Anthropic API key** at console.anthropic.com and add a little credit. Reading about 59 pages every 2 days uses a small model; expect a few dollars a month at most.
4. In the repo: **Settings > Secrets and variables > Actions > New repository secret**. Name it `ANTHROPIC_API_KEY` and paste the key.
5. **Turn on the website:** Settings > Pages > Build and deployment > Source: *Deploy from a branch*, branch `main`, folder `/ (root)`. After a minute your site is live at `https://YOUR-NAME.github.io/ai-tool-atlas/`.
6. **Run the first update by hand:** Actions tab > *Update prices* > *Run workflow*. After that it runs by itself every 2 days.

Netlify or Vercel also work: connect the repo, no build command, publish directory `/`.

## First run: expect some "Needs review"

Each tool has a `pricing_url` in `prices.json`. Many of those were guessed as `<site>/pricing`, and some vendors load prices with JavaScript, which a simple page download cannot see. When that happens the robot keeps the old price and lists the tool in `changes.md` under *Needs review*. Fix it by editing that tool's `pricing_url` in `prices.json` to the page that shows the plans in plain text, then run again.

## Safety built in

- A page that cannot be read never overwrites a price.
- A lowest price that jumps by more than 3x is not applied; it is flagged instead.
- The site escapes all text and only links to `https://` addresses.
- Every change is a commit, so you can undo any update from the repo history.

## Run it on your own computer

```
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key
python updater/update_prices.py --dry-run          # preview, writes nothing
python updater/update_prices.py --only Claude      # test one tool
python -m http.server 8000                         # then open http://localhost:8000
```

Opening `index.html` by double-click will not work because browsers block loading `prices.json` from a file; use the small server above.

## Adding a tool

Add an entry to `prices.json` with `name`, `cat` (one of the keys in `categories`), `url`, `pricing_url`, `does`, `free` (empty text if no free plan), `plans` and `from`. The updater picks it up on the next run.

## Honest limits

The robot reads what each vendor's page says and a model extracts it, so an odd page layout can still produce a wrong or missing value. Skim `changes.md` after runs, especially the first few. The model name can be changed with the `ATLAS_MODEL` environment variable.
