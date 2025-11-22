#!/usr/bin/env python3
"""
Update Supabase embeddings table from 384 to 1536 dimensions
Migrates from SentenceTransformers to Azure OpenAI embeddings
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

print("🔄 Updating mba_embeddings table for Azure OpenAI Embeddings")
print("=" * 60)

# Connect to Supabase
conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    database='postgres',
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    port=int(os.getenv('DB_PORT', '6543')),
    sslmode='require'
)

cursor = conn.cursor()

print("\n📊 Current table status:")
try:
    cursor.execute("""
        SELECT COUNT(*) FROM mba_embeddings;
    """)
    count = cursor.fetchone()[0]
    print(f"   Current embeddings count: {count}")
except:
    print("   Table doesn't exist yet")

print("\n🔨 Updating schema...")

try:
    # Drop existing embeddings table (data will be regenerated)
    cursor.execute("DROP TABLE IF EXISTS mba_embeddings CASCADE;")
    print("   ✅ Dropped old mba_embeddings table")
    
    # Create new table with 1536-dimensional vectors
    cursor.execute("""
        CREATE TABLE mba_embeddings (
            id SERIAL PRIMARY KEY,
            university_id INTEGER REFERENCES universities(id),
            content_type VARCHAR(50),
            content_source VARCHAR(100),
            university_name VARCHAR(255),
            content_text TEXT,
            embedding vector(1536),
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("   ✅ Created new mba_embeddings table with vector(1536)")
    
    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_mba_embeddings_university 
        ON mba_embeddings(university_id);
    """)
    print("   ✅ Created university_id index")
    
    # Note: Vector index will be created after data is populated
    print("   ⚠️ Vector index will be created after embeddings are populated")
    
    conn.commit()
    
    print("\n✅ Schema update completed successfully!")
    print("\n📋 Next Steps:")
    print("   1. Run: python scraper.py (to regenerate embeddings with Azure OpenAI)")
    print("   2. After embeddings are created, run this to create vector index:")
    print("      CREATE INDEX mba_embeddings_vector_idx ON mba_embeddings")
    print("      USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);")
    
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()

cursor.close()
conn.close()

print("\n" + "=" * 60)
print("🎯 Migration Complete!")
print("\nIMPORTANT: Your embeddings table is now ready for Azure OpenAI")
print("embeddings (1536 dimensions) instead of SentenceTransformers")
print("(384 dimensions). You need to regenerate all embeddings.")
