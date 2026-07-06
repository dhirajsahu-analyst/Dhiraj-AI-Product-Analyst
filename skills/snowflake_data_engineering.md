# ❄️ Expert Skill: Snowflake Data Engineering

This guide details advanced Snowflake SQL patterns, join configurations, and identity graph casting rules tailored specifically for Alteryx product telemetry.

---

## 📐 Topic 1: Standardizing Timezone Conversions
All raw client-side telemetry events log timestamps in UTC. For standardized business reporting, you must cast timestamps to Eastern Standard Time (America/New_York) to maintain dashboard parity:

```sql
SELECT 
    DAY AS raw_utc_date,
    CONVERT_TIMEZONE('UTC', 'America/New_York', PAYLOAD_DTS)::DATE AS local_activity_date
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.AI_TOOLS_USAGE_DAILY_USER_SUMMARY_AT;
```

---

## 📐 Topic 2: Bypassing the Implicit Casting Trap
*   **The Problem:** `USER_ID` in AI Tools contains string email addresses, while `USER_ID` in LLM Connections contains numeric GUIDs. Joining these directly triggers a `Numeric value 'user@domain.com' is not recognized` compilation crash, because Snowflake attempts to implicitly cast the string email column to a numeric type.
*   **The Rule:** **NEVER** join these tables on `USER_ID`. You must join strictly on the lowercase `USER_EMAIL` string keys:

```sql
-- CORRECT JOIN PATTERN
SELECT a.USER_ID AS email, l.CONNECTION_ID
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.AI_TOOLS_USAGE_DAILY_USER_SUMMARY_AT a
INNER JOIN DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.LLM_CONNECTIONS_DAILY_USER_SUMMARY_AV l 
    ON LOWER(a.USER_ID) = LOWER(l.USER_EMAIL);
```

---

## 📐 Topic 3: Join Fan-Out Prevention (Defensive SQL)
*   **The Problem:** Joining transaction tables to daily user-state or account snapshot tables (like `AYX_MONTHLY_ACCOUNT_AT` or `USERS_DAILY_AT`) duplicates rows, artificially fanning out and inflating run volumes.
*   **The Rule:** Always wrap the snapshot table in a deduplication window utilizing the `QUALIFY ROW_NUMBER() OVER (PARTITION BY ...)` pattern:

```sql
-- CORRECT DEFENSIVE SNAPSHOT JOIN
SELECT 
    at.DAY,
    at.USER_ID,
    at.SUCCESSFUL_RUN_FLAG,
    dim.ACTIVE_ACV
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.AI_TOOLS_USAGE_DAILY_USER_SUMMARY_AT at
LEFT JOIN (
    SELECT BILLING_ACCOUNT_ID, ACTIVE_ACV
    FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.AYX_MONTHLY_ACCOUNT_AT
    QUALIFY ROW_NUMBER() OVER (PARTITION BY BILLING_ACCOUNT_ID ORDER BY CUSTOMER_SINCE_DATE DESC) = 1
) dim ON at.ACCOUNT_CID = dim.BILLING_ACCOUNT_ID;
```
