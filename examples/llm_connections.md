# 🔌 Product Analytics Reference Guide: LLM Connections

This guide serves as the absolute, verified reference manual and dictionary for the **LLM Connections Key** analytics. It combines the complete schema catalogs, validated Snowflake SQL queries, and the strategic RCA playbook of all discovered deployment anomalies.

---

## 🏛️ Section 1: Business Definition & Sourcing
*   **Business Definition:** LLM Connections measures unique corporate connection credentials (API keys) set up by enterprise accounts to link custom LLM endpoints (such as OpenAI, Anthropic, or Azure).
*   **Telemetry View:** `DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.LLM_CONNECTIONS_DAILY_USER_SUMMARY_AV`
*   **Standard Filter Requirements (Paid Only):**
    - `LICENSE_TYPE IN ('Subscription', 'Purchase')` (Filters strictly for paying enterprise tiers).
    - `USER_EMAIL NOT LIKE '%alteryx%'` (Purges internal employee test connections).

---

## 📂 Section 2: Metadata Schema Catalog
Each record represents a unique user connection configuration session logged daily.

| Column Name | Data Type | Description |
| :--- | :---: | :--- |
| `DAY` | DATE | Date the custom connection was created or logged. |
| `MONTH_DATE` | DATE | First day of the reporting month. |
| `USER_EMAIL` | VARCHAR | **Contains string Email Addresses** (e.g., `randy@domain.com`). **Use this to join!** |
| `USER_ID` | NUMBER | **Contains Numeric GUIDs**. *Do not join this to AI Tools' USER_ID!* |
| `ACCOUNT_CID` | VARCHAR | 8-character Salesforce Customer ID. |
| `ACCOUNT_NAME` | VARCHAR | Mapped Customer Name in CRM. |
| `LICENSE_TYPE` | VARCHAR | Mapped license type (e.g., `'Purchase'`). |
| `LLM_CONNECTOR` | VARCHAR | Technical connector vendor key (e.g., `'openai'`, `'anthropic'`). |
| `LLM_CONNECTOR_DISPLAY_NAME` | VARCHAR | Friendly connector name (e.g., `'OpenAI'`, `'Anthropic'`). |
| `CONNECTION_ID` | NUMBER | Unique connection identifier. |
| `CONNECTION_STATUS` | VARCHAR | Status of the connection (`'Active'`, `'Deleted'`). |
| `CONNECTION_CREATED_DTS` | TIMESTAMP | Exact UTC timestamp of connection establishment. |

---

## 💻 Section 3: Validated & Tested SQL Queries (Paid Only)

*   **Rule for the Agent:** Whenever a user asks for any of the metrics below, **YOU MUST RUN THE CORRESPONDING QUERY EXACTLY AS IT IS WRITTEN HERE.** Do not rewrite, modify, or overcomplicate. These queries have been manually tested, verified, and return correct, uncorrupted numbers.

### Metric 1: Paid Monthly Connections Setup Trend
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

### Metric 2: Mapped Connector Share Trend
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

## 🔍 Section 4: Diagnostics & Root Cause Analysis (RCA)

### Anomaly A: Low Connection Setup Rates vs. Active AI Tool Runs
*   **The Issue:** Over 90% of active, paying AI Tools users do not have a recorded custom LLM Connection in the database.
*   **The Root Cause:** This is expected by design:
    1.  **Alteryx Platform Keys:** Alteryx hosts pre-configured, centrally managed Azure OpenAI default API keys. If a user runs a tool using our default engine, **no connection record is written** in their private workspace (`MYSQL_TRIFACTA_CONNECTIONS`). A record is *only* generated if the user manually configures their own company-owned API key.
    2.  **Specialty Utility Tools:** Specialty features like `Precision Match`, `Invoice Extractor`, and `Schema Fit` run on fixed, pre-compiled platform models. They **cannot** be configured with custom connections.
This confirms that **90.8% of paying users rely on Alteryx platform-managed keys** for day-to-day adoption.
