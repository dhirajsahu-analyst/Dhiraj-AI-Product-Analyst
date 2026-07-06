# 📊 Product Engagement Guide: AI Tools Suite

This guide outlines standard analytical queries and metrics for measuring adoption, volume, and performance within the **Alteryx AI Tools Suite**, strictly focused on paid subscription customers.

---

## 🏛️ Ground Truth Target Schema
All queries must target:
*   **Table:** `DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.AI_TOOLS_USAGE_DAILY_USER_SUMMARY_AT`
*   **Paid User Filter:** `LICENSE_TYPE IN ('Subscription', 'Purchase')`
*   **Tester Filter:** `USER_ID NOT LIKE '%alteryx%'`

---

## 📈 Key Metric Queries

### 1. Paid Monthly Active Users (MAU) Trend
Returns unique paid subscription users with at least one successful execution in each calendar month:
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

### 2. GenAI Tool Adoption, Volume, and Success Rates
Ranks our suite features (Prompt, LLM Override, Precision Match, etc.) by adoption breadth and reliability:
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

## 🔍 Diagnostics & Outages (RCA)

### Why is there a 10x discrepancy between active raw logs and the KPI summary table?
The high-level KPI dashboard table `AI_TOOLS_MONTHLY_KPI_SUMMARY` is built using a strict formula:
`WHERE LICENSE_TYPE = 'Subscription' AND SUCCESSFUL_RUN_FLAG = 1`
This silently filters out trials, guest evaluations, academic profiles, and any subscription accounts that had only failed runs during the month.

To prove this, execute this count comparison:
```sql
SELECT 
    COUNT(DISTINCT USER_ID) AS raw_users,
    COUNT(DISTINCT CASE WHEN LICENSE_TYPE = 'Subscription' AND SUCCESSFUL_RUN_FLAG = 1 THEN USER_ID END) AS kpi_users
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.AI_TOOLS_USAGE_DAILY_USER_SUMMARY_AT
WHERE DAY BETWEEN '2026-06-01' AND '2026-06-30';
```
