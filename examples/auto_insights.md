# 📊 Cloud Product Engagement Guide: Auto Insights

This guide outlines standard analytical queries and metrics for measuring user personas, dashboard views, and AI adoption within the **Alteryx Auto Insights** cloud portal, strictly focused on paid subscription customers.

---

## 🏛️ Ground Truth Target Schema
All queries must target:
*   **View:** `DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.SEM_AUTO_INSIGHTS_ACCOUNT_MONTHLY`
*   **Paid User Filter:** `LICENSE_TYPE IN ('Subscription', 'Purchase')`
*   **Tester Filter:** `ACCOUNT_NAME NOT LIKE '%Alteryx%'`

---

## 📈 Key Metric Queries

### 1. Paid Monthly Active Users (MAU) & Accounts Trend
Returns unique paid active accounts, users, and overall activity volume:
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

### 2. GenAI Mission Generation Trend (Paid Only)
Tracks the adoption of the GenAI Use Case and automatic report generator:
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

## 🔍 Diagnostics & Outages (RCA)

### Why do some active users show empty emails or "NoUser" in billing reports?
This is caused by the **Workspace Ingestion Orphan Bug**:
When an enterprise admin invites a new user directly to an active Trifacta/Auto Insights workspace, the user record is provisioned in the application but does **not** generate an automatic Salesforce Contact or Lead identity record in CRM databases. Consequently, their email maps to NULL or is missing from downstream billing-account joins.

PMs can identify affected workspaces using this diagnostic query:
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
