-- ============================================================================
-- VIEW: SEM_LLM_CONNECTIONS_USER_DAILY
-- DOMAIN: LLM Connections
-- GRAIN: 1 row per Connection, per User, per Day
-- ============================================================================

CREATE OR REPLACE VIEW DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.SEM_LLM_CONNECTIONS_USER_DAILY AS

WITH canonical_identity_graph AS (
    SELECT
        WORKSPACE_ID_RAW AS WORKSPACE_ID,
        USER_ID_RAW AS USER_ID,
        COMPANY_DOMAIN,
        USER_TYPE,
        WORKSPACE_NAME,
        BILLING_ACCOUNT_ID_RAW AS BILLING_ACCOUNT_ID,
        SFDC_ACCOUNT_ID,
        ACCOUNT_NAME,
        LICENSE_TYPE
    FROM DISCOVERY_PRODUCT_MANAGEMENT.PI_CLOUD.AAC_IDENTITY_GRAPH_UT
    WHERE PIPELINE_REGION = 'US'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY USER_ID_RAW ORDER BY DATE DESC NULLS LAST) = 1
),
gen_ai_workspaces_dim AS (
    SELECT
        WORKSPACE_ID, NULL AS COMPANY_DOMAIN, 'Private Preview' AS USER_TYPE,
        WORKSPACE_NAME, BILLING_ACCOUNT_ID, SFDC_ACCOUNT_ID,
        BILLING_ACCOUNT_NAME AS ACCOUNT_NAME, LICENSE_TYPE
    FROM DISCOVERY_PRODUCT_MANAGEMENT.PI_CLOUD.GEN_AI_WORKSPACES
),
workspace_master AS (
    SELECT
        COALESCE(ig.WORKSPACE_ID, gaw.WORKSPACE_ID) AS WORKSPACE_ID,
        COALESCE(ig.COMPANY_DOMAIN, gaw.COMPANY_DOMAIN) AS COMPANY_DOMAIN,
        COALESCE(ig.USER_TYPE, gaw.USER_TYPE) AS USER_TYPE,
        COALESCE(ig.WORKSPACE_NAME, gaw.WORKSPACE_NAME) AS WORKSPACE_NAME,
        COALESCE(ig.BILLING_ACCOUNT_ID, gaw.BILLING_ACCOUNT_ID) AS BILLING_ACCOUNT_ID,
        COALESCE(ig.SFDC_ACCOUNT_ID, gaw.SFDC_ACCOUNT_ID) AS SFDC_ACCOUNT_ID,
        COALESCE(ig.ACCOUNT_NAME, gaw.ACCOUNT_NAME) AS ACCOUNT_NAME,
        COALESCE(ig.LICENSE_TYPE, gaw.LICENSE_TYPE) AS LICENSE_TYPE
    FROM canonical_identity_graph AS ig
    FULL OUTER JOIN gen_ai_workspaces_dim AS gaw ON ig.WORKSPACE_ID = gaw.WORKSPACE_ID
),
golden_users_bridge AS (
    SELECT 
        USER_EMAIL, SFDC_ACCOUNT_ID, ACCOUNT_CID, ACCOUNT_OWNER_NAME,
        ACCOUNT_SALES_REGION, ACCOUNT_SALES_SEGMENT, ACCOUNT_TYPE,
        ACTIVE_ACV, ACTIVE_ACV_RANGE, BILLING_COUNTRY, CUSTOMER_SINCE_DATE, G2K, INDUSTRY
    FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.USERS_DAILY_AT
    WHERE USER_EMAIL IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (PARTITION BY USER_EMAIL ORDER BY DATE DESC NULLS LAST) = 1
),
connections_bronze AS (
    SELECT DISTINCT
        C.PIPELINE_REGION, C.WORKSPACE_ID_RAW AS WORKSPACE_ID, JC.VENDOR AS LLM_CONNECTOR,
        C.ID AS CONNECTION_ID, C.NAME AS CONNECTION_NAME, C.CREATED_BY_RAW AS USER_ID_RAW,
        US.USER_EMAIL AS user_email, US.ACCOUNT_CID AS telemetry_account_cid, US.ACCOUNT_EDITION AS account_edition,
        TRY_TO_TIMESTAMP_NTZ(C.CREATED_AT) AS CONNECTION_CREATED_DTS,
        TRY_TO_DATE(C.CREATED_AT) AS CONNECTION_CREATED_DATE,
        TRY_TO_TIMESTAMP_NTZ(C.DELETED_AT) AS CONNECTION_DELETED_DTS,
        TRY_TO_DATE(C.DELETED_AT) AS CONNECTION_DELETED_DATE,
        CASE WHEN C.DELETED_AT IS NULL THEN 'Active' ELSE 'Deleted' END AS CONNECTION_STATUS,
        CASE WHEN C.CREATED_AT IS NOT NULL THEN 1 ELSE 0 END AS CONNECTION_CREATED_FLAG,
        CASE WHEN C.DELETED_AT IS NOT NULL THEN 1 ELSE 0 END AS CONNECTION_DELETED_FLAG
    FROM DISCOVERY_PRODUCT_MANAGEMENT.PI_TELEMETRY_RAW.MYSQL_TRIFACTA_CONNECTIONS AS C
    LEFT JOIN DISCOVERY_PRODUCT_MANAGEMENT.PI_TELEMETRY_RAW.MYSQL_TRIFACTA_JDBCCONNECTIONS AS JC ON C.ID = JC.CONNECTION_ID
    LEFT JOIN (
        SELECT USER_ID_RAW, PIPELINE_REGION, USER_EMAIL, ACCOUNT_CID, ACCOUNT_EDITION
        FROM DISCOVERY_PRODUCT_MANAGEMENT.PI_CLOUD.AAC_IDENTITY_GRAPH_UT
        WHERE PIPELINE_REGION = 'US'
        QUALIFY ROW_NUMBER() OVER (PARTITION BY USER_ID_RAW, PIPELINE_REGION ORDER BY DATE DESC) = 1
    ) AS US ON C.CREATED_BY_RAW = US.USER_ID_RAW AND C.PIPELINE_REGION = US.PIPELINE_REGION
    WHERE C.PIPELINE_REGION = 'US'
      AND JC.VENDOR IN (
            'openai', 'openai_compatible', 'google_vertex_ai', 'anthropic', 'aws_bedrock',
            'databricks_mosaic_ai', 'huggingface', 'mistral', 'cohere', 'deepseek', 'groq',
            'perplexity', 'xai', 'azure', 'litellm_proxy'
      )
)
SELECT 
    cb.CONNECTION_CREATED_DATE AS activity_date,
    DATE_TRUNC('MONTH', cb.CONNECTION_CREATED_DATE)::DATE AS month_start_date,
    cb.PIPELINE_REGION AS deployment_region,
    wad.COMPANY_DOMAIN AS customer_domain,
    wad.USER_TYPE AS user_role,
    cb.WORKSPACE_ID,
    wad.WORKSPACE_NAME,
    wad.BILLING_ACCOUNT_ID AS billing_account_id,
    COALESCE(
        NULLIF(TRIM(cb.telemetry_account_cid), ''),       
        NULLIF(TRIM(wad.SFDC_ACCOUNT_ID), ''),           
        NULLIF(TRIM(dim.SFDC_ACCOUNT_ID), ''),           
        NULLIF(TRIM(dim.ACCOUNT_CID), ''),               
        'Shadow Account'                                 
    ) AS final_account_cid,
    COALESCE(wad.ACCOUNT_NAME, 'Shadow Guest Account') AS customer_name,
    cb.account_edition,
    COALESCE(wad.LICENSE_TYPE, 'NULL / Trial') AS license_type,
    cb.USER_ID_RAW AS user_id,
    cb.user_email AS user_email,
    cb.LLM_CONNECTOR AS connector_type,
    CASE
        WHEN cb.LLM_CONNECTOR = 'openai' THEN 'OpenAI'
        WHEN cb.LLM_CONNECTOR = 'openai_compatible' THEN 'OpenAI Compatible'
        WHEN cb.LLM_CONNECTOR = 'google_vertex_ai' THEN 'Google Vertex AI'
        WHEN cb.LLM_CONNECTOR = 'anthropic' THEN 'Anthropic'
        WHEN cb.LLM_CONNECTOR = 'aws_bedrock' THEN 'AWS Bedrock'
        WHEN cb.LLM_CONNECTOR = 'databricks_mosaic_ai' THEN 'Databricks Mosaic AI'
        WHEN cb.LLM_CONNECTOR = 'huggingface' THEN 'Hugging Face'
        WHEN cb.LLM_CONNECTOR = 'mistral' THEN 'Mistral'
        WHEN cb.LLM_CONNECTOR = 'cohere' THEN 'Cohere'
        WHEN cb.LLM_CONNECTOR = 'deepseek' THEN 'DeepSeek'
        WHEN cb.LLM_CONNECTOR = 'groq' THEN 'Groq'
        WHEN cb.LLM_CONNECTOR = 'perplexity' THEN 'Perplexity'
        WHEN cb.LLM_CONNECTOR = 'xai' THEN 'xAI'
        WHEN cb.LLM_CONNECTOR = 'azure' THEN 'Azure'
        WHEN cb.LLM_CONNECTOR = 'litellm_proxy' THEN 'LiteLLM Proxy'
        ELSE cb.LLM_CONNECTOR
    END AS connector_display_name,
    cb.CONNECTION_ID AS connection_id,
    cb.CONNECTION_NAME AS connection_name,
    cb.CONNECTION_STATUS AS connection_status,
    cb.CONNECTION_CREATED_DTS AS connection_created_timestamp,
    cb.CONNECTION_DELETED_DTS AS connection_deleted_timestamp,
    cb.CONNECTION_CREATED_FLAG AS is_new_connection,
    cb.CONNECTION_DELETED_FLAG AS is_deleted_connection,
    dim.ACCOUNT_OWNER_NAME AS account_manager,
    dim.ACCOUNT_SALES_REGION AS sales_region,
    dim.ACCOUNT_SALES_SEGMENT AS market_segment,
    dim.ACCOUNT_TYPE AS account_tier,
    COALESCE(dim.ACTIVE_ACV, 0.0) AS contract_acv,
    dim.ACTIVE_ACV_RANGE AS acv_bucket,
    dim.BILLING_COUNTRY AS country,
    dim.CUSTOMER_SINCE_DATE AS customer_start_date,
    COALESCE(dim.G2K, FALSE) AS is_global_2000,
    dim.INDUSTRY AS industry_vertical
FROM connections_bronze cb
LEFT JOIN workspace_master wad ON cb.WORKSPACE_ID = wad.WORKSPACE_ID
LEFT JOIN golden_users_bridge dim ON LOWER(cb.user_email) = LOWER(dim.USER_EMAIL)
WHERE cb.user_email NOT LIKE '%alteryx%'
QUALIFY ROW_NUMBER() OVER (PARTITION BY cb.CONNECTION_ID ORDER BY cb.CONNECTION_CREATED_DTS DESC) = 1;
