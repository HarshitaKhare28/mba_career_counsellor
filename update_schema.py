#!/usr/bin/env python3
"""
Database schema update script to add Alumni Status and Reviews fields
"""
import psycopg2
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_database_schema():
    """Add new columns for Alumni Status and Reviews"""
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'mba_data'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD'),
        'port': int(os.getenv('DB_PORT', 5432))
    }
    
    # Add SSL mode for Supabase support
    if 'supabase' in db_config.get('host', '').lower():
        db_config['sslmode'] = 'require'
        logger.info("Detected Supabase connection - SSL enabled")
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        logger.info("Adding new columns to universities table...")
        
        # Add Alumni Status column
        cursor.execute("""
            ALTER TABLE universities 
            ADD COLUMN IF NOT EXISTS alumni_status BOOLEAN DEFAULT TRUE;
        """)
        
        # Add Reviews columns
        cursor.execute("""
            ALTER TABLE universities 
            ADD COLUMN IF NOT EXISTS review_rating DECIMAL(2,1) DEFAULT 0.0;
        """)
        
        cursor.execute("""
            ALTER TABLE universities 
            ADD COLUMN IF NOT EXISTS review_count INTEGER DEFAULT 0;
        """)
        
        cursor.execute("""
            ALTER TABLE universities 
            ADD COLUMN IF NOT EXISTS review_sentiment TEXT[];
        """)
        
        cursor.execute("""
            ALTER TABLE universities 
            ADD COLUMN IF NOT EXISTS review_source TEXT DEFAULT 'Not Available';
        """)
        
        conn.commit()
        
        # Verify the changes
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'universities' 
            AND column_name IN ('alumni_status', 'review_rating', 'review_count', 'review_sentiment', 'review_source')
            ORDER BY column_name;
        """)
        
        new_columns = cursor.fetchall()
        logger.info("Successfully added columns:")
        for col_name, data_type, nullable in new_columns:
            logger.info(f"  {col_name}: {data_type}")
        
        conn.close()
        logger.info("✅ Database schema updated successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating database schema: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔄 Updating database schema for Alumni Status and Reviews...")
    success = update_database_schema()
    if success:
        print("\n🎉 Schema update completed! Ready to add Alumni Status and Reviews features.")
    else:
        print("\n💥 Schema update failed. Please check the logs.")