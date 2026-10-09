#!/usr/bin/env python3
"""Refresh prices.json by reading each vendor's pricing page.

For every tool in prices.json:
  1. download its pricing page (pricing_url),
  2. ask an AI model to extract free-plan limits and paid plans,
  3. check the answer, and only then update the entry.

Safety rules (a bad update is worse than an old price):
  - If the page cannot be fetched or has no readable prices, the old entry is kept
    and the tool is listed under "Needs review".
  - If a price moves by more than 3x, the old entry is kept and flagged.
  - Nothing is written unless something really changed.

Usage:
  python updater/update_prices.py                 # all tools
  python updater/update_prices.py --only Claude   # one tool (name match)
  python updater/update_prices.py --dry-run       # show changes, write nothing
Needs ANTHROPIC_API_KEY in the environment.
"""
import argparse
import datetime
import json
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRICES = os.path.join(ROOT, "prices.json")
REPORT = os.path.join(ROOT, "changes.md")
MODEL = os.environ.get("ATLAS_MODEL", "claude-haiku-5-5")
MAX_PAGE_CHARS = 30000
MAX_JUMP = 3.0  # flag any price that moves by more than this factor
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AI-Tool-Atlas-updater/1.0)"}

PROMPT = """You maintain a directory of AI tools. Read the pricing page text below for "{name}" and report what the page itself says. Do not use outside knowledge.

Current entry (may be outdated):
{current}

Return ONLY one JSON object, no other text:
{{
  "status": "ok" or "unclear",
  "free": "one short sentence on the free plan's limits, or an empty string if the page shows no free plan",
  "plans": [{{"n": "plan name", "p": "price as shown, e.g. $20 or $12 (billed yearly)"}}],
  "from": lowest paid monthly price in USD as a number, or null if there is none or it is not monthly USD,
  "evidence": "a short quote from the page that supports the main price"
}}

Rules:
- Use "unclear" if the text has no pricing (for example the page needs JavaScript or a login).
- Prices per month in USD. If only yearly is shown, say so in "p".
- Keep at most 6 plans, cheapest first. Keep names short.
- Never invent a plan or a price that is not in the text.

PAGE TEXT:
{text}
"""


def fetch_text(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer"]):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ")).strip()
    return text[:MAX_PAGE_CHARS]


def ask_model(client, name, current, text):
    msg = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        messages=[{"role": "user", "content": PROMPT.format(
            name=name, current=json.dumps(current, ensure_ascii=False), text=text)}],
    )
    out = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    m = re.search(r"\{.*\}", out, re.S)
    if not m:
        raise ValueError("model did not return JSON")
    return json.loads(m.group(0))


def clean(result):
    """Validate the model's answer. Returns a clean dict or raises ValueError."""
    if result.get("status") != "ok":
        raise ValueError("page had no clear pricing")
    free = result.get("free", "")
    if not isinstance(free, str) or len(free) > 220:
        raise ValueError("bad free text")
    plans = []
    for p in result.get("plans", [])[:6]:
        n, pr = str(p.get("n", "")).strip(), str(p.get("p", "")).strip()
        if not n or not pr or len(n) > 80 or len(pr) > 80:
            raise ValueError("bad plan entry")
        plans.append({"n": n, "p": pr})
    frm = result.get("from")
    if frm is not None:
        if not isinstance(frm, (int, float)) or frm < 0 or frm > 10000:
            raise ValueError("bad 'from' price")
    if not plans and not free:
        raise ValueError("no plans and no free plan")
    return {"free": free.strip(), "plans": plans, "from": frm}


def describe(old, new):
    parts = []
    if (old["free"] or "") != new["free"]:
        parts.append("free plan: %r -> %r" % (old["free"], new["free"]))
    if old["from"] != new["from"]:
        parts.append("lowest paid price: %s -> %s" % (old["from"], new["from"]))
    if old["plans"] != new["plans"]:
        o = ", ".join("%s %s" % (p["n"], p["p"]) for p in old["plans"]) or "none"
        n = ", ".join("%s %s" % (p["n"], p["p"]) for p in new["plans"]) or "none"
        parts.append("plans: %s -> %s" % (o, n))
    return "; ".join(parts)


def big_jump(old, new):
    a, b = old["from"], new["from"]
    if a and b and (b / a > MAX_JUMP or a / b > MAX_JUMP):
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="only tools whose name contains this text")
    args = ap.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")
    import anthropic
    client = anthropic.Anthropic()

    with open(PRICES, encoding="utf-8") as f:
        data = json.load(f)

    today = datetime.date.today().isoformat()
    changed, review, ok_same = [], [], 0

    for tool in data["tools"]:
        name = tool["name"]
        if args.only and args.only.lower() not in name.lower():
            continue
        current = {"free": tool["free"], "plans": tool["plans"], "from": tool["from"]}
        try:
            text = fetch_text(tool.get("pricing_url") or tool["url"])
            if len(text) < 300:
                raise ValueError("page text too short (probably needs JavaScript)")
            new = clean(ask_model(client, name, current, text))
        except Exception as e:  # keep old data on ANY problem
            review.append("%s: %s" % (name, e))
            print("REVIEW", name, "-", e)
            time.sleep(1)
            continue

        tool["last_checked"] = today
        if big_jump(current, new):
            review.append("%s: price moved more than %sx (%s -> %s); kept old value" % (
                name, MAX_JUMP, current["from"], new["from"]))
            print("REVIEW", name, "- big price jump")
            continue
        diff = describe(current, new)
        if diff:
            changed.append("**%s** - %s" % (name, diff))
            tool.update(new)
            print("CHANGED", name)
        else:
            ok_same += 1
            print("same   ", name)
        time.sleep(1)

    lines = ["# Price update %s" % today, ""]
    lines += ["## Changed (%d)" % len(changed)] + (["- " + c for c in changed] or ["- none"]) + [""]
    lines += ["## Needs review (%d)" % len(review)] + (["- " + r for r in review] or ["- none"]) + [""]
    lines += ["Unchanged: %d" % ok_same, ""]
    report = "\n".join(lines)
    print("\n" + report)

    if args.dry_run:
        print("(dry run: nothing written)")
        return
    if changed:
        data["updated"] = today
    with open(PRICES, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(report)


if __name__ == "__main__":
    main()
