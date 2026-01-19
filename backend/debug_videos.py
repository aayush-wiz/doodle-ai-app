import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
db_url = DATABASE_URL.replace('+asyncpg', '')
if '?ssl=require' in db_url:
    db_url = db_url.replace('?ssl=require', '?sslmode=require')

conn = psycopg2.connect(db_url)
cur = conn.cursor()

# Check what's in videos table
print("=== ALL VIDEOS IN DB ===")
cur.execute("SELECT id, title, url, user_id, created_at FROM videos ORDER BY created_at DESC LIMIT 10;")
rows = cur.fetchall()
for row in rows:
    print(f"ID: {row[0]}, Title: {row[1][:50]}..., URL: {row[2]}, User: {row[3]}")

cur.close()
conn.close()
