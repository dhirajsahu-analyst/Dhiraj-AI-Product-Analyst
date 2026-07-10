# ⚡ Product Analytics Reference Guide: Livequery (LQ)

This guide serves as the absolute, verified reference manual and dictionary for **Livequery** cloud analytics. It combines the complete schema catalogs and validated Snowflake SQL queries.

---

## 🏛️ Section 1: Business Definition & Sourcing
*   **Business Definition:** Livequery (LQ) measures the capability for users to run analytical workflows directly against cloud data platforms (CDP) without extracting the data locally.
*   **Telemetry Views:** 
    - `DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.LIVE_QUERY_MONTHLY_ADOPTION_AV` (Seat & License tracking)
    - `DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.LIVE_QUERY_MONTHLY_USAGE_AV` (Run & Engagement tracking)
*   **Standard Filter Requirements:**
    - `LICENSE_TYPE = 'Purchase'` (Strictly filters for paying enterprise deployments).

---

## 📂 Section 2: Metadata Schema Catalog

### 1. Adoption View (`LIVE_QUERY_MONTHLY_ADOPTION_AV`)
Tracks seat allocations and user provisioning.
*   `YEAR_MONTH`: Reporting month.
*   `BILLING_ACCOUNT_ID`: Corporate billing identifier.
*   `TOTAL_AVAILABLE_SEATS` / `TOTAL_AVAILABLE_OLD_PP_SEATS`: Max licenses purchased.
*   `INVITED_FULL_USERS` / `INVITED_BASIC_USERS`: Users sent provisioning invites.
*   `ACTIVATED_FULL_USERS` / `ACTIVATED_BASIC_USERS`: Users who accepted invites and logged in.

### 2. Usage View (`LIVE_QUERY_MONTHLY_USAGE_AV`)
Tracks active engagement and execution volumes.
*   `LIVE_QUERY_ACTIVE_USERS`: Users who executed a Livequery.
*   `LIVE_QUERY_ENGAGED_USERS`: Power users exceeding an active usage threshold.
*   `LIVE_QUERY_RUNS`: Total execution volume.
*   `LIVE_QUERY_MANUAL_RUNS` / `LIVE_QUERY_AUTOMATED_RUNS`: Platform execution type.
*   `LIVE_QUERY_WORKFLOWS_CREATED`: Net new workflows built with LQ tools.

---

## 💻 Section 3: Validated & Tested SQL Queries (Paid Only)

*   **Rule for the Agent:** Whenever a user asks for any of the metrics below, **YOU MUST RUN THE CORRESPONDING QUERY EXACTLY AS IT IS WRITTEN HERE.** 

### Metric 1: Livequery Seat Adoption & Funnel
**Goal:** Track the provisioning funnel from purchased seats to activated users.
```sql
SELECT 
    DATE(YEAR_MONTH) AS reporting_month, 
    COUNT(DISTINCT BILLING_ACCOUNT_ID) AS total_live_query_accounts,
    SUM(TOTAL_AVAILABLE_SEATS) + SUM(TOTAL_AVAILABLE_OLD_PP_SEATS) AS total_available_seats,
    SUM(INVITED_FULL_USERS) + SUM(INVITED_BASIC_USERS) AS total_invited_users,
    SUM(ACTIVATED_FULL_USERS) + SUM(ACTIVATED_BASIC_USERS) AS total_activated_users
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.LIVE_QUERY_MONTHLY_ADOPTION_AV
WHERE LICENSE_TYPE = 'Purchase'
GROUP BY 1 ORDER BY 1 DESC;
```

### Metric 2: Livequery Active Accounts & Users
**Goal:** Track total active users and measure net new account acquisition.
```sql
SELECT 
    DATE(YEAR_MONTH) AS reporting_month,
    COUNT(DISTINCT CASE WHEN LIVE_QUERY_ACTIVE_USERS > 0 THEN BILLING_ACCOUNT_ID END) AS active_accounts,
    COUNT(DISTINCT CASE WHEN LIVE_QUERY_ACTIVE_ACCOUNTS_NEW > 0 THEN BILLING_ACCOUNT_ID END) AS net_new_accounts,
    SUM(LIVE_QUERY_ACTIVE_USERS) AS active_users
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.LIVE_QUERY_MONTHLY_USAGE_AV
WHERE LICENSE_TYPE = 'Purchase'
GROUP BY 1 ORDER BY 1 DESC;
```

### Metric 3: Livequery Run Volumes (Manual vs Automated)
**Goal:** Analyze execution scale and measure automated scheduled runs versus interactive manual runs.
```sql
SELECT 
    DATE(YEAR_MONTH) AS reporting_month, 
    SUM(LIVE_QUERY_RUNS) AS total_runs,
    SUM(LIVE_QUERY_MANUAL_RUNS) AS manual_runs,
    SUM(LIVE_QUERY_AUTOMATED_RUNS) AS automated_runs,
    ROUND(SUM(LIVE_QUERY_RUNS) / NULLIF(COUNT(DISTINCT CASE WHEN LIVE_QUERY_ACTIVE_USERS > 0 THEN BILLING_ACCOUNT_ID END), 0), 1) AS avg_runs_per_active_account
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.LIVE_QUERY_MONTHLY_USAGE_AV
WHERE LICENSE_TYPE = 'Purchase'
GROUP BY 1 ORDER BY 1 DESC;
```

### Metric 4: User Engagement Intensity
**Goal:** Identify power users and average session density.
```sql
SELECT 
    DATE(YEAR_MONTH) AS reporting_month, 
    SUM(LIVE_QUERY_ENGAGED_USERS) AS engaged_users,
    SUM(LIVE_QUERY_FREQUENT_USERS) AS frequent_users,
    ROUND(SUM(SUM_LQ_ACTIVE_DAYS_PER_ACCOUNT) / NULLIF(SUM(LQ_ACTIVE_USER_PER_ACCOUNT), 0), 2) AS avg_active_days_per_user,
    ROUND(SUM(LIVE_QUERY_FREQUENT_USERS) * 100.0 / NULLIF(SUM(LIVE_QUERY_ACTIVE_USERS), 0), 2) AS pct_frequent_users
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.LIVE_QUERY_MONTHLY_USAGE_AV
WHERE LICENSE_TYPE = 'Purchase'
GROUP BY 1 ORDER BY 1 DESC;
```

### Metric 5: Livequery Workflow Creation
**Goal:** Track the buildup of new logic versus the reuse of existing workflows.
```sql
SELECT 
    DATE(YEAR_MONTH) AS reporting_month,
    SUM(LIVE_QUERY_WORKFLOWS_CREATED) AS new_workflows_created,
    SUM(LIVE_QUERY_WORKFLOWS_EXISTING) AS existing_workflows_run
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.LIVE_QUERY_MONTHLY_USAGE_AV
WHERE LICENSE_TYPE = 'Purchase'
GROUP BY 1 ORDER BY 1 DESC;
```

### Metric 6: Cloud Native Adoption Metrics
**Goal:** Specifically slice adoption for Cloud Native executions.
```sql
SELECT 
    DATE(YEAR_MONTH) AS reporting_month, 
    SUM(TOTAL_CLOUD_NATIVE_ACCOUNTS) AS total_cloud_native_accounts,
    SUM(CLOUD_NATIVE_ACTIVE_ACCOUNTS) AS active_cloud_native_accounts,
    ROUND(SUM(CLOUD_NATIVE_ACTIVE_ACCOUNTS) * 100.0 / NULLIF(SUM(TOTAL_CLOUD_NATIVE_ACCOUNTS), 0), 2) AS pct_active_cloud_native_accounts,
    SUM(ONLY_CLOUD_NATIVE_ACTIVE_ACCOUNTS) AS pure_cloud_native_accounts,
    SUM(CLOUD_NATIVE_WORKFLOWS_CREATED) AS new_cloud_native_workflows,
    SUM(CLOUD_NATIVE_RUNS) AS cloud_native_total_runs,
    SUM(CLOUD_NATIVE_AUTOMATED_RUNS) AS cloud_native_automated_runs
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.LIVE_QUERY_MONTHLY_USAGE_AV
WHERE LICENSE_TYPE = 'Purchase'
GROUP BY 1 ORDER BY 1 DESC;
```
