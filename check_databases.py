import sqlite3

def inspect_db(db_path):
    print(f"\n=== {db_path} ===")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables: {[t[0] for t in tables]}")
        
        # Get row counts for each table
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} rows")
            
            # Get schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print(f"    Columns: {[col[1] for col in columns]}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_db("saas.db")
    inspect_db("database/business_ai.sqlite3")
