# 🔌 Infrastructure Adoption Guide: LLM Connections

This guide outlines standard analytical queries and metrics for measuring user adoption, connector selection, and temporal setups of **LLM Connection keys**, strictly focused on paid subscription customers.

---

## 🏛️ Ground Truth Target Schema
All queries must target:
*   **View:** `DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.LLM_CONNECTIONS_DAILY_USER_SUMMARY_AV`
*   **Paid User Filter:** `LICENSE_TYPE IN ('Subscription', 'Purchase')`
*   **Tester Filter:** `USER_EMAIL NOT LIKE '%alteryx%'`

---

## 📈 Key Metric Queries

### 1. Paid Monthly Connection Setup Trend
Returns unique paid subscription users with at least one active connection created per month:
```sql
SELECT 
    MONTH_DATE AS reporting_month,
    COUNT(DISTINCT ACCOUNT_CID) AS paid_active_accounts,
    COUNT(DISTINCT USER_EMAIL) AS paid_active_users,
    COUNT(DISTINCT CONNECTION_ID) AS total_connections_created
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.LLM_CONNECTIONS_DAILY_USER_SUMMARY_AV
WHERE DAY BETWEEN '2026-01-01' AND '2026-06-30'
  AND LICENSE_TYPE IN ('Subscription', 'Purchase')
  AND USER_EMAIL NOT LIKE '%alteryx%'
GROUP BY 1
ORDER BY 1 ASC;
```

### 2. Connector Vendor Deployment Shares
Shows which third-party LLM connectors (OpenAI, Anthropic, Google Vertex) are most popular among paid accounts:
```sql
SELECT 
    LLM_CONNECTOR_DISPLAY_NAME AS connector,
    COUNT(DISTINCT ACCOUNT_CID) AS paid_active_accounts,
    COUNT(DISTINCT USER_EMAIL) AS paid_active_users,
    COUNT(DISTINCT CONNECTION_ID) AS total_connections_created
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.LLM_CONNECTIONS_DAILY_USER_SUMMARY_AV
WHERE DAY BETWEEN '2026-01-01' AND '2026-06-30'
  AND LICENSE_TYPE IN ('Subscription', 'Purchase')
  AND USER_EMAIL NOT LIKE '%alteryx%'
GROUP BY 1
ORDER BY total_connections_created DESC;
```

---

## 🔍 Diagnostics & Outages (RCA)

### Why are 90% of our active AI Tools users running without an active LLM Connection?
This is a critical product design detail:
1.  **Alteryx-Managed Platform Default Keys:** Alteryx hosts pre-configured, centrally managed Azure OpenAI default API keys. If a user runs a workflow using our default engine, **no connection record is written** in their private workspace (`MYSQL_TRIFACTA_CONNECTIONS`). A record is *only* generated if the user manually configures their own company-owned API key.
2.  **Specialty Utility Tools:** Specialty features like `Precision Match`, `Invoice Extractor`, and `Schema Fit` run on fixed, pre-compiled platform models. They **cannot** be configured with custom connections.
This confirms that **90.8% of paying users rely on Alteryx platform-managed keys** for day-to-day adoption.
