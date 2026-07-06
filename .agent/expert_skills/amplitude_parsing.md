# 📈 Expert Skill: Amplitude Product Analytics

This guide details our standardized patterns for parsing client-side Amplitude event payloads, extracting nested JSON user properties, and mapping event taxonomies inside Snowflake.

---

## 📐 Topic 1: Parsing Nested JSON Payloads
Amplitude client telemetry is ingested into Snowflake as nested JSON string payloads inside variant columns (typically named `USER_PROPERTIES` or `EVENT_PROPERTIES`). 
You must use Snowflake's native colon `:` operator and explicit string casts to extract these fields securely:

```sql
SELECT 
    USER_ID,
    -- Extracting nested email
    NULLIF(TRIM(PARSE_JSON(USER_PROPERTIES):email::STRING), '') AS user_email,
    -- Extracting nested subscription details
    NULLIF(TRIM(PARSE_JSON(USER_PROPERTIES):accountQuoteType::STRING), '') AS license_type,
    -- Extracting trial status
    COALESCE(PARSE_JSON(USER_PROPERTIES):isTrialUser::BOOLEAN, FALSE) AS is_trial_user
FROM DISCOVERY_PRODUCT_MANAGEMENT.PI_CLOUD.AMPLITUDE_ALL_EVENTS
WHERE EVENT_TYPE = 'view_insight';
```

---

## 📐 Topic 2: Standard Event Taxonomies for Auto Insights
When querying the raw Amplitude stream, map user behaviors to these specific events:

-   `start_app`: User initiates a new app instance.
-   `view_insight`: User successfully loads and views an automated dashboard report.
-   `create_report`: User builds a custom report, dataset configuration, or Mission.
-   `execute_explore`: User triggers a dynamic database search or exploration.
-   `generate_ai_use_cases`: User executes an AI-driven, automated workflow generation.

---

## 📐 Topic 3: Constructing Activation Funnels
When designing user conversion and activation pipelines, chain these events sequentially to trace drop-off steps:

```sql
WITH funnel_steps AS (
    SELECT 
        USER_ID,
        MAX(CASE WHEN EVENT_TYPE = 'start_app' THEN 1 ELSE 0 END) AS step_1_opened,
        MAX(CASE WHEN EVENT_TYPE = 'view_insight' THEN 1 ELSE 0 END) AS step_2_viewed,
        MAX(CASE WHEN EVENT_TYPE = 'create_report' THEN 1 ELSE 0 END) AS step_3_created
    FROM DISCOVERY_PRODUCT_MANAGEMENT.PI_CLOUD.AMPLITUDE_ALL_EVENTS
    WHERE EVENT_TIME BETWEEN '2026-01-01' AND '2026-06-30'
    GROUP BY USER_ID
)
SELECT 
    SUM(step_1_opened) AS total_opened,
    SUM(step_2_viewed) AS total_viewed,
    SUM(step_3_created) AS total_created,
    ROUND(SUM(step_2_viewed) * 100.0 / NULLIF(SUM(step_1_opened), 0), 2) AS opened_to_viewed_pct,
    ROUND(SUM(step_3_created) * 100.0 / NULLIF(SUM(step_2_viewed), 0), 2) AS viewed_to_created_pct
FROM funnel_steps;
```
