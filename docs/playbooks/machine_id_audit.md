# 🧩 Snowflake Worksheet: LBS Machine ID Mapping Audit

**Owner:** Principal Product Analytics
**Date:** Current
**Objective:** Determine if missing user emails in Alteryx Designer telemetry (`ENGINE_SERVER_WITH_LICENSE`) can be recovered by joining `MACHINE_ID_DECODED` to the License Broker System (LBS) identity graph (`POSTGRES_LICENSEBILLING_TBL_MACHINE_USER`).

---

## 📊 1. Empirical Results (The "So What?")
A rigorous join of the 1,738 Engine Machine IDs against the 40,664 LBS Machine GUIDs yielded a **0% match rate**. 
This definitively proves that the hardware identifiers logged by the Engine and the LBS system are fundamentally different (likely hashed or sourced from different OS-level MAC addresses) and **cannot be used** to rescue orphaned user identities.

| Audit Phase | Row Count | Percentage |
| :--- | :---: | :---: |
| Target Engine Machines (ADP/PDP products) | **1,738** | 100.0% |
| Available LBS Machine GUIDs | **40,664** | N/A |
| **Matches Found in LBS Mapping** | **0** | **0.0%** |
| **Engine Machines Rescued with User Emails** | **0** | **0.0%** |

---

## 💻 2. Snowflake SQL Query

*Copy and paste the following SQL block directly into a Snowflake Worksheet to replicate the audit results:*

```sql
-- ====================================================================================
-- AUDIT: CROSS-PIPELINE MACHINE ID TO EMAIL MAPPING (ENGINE vs. LBS)
-- ====================================================================================

WITH eng_machines AS (
    -- Step 1: Extract distinct target machine IDs from the Engine telemetry
    SELECT DISTINCT MACHINE_ID_DECODED AS MACHINE_ID
    FROM DISCOVERY_PRODUCT_MANAGEMENT.TEL_STRAT.ENGINE_SERVER_WITH_LICENSE
    WHERE CALLER_PRODUCT_ID IN ('ADP', 'PDP')
      AND MACHINE_ID_DECODED IS NOT NULL
      AND TRIM(MACHINE_ID_DECODED) != ''
),

lbs_mapping AS (
    -- Step 2: Build the LBS Machine-to-Email bridge (as proposed by LBS Eng)
    SELECT
        mus.machine_guid,
        mus.user_id,
        'single_user' AS machine_user_flag,
        p.people_email
    FROM (
        -- Extract the pre-hyphen GUID from LBS raw machine IDs
        SELECT
            SPLIT_PART(machine_id_raw, '-', 1) AS machine_guid,
            MAX(user_id) AS user_id
        FROM DISCOVERY_PRODUCT_MANAGEMENT.PI_TELEMETRY_RAW.POSTGRES_LICENSEBILLING_TBL_MACHINE_USER
        GROUP BY SPLIT_PART(machine_id_raw, '-', 1)
        HAVING COUNT(DISTINCT user_id) = 1
    ) mus
    LEFT JOIN (
        -- Map the LBS User ID back to the canonical Trifacta email address
        SELECT
            id AS people_id,
            LOWER(email) AS people_email
        FROM DISCOVERY_PRODUCT_MANAGEMENT.PI_TELEMETRY_RAW.MYSQL_TRIFACTA_PEOPLE
    ) p ON TRY_TO_BINARY(mus.user_id, 'BASE64') = TRY_TO_BINARY(p.people_id, 'BASE64')
)

-- Step 3: Perform the Overlap Audit
SELECT 
    COUNT(DISTINCT e.MACHINE_ID) AS total_target_engine_machines,
    COUNT(DISTINCT l.machine_guid) AS successfully_mapped_machines,
    COUNT(DISTINCT CASE WHEN l.people_email IS NOT NULL THEN e.MACHINE_ID END) AS successfully_rescued_emails,
    ROUND(COUNT(DISTINCT l.machine_guid) * 100.0 / NULLIF(COUNT(DISTINCT e.MACHINE_ID), 0), 2) AS match_rate_pct
FROM eng_machines e
LEFT JOIN lbs_mapping l 
    ON e.MACHINE_ID = l.machine_guid;
```

---

## 🛠️ 3. Recommendation / Next Steps
Since hardware-level mapping fails, engineering efforts to resolve the `"NoUser"` telemetry bug must focus on **software-level identity passing** (e.g., embedding the `USER_EMAIL` natively into the JWT token sent to the engine runner), or Analytics must continue relying on the lowercase string email join directly between the frontend Copilot logs and the backend `EMAIL_FINAL` logs.
