---
name: refresh-dashboard
description: >
  Refresh a dashboard's numbers and insights from Snowflake WITHOUT changing its
  layout or design. Use when the user asks to "refresh the dashboard", "update the
  numbers", "refresh the data", "update the scorecard", or "pull the latest metrics".
  Regenerates the data only — the HTML template (layout, CSS, charts) is never edited.
  If more than one dashboard exists, ask which one to refresh first.
---

# Refresh Dashboard (numbers only)

Manual, interim refresh. Re-queries Snowflake, recomputes every metric, re-injects the
data into the dashboard's **fixed template**, and **re-publishes to the same hosted link**
so the shared URL shows the fresh numbers. Layout, styling, and chart structure stay
identical; only the numbers — and the insights/actions computed from them — change. The
hosted link never changes.

## Golden rule

**Never hand-edit numbers in the generated HTML, and never touch the template's layout/CSS
during a refresh.** A refresh = run the generator script, which swaps the injected
`const DASHBOARD_DATA = {…}` blob and nothing else. If the user wants a *design* change,
that's a different task (edit `dashboard_template.html`) — not this skill.

## Dashboard registry

Each refreshable dashboard = one generator script that reads a template and writes an
output HTML, plus a fixed hosted artifact URL it always re-publishes to. Current
dashboards in this repo:

| # | Dashboard | Generator | Template (layout — do not edit) | Output | Hosted link (re-publish target — keep stable) | Favicon |
|---|-----------|-----------|--------------------------------|--------|-----------------------------------------------|---------|
| 1 | Ask Alteryx — Copilot Adoption Scorecard | `refresh_dashboard.py` | `dashboard_template.html` | `ask_alteryx_dashboard.html` | `https://claude.ai/code/artifact/c59718dc-0d0f-4c15-938e-42362ce2b911` | 🤖📊 |

*(To add a dashboard later: give it its own generator + template + hosted URL, then add a row here.)*

## Steps

1. **Discover dashboards.** List candidates so the registry can't drift:
   ```bash
   ls -1 *_dashboard.html 2>/dev/null; echo "--- generators ---"; ls -1 refresh*dashboard*.py 2>/dev/null
   ```
   - If exactly **one** dashboard → use it, no need to ask.
   - If **more than one** → STOP and ask the user which dashboard to refresh (offer the
     names from the registry as options). Do not guess.

2. **Run that dashboard's generator** (this opens a browser SSO popup — tell the user to
   complete the login; it can take 10–30s):
   ```bash
   python3 refresh_dashboard.py --json
   ```
   The script re-queries Snowflake, rebuilds the data blob, and writes the output HTML by
   injecting data into the template. Filter the noisy connector warnings when showing output:
   ```bash
   python3 refresh_dashboard.py --json 2>&1 | grep -v -E "NotOpenSSLWarning|warnings.warn|urllib3|keyring|pip install|secure-local-storage|PythonDeprecation|boto3|aws.amazon|Initiating login|Going to open|browser window should"
   ```

3. **Verify the refresh succeeded.** Confirm the script printed `✅ Wrote …_dashboard.html`
   and echo the headline numbers it reports (adoption %, active users, etc.). If it errored:
   - `Injection marker not found` → someone edited the template's `const DASHBOARD_DATA = null;`
     line; restore it.
   - Snowflake auth/VPN error → see `SCHEDULER_SETUP.md` troubleshooting.

4. **Re-publish to the hosted link — ALWAYS (not optional).** A refresh only rewrites the
   local file; the hosted link keeps showing old numbers until it is re-published. So after a
   successful regenerate, immediately re-publish with the **`Artifact` tool**, passing the
   dashboard's **exact hosted URL from the registry** as `url=` so it redeploys to the *same
   link* (the link must never change). Keep `favicon` and `description` stable across redeploys.
   For dashboard #1:
   - `file_path`: `ask_alteryx_dashboard.html`
   - `url`: `https://claude.ai/code/artifact/c59718dc-0d0f-4c15-938e-42362ce2b911`
   - `favicon`: `🤖📊`
   - `label`: something like `refresh-<today>` (this only names the version, not the URL)

   Confirm the tool returns the **same** URL you passed in. If it returns a *different* URL, the
   `url=` was omitted — do not accept it; re-run with the registry URL. (Only skip re-publishing
   if the user explicitly says "local only / don't publish.")

   *(Optional) to eyeball the layout is intact after the data swap, screenshot headless first:*
   ```bash
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
     --window-size=1220,900 --screenshot=/tmp/dash_check.png --virtual-time-budget=3000 \
     "file://$(pwd)/ask_alteryx_dashboard.html"
   ```

5. **Report** what changed: the new headline figures, the "Generated at" timestamp, and confirm
   the hosted link is updated (same URL). Keep it short.

## Why layout is safe

- Design lives in `dashboard_template.html` (untouched by the generator).
- Data lives in a single injected `const DASHBOARD_DATA = {…}` object.
- KPIs, charts, **insights, and action items are all rendered in JS from that object**, so
  refreshing the data automatically re-ranks insights/actions — with zero layout drift.

## Re-render without hitting Snowflake

If the data was already pulled this session (`dashboard_data.json` exists) and you only need to
regenerate the HTML from the saved data (e.g. after confirming a value), you can skip the SSO round-trip:
```bash
python3 -c "import json, refresh_dashboard as rd; rd.render(json.load(open('dashboard_data.json')))"
```
