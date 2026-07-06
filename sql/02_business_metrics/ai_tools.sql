-- ============================================================================
-- 📊 AI Tools Product Suite Analytics
-- Enforce: Standard license and employee filter rules.
-- ============================================================================

-- Query 1: Paid Monthly Active Users (MAU) & Active Account Trend
SELECT 
    MONTH_DATE AS reporting_month,
    COUNT(DISTINCT ACCOUNT_CID) AS paid_active_accounts,
    COUNT(DISTINCT USER_ID) AS paid_active_users,
    COUNT(*) AS total_runs
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.AI_TOOLS_USAGE_DAILY_USER_SUMMARY_AT
WHERE DAY BETWEEN '2026-01-01' AND '2026-06-30'
  AND LICENSE_TYPE IN ('Subscription', 'Purchase')
  AND USER_ID NOT LIKE '%alteryx%'
  AND SUCCESSFUL_RUN_FLAG = 1
GROUP BY 1
ORDER BY 1 ASC;

-- Query 2: GenAI Suite Tool Adoption, Volume, and Success Rates
SELECT 
    COALESCE(GEN_AI_TOOL_NAME, 'Other / Unknown') AS tool_name,
    COUNT(DISTINCT ACCOUNT_CID) AS paid_active_accounts,
    COUNT(DISTINCT USER_ID) AS paid_active_users,
    COUNT(*) AS total_runs,
    ROUND(SUM(SUCCESSFUL_RUN_FLAG) * 100.0 / NULLIF(COUNT(*), 0), 2) AS success_rate_pct
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.AI_TOOLS_USAGE_DAILY_USER_SUMMARY_AT
WHERE DAY BETWEEN '2026-01-01' AND '2026-06-30'
  AND LICENSE_TYPE IN ('Subscription', 'Purchase')
  AND USER_ID NOT LIKE '%alteryx%'
GROUP BY 1
ORDER BY total_runs DESC;
