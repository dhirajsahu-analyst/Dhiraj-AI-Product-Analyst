.PHONY: install clean help connect query

help:
	@echo "Dhiraj AI Product Analyst - Enterprise Commands"
	@echo "-----------------------------------------------"
	@echo "make install    - Install Python dependencies (Snowflake CLI, Connectors)"
	@echo "make connect    - Run the interactive Snowflake SSO BYOC setup"
	@echo "make query      - Execute a SQL metric file (Usage: make query file=sql/02_business_metrics/ai_tools.sql)"
	@echo "make clean      - Remove __pycache__ and local env temp files"

install:
	pip install -r requirements.txt
	@echo "Dependencies installed. You can now run 'make connect'."

connect:
	python3 src/auth/snowflake_sso.py

query:
	@if [ -z "$(file)" ]; then echo "Error: Please specify a file, e.g., make query file=sql/03_data_quality/freshness_check.sql"; exit 1; fi
	python3 src/runners/execute_sql.py $(file)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Cleaned python cache files."
