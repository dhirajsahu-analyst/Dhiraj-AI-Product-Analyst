# 🤖 Desktop Copilot Guide: Ask Alteryx

This guide outlines standard analytical queries and metrics for measuring user funnel stages, onboarding, active chat volume, and long-term cohort retention for the **Ask Alteryx (Copilot)** desktop AI assistant, strictly focused on paid subscription customers.

---

## 🏛️ Ground Truth Target Schema
All queries must target:
*   **Table:** `DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.COPILOT_ACTIVITY_USAGE_AT`
*   **Paid User Filter:** `LICENSE_TYPE = 'Purchase'`
*   **Paid User Type:** `USER_TYPE = 'aacp'`
*   **Tester Filter:** `USER_EMAIL NOT LIKE '%alteryx.com%'`

---

## 📈 Key Metric Queries

### 1. Paid Active Users Onboarding Funnel (Paid Only)
Ranks user stages from onboarding (entered session) to active chatting (`CHAT_ID IS NOT NULL`) to workflow attachment:
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

### 2. Paid User Returning Rate % (30–60 Day Cohort)
Measures long-term "habit loop" and stickiness strictly for paid users whose first interaction occurred at least 60 days ago (complete-window fairness):
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
    -- Filters denominator strictly to users who have completed their full 60-day observation window
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

## 🔍 Diagnostics & Outages (RCA)

### Why are some Designer engine runs missing emails, causing "% Workflows Run by Copilot" to drop?
This is the **"NoUser" Telemetry Outage (TMM-516 / GDD-14007)**:
Following the migration to the Licensing Broker Service (LBS) on Designer 2025.1+, new users who hadn't previously installed a local Flexera license bypassed local email telemetry, resulting in missing email mappings in workflow engine runs. 

We bypass this in our queries by mapping Copilot's `WORKFLOW_ID` (from backend telemetry) directly to the engine-run table using lowercase joins:
`ON LOWER(copilot.ALTERYX_USER_EMAIL) = LOWER(engine.EMAIL_FINAL)`
This allows the agent to reconstruct accurate workflow-level adoption rates.
