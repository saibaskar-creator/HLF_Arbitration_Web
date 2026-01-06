import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def inspect_schema():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("❌ No DATABASE_URL found")
        return

    try:
        print(f"🔌 Connecting to: {url.split('@')[1] if '@' in url else 'DB'}...")
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        
        # Get all tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        
        if not tables:
            print("⚠️ No tables found in 'public' schema.")
        else:
            print(f"✅ Found {len(tables)} tables:")
            for t in tables:
                table_name = t[0]
                print(f"\n   📄 TABLE: {table_name}")
                
                # Get columns for each table
                cur.execute(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                """)
                cols = cur.fetchall()
                for c in cols:
                    print(f"      - {c[0]} ({c[1]}) {'NULL' if c[2]=='YES' else 'NOT NULL'}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    inspect_schema()
