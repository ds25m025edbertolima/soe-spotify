import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

host = "localhost"
user = "postgres"
pw = "admin"
port = "5432"
dbname = "soe_spotify"

try:
    # Connect to postgres to create the database
    conn = psycopg2.connect(
        host=host,
        user=user,
        password=pw,
        port=port,
        dbname="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    print(f"Creating database '{dbname}'...")
    cur.execute(f"CREATE DATABASE {dbname};")
    print(f"Database '{dbname}' created successfully.")
    
    cur.close()
    conn.close()
except psycopg2.errors.DuplicateDatabase:
    print(f"Database '{dbname}' already exists.")
except Exception as e:
    print(f"Error: {e}")
