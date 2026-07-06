# 🤖 Product Analytics Reference Guide: Ask Alteryx (Copilot)

This guide serves as the absolute, verified reference manual and dictionary for the **Ask Alteryx (Copilot)** desktop AI assistant. It combines the complete schema catalogs, validated Snowflake SQL queries, and the strategic RCA playbook of all discovered pipeline anomalies.

---

## 🏛️ Section 1: Business Definition & Sourcing
*   **Business Definition:** Ask Alteryx is the in-product Alteryx Designer Desktop AI assistant, measuring user conversational onboarding, active chatting, and workflow Canvas drop-interactions.
*   **Telemetry Table:** `DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.COPILOT_ACTIVITY_USAGE_AT`
*   **Standard Filter Requirements (Paid Only):**
    - `LICENSE_TYPE = 'Purchase'` (Filters strictly for paying enterprise tiers).
    - `USER_TYPE = 'aacp'` (Focuses on paid, activated workspace accounts).
    - `USER_EMAIL NOT LIKE '%alteryx.com%'` (Purges internal employee test executions).

---

## 📂 Section 2: Metadata Schema Catalog
Each record represents a unique user chat conversation, message, or tool drop log.

| Column Name | Data Type | Description |
| :--- | :---: | :--- |
| `ALTERYX_USER_EMAIL` | VARCHAR | User's Email Address captured from Designer Desktop Telemetry (Join Key). |
| `USER_ID_RAW` | VARCHAR | Decoded numeric User ID from Designer Desktop Telemetry. |
| `LICENSE_TYPE` | VARCHAR | User's license type (e.g., `'Purchase'`). |
| `PRICING_AND_PACKAGING` | VARCHAR | Pricing model year (e.g., `'2025'`). |
| `COPILOT_ENABLED` | BOOLEAN | `TRUE` if Copilot capability is active for this workspace. |
| `ACCOUNT_EDITION` | VARCHAR | Mapped CRM tier (`'Professional'`, `'Enterprise'`). |
| `BILLING_ACCOUNT_ID_RAW` | VARCHAR | Raw corporate billing account locator key from CRM. |
| `MAXIMUM_RAW_PRODUCT_VERSION` | VARCHAR | Highest raw Alteryx Designer software version logged (e.g., `2025.2`). |
| `STATUS` | VARCHAR | User provisioning status. Active users are marked as `'ACTIVATED'`. |
| `USER_EMAIL` | VARCHAR | User Email Address recorded directly in the Copilot database. |
| `USER_TYPE` | VARCHAR | Copilot user type. Core value for paying users: `'aacp'`. |
| `CONV_CREATED_DATE` | DATE | Date the Copilot conversation was initiated. |
| `CHAT_ID` | VARCHAR | Unique identifier for an individual chat message sent. |
| `CONVERSATION_ID` | VARCHAR | Unique identifier for a continuous chat session thread. |
| `WORKFLOW_ID` | VARCHAR | Active workflow ID open in Designer when the chat was sent. |

---

## 💻 Section 3: Validated & Tested SQL Queries (Paid Only)

*   **Rule for the Agent:** Whenever a user asks for any of the metrics below, **YOU MUST RUN THE CORRESPONDING QUERY EXACTLY AS IT IS WRITTEN HERE.** Do not rewrite, modify, or overcomplicate. These queries have been manually tested, verified, and return correct, uncorrupted numbers.

### Metric 1: Paid Active Users Onboarding Funnel
```sql
SELECT 
    COUNT(DISTINCT CASE WHEN USER_EMAIL IS NOT NULL THEN USER_ID_RAW END) AS paid_onboarded_users,
    COUNT(DISTINCT CASE WHEN CHAT_ID IS NOT NULL THEN USER_ID_RAW END) AS paid_active_users,
    COUNT(DISTINCT CASE WHEN CHAT_ID IS NOT NULL AND WORKFLOW_ID IS NOT NULL AND WORKFLOW_ID <> '' THEN USER_ID_RAW END) AS paid_active_users_with_workflow
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.COPILOT_ACTIVITY_USAGE_AT
WHERE LICENSE_TYPE = 'Purchase'
  AND USER_TYPE = 'aacp'
  AND USER_EMAIL NOT LIKE '%alteryx.com%';
```

### Metric 2: Paid User Returning Rate % (30–60 Day Cohort)
```sql
WITH user_activity AS (   
    SELECT
        USER_ID_RAW AS user_key,
        CAST(CONV_CREATED_DATE AS DATE) AS activity_date
    FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.COPILOT_ACTIVITY_USAGE_AT
    WHERE ACCOUNT_EDITION IN ('Professional', 'Enterprise')
      AND LICENSE_TYPE = 'Purchase'
      AND CHAT_ID IS NOT NULL
      AND USER_EMAIL NOT LIKE '%alteryx.com%'
),
first_use AS (
    SELECT
        user_key,
        MIN(activity_date) AS first_date
    FROM user_activity
    GROUP BY user_key
),
eligible_cohort AS (
    SELECT
        user_key,
        first_date
    FROM first_use
    WHERE first_date <= DATEADD(day, -60, CURRENT_DATE())
),
returns_30_60 AS (
    SELECT
        e.user_key
    FROM eligible_cohort e
    JOIN user_activity ua
      ON ua.user_key = e.user_key
     AND ua.activity_date BETWEEN DATEADD(day, 30, e.first_date)
                              AND DATEADD(day, 60, e.first_date)
    GROUP BY e.user_key
)
SELECT
    (SELECT COUNT(*) FROM eligible_cohort) AS total_eligible_cohort,
    (SELECT COUNT(*) FROM returns_30_60)   AS returned_users_count,
    ROUND((SELECT COUNT(*) FROM returns_30_60) * 100.0 / NULLIF((SELECT COUNT(*) FROM eligible_cohort), 0), 2) AS return_rate_30_60d_pct;
```

---

## 🔍 Section 4: Diagnostics & Root Cause Analysis (RCA)

### Anomaly A: The "NoUser" Telemetry Outage (TMM-516 / GDD-14007)
*   **The Issue:** Over 15% of active Copilot users had missing emails in workflow engine runs, skewing and undercounting workflow-level adoption rates.
*   **The Root Cause:** Following the migration to the Licensing Broker Service (LBS) on Designer 2025.1+, new users who hadn't previously configured a local Flexera license bypassed local email telemetry, resulting in missing email mappings in workflow engine runs.
*   **The Resolution Query (Bypasses "NoUser" by joining on lowercase emails):**
```sql
WITH copilot_eligible_users AS (
    SELECT DISTINCT alteryx_user_email AS email
    FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.COPILOT_ACTIVITY_USAGE_AT
    WHERE license_type = 'Purchase'
      AND status = 'ACTIVATED'
      AND chat_id IS NOT NULL
      AND alteryx_user_email NOT LIKE '%alteryx.com%'
),
first_copilot_interaction AS (
    SELECT
        LOWER(alteryx_user_email) AS user_email,
        MIN(conv_created_date)    AS first_conv_created_at
    FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.COPILOT_ACTIVITY_USAGE_AT
    WHERE chat_id IS NOT NULL
      AND alteryx_user_email IS NOT NULL
    GROUP BY 1
),
denominator AS (
    SELECT DISTINCT
        es.workflow_id
    FROM DISCOVERY_PRODUCT_MANAGEMENT.TEL_STRAT.COPILOT_ENGINE_RUN_VW es
    INNER JOIN copilot_eligible_users eu
        ON LOWER(es.email_final) = LOWER(eu.email)
    INNER JOIN first_copilot_interaction fci
        ON LOWER(es.email_final) = fci.user_email
    WHERE es.payload_dts >= '2025-12-03'::timestamp
      AND es.payload_dts >= fci.first_conv_created_at
      AND es.PRODUCT_NAME = 'Designer'
),
numerator AS (
    SELECT DISTINCT
        es.workflow_id
    FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.COPILOT_ACTIVITY_USAGE_AT co
    LEFT JOIN DISCOVERY_PRODUCT_MANAGEMENT.TEL_STRAT.COPILOT_ENGINE_RUN_VW es
        ON co.workflow_id = es.workflow_id
    WHERE co.workflow_id IS NOT NULL
      AND co.user_email IN (SELECT email FROM copilot_eligible_users)
      AND co.chat_id IS NOT NULL
)
SELECT
    (SELECT COUNT(DISTINCT workflow_id) FROM numerator) AS copilot_mapped_runs,
    (SELECT COUNT(DISTINCT workflow_id) FROM denominator) AS total_active_user_runs,
    ROUND(
        100.0 * (SELECT COUNT(DISTINCT workflow_id) FROM numerator) /
        NULLIF((SELECT COUNT(DISTINCT workflow_id) FROM denominator), 0),
        4
    ) AS copilot_pct_of_active_runs;
```
