-- ============================================================================
-- VIEW: SEM_AI_TOOLS_ACCOUNT_MONTHLY
-- DOMAIN: AI Tools Suite
-- GRAIN: 1 row per Account, per Tool, per Month
-- ============================================================================

CREATE OR REPLACE VIEW DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.SEM_AI_TOOLS_ACCOUNT_MONTHLY AS

SELECT
    month_start_date AS reporting_month,
    final_account_cid AS customer_id,
    billing_account_id,
    customer_name,
    company_group,
    license_type,
    tool_category,
    model_name,
    tool_action,
    SUM(total_runs) AS total_runs,
    SUM(successful_runs) AS successful_runs,
    SUM(failed_runs) AS failed_runs,
    ROUND((SUM(successful_runs) * 100.0) / NULLIF(SUM(total_runs), 0), 2) AS success_rate_pct,
    ROUND((SUM(failed_runs) * 100.0) / NULLIF(SUM(total_runs), 0), 2) AS failure_rate_pct,
    COUNT(DISTINCT user_id) AS total_users,
    COUNT(DISTINCT CASE WHEN successful_runs > 0 THEN user_id END) AS successful_active_users,
    COUNT(DISTINCT workflow_id) AS total_workflows,
    ROUND(SUM(total_runs) / NULLIF(COUNT(DISTINCT user_id), 0), 1) AS runs_per_user,
    ROUND(AVG(duration_seconds), 2) AS avg_duration_seconds,
    MIN(run_timestamp) AS first_used_timestamp,
    MAX(run_timestamp) AS last_used_timestamp,
    sales_region,
    market_segment,
    MAX(contract_acv) AS contract_acv,
    is_global_2000,
    industry_vertical
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.SEM_AI_TOOLS_USER_DAILY
WHERE final_account_cid != 'Shadow Account'
GROUP BY 
    reporting_month,
    final_account_cid,
    billing_account_id,
    customer_name,
    company_group,
    license_type,
    tool_category,
    model_name,
    tool_action,
    sales_region,
    market_segment,
    is_global_2000,
    industry_vertical;
