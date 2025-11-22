#!/usr/bin/env python3
"""
Database Validation Script
Checks if the database is properly set up with all required tables and data
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

def validate_database():
    """Validate database setup and data"""
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'mba_data'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD'),
        'port': int(os.getenv('DB_PORT', '5432'))
    }
    
    if not db_config['password']:
        print("❌ Database password not found in environment variables")
        return False
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        print("🔍 Database Validation Report")
        print("=" * 50)
        
        # Check if pgvector extension is installed
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        if cursor.fetchone():
            print("✅ pgvector extension installed")
        else:
            print("❌ pgvector extension not found")
            return False
        
        # Check tables exist
        tables = ['universities', 'mba_embeddings', 'conversations']
        for table in tables:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table}'
                );
            """)
            if cursor.fetchone()[0]:
                print(f"✅ Table '{table}' exists")
            else:
                print(f"❌ Table '{table}' missing")
                return False
        
        # Check universities table structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'universities'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        
        required_columns = [
            'id', 'name', 'specialization', 'fees_per_semester', 'subsidy_cashback',
            'accreditations', 'website', 'landing_page_url', 'brochure_url',
            'brochure_file_path', 'raw_data', 'alumni_status', 'review_rating',
            'review_count', 'review_sentiment', 'review_source', 'created_at'
        ]
        
        existing_columns = [col[0] for col in columns]
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        if missing_columns:
            print(f"❌ Missing columns in universities table: {missing_columns}")
            return False
        else:
            print("✅ Universities table has all required columns")
        
        # Check data counts
        cursor.execute("SELECT COUNT(*) FROM universities;")
        university_count = cursor.fetchone()[0]
        print(f"📊 Universities in database: {university_count}")
        
        cursor.execute("SELECT COUNT(*) FROM mba_embeddings;")
        embedding_count = cursor.fetchone()[0]
        print(f"📊 Embeddings in database: {embedding_count}")
        
        # Check review data
        cursor.execute("SELECT COUNT(*) FROM universities WHERE review_rating > 0;")
        reviewed_count = cursor.fetchone()[0]
        print(f"📊 Universities with reviews: {reviewed_count}")
        
        cursor.execute("SELECT COUNT(*) FROM universities WHERE alumni_status = true;")
        alumni_count = cursor.fetchone()[0]
        print(f"📊 Universities with alumni status: {alumni_count}")
        
        # Sample data check
        cursor.execute("""
            SELECT name, review_rating, review_count, alumni_status 
            FROM universities 
            WHERE review_rating > 0 
            LIMIT 5;
        """)
        sample_data = cursor.fetchall()
        
        if sample_data:
            print("\n📋 Sample University Data:")
            print("-" * 30)
            for name, rating, count, alumni in sample_data:
                print(f"• {name}: {rating}/5 ({count} reviews), Alumni: {alumni}")
        else:
            print("⚠️ No review data found - consider running reviews_scraper.py")
        
        conn.close()
        
        # Overall assessment
        if university_count > 0 and embedding_count > 0:
            print(f"\n🎉 Database validation passed!")
            print("✅ Your MBA Bot database is ready for use")
            return True
        else:
            print(f"\n❌ Database validation failed - missing data")
            return False
            
    except Exception as e:
        print(f"❌ Database validation error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Validating MBA Bot Database Setup...")
    success = validate_database()
    
    if success:
        print("\n✨ Ready to start the MBA Bot application!")
        print("Run: python app.py")
    else:
        print("\n💥 Database validation failed. Please check the setup.")
        print("Try running: python full_setup.py")