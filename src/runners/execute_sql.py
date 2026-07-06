import os
import sys
import snowflake.connector
from dotenv import load_dotenv

# Load local environment
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir  = os.path.dirname(current_dir)
load_dotenv(os.path.join(parent_dir, '.env'))

def get_connection():
    try:
        return snowflake.connector.connect(
            user=os.getenv('SNOWFLAKE_USER'), account=os.getenv('SNOWFLAKE_ACCOUNT'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'), database=os.getenv('SNOWFLAKE_DATABASE'),
            schema=os.getenv('SNOWFLAKE_SCHEMA'), role=os.getenv('SNOWFLAKE_ROLE'),
            authenticator=os.getenv('SNOWFLAKE_AUTHENTICATOR')
        )
    except Exception as e:
        print(f"❌ Failed to connect to Snowflake: {e}")
        print("Please run 'make connect' to initialize your credentials.")
        sys.exit(1)

def run_query(file_path):
    if not os.path.exists(file_path):
        print(f"❌ Error: File '{file_path}' not found.")
        sys.exit(1)

    print(f"🚀 Executing query from: {file_path}")
    print("🔗 Connecting to Snowflake (may prompt for SSO)...")
    
    with open(file_path, 'r') as f:
        sql = f.read()

    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(sql)
        # Fetch columns and data
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
        
        # Format as Markdown Table
        if not rows:
            print("\n✅ Query executed successfully. 0 rows returned.")
        else:
            print("\n" + "="*80)
            print("📊 QUERY RESULTS")
            print("="*80)
            
            # Create a simple fixed-width layout
            header = " | ".join([f"{col:<20}" for col in cols])
            print(header)
            print("-" * len(header))
            
            # Print up to 50 rows
            for row in rows[:50]:
                formatted_row = " | ".join([f"{str(val)[:20]:<20}" for val in row])
                print(formatted_row)
            
            if len(rows) > 50:
                print(f"... and {len(rows) - 50} more rows.")
                
            print("="*80)

    except Exception as e:
        print(f"\n❌ Error executing SQL: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 src/run_query.py <path/to/query.sql>")
        sys.exit(1)
    
    run_query(sys.argv[1])
