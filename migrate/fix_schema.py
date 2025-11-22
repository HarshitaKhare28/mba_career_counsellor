#!/usr/bin/env python3
"""
Quick fix: Add missing content_source column to mba_embeddings table in Supabase
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Supabase connection
conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    database='postgres',
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    port=int(os.getenv('DB_PORT', '6543')),
    sslmode='require'
)

cursor = conn.cursor()

print("🔧 Adding content_source column to mba_embeddings table...")

try:
    cursor.execute("""
        ALTER TABLE mba_embeddings 
        ADD COLUMN IF NOT EXISTS content_source VARCHAR(100);
    """)
    conn.commit()
    print("✅ Column added successfully!")
    
    # Verify
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'mba_embeddings'
        ORDER BY ordinal_position;
    """)
    
    print("\n📋 Current columns in mba_embeddings:")
    for row in cursor.fetchall():
        print(f"   • {row[0]}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()

cursor.close()
conn.close()
