-- ============================================================================
-- VIEW: SEM_AI_TOOLS_USER_DAILY
-- DOMAIN: AI Tools Suite
-- GRAIN: 1 row per User, per Tool, per Day (Deduplicated)
-- ============================================================================

CREATE OR REPLACE VIEW DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.SEM_AI_TOOLS_USER_DAILY AS

WITH raw_telemetry AS (
    SELECT *
    FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.AI_TOOLS_USAGE_DAILY_USER_SUMMARY_AT
    WHERE USER_ID IS NOT NULL 
      AND USER_ID NOT LIKE '%alteryx%'
),
golden_users_bridge AS (
    SELECT 
        USER_EMAIL, SFDC_ACCOUNT_ID, ACCOUNT_CID, ACCOUNT_OWNER_NAME,
        ACCOUNT_SALES_REGION, ACCOUNT_SALES_SEGMENT, ACCOUNT_TYPE,
        ACTIVE_ACV, ACTIVE_ACV_RANGE, BILLING_COUNTRY, CUSTOMER_SINCE_DATE,
        G2K, INDUSTRY
    FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.USERS_DAILY_AT
    WHERE USER_EMAIL IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (PARTITION BY USER_EMAIL ORDER BY DATE DESC NULLS LAST) = 1
)
SELECT
    at.DAY AS activity_date,
    at.MONTH_DATE AS month_start_date,
    at.PAYLOAD_DTS AS run_timestamp,
    at.USER_ID AS user_id,
    at.PAYLOAD_ID AS payload_id,
    COALESCE(
        NULLIF(TRIM(at.ACCOUNT_CID), ''),               
        NULLIF(TRIM(dim.SFDC_ACCOUNT_ID), ''),          
        NULLIF(TRIM(dim.ACCOUNT_CID), ''),               
        'Shadow Account'                                
    ) AS final_account_cid,
    at.BILLING_ACCOUNT_ID AS billing_account_id,
    COALESCE(at.BILLING_ACCOUNT_NAME, 'Shadow Guest Account') AS customer_name,
    COALESCE(at.NAMED_COMPANY, 'Shadow Group') AS company_group,
    COALESCE(at.LICENSE_TYPE, 'NULL / Trial') AS license_type,
    at.TOOL_GROUP AS tool_category,
    at.GEN_AI_TOOL_NAME AS model_name,
    at.TOOL_NAME AS tool_action,
    at.WORKFLOW_ID AS workflow_id,
    at.VERSION AS product_version,
    at.PRODUCT_NAME AS platform_name,
    at.WORKFLOW_TYPE AS execution_type,
    at.DURATION_NUM AS duration_seconds,
    at.RUN_STATUS AS execution_status,
    COALESCE(at.SUCCESSFUL_RUN_FLAG, 0) AS successful_runs,
    COALESCE(at.FAILED_RUN_FLAG, 0) AS failed_runs,
    (COALESCE(at.SUCCESSFUL_RUN_FLAG, 0) + COALESCE(at.FAILED_RUN_FLAG, 0)) AS total_runs,
    CASE 
        WHEN (COALESCE(at.SUCCESSFUL_RUN_FLAG, 0) + COALESCE(at.FAILED_RUN_FLAG, 0)) > 0 
        THEN (COALESCE(at.SUCCESSFUL_RUN_FLAG, 0) * 100.0) / (COALESCE(at.SUCCESSFUL_RUN_FLAG, 0) + COALESCE(at.FAILED_RUN_FLAG, 0))
        ELSE 100.0 
    END AS success_rate_pct,
    COALESCE(at.ACCOUNT_MANAGER, dim.ACCOUNT_OWNER_NAME, 'Unknown AM') AS account_manager,
    COALESCE(at.ACCOUNT_SALES_REGION, dim.ACCOUNT_SALES_REGION, 'Unknown Region') AS sales_region,
    COALESCE(at.ACCOUNT_SALES_SEGMENT, dim.ACCOUNT_SALES_SEGMENT, 'Unknown Segment') AS market_segment,
    COALESCE(at.ACCOUNT_TYPE, dim.ACCOUNT_TYPE, 'Trial / Unknown') AS account_tier,
    COALESCE(at.ACTIVE_ACV, dim.ACTIVE_ACV, 0.0) AS contract_acv,
    COALESCE(at.ACTIVE_ACV_RANGE, dim.ACTIVE_ACV_RANGE, 'Unknown Band') AS acv_bucket,
    COALESCE(at.BILLING_COUNTRY, dim.BILLING_COUNTRY, 'Unknown Country') AS country,
    COALESCE(at.CUSTOMER_SINCE_DATE, dim.CUSTOMER_SINCE_DATE) AS customer_start_date,
    COALESCE(at.G2K, dim.G2K, FALSE) AS is_global_2000,
    COALESCE(at.INDUSTRY, dim.INDUSTRY, 'Unknown Industry') AS industry_vertical
FROM raw_telemetry at
LEFT JOIN golden_users_bridge dim ON LOWER(at.USER_ID) = LOWER(dim.USER_EMAIL)
QUALIFY ROW_NUMBER() OVER (PARTITION BY at.PAYLOAD_ID, at.TOOL_NAME ORDER BY at.PAYLOAD_DTS DESC) = 1;
