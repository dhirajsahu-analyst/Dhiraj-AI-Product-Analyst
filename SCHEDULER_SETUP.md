# 🔄 Ask Alteryx Dashboard — Refresh & 24h Auto-Update

The dashboard **design is fixed**. Only the *numbers* (and the data-driven insights &
action items) refresh. Three ways to refresh, from manual to fully automatic.

## How it fits together

```
Snowflake  ──▶  refresh_dashboard.py  ──▶  dashboard_data.json
(COPILOT_        (runs all queries,          +
 ACTIVITY_        computes metrics)     ask_alteryx_dashboard.html   ◀── you view this
 USAGE_AT)                              (design from dashboard_template.html,
                                         numbers injected as a JS data blob)

serve_dashboard.py   →  the “Refresh data” button in the page hits /api/refresh
launchd job          →  runs refresh_dashboard.py every 24h, unattended
```

- **`dashboard_template.html`** — the design + all rendering logic (never changes).
- **`refresh_dashboard.py`** — pulls data, injects it into the template → `ask_alteryx_dashboard.html`.
- **`serve_dashboard.py`** — local server so the in-page button can refresh live.
- Insights & action items are **computed from the numbers in JS**, so they update on every refresh with no design change.

---

## 1. Manual refresh (simplest)

```bash
python3 refresh_dashboard.py
```
Opens a browser SSO popup, queries Snowflake, rewrites `ask_alteryx_dashboard.html`. Open the file.

## 2. The in-page "Refresh data" button (live)

```bash
python3 serve_dashboard.py         # → http://localhost:8000
```
Open `http://localhost:8000` and click **Refresh data**. It calls `/api/refresh`,
re-queries Snowflake, and re-renders in place. (With SSO auth, each click opens a
popup — configure key-pair auth below to make it popup-free.)

> Opening the raw `.html` file directly (file://) still shows the last generated
> numbers, but the button needs the server to reach Snowflake — it'll tell you so.

---

## 3. Automatic every 24h — the "without fail" setup

Two parts: **(A)** popup-free auth, then **(B)** the scheduled job.

### A. Key-pair auth (required for unattended runs)

An unattended job **cannot** complete browser SSO. Switch to Snowflake key-pair auth:

```bash
# 1. Generate a key pair
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out ~/.snowflake/ayx_key.p8 -nocrypt
openssl rsa -in ~/.snowflake/ayx_key.p8 -pubout -out ~/.snowflake/ayx_key.pub

# 2. Register the PUBLIC key on your Snowflake user (run in a Snowflake worksheet;
#    paste the pub key body without the BEGIN/END lines):
#    ALTER USER "AYX105566@ALTERYX.COM" SET RSA_PUBLIC_KEY='MIIB...';

# 3. Point .env at the PRIVATE key
echo 'SNOWFLAKE_PRIVATE_KEY_PATH=/Users/ayx105566/.snowflake/ayx_key.p8' >> .env

# 4. (once) install the crypto dependency
python3 -m pip install --user cryptography
```

`refresh_dashboard.py` auto-detects `SNOWFLAKE_PRIVATE_KEY_PATH` and uses JWT auth
(no popup). Without it, it falls back to browser SSO — so **manual runs still use SSO,
scheduled runs use the key**. Verify:

```bash
python3 refresh_dashboard.py     # should print "🔑 Using key-pair (JWT) auth"
```

> **VPN note:** if Snowflake requires corporate VPN, the machine must be on VPN when
> the job fires. A laptop that's asleep/offline at 06:00 will run the job on next wake
> (launchd catches the missed run).

### B. Install the launchd job (macOS)

The paths in `com.alteryx.askalteryx-dashboard.plist` are already set for this repo.

```bash
# copy into your LaunchAgents and load it
cp "com.alteryx.askalteryx-dashboard.plist" ~/Library/LaunchAgents/
launchctl load  ~/Library/LaunchAgents/com.alteryx.askalteryx-dashboard.plist

# check it's registered / run once now to test
launchctl list | grep askalteryx
launchctl start com.alteryx.askalteryx-dashboard
tail -f refresh.log
```

Change the time by editing `Hour`/`Minute` in the plist, then `unload` + `load` again.
To remove:

```bash
launchctl unload ~/Library/LaunchAgents/com.alteryx.askalteryx-dashboard.plist
```

### Alt: plain cron

```bash
crontab -e
# refresh every day at 06:00
0 6 * * * /Users/ayx105566/Desktop/AI\ Github\ test/Dhiraj-AI-Product-Analyst/run_refresh.sh
```

---

## Why not the Claude cloud scheduler / routines?

Claude Code's scheduled **cloud agents** run in Anthropic's cloud — they have **no
access to your corporate VPN or Snowflake SSO**, so they can't query this data. The
refresh must run on a machine that can reach Snowflake. `launchd`/`cron` on your Mac
(or any always-on host / CI runner with the key) is the right tool. Claude Code is
perfect for *building and changing* the dashboard; the recurring data pull is a plain
local scheduled job.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Button says "needs the local server" | Start `serve_dashboard.py`, open `localhost:8000` (not the file://). |
| Scheduled job did nothing | `tail refresh.log`; ensure key-pair auth is set (no popup possible unattended). |
| `Injection marker not found` | Don't edit the `const DASHBOARD_DATA = null;` line in the template. |
| Numbers look stale | Re-run `python3 refresh_dashboard.py`; check `dashboard_data.json` timestamp. |
