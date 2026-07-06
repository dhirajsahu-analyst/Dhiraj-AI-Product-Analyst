#!/usr/bin/env python3
"""
❄️ Standardized Snowflake BYOC Connector Script

This script is designed for the Alteryx team to connect to Snowflake securely 
without hardcoding any personal credentials. It handles two modes:
1. Local `.env` configuration file.
2. Direct integration with the native Snowflake CLI configuration (`~/.snowflake/config.toml`).

If neither exists, it will interactively guide the user through setting up their 
connection and write a local, Git-ignored `.env` file for future runs.
"""

import os
import re
import sys
import snowflake.connector
from dotenv import load_dotenv

def parse_snowflake_cli_config():
    """Parses local ~/.snowflake/config.toml to extract connection profiles."""
    home_dir = os.path.expanduser("~")
    config_path = os.path.join(home_dir, ".snowflake", "config.toml")
    
    if not os.path.exists(config_path):
        return None
        
    profiles = {}
    current_profile = None
    
    # Simple, dependency-free TOML parser
    with open(config_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Match [connections.profile_name]
            profile_match = re.match(r"\[connections\.(.+?)\]", line)
            if profile_match:
                current_profile = profile_match.group(1)
                profiles[current_profile] = {}
                continue
            # Match key = "value"
            val_match = re.match(r"(.+?)\s*=\s*\"(.+?)\"", line)
            if val_match and current_profile:
                key = val_match.group(1).strip()
                val = val_match.group(2).strip()
                profiles[current_profile][key] = val
                
    return profiles if profiles else None

def get_connection_params():
    """Fetches connection details via .env, config.toml, or interactive input."""
    # 1. Attempt to load from existing .env
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(current_dir, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    user = os.getenv("SNOWFLAKE_USER")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
    database = os.getenv("SNOWFLAKE_DATABASE")
    schema = os.getenv("SNOWFLAKE_SCHEMA")
    role = os.getenv("SNOWFLAKE_ROLE")
    authenticator = os.getenv("SNOWFLAKE_AUTHENTICATOR", "externalbrowser")
    
    if all([account, user, warehouse, database, schema, role]):
        print("💡 Loaded connection details from local .env file.")
        return {
            "account": account, "user": user, "warehouse": warehouse,
            "database": database, "schema": schema, "role": role, "authenticator": authenticator
        }

    # 2. If no .env, attempt to read from native Snowflake CLI config
    print("🔍 No complete .env file found. Checking local Snowflake CLI profiles...")
    cli_profiles = parse_snowflake_cli_config()
    
    if cli_profiles:
        print("\n🎉 Found local Snowflake CLI profiles:")
        profile_names = list(cli_profiles.keys())
        for idx, name in enumerate(profile_names, 1):
            print(f"  [{idx}] {name} (User: {cli_profiles[name].get('user', 'unspecified')})")
            
        print("\nWould you like to import one of these profiles?")
        try:
            choice = input(f"Select profile [1-{len(profile_names)}] (or hit Enter to configure manually): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(profile_names):
                selected_profile = profile_names[int(choice) - 1]
                p = cli_profiles[selected_profile]
                
                # Extract and map variables
                params = {
                    "account": p.get("account"),
                    "user": p.get("user"),
                    "warehouse": p.get("warehouse", "EDM_WH"),
                    "database": p.get("database", "DISCOVERY_PRODUCT_MANAGEMENT"),
                    "schema": p.get("schema", "METRIC_STORE"),
                    "role": p.get("role"),
                    "authenticator": p.get("authenticator", "externalbrowser")
                }
                
                # Write to .env for future runs
                write_env_file(env_path, params)
                return params
        except KeyboardInterrupt:
            print("\nAborted.")
            sys.exit(0)
            
    # 3. Fallback to full interactive manual configuration
    print("\n✍️ Manual Snowflake Connection Setup:")
    print("Please enter your corporate connection details (your password is NOT required as SSO is enforced):")
    try:
        user_email = input("1. Enter your corporate email (SNOWFLAKE_USER): ").strip()
        account_loc = input("2. Enter your Snowflake account locator (SNOWFLAKE_ACCOUNT): ").strip()
        warehouse_nm = input("3. Enter your active Warehouse (SNOWFLAKE_WAREHOUSE) [EDM_WH]: ").strip() or "EDM_WH"
        database_nm = input("4. Enter Database (SNOWFLAKE_DATABASE) [DISCOVERY_PRODUCT_MANAGEMENT]: ").strip() or "DISCOVERY_PRODUCT_MANAGEMENT"
        schema_nm = input("5. Enter Schema (SNOWFLAKE_SCHEMA) [METRIC_STORE]: ").strip() or "METRIC_STORE"
        role_nm = input("6. Enter your Role Name (SNOWFLAKE_ROLE): ").strip()
        
        params = {
            "user": user_email,
            "account": account_loc,
            "warehouse": warehouse_nm,
            "database": database_nm,
            "schema": schema_nm,
            "role": role_nm,
            "authenticator": "externalbrowser"
        }
        
        write_env_file(env_path, params)
        return params
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(0)

def write_env_file(path, params):
    """Writes connection parameters to a local git-ignored .env file."""
    with open(path, "w") as f:
        f.write("# ❄️ Local Snowflake Credentials (Git-ignored)\n")
        for k, v in params.items():
            f.write(f"SNOWFLAKE_{k.upper()}={v}\n")
    print(f"\n💾 Successfully saved connection profile to local file: {path}")

def test_connection(p):
    """Initiates and tests a browser SSO connection to Snowflake."""
    print(f"\nAttempting secure SSO connection to {p['account']} as {p['user']}...")
    print("🔗 Opening your default browser for Okta / Azure AD authentication...")
    
    try:
        conn = snowflake.connector.connect(
            user=p["user"],
            account=p["account"],
            warehouse=p["warehouse"],
            database=p["database"],
            schema=p["schema"],
            role=p["role"],
            authenticator=p["authenticator"]
        )
        cur = conn.cursor()
        
        # Run test verification
        cur.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_VERSION()")
        user, role, wh, ver = cur.fetchone()
        
        print("\n" + "=" * 60)
        print("🎉 SNOWFLAKE CONNECTION SUCCESSFUL!")
        print("=" * 60)
        print(f"  User:      {user}")
        print(f"  Role:      {role}")
        print(f"  Warehouse: {wh}")
        print(f"  Version:   {ver}")
        print("=" * 60)
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"\n❌ Snowflake Connection Failed: {e}")
        print("\nTroubleshooting tips:")
        print("  1. Verify your SNOWFLAKE_ACCOUNT and SNOWFLAKE_ROLE values are correct.")
        print("  2. Ensure your local machine has an active, authenticated internet connection.")
        print("  3. Double-check that your active corporate VPN is connected if required.")

if __name__ == "__main__":
    params = get_connection_params()
    if params:
        test_connection(params)
