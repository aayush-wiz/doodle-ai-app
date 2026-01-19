import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
# R2 Public URL base - using the one from env or the hardcoded one if env is placeholder
R2_BASE_URL = os.getenv("R2_PUBLIC_URL", "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev")

# The 10 Seed Videos
SEED_VIDEOS = [
    {
        "title": "How Human Evolution Works",
        "author": "Evolution Studies",
        "views": "2.0M",
        "duration": "02:00",
        "image": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=800&auto=format&fit=crop",
        "category": "Science",
        "url_path": "category/how_the_human_evolution_works.mp4"
    },
    {
        "title": "How the Stock Market Works",
        "author": "Finance Hub",
        "views": "1.5M",
        "duration": "03:00",
        "image": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=800&auto=format&fit=crop",
        "category": "Technology",
        "url_path": "category/how_stock_market_works_in_new_york_and_london_tech_centers.mp4"
    },
    {
        "title": "How Linear Regression Works",
        "author": "ML Academy",
        "views": "890K",
        "duration": "02:15",
        "image": "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?q=80&w=800&auto=format&fit=crop",
        "category": "Math",
        "url_path": "category/how_linear_regression_works.mp4"
    },
    {
        "title": "Transformer Architecture Explained",
        "author": "AI Insights",
        "views": "950K",
        "duration": "02:45",
        "image": "https://images.unsplash.com/photo-1677442135703-1787eea5ce01?q=80&w=800&auto=format&fit=crop",
        "category": "Technology",
        "url_path": "category/what_is_encoder_decoder_transformer_architecture_and_how_it_works.mp4"
    },
    {
        "title": "How Human DNA Evolves",
        "author": "Biology Channel",
        "views": "1.1M",
        "duration": "01:50",
        "image": "https://images.unsplash.com/photo-1628595351029-c2bf17511435?q=80&w=800&auto=format&fit=crop",
        "category": "Science",
        "url_path": "category/how_the_human_dna_evolves.mp4"
    },
    {
        "title": "How Black Holes Are Formed",
        "author": "Cosmos Academy",
        "views": "2.3M",
        "duration": "01:45",
        "image": "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?q=80&w=800&auto=format&fit=crop",
        "category": "Science",
        "url_path": "category/how_black_holes_are_formed.mp4"
    },
    {
        "title": "How Black Holes Form",
        "author": "Space Explorers",
        "views": "1.8M",
        "duration": "01:30",
        "image": "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?q=80&w=800&auto=format&fit=crop",
        "category": "Science",
        "url_path": "category/how_black_holes_form.mp4"
    },
    {
        "title": "Special Theory of Relativity",
        "author": "Physics Pro",
        "views": "3.2M",
        "duration": "02:30",
        "image": "https://images.unsplash.com/photo-1507413245164-6160d8298b31?q=80&w=800&auto=format&fit=crop",
        "category": "Science",
        "url_path": "category/special_theory_of_relativity.mp4"
    },
    {
        "title": "LSTM with Self Attention",
        "author": "Deep Learning Lab",
        "views": "720K",
        "duration": "02:10",
        "image": "https://images.unsplash.com/photo-1555949963-aa79dcee981c?q=80&w=800&auto=format&fit=crop",
        "category": "Technology",
        "url_path": "category/lstm_with_self_attention.mp4"
    },
    {
        "title": "How a Combustion Engine Works",
        "author": "Engineering World",
        "views": "1.4M",
        "duration": "01:55",
        "image": "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?q=80&w=800&auto=format&fit=crop",
        "category": "Technology",
        "url_path": "category/combustion_engine.mp4"
    }
]

def setup_categories():
    print(f"Connecting to DB...")
    
    # Fix protocol for psycopg2 if needed (remove +asyncpg if present)
    db_url = DATABASE_URL.replace('+asyncpg', '')
    if '?ssl=require' in db_url:
        db_url = db_url.replace('?ssl=require', '?sslmode=require')

    
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # 1. Create Table (Drop if exists to reset)
        print("Creating table category_videos...")
        cur.execute("DROP TABLE IF EXISTS category_videos;")
        cur.execute("""
            CREATE TABLE category_videos (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                author VARCHAR(255),
                views VARCHAR(50),
                duration VARCHAR(50),
                image TEXT,
                category VARCHAR(100),
                url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 2. Insert Data
        print("Seeding data...")
        for vid in SEED_VIDEOS:
            full_url = f"{R2_BASE_URL}/{vid['url_path']}"
            cur.execute("""
                INSERT INTO category_videos (title, author, views, duration, image, category, url)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (vid['title'], vid['author'], vid['views'], vid['duration'], vid['image'], vid['category'], full_url))
            
        conn.commit()
        print(f"Successfully inserted {len(SEED_VIDEOS)} category videos.")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    setup_categories()
