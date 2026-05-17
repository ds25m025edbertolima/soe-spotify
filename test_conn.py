import os
os.environ["PGCLIENTENCODING"] = "UTF8"
import psycopg2
from dotenv import load_dotenv

load_dotenv(override=True)
url = os.getenv("DATABASE_URL")
print(f"Testing connection to: {url}")

try:
    conn = psycopg2.connect(url)
    print("SUCCESS")
    conn.close()
except Exception as e:
    print(f"FAILED: {type(e).__name__}")
    try:
        # Use repr to see raw bytes if possible
        print(f"Error (repr): {repr(e)}")
    except:
        print("Could not even print repr(e)")
