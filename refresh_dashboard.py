#!/usr/bin/env python3
"""
🔄 Ask Alteryx Dashboard — Data Refresh & Generator  (AARRR scorecard edition)

Pulls the full Ask Alteryx (Copilot) paid-tier metric set from Snowflake, organised
around the org's three-pillar framework — Acquisition → Activation → Retention —
assembles a single JSON data blob, and injects it into `dashboard_template.html` to
produce `ask_alteryx_dashboard.html`. The DESIGN never changes; only the numbers
(and the data-driven insights / actions) refresh.

Data lineage (source per metric):
  Acquisition · Eligible Accounts   → METRIC_STORE.COPILOT_ELIGIBLE_ACCOUNT_FUNNEL (monthly)
  Acquisition · Eligible Users      → METRIC_STORE.COPILOT_ELIGBLE_USERS
  Activation  · Activity funnels    → live COPILOT_ACTIVITY_USAGE_AT (reconciles to scorecard)
  Retention   · Return rates        → METRIC_STORE.COPILOT_7_15 / 30_60_RETENTION_RATE
  Retention   · Mapped workflow runs→ METRIC_STORE.COPILOT_DESIGNER_WORKFLOW_PCT_AT

Auth: browser SSO by default; set SNOWFLAKE_PRIVATE_KEY_PATH for unattended key-pair.
Usage: python3 refresh_dashboard.py [--json]
"""

import os
import sys
import json
import datetime
import snowflake.connector
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "dashboard_template.html")
OUTPUT = os.path.join(HERE, "ask_alteryx_dashboard.html")
DATA_JSON = os.path.join(HERE, "dashboard_data.json")

PAID = "LICENSE_TYPE = 'Purchase' AND USER_TYPE = 'aacp' AND USER_EMAIL NOT LIKE '%alteryx.com%'"
MS = "DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE"
TABLE = f"{MS}.COPILOT_ACTIVITY_USAGE_AT"

TARGET_ADOPTION = 40.0   # % — official target
TARGET_RETENTION = 30.0  # % — official target
ENGAGED_MIN_DAYS = 3     # "engaged" = active on ≥ this many distinct days


# ----------------------------------------------------------------------------- connection
def get_connection():
    load_dotenv(os.path.join(HERE, ".env"))
    params = dict(
        user=os.getenv("SNOWFLAKE_USER"), account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"), database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"), role=os.getenv("SNOWFLAKE_ROLE"),
    )
    key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")
    if key_path and os.path.exists(key_path):
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        with open(key_path, "rb") as f:
            pkey = serialization.load_pem_private_key(
                f.read(),
                password=(os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE") or "").encode() or None,
                backend=default_backend())
        params["private_key"] = pkey.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption())
        print("🔑 Key-pair (JWT) auth — unattended mode.")
    else:
        params["authenticator"] = os.getenv("SNOWFLAKE_AUTHENTICATOR", "externalbrowser")
        print("🌐 Browser SSO auth — interactive mode.")
    return snowflake.connector.connect(**params)


def f1(x):  # Decimal/None -> float
    return float(x) if x is not None else 0.0


# ----------------------------------------------------------------------------- queries
def fetch_metrics(cur):
    d = {}

    # ============ ACQUISITION ============
    # Eligible Accounts funnel — canonical monthly snapshot table (+ history)
    cur.execute(f"""
        SELECT MONTH_YEAR, TOTAL_AYX_ACCOUNTS, TOTAL_AYX1_ACCOUNTS,
               ACCOUNTS_WITH_ENT_AND_PRO, COPILOT_ELIGIBLE_ACCOUNTS
        FROM {MS}.COPILOT_ELIGIBLE_ACCOUNT_FUNNEL ORDER BY MONTH_YEAR
    """)
    rows = cur.fetchall()
    latest = rows[-1]
    acc_trend = [{"month": r[0].strftime("%Y-%m"), "eligible": r[4]} for r in rows]
    acc_funnel = [
        {"label": "Total AYX accounts", "value": latest[1]},
        {"label": "AYX1 deployed", "value": latest[2]},
        {"label": "Enterprise & Professional", "value": latest[3]},
        {"label": "Ask Alteryx eligible", "value": latest[4]},
    ]

    # Eligible Users funnel — canonical single row
    cur.execute(f"""
        SELECT ENTERPRISE_PRO_USERS, COPILOT_ENABLED_USERS, ELIGIBLE_USERS_2025_2, COPILOT_ELIGIBLE_USERS
        FROM {MS}.COPILOT_ELIGBLE_USERS
    """)
    eu = cur.fetchone()
    eligible_users = eu[3]
    users_funnel = [
        {"label": "Enterprise & Professional users", "value": eu[0]},
        {"label": "Ask Alteryx-enabled users", "value": eu[1]},
        {"label": "Users on v25.2+", "value": eu[2], "flag": "Version telemetry gap (TMM-516)"},
        {"label": "Eligible users (Desktop-activated)", "value": eu[3]},
    ]
    d["acquisition"] = {"accounts_funnel": acc_funnel, "users_funnel": users_funnel,
                        "accounts_trend": acc_trend, "eligible_users": eligible_users,
                        "eligible_accounts": latest[4], "latest_month": latest[0].strftime("%Y-%m")}

    # ============ ACTIVATION ============  (live base table — reconciles to scorecard)
    cur.execute(f"""
        SELECT
          COUNT(DISTINCT CASE WHEN USER_EMAIL IS NOT NULL THEN USER_ID_RAW END),
          COUNT(DISTINCT CASE WHEN CHAT_ID IS NOT NULL THEN USER_ID_RAW END),
          COUNT(DISTINCT CASE WHEN CHAT_ID IS NOT NULL AND WORKFLOW_ID IS NOT NULL AND WORKFLOW_ID<>'' THEN USER_ID_RAW END)
        FROM {TABLE} WHERE {PAID}
    """)
    uo, ua, uw = cur.fetchone()
    cur.execute(f"""
        SELECT COUNT(*) FROM (
          SELECT USER_ID_RAW FROM {TABLE} WHERE {PAID} AND CHAT_ID IS NOT NULL
          GROUP BY USER_ID_RAW HAVING COUNT(DISTINCT CONV_CREATED_DATE) >= {ENGAGED_MIN_DAYS})
    """)
    ue = cur.fetchone()[0]

    cur.execute(f"""
        SELECT
          COUNT(DISTINCT BILLING_ACCOUNT_ID_RAW),
          COUNT(DISTINCT CASE WHEN CHAT_ID IS NOT NULL THEN BILLING_ACCOUNT_ID_RAW END),
          COUNT(DISTINCT CASE WHEN CHAT_ID IS NOT NULL AND WORKFLOW_ID IS NOT NULL AND WORKFLOW_ID<>'' THEN BILLING_ACCOUNT_ID_RAW END)
        FROM {TABLE} WHERE {PAID}
    """)
    ao, aa, aw = cur.fetchone()
    cur.execute(f"""
        SELECT COUNT(*) FROM (
          SELECT BILLING_ACCOUNT_ID_RAW FROM {TABLE} WHERE {PAID} AND CHAT_ID IS NOT NULL
          GROUP BY BILLING_ACCOUNT_ID_RAW HAVING COUNT(DISTINCT CONV_CREATED_DATE) >= {ENGAGED_MIN_DAYS})
    """)
    ae = cur.fetchone()[0]

    adoption_pct = round(ua * 100.0 / eligible_users, 2) if eligible_users else 0.0
    d["activation"] = {
        "users": {"onboarded": uo, "active": ua, "workflow": uw, "engaged": ue},
        "accounts": {"onboarded": ao, "active": aa, "workflow": aw, "engaged": ae},
        "adoption": {"active": ua, "eligible": eligible_users, "pct": adoption_pct, "target": TARGET_ADOPTION},
    }

    # Monthly activation trend
    cur.execute(f"""
        SELECT TO_CHAR(DATE_TRUNC('month', CONV_CREATED_DATE),'YYYY-MM'),
               COUNT(DISTINCT USER_ID_RAW), COUNT(DISTINCT CONVERSATION_ID), COUNT(DISTINCT CHAT_ID)
        FROM {TABLE} WHERE {PAID} AND CHAT_ID IS NOT NULL AND CONV_CREATED_DATE IS NOT NULL
        GROUP BY 1 ORDER BY 1
    """)
    d["activation"]["monthly"] = [{"month": m, "active": a, "conversations": c, "messages": ms}
                                  for m, a, c, ms in cur.fetchall()]

    # ============ RETENTION ============  (canonical curated tables)
    cur.execute(f"SELECT TOTAL_USERS, RETURNING_USERS_7_15D, RETURNING_RATE_PCT FROM {MS}.COPILOT_7_15_RETENTION_RATE")
    den, num, pct = cur.fetchone()
    d["retention"] = {"r7_15": {"den": den, "num": num, "pct": round(f1(pct) * 100, 2), "target": TARGET_RETENTION}}
    cur.execute(f"SELECT TOTAL_USERS, RETURNING_USERS_30_60D, RETURNING_RATE_PCT FROM {MS}.COPILOT_30_60_RETENTION_RATE")
    den, num, pct = cur.fetchone()
    d["retention"]["r30_60"] = {"den": den, "num": num, "pct": round(f1(pct) * 100, 2), "target": TARGET_RETENTION}
    cur.execute(f"SELECT COPILOT_MAPPED_WORKFLOW_RUNS, COPILOT_ACTIVE_USER_WORKFLOW_RUN, COPILOT_PCT_WORKFLOW_RUNS FROM {MS}.COPILOT_DESIGNER_WORKFLOW_PCT_AT")
    mapped, total, mpct = cur.fetchone()
    d["retention"]["mapped_runs"] = {"mapped": mapped, "total": total, "pct": round(f1(mpct), 2)}

    # ============ ENGAGEMENT + STICKINESS ============
    cur.execute(f"SELECT COUNT(DISTINCT CONVERSATION_ID), COUNT(DISTINCT CHAT_ID) FROM {TABLE} WHERE {PAID} AND CHAT_ID IS NOT NULL")
    convs, msgs = cur.fetchone()
    d["engagement"] = {"conversations": convs, "messages": msgs,
                       "msgs_per_active": round(msgs / (ua or 1), 1), "convs_per_active": round(convs / (ua or 1), 1)}
    cur.execute(f"""
        WITH ud AS (SELECT DISTINCT USER_ID_RAW k, CAST(CONV_CREATED_DATE AS DATE) dt FROM {TABLE}
          WHERE {PAID} AND CHAT_ID IS NOT NULL AND CONV_CREATED_DATE >= DATEADD(day,-28,CURRENT_DATE()))
        SELECT COUNT(DISTINCT k), COUNT(*)/28.0,
          (SELECT COUNT(*) FROM (SELECT k FROM ud GROUP BY k HAVING COUNT(DISTINCT dt)>=5)) FROM ud
    """)
    mau, avg_dau, power = cur.fetchone()
    d["stickiness"] = {"mau": mau or 0, "avg_dau": round(f1(avg_dau), 1), "power": power,
                       "pct": round(f1(avg_dau) * 100 / mau, 2) if mau else 0.0}

    # ============ SEGMENTS ============
    cur.execute(f"""
        SELECT COALESCE(ACCOUNT_EDITION,'Unknown'),
          COUNT(DISTINCT CASE WHEN USER_EMAIL IS NOT NULL THEN USER_ID_RAW END),
          COUNT(DISTINCT CASE WHEN CHAT_ID IS NOT NULL THEN USER_ID_RAW END)
        FROM {TABLE} WHERE {PAID} GROUP BY 1 ORDER BY 3 DESC
    """)
    d["segments"] = {"by_edition": [{"edition": e, "onboarded": o, "active": a} for e, o, a in cur.fetchall()]}
    cur.execute(f"""
        SELECT COALESCE(MAXIMUM_RAW_PRODUCT_VERSION,'Unknown'),
          COUNT(DISTINCT CASE WHEN CHAT_ID IS NOT NULL THEN USER_ID_RAW END)
        FROM {TABLE} WHERE {PAID} GROUP BY 1 ORDER BY 2 DESC LIMIT 8
    """)
    d["segments"]["by_version"] = [{"version": v, "active": a} for v, a in cur.fetchall()]

    return d


# ----------------------------------------------------------------------------- assemble + render
def build_data():
    conn = get_connection()
    try:
        cur = conn.cursor()
        print("📊 Querying Snowflake …")
        d = fetch_metrics(cur)
        cur.close()
    finally:
        conn.close()
    now = datetime.datetime.now()
    cur_month = now.strftime("%Y-%m")
    for m in d["activation"].get("monthly", []):
        m["partial"] = (m["month"] == cur_month)
    d["generated_at"] = now.isoformat(timespec="seconds")
    d["generated_display"] = now.strftime("%-d %b %Y, %-I:%M %p")
    d["as_of"] = now.strftime("%-d %b %Y")
    d["targets"] = {"adoption": TARGET_ADOPTION, "retention": TARGET_RETENTION}
    d["scope"] = {"tier": "Paid users", "filters": "Purchase · aacp · non-internal",
                  "source": "METRIC_STORE (canonical) + COPILOT_ACTIVITY_USAGE_AT (live)"}
    return d


def render(data):
    with open(TEMPLATE, "r") as f:
        html = f.read()
    marker = "const DASHBOARD_DATA = null;"
    if marker not in html:
        print(f"❌ Injection marker not found: `{marker}`", file=sys.stderr); sys.exit(1)
    html = html.replace(marker, f"const DASHBOARD_DATA = {json.dumps(data, separators=(',', ':'))};", 1)
    with open(OUTPUT, "w") as f:
        f.write(html)
    print(f"✅ Wrote {OUTPUT}")


def main():
    data = build_data()
    render(data)
    if "--json" in sys.argv:
        with open(DATA_JSON, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"✅ Wrote {DATA_JSON}")
    a = data["activation"]
    print(f"\n   Adoption {a['adoption']['pct']}% (target {a['adoption']['target']}%)")
    print(f"   Users: onboarded {a['users']['onboarded']:,} · active {a['users']['active']:,} · "
          f"workflow {a['users']['workflow']:,} · engaged {a['users']['engaged']:,}")
    print(f"   Accounts: onboarded {a['accounts']['onboarded']:,} · active {a['accounts']['active']:,} · "
          f"workflow {a['accounts']['workflow']:,} · engaged {a['accounts']['engaged']:,}")
    print(f"   Refreshed {data['generated_display']}")


if __name__ == "__main__":
    main()
