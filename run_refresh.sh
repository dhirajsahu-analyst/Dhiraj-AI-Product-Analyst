#!/bin/bash
# Wrapper the launchd/cron job calls once every 24h to refresh the dashboard.
# Logs to refresh.log so failures are visible.
cd "$(dirname "$0")" || exit 1
echo "===== refresh started $(date) =====" >> refresh.log
/usr/bin/python3 refresh_dashboard.py --json >> refresh.log 2>&1
echo "===== refresh finished $(date) (exit $?) =====" >> refresh.log
