import asyncio
from database import engine
from sqlalchemy import text

async def migrate():
    async with engine.begin() as conn:
        print("Migrating users table...")
        
        # Add plan column
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS plan VARCHAR DEFAULT 'free'"))
            print("Added 'plan' column.")
        except Exception as e:
            print(f"Error adding 'plan': {e}")

        # Add video_count column
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS video_count INTEGER DEFAULT 0"))
            print("Added 'video_count' column.")
        except Exception as e:
            print(f"Error adding 'video_count': {e}")
            
        print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
