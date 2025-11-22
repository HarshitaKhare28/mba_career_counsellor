#!/usr/bin/env python3
"""
Supabase Setup Script for MBA Bot
Configures and tests Supabase connection with pgvector
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SupabaseSetup:
    def __init__(self):
        load_dotenv()
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'port': int(os.getenv('DB_PORT', '6543')),
            'sslmode': 'require'  # Supabase requires SSL
        }
    
    def validate_env_variables(self):
        """Validate that all required environment variables are set"""
        print("🔍 Validating environment variables...")
        
        required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            print("\n💡 Please update your .env file with Supabase credentials:")
            print("   DB_HOST=aws-0-region.pooler.supabase.com")
            print("   DB_USER=postgres.xxxxxxxxxxxxx")
            print("   DB_PASSWORD=your_supabase_password")
            print("   DB_PORT=6543")
            return False
        
        print("✅ Environment variables configured")
        return True
    
    def test_connection(self):
        """Test connection to Supabase database"""
        print("\n🔌 Testing Supabase connection...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Get PostgreSQL version
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ Connected to PostgreSQL")
            print(f"   Version: {version.split(',')[0]}")
            
            # Get current database
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()[0]
            print(f"   Database: {db_name}")
            
            # Get connection info
            print(f"   Host: {self.db_config['host']}")
            print(f"   Port: {self.db_config['port']}")
            print(f"   SSL: {self.db_config.get('sslmode', 'require')}")
            
            conn.close()
            return True
            
        except psycopg2.OperationalError as e:
            print(f"❌ Connection failed: {e}")
            print("\n💡 Troubleshooting tips:")
            print("   1. Verify your Supabase project is active")
            print("   2. Check your connection string in Supabase dashboard")
            print("   3. Ensure password is correct")
            print("   4. Try using direct connection (port 5432) instead")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def check_pgvector_extension(self):
        """Check if pgvector extension is installed"""
        print("\n📦 Checking pgvector extension...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check if vector extension exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_extension WHERE extname = 'vector'
                );
            """)
            
            exists = cursor.fetchone()[0]
            
            if exists:
                # Get vector extension version
                cursor.execute("""
                    SELECT extversion FROM pg_extension WHERE extname = 'vector';
                """)
                version = cursor.fetchone()[0]
                print(f"✅ pgvector extension installed (version {version})")
            else:
                print("⚠️ pgvector extension not enabled")
                print("   Attempting to enable...")
                
                try:
                    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    conn.commit()
                    print("✅ pgvector extension enabled successfully")
                except Exception as e:
                    print(f"❌ Failed to enable pgvector: {e}")
                    print("\n💡 Enable pgvector manually in Supabase SQL Editor:")
                    print("   CREATE EXTENSION IF NOT EXISTS vector;")
                    conn.close()
                    return False
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error checking pgvector: {e}")
            return False
    
    def check_existing_tables(self):
        """Check if tables already exist"""
        print("\n📊 Checking existing tables...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            tables = ['universities', 'mba_embeddings', 'conversations']
            existing_tables = []
            
            for table in tables:
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    );
                """)
                if cursor.fetchone()[0]:
                    existing_tables.append(table)
            
            if existing_tables:
                print(f"⚠️ Found existing tables: {', '.join(existing_tables)}")
                
                # Get row counts
                for table in existing_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table};")
                    count = cursor.fetchone()[0]
                    print(f"   • {table}: {count} rows")
                
                return existing_tables
            else:
                print("✅ No existing tables found (clean database)")
                return []
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error checking tables: {e}")
            return None
    
    def get_database_size(self):
        """Get database size information"""
        print("\n💾 Database storage information...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Get database size
            cursor.execute("SELECT pg_database_size(current_database());")
            size_bytes = cursor.fetchone()[0]
            size_mb = size_bytes / (1024 * 1024)
            
            print(f"   Database size: {size_mb:.2f} MB")
            
            # Supabase free tier limit
            free_tier_limit = 500  # MB
            usage_percent = (size_mb / free_tier_limit) * 100
            
            print(f"   Free tier usage: {usage_percent:.1f}% ({size_mb:.2f}/{free_tier_limit} MB)")
            
            if usage_percent > 80:
                print("   ⚠️ Warning: Approaching free tier storage limit")
            elif usage_percent > 100:
                print("   ❌ Warning: Exceeded free tier storage limit")
            else:
                print("   ✅ Storage within free tier limits")
            
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Could not retrieve database size: {e}")
    
    def create_tables(self):
        """Create all required tables in Supabase"""
        print("\n🔨 Creating database tables...")
        
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Universities table with reviews and alumni status
            print("   Creating universities table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS universities (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    specialization TEXT,
                    fees_per_semester NUMERIC,
                    subsidy_cashback TEXT,
                    accreditations TEXT,
                    website TEXT,
                    landing_page_url TEXT,
                    brochure_url TEXT,
                    brochure_file_path TEXT,
                    raw_data JSONB,
                    alumni_status BOOLEAN DEFAULT TRUE,
                    review_rating DECIMAL(2,1) DEFAULT 0.0,
                    review_count INTEGER DEFAULT 0,
                    review_sentiment TEXT[],
                    review_source TEXT DEFAULT 'Not Available',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("   ✅ Universities table created")
            
            # Vector embeddings table
            print("   Creating mba_embeddings table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mba_embeddings (
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
            print("   ✅ MBA embeddings table created")
            
            # Conversation history for chatbot
            print("   Creating conversations table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    user_message TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    context JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("   ✅ Conversations table created")
            
            # Create indexes for better performance
            print("   Creating indexes...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_universities_name ON universities(name);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_universities_rating ON universities(review_rating);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
            """)
            
            # Vector index (requires pgvector)
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS mba_embeddings_vector_idx ON mba_embeddings 
                    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
                """)
                print("   ✅ Vector index created")
            except Exception as e:
                print(f"   ⚠️ Vector index creation skipped (will be created when data is added): {e}")
            
            conn.commit()
            conn.close()
            
            print("✅ All tables and indexes created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            if conn is not None:
                conn.rollback()
                conn.close()
            return False
    
    def run_full_setup(self):
        """Run complete Supabase setup"""
        print("🚀 Supabase Setup for MBA Bot")
        print("=" * 60)
        
        # Step 1: Validate environment
        if not self.validate_env_variables():
            return False
        
        # Step 2: Test connection
        if not self.test_connection():
            return False
        
        # Step 3: Check pgvector
        if not self.check_pgvector_extension():
            return False
        
        # Step 4: Check existing tables
        existing_tables = self.check_existing_tables()
        if existing_tables is None:
            return False
        
        # Step 5: Create tables if they don't exist
        if not existing_tables:
            print("\n📋 No tables found. Creating database schema...")
            if not self.create_tables():
                return False
        else:
            print(f"\n✅ Found existing tables: {', '.join(existing_tables)}")
        
        # Step 6: Database size
        self.get_database_size()
        
        print("\n" + "=" * 60)
        print("✅ Supabase setup completed successfully!")
        print("\n📋 Next Steps:")
        
        if not existing_tables:
            print("   1. Run: python scraper.py (populate universities)")
            print("   2. Run: python reviews_scraper.py (add reviews)")
            print("   3. Run: python app.py (start chatbot)")
        else:
            print("   • Your database already has tables and data")
            print("   • Run: python app.py (start chatbot)")
            print("   • Or run: python validate_setup.py (verify setup)")

        
        return True

def main():
    """Main execution"""
    setup = SupabaseSetup()
    
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("\n💡 Create .env file with your Supabase credentials:")
        print("   1. Go to your Supabase project dashboard")
        print("   2. Navigate to Settings → Database")
        print("   3. Copy connection pooling string")
        print("   4. Update .env file with these values")
        print("\nSee 'supabase_setup.md' for detailed instructions.")
        return False
    
    success = setup.run_full_setup()
    
    if not success:
        print("\n❌ Setup incomplete. Please resolve the issues above.")
        print("📖 Read supabase_setup.md for detailed migration guide")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
