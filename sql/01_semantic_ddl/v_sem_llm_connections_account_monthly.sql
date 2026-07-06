-- ============================================================================
-- VIEW: SEM_LLM_CONNECTIONS_ACCOUNT_MONTHLY
-- DOMAIN: LLM Connections
-- GRAIN: 1 row per Salesforce Account, per Month
-- ============================================================================

CREATE OR REPLACE VIEW DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.SEM_LLM_CONNECTIONS_ACCOUNT_MONTHLY AS

SELECT
    month_start_date AS reporting_month,
    final_account_cid AS customer_id,
    billing_account_id,
    customer_name,
    license_type,
    COUNT(DISTINCT connection_id) AS total_connections_created,
    COUNT(DISTINCT CASE WHEN connection_status = 'Active' THEN connection_id END) AS total_active_connections,
    COUNT(DISTINCT user_id) AS total_active_users,
    COUNT(DISTINCT connector_type) AS distinct_llm_connectors_used,
    sales_region,
    market_segment,
    MAX(contract_acv) AS contract_acv,
    is_global_2000,
    industry_vertical
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.SEM_LLM_CONNECTIONS_USER_DAILY
WHERE final_account_cid != 'Shadow Account'
GROUP BY 
    reporting_month,
    final_account_cid,
    billing_account_id,
    customer_name,
    license_type,
    sales_region,
    market_segment,
    is_global_2000,
    industry_vertical;
