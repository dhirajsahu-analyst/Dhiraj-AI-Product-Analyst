-- ============================================================================
-- 🔌 LLM Connections Key Analytics
-- Enforce: Lowercase email joins when crossing product pipelines.
-- ============================================================================

-- Query 1: Paid Monthly Connections Setup Trend
SELECT 
    MONTH_DATE AS reporting_month,
    COUNT(DISTINCT ACCOUNT_CID) AS paid_active_accounts,
    COUNT(DISTINCT USER_EMAIL) AS paid_active_users,
    COUNT(DISTINCT CONNECTION_ID) AS total_connections_created
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.LLM_CONNECTIONS_DAILY_USER_SUMMARY_AV
WHERE DAY BETWEEN '2026-01-01' AND '2026-06-30'
  AND LICENSE_TYPE IN ('Subscription', 'Purchase')
  AND USER_EMAIL NOT LIKE '%alteryx%'
GROUP BY 1
ORDER BY 1 ASC;

-- Query 2: Mapped Connector Share Trend
SELECT 
    LLM_CONNECTOR_DISPLAY_NAME AS connector,
    COUNT(DISTINCT ACCOUNT_CID) AS paid_active_accounts,
    COUNT(DISTINCT USER_EMAIL) AS paid_active_users,
    COUNT(DISTINCT CONNECTION_ID) AS total_connections_created
FROM DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE.LLM_CONNECTIONS_DAILY_USER_SUMMARY_AV
WHERE DAY BETWEEN '2026-01-01' AND '2026-06-30'
  AND LICENSE_TYPE IN ('Subscription', 'Purchase')
  AND USER_EMAIL NOT LIKE '%alteryx%'
GROUP BY 1
ORDER BY total_connections_created DESC;
