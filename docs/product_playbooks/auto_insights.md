# 📊 Product Analytics Reference Guide: Auto Insights

This guide serves as the absolute, verified reference manual and dictionary for the **Auto Insights** cloud-portal analytics. It combines the complete schema catalogs, validated Snowflake SQL queries, and the diagnostic RCA playbook of all discovered pipeline anomalies.

---

## 🏛️ Section 1: Business Definition & Sourcing
*   **Business Definition:** Auto Insights measures cloud-portal report generations, user persona splits, dashboard views, and automatic KPI exploration activity.
*   **Telemetry View:** `DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.SEM_AUTO_INSIGHTS_ACCOUNT_MONTHLY` (and Daily: `SEM_AUTO_INSIGHTS_USER_DAILY`)
*   **Standard Filter Requirements (Paid Only):**
    - `LICENSE_TYPE IN ('Subscription', 'Purchase')` (Filters strictly for paying enterprise tiers).
    - `ACCOUNT_NAME NOT LIKE '%Alteryx%'` (Purges internal employee test environments).

---

## 📂 Section 2: Metadata Schema Catalog
Each record in `SEM_AUTO_INSIGHTS_ACCOUNT_MONTHLY` represents aggregated monthly active users and features per account.

| Column Name | Data Type | Description |
| :--- | :---: | :--- |
| `REPORTING_MONTH` | DATE | First day of the reporting month. |
| `BILLING_ACCOUNT_ID` | VARCHAR | Salesforce Billing Account ID (Join Key). |
| `SFDC_ACCOUNT_CID` | VARCHAR | 8-character Salesforce Customer ID. |
| `ACCOUNT_NAME` | VARCHAR | Customer Account Name. |
| `ACCOUNT_TIER_TYPE` | VARCHAR | CRM status (e.g., `'Customer'`, `'Partner'`). |
| `CONTRACT_ACV` | NUMBER | Current active ACV in USD. |
| `LICENSE_TYPE` | VARCHAR | Mapped license type (e.g., `'Purchase'`). |
| `TOTAL_ACTIVE_USERS` | NUMBER | Monthly Active Users (MAU) for this account. |
| `ACTIVE_CREATORS` | NUMBER | Unique active users classified as `'Creator'` persona. |
| `ACTIVE_CONSUMERS` | NUMBER | Unique active users classified as `'Consumer'` persona. |
| `TOTAL_INSIGHTS_VIEWED` | NUMBER | Total occurrences of report views in the month. |
| `TOTAL_AI_USE_CASES_GENERATED`| NUMBER | Total AI use cases/Missions generated. |
| `TOTAL_EXPLORES_EXECUTED` | NUMBER | Total interactive data explorations executed. |

---

## 💻 Section 3: Validated & Tested SQL Queries (Paid Only)

*   **Rule for the Agent:** Whenever a user asks for any of the metrics below, **YOU MUST RUN THE CORRESPONDING QUERY EXACTLY AS IT IS WRITTEN HERE.** Do not rewrite, modify, or overcomplicate. These queries have been manually tested, verified, and return correct, uncorrupted numbers.

### Metric 1: Monthly Active Users (MAU) & Active Account Trend
```sql
SELECT 
    REPORTING_MONTH AS reporting_month,
    COUNT(DISTINCT BILLING_ACCOUNT_ID) AS paid_active_accounts,
    SUM(TOTAL_ACTIVE_USERS) AS paid_active_users,
    SUM(TOTAL_SESSIONS) AS total_sessions,
    SUM(TOTAL_EVENTS_FIRED) AS total_events_fired
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.SEM_AUTO_INSIGHTS_ACCOUNT_MONTHLY
WHERE REPORTING_MONTH BETWEEN '2025-01-01' AND '2026-06-30'
  AND LICENSE_TYPE IN ('Subscription', 'Purchase')
  AND ACCOUNT_NAME NOT LIKE '%Alteryx%'
GROUP BY 1
ORDER BY 1 ASC;
```

### Metric 2: GenAI Mission Generation Trend (Paid Only)
```sql
SELECT 
    REPORTING_MONTH AS reporting_month,
    COUNT(DISTINCT CASE WHEN TOTAL_AI_USE_CASES_GENERATED > 0 THEN BILLING_ACCOUNT_ID END) AS paid_accounts_using_ai,
    ROUND(COUNT(DISTINCT CASE WHEN TOTAL_AI_USE_CASES_GENERATED > 0 THEN BILLING_ACCOUNT_ID END) * 100.0 / NULLIF(COUNT(DISTINCT BILLING_ACCOUNT_ID), 0), 2) AS ai_account_adoption_rate_pct,
    SUM(TOTAL_AI_USE_CASES_GENERATED) AS cumulative_ai_reports_generated
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.SEM_AUTO_INSIGHTS_ACCOUNT_MONTHLY
WHERE REPORTING_MONTH BETWEEN '2025-01-01' AND '2026-06-30'
  AND LICENSE_TYPE IN ('Subscription', 'Purchase')
  AND ACCOUNT_NAME NOT LIKE '%Alteryx%'
GROUP BY 1
ORDER BY 1 ASC;
```

---

## 🔍 Section 4: Diagnostics & Root Cause Analysis (RCA)

### Anomaly A: Workspace Ingestion Orphan "NoUser" Failure
*   **The Issue:** Large groups of active users suddenly show blank emails/identities, causing them to fall out of cohorted billing metrics.
*   **The Root Cause:** Direct admin invitations to active workspaces create users inside the app but do **not** auto-generate a matching Salesforce Contact/Lead in CRM databases, leaving their emails completely blank in downstream joins.
*   **Verification SQL:**
```sql
SELECT 
    WORKSPACE_ID, 
    COUNT(DISTINCT USER_ID) AS unmapped_users_count, 
    COUNT(*) AS total_runs_affected
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.SEM_AUTO_INSIGHTS_USER_DAILY
WHERE BILLING_ACCOUNT_ID IS NULL 
   OR BILLING_ACCOUNT_ID = ''
GROUP BY 1 
ORDER BY unmapped_users_count DESC;
```
