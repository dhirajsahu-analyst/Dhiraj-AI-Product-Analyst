-- ============================================================================
-- 📡 TELEMETRY DATA FRESHNESS AUDIT
-- Enforce: Always verify dataload sync status before compiling trend metrics.
-- ============================================================================

SELECT 
    'AI_TOOLS_USAGE_DAILY_USER' AS table_name,
    MIN(DAY) AS earliest_event_logged,
    MAX(DAY) AS latest_event_logged,
    DATEDIFF('day', MAX(DAY), CURRENT_DATE) AS pipeline_staleness_days,
    COUNT(*) AS total_row_count
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.AI_TOOLS_USAGE_DAILY_USER_SUMMARY_AT

UNION ALL

SELECT 
    'LLM_CONNECTIONS_DAILY_USER' AS table_name,
    MIN(DAY) AS earliest_event_logged,
    MAX(DAY) AS latest_event_logged,
    DATEDIFF('day', MAX(DAY), CURRENT_DATE) AS pipeline_staleness_days,
    COUNT(*) AS total_row_count
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.LLM_CONNECTIONS_DAILY_USER_SUMMARY_AT

UNION ALL

SELECT 
    'COPILOT_ACTIVITY_USAGE' AS table_name,
    MIN(CONV_CREATED_DATE) AS earliest_event_logged,
    MAX(CONV_CREATED_DATE) AS latest_event_logged,
    DATEDIFF('day', MAX(CONV_CREATED_DATE), CURRENT_DATE) AS pipeline_staleness_days,
    COUNT(*) AS total_row_count
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.COPILOT_ACTIVITY_USAGE_AT;
