import psycopg2
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Common passwords to test
passwords = ["admin", "postgres", "root", ""]
host = "localhost"
user = "postgres"
port = "5432"

print(f"Checking PostgreSQL on {host}:{port} with user '{user}'...")

found_pw = None
for pw in passwords:
    try:
        # Connect to default 'postgres' db first to check credentials
        conn = psycopg2.connect(
            host=host,
            user=user,
            password=pw,
            port=port,
            dbname="postgres",
            connect_timeout=3
        )
        print(f"  [v] Success with password: '{pw}'")
        found_pw = pw
        conn.close()
        break
    except Exception as e:
        print(f"  [x] Failed with password: '{pw}'")

if found_pw is not None:
    print("\nChecking if 'soe_spotify' database exists...")
    try:
        conn = psycopg2.connect(
            host=host,
            user=user,
            password=found_pw,
            port=port,
            dbname="postgres"
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT datname FROM pg_database;")
        databases = [r[0] for row in cur.fetchall() for r in [row]]
        
        if "soe_spotify" in databases:
            print("  [v] Database 'soe_spotify' EXISTS.")
        else:
            print("  [!] Database 'soe_spotify' DOES NOT EXIST.")
            print(f"      Available databases: {', '.join(databases)}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"  [!] Error while listing databases: {e}")
else:
    print("\n[!] Could not connect to PostgreSQL with common credentials.")
    print("    Is Docker/PostgreSQL running? Use 'docker ps' to check.")
