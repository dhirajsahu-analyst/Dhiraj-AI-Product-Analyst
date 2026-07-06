# 📊 Product Analytics Reference Guide: AI Tools Suite

This guide serves as the absolute, verified reference manual and dictionary for the **Alteryx AI Tools Suite** product analytics. It combines the complete schema catalogs, validated Snowflake SQL queries, and the diagnostic RCA playbook of all discovered telemetry anomalies.

---

## 🏛️ Section 1: Business Definition & Sourcing
*   **Business Definition:** AI Tools measures active user executions of GenAI features (Prompt, LLM Override, Precision Match, etc.) within Alteryx Designer Desktop and Server.
*   **Telemetry Table:** `DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.AI_TOOLS_USAGE_DAILY_USER_SUMMARY_AT`
*   **Standard Filter Requirements (Paid Only):**
    - `LICENSE_TYPE IN ('Subscription', 'Purchase')` (Filters strictly for paying enterprise tiers).
    - `USER_ID NOT LIKE '%alteryx%'` (Purges internal employee test executions).

---

## 📂 Section 2: Metadata Schema Catalog
Each record in `AI_TOOLS_USAGE_DAILY_USER_SUMMARY_AT` represents aggregated daily tool activity per user.

| Column Name | Data Type | Description |
| :--- | :---: | :--- |
| `DAY` | DATE | Local calendar activity date of the tool execution. |
| `MONTH_DATE` | DATE | First day of the reporting month. |
| `PAYLOAD_ID` | VARCHAR | Unique ID generated per execution (subject to co-firing duplicates). |
| `USER_ID` | VARCHAR | **Contains string Email Addresses** (e.g., `user@domain.com`). Unique user key. |
| `ACCOUNT_CID` | VARCHAR | 8-character Salesforce Customer ID (e.g., `A1234567`). Can be NULL. |
| `BILLING_ACCOUNT_ID` | VARCHAR | Raw corporate billing account locator key from the customer database. |
| `BILLING_ACCOUNT_NAME` | VARCHAR | Mapped customer account name in CRM. |
| `LICENSE_TYPE` | VARCHAR | User's license tier (e.g., `'Subscription'`, `'Purchase'`). |
| `GEN_AI_TOOL_NAME` | VARCHAR | Friendly tool name (e.g., `'Prompt'`, `'LLM Override'`, `'Invoice Extractor'`). |
| `WORKFLOW_ID` | VARCHAR | Unique ID of the Alteryx Designer workflow containing this GenAI tool. |
| `PRODUCT_NAME` | VARCHAR | Executing platform (e.g., `'Designer'`, `'Server'`). |
| `RUN_STATUS` | VARCHAR | Run outcome: `'Successful'` or `'Failed'`. |
| `SUCCESSFUL_RUN_FLAG` | NUMBER | `1` if successful, `0` otherwise. |
| `FAILED_RUN_FLAG` | NUMBER | `1` if failed, `0` otherwise. |
| `MESSAGE` | VARCHAR | Error message string if the run failed. |
| `ACTIVE_ACV` | NUMBER | Customer's active Annual Contract Value in USD. |

---

## 💻 Section 3: Validated & Tested SQL Queries (Paid Only)

*   **Rule for the Agent:** Whenever a user asks for any of the metrics below, **YOU MUST RUN THE CORRESPONDING QUERY EXACTLY AS IT IS WRITTEN HERE.** Do not rewrite, modify, or overcomplicate. These queries have been manually tested, verified, and return correct, uncorrupted numbers.

### Metric 1: Monthly Active Users (MAU) & Active Account Trend
```sql
SELECT 
    MONTH_DATE AS reporting_month,
    COUNT(DISTINCT ACCOUNT_CID) AS paid_active_accounts,
    COUNT(DISTINCT USER_ID) AS paid_active_users,
    COUNT(*) AS total_runs
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.AI_TOOLS_USAGE_DAILY_USER_SUMMARY_AT
WHERE DAY BETWEEN '2026-01-01' AND '2026-06-30'
  AND LICENSE_TYPE IN ('Subscription', 'Purchase')
  AND USER_ID NOT LIKE '%alteryx%'
  AND SUCCESSFUL_RUN_FLAG = 1
GROUP BY 1
ORDER BY 1 ASC;
```

### Metric 2: GenAI Suite Tool Adoption, Volume, and Success Rates
```sql
SELECT 
    COALESCE(GEN_AI_TOOL_NAME, 'Other / Unknown') AS tool_name,
    COUNT(DISTINCT ACCOUNT_CID) AS paid_active_accounts,
    COUNT(DISTINCT USER_ID) AS paid_active_users,
    COUNT(*) AS total_runs,
    ROUND(SUM(SUCCESSFUL_RUN_FLAG) * 100.0 / NULLIF(COUNT(*), 0), 2) AS success_rate_pct
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.AI_TOOLS_USAGE_DAILY_USER_SUMMARY_AT
WHERE DAY BETWEEN '2026-01-01' AND '2026-06-30'
  AND LICENSE_TYPE IN ('Subscription', 'Purchase')
  AND USER_ID NOT LIKE '%alteryx%'
GROUP BY 1
ORDER BY total_runs DESC;
```

---

## 🔍 Section 4: Diagnostics & Root Cause Analysis (RCA)

### Anomaly A: The 10x KPI Account Undercount (C1)
*   **The Issue:** June 2026 reports 46 users/39 accounts in executive summaries but 167 users/77 accounts in daily raw logs.
*   **The Root Cause:** Executive KPI tables are strictly filtered by:
    `WHERE LICENSE_TYPE = 'Subscription' AND SUCCESSFUL_RUN_FLAG = 1`
    This silently drops trial, partner (NFR), internal, and academic users, as well as subscription users with only failing runs.
*   **Verification SQL:**
```sql
SELECT 
    COUNT(DISTINCT USER_ID) AS raw_users,
    COUNT(DISTINCT CASE WHEN LICENSE_TYPE = 'Subscription' AND SUCCESSFUL_RUN_FLAG = 1 THEN USER_ID END) AS kpi_users
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.AI_TOOLS_USAGE_DAILY_USER_SUMMARY_AT
WHERE DAY BETWEEN '2026-06-01' AND '2026-06-30';
```

### Anomaly B: Duplicate Payload Ingestions (`SAME_TOOL_TRUE_DUP`)
*   **The Issue:** Over 2,000 duplicate rows exist in June 2026 where the exact same `PAYLOAD_ID` is ingested multiple times for the same tool.
*   **The Root Cause:** A frontend retry loop double-fires payloads when executions experience latency. It is highly concentrated in the `Prompt_1_0` and `LLMOverride_1_0` tools.
*   **Deduplication SQL (On-the-fly):**
```sql
SELECT *
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.AI_TOOLS_USAGE_DAILY_USER_SUMMARY_AT
QUALIFY ROW_NUMBER() OVER (PARTITION BY PAYLOAD_ID, TOOL_NAME ORDER BY PAYLOAD_DTS DESC) = 1;
```
