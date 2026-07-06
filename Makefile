.PHONY: install clean help

help:
	@echo "Dhiraj AI Product Analyst - Quickstart Commands"
	@echo "-----------------------------------------------"
	@echo "make install    - Install Python dependencies (Snowflake CLI, Connectors)"
	@echo "make connect    - Run the interactive Snowflake SSO connector setup"
	@echo "make clean      - Remove __pycache__ and local env temp files"

install:
	pip install -r requirements.txt
	@echo "Dependencies installed. You can now run 'make connect'."

connect:
	python3 src/snowflake_connector.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Cleaned python cache files."
