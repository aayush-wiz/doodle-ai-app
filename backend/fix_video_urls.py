import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev")

db_url = DATABASE_URL.replace('+asyncpg', '')
if '?ssl=require' in db_url:
    db_url = db_url.replace('?ssl=require', '?sslmode=require')

conn = psycopg2.connect(db_url)
cur = conn.cursor()

# Get all videos with local paths (not starting with http)
print("=== Fixing Video URLs ===")
cur.execute("SELECT id, title, url, r2_key FROM videos WHERE url NOT LIKE 'http%';")
rows = cur.fetchall()

for row in rows:
    video_id, title, old_url, r2_key = row
    
    # If r2_key exists, use it. Otherwise, derive from old_url
    if r2_key and r2_key.startswith('http'):
        # r2_key is already a full URL (shouldn't happen but check)
        new_url = r2_key
    elif r2_key:
        new_url = f"{R2_PUBLIC_URL}/{r2_key}"
    else:
        # Extract filename from local path
        filename = os.path.basename(old_url)
        new_url = f"{R2_PUBLIC_URL}/generated/{filename}"
    
    print(f"ID: {video_id} | Old: {old_url} | New: {new_url}")
    cur.execute("UPDATE videos SET url = %s WHERE id = %s;", (new_url, video_id))

conn.commit()
print(f"\nUpdated {len(rows)} videos.")

cur.close()
conn.close()
