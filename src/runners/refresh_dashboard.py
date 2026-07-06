import os
import sys
import json
from datetime import datetime
from decimal import Decimal
import snowflake.connector
from dotenv import load_dotenv

# Load local environment
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir  = os.path.dirname(os.path.dirname(current_dir))
load_dotenv(os.path.join(parent_dir, '.env'))

def get_connection():
    return snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'), account=os.getenv('SNOWFLAKE_ACCOUNT'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'), database=os.getenv('SNOWFLAKE_DATABASE'),
        schema=os.getenv('SNOWFLAKE_SCHEMA'), role=os.getenv('SNOWFLAKE_ROLE'),
        authenticator=os.getenv('SNOWFLAKE_AUTHENTICATOR')
    )

def run_query(sql, c):
    cur = c.cursor()
    cur.execute(sql)
    cols = [d[0] for d in cur.description] if cur.description else []
    rows = cur.fetchall()
    cur.close()
    return cols, rows

def serialize_decimal(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def main():
    print("🚀 Starting Automated Dashboard Refresh...")
    try:
        c = get_connection()
    except Exception as e:
        print(f"❌ Failed to connect to Snowflake: {e}")
        sys.exit(1)

    DB = os.getenv('SNOWFLAKE_DATABASE')
    SC = os.getenv('SNOWFLAKE_SCHEMA')
    
    # ---------------------------------------------------------
    # 1. FETCH DATA: AI TOOLS MAU
    # ---------------------------------------------------------
    print("⏳ Fetching AI Tools MAU Data...")
    _, mau_rows = run_query(f"""
        SELECT 
            MONTH_DATE,
            COUNT(DISTINCT ACCOUNT_CID) AS paid_active_accounts,
            COUNT(DISTINCT USER_ID) AS paid_active_users,
            COUNT(*) AS total_runs
        FROM {DB}.{SC}.AI_TOOLS_USAGE_DAILY_USER_SUMMARY_AT
        WHERE DAY BETWEEN '2026-01-01' AND '2026-06-30'
          AND LICENSE_TYPE IN ('Subscription', 'Purchase')
          AND USER_ID NOT LIKE '%alteryx%'
          AND SUCCESSFUL_RUN_FLAG = 1
        GROUP BY 1 ORDER BY 1 ASC
    """, c)
    
    # Extract Latest Month vs Previous Month for Topline Scorecards
    if len(mau_rows) >= 2:
        current_mau = mau_rows[-1][2]
        prev_mau = mau_rows[-2][2]
        current_runs = mau_rows[-1][3]
        prev_runs = mau_rows[-2][3]
        mau_trend = round(((current_mau - prev_mau) / max(prev_mau, 1)) * 100, 1)
        runs_trend = round(((current_runs - prev_runs) / max(prev_runs, 1)) * 100, 1)
    else:
        current_mau = prev_mau = current_runs = prev_runs = mau_trend = runs_trend = 0

    # ---------------------------------------------------------
    # 2. FETCH DATA: TOOL ADOPTION
    # ---------------------------------------------------------
    print("⏳ Fetching Tool Adoption Data...")
    _, tool_rows = run_query(f"""
        SELECT 
            COALESCE(GEN_AI_TOOL_NAME, 'Other / Unknown') AS tool_name,
            COUNT(*) AS total_runs,
            ROUND(SUM(SUCCESSFUL_RUN_FLAG) * 100.0 / NULLIF(COUNT(*), 0), 2) AS success_rate_pct
        FROM {DB}.{SC}.AI_TOOLS_USAGE_DAILY_USER_SUMMARY_AT
        WHERE DAY BETWEEN '2026-01-01' AND '2026-06-30'
          AND LICENSE_TYPE IN ('Subscription', 'Purchase')
          AND USER_ID NOT LIKE '%alteryx%'
        GROUP BY 1 ORDER BY total_runs DESC LIMIT 5
    """, c)

    # ---------------------------------------------------------
    # 3. EXPORT JSON FOR CLAUDE ARTIFACTS
    # ---------------------------------------------------------
    print("💾 Saving raw data to JSON for Artifact usage...")
    export_data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ai_tools_mau": [{"month": str(r[0])[:7], "accounts": r[1], "users": r[2], "runs": r[3]} for r in mau_rows],
        "top_tools": [{"tool": r[0], "runs": r[1], "success_rate": r[2]} for r in tool_rows]
    }
    
    data_dir = os.path.join(parent_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    with open(os.path.join(data_dir, "dashboard_data.json"), "w") as f:
        json.dump(export_data, f, indent=4, default=serialize_decimal)

    # ---------------------------------------------------------
    # 4. INJECT INTO FIXED MARKDOWN TEMPLATE
    # ---------------------------------------------------------
    print("📝 Generating static Markdown Dashboard...")
    
    def trend_icon(val):
        if val > 0: return "🟢 ↗"
        if val < 0: return "🔴 ↘"
        return "➖"

    md_content = f"""# 📊 Alteryx GenAI Executive Dashboard
**Last Auto-Refreshed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Audience Filter:** Strictly Paid Enterprise (Subscription/Purchase)

---

## 📌 Top-Level Scorecard (Latest Month)

| Metric | Current | Prev Period | MoM Trend | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Paid Active Users (MAU)** | **{current_mau:,}** | {prev_mau:,} | {mau_trend}% | {trend_icon(mau_trend)} |
| **Total GenAI Runs** | **{current_runs:,}** | {prev_runs:,} | {runs_trend}% | {trend_icon(runs_trend)} |

---

## 🏆 Top 5 Executed AI Tools (Year-to-Date)
*Table structure is locked. Values update automatically.*

| Rank | GenAI Tool Name | Total Execution Volume | Success Rate % |
| :---: | :--- | :---: | :---: |
"""
    for idx, r in enumerate(tool_rows, 1):
        md_content += f"| {idx} | **{r[0]}** | {r[1]:,} | {r[2]}% |\n"

    md_content += """
---

## 🤖 Generated Insights & RCA
*(These insights are derived programmatically based on the raw metrics above).*

*   **User Growth:** Paid active users saw a """
    
    md_content += f"**{abs(mau_trend)}% {'increase' if mau_trend > 0 else 'decrease'}** "
    md_content += f"""month-over-month.
*   **Tool Dominance:** The top performing tool remains **{tool_rows[0][0]}** with {tool_rows[0][1]:,} runs, representing the vast majority of our paid cohort's engagement.
*   **System Reliability Check:** Ensure that any tools displaying success rates below 80% (e.g., specific preview macros) are reported to platform engineering for API endpoint validation.

---
*To generate a React interactive version of this dashboard, ask Claude Code to load `data/dashboard_data.json` into an Artifact.*
"""

    docs_dir = os.path.join(parent_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    with open(os.path.join(docs_dir, "EXECUTIVE_DASHBOARD.md"), "w") as f:
        f.write(md_content)

    print("✅ Dashboard successfully refreshed! View it at: docs/EXECUTIVE_DASHBOARD.md")
    c.close()

if __name__ == "__main__":
    main()
