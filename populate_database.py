#!/usr/bin/env python3
"""
Database Population Script
This script takes the embeddings from the JSON files created by demo_scraper.py
and populates a PostgreSQL database with pgvector extension for RAG chatbot usage.
"""

import json
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
from azure_embeddings import AzureEmbeddings
import logging
import os
from dotenv import load_dotenv
from typing import Dict, List, Any

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabasePopulator:
    def __init__(self):
        """Initialize the database populator"""
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'mba_data'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD'),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        
        # Load data from JSON files
        self.embeddings_data: Dict = {}
        self.scraped_content: Dict = {}
        self.downloaded_files: Dict = {}
        self.df: pd.DataFrame = pd.DataFrame()
        
        # Load Azure OpenAI embedding model
        self.embedding_model = AzureEmbeddings()
        logger.info("Using Azure OpenAI Embeddings (text-embedding-ada-002)")
        
    def load_data_files(self):
        """Load data from JSON files and CSV"""
        try:
            # Load embeddings
            logger.info("Loading embeddings from results/embeddings.json...")
            with open("results/embeddings.json", "r", encoding='utf-8') as f:
                self.embeddings_data = json.load(f)
            
            # Load scraped content
            logger.info("Loading scraped content from results/scraped_content.json...")
            with open("results/scraped_content.json", "r", encoding='utf-8') as f:
                self.scraped_content = json.load(f)
            
            # Load downloaded files info
            logger.info("Loading file info from results/downloaded_files.json...")
            with open("results/downloaded_files.json", "r", encoding='utf-8') as f:
                self.downloaded_files = json.load(f)
            
            # Load CSV data
            logger.info("Loading CSV data...")
            self.df = pd.read_csv("Online MBA Website with All Data.csv")
            # Fill NaN values with empty strings to avoid JSON serialization issues
            self.df = self.df.fillna('')
            
            logger.info("All data files loaded successfully!")
            return True
            
        except FileNotFoundError as e:
            logger.error(f"Required file not found: {e}")
            logger.error("Please run demo_scraper.py first to generate the required files.")
            return False
        except Exception as e:
            logger.error(f"Error loading data files: {e}")
            return False
    
    def setup_database(self):
        """Setup PostgreSQL database with pgvector extension and required tables"""
        try:
            # Connect to database
            logger.info("Connecting to PostgreSQL database...")
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Enable pgvector extension
            logger.info("Enabling pgvector extension...")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Drop existing tables if they exist
            logger.info("Creating/recreating database schema...")
            cursor.execute("DROP TABLE IF EXISTS mba_embeddings CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS universities CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS conversations CASCADE;")
            
            # Create universities table
            cursor.execute("""
                CREATE TABLE universities (
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create embeddings table with proper vector dimension
            cursor.execute("""
                CREATE TABLE mba_embeddings (
                    id SERIAL PRIMARY KEY,
                    university_id INTEGER REFERENCES universities(id),
                    content_type VARCHAR(50) NOT NULL,
                    content_source VARCHAR(50) NOT NULL,
                    content_text TEXT,
                    embedding vector(384),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create conversations table for chatbot memory
            cursor.execute("""
                CREATE TABLE conversations (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    user_message TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    context JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS mba_embeddings_vector_idx 
                ON mba_embeddings USING ivfflat (embedding vector_cosine_ops) 
                WITH (lists = 100);
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_universities_name ON universities(name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_content_type ON mba_embeddings(content_type);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);")
            
            conn.commit()
            conn.close()
            logger.info("Database schema setup completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Database setup error: {str(e)}")
            return False
    
    def _clean_row_data(self, row):
        """Clean pandas row data, replacing NaN values with empty strings"""
        cleaned = {}
        for k, v in dict(row).items():
            if pd.isna(v):
                cleaned[k] = ''
            else:
                cleaned[k] = v
        return cleaned
    
    def populate_universities_table(self):
        """Populate the universities table with data from CSV"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            logger.info("Populating universities table...")
            
            for _, row in self.df.iterrows():
                cursor.execute("""
                    INSERT INTO universities (
                        name, specialization, fees_per_semester, subsidy_cashback,
                        accreditations, website, landing_page_url, brochure_url,
                        brochure_file_path, raw_data
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        specialization = EXCLUDED.specialization,
                        fees_per_semester = EXCLUDED.fees_per_semester,
                        subsidy_cashback = EXCLUDED.subsidy_cashback,
                        accreditations = EXCLUDED.accreditations,
                        website = EXCLUDED.website,
                        landing_page_url = EXCLUDED.landing_page_url,
                        brochure_url = EXCLUDED.brochure_url,
                        brochure_file_path = EXCLUDED.brochure_file_path,
                        raw_data = EXCLUDED.raw_data;
                """, (
                    row['Brand University'],
                    row.get('Specialization', ''),
                    self._parse_fees(row.get('Course Fees', '')),
                    row.get('Subsidy Cashback on Full Payment', ''),
                    row.get('Accredations', ''),
                    row.get('Website', ''),
                    row.get('Landing Page Link', ''),
                    row.get('Brouchure Link', ''),
                    self.downloaded_files.get(row['Brand University'], ''),
                    json.dumps(self._clean_row_data(row))
                ))
            
            conn.commit()
            conn.close()
            logger.info(f"Successfully populated {len(self.df)} universities!")
            return True
            
        except Exception as e:
            logger.error(f"Error populating universities table: {str(e)}")
            return False
    
    def populate_embeddings_table(self):
        """Populate the embeddings table with vector embeddings"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            logger.info("Populating embeddings table...")
            
            total_embeddings = 0
            
            # Process all embeddings from JSON
            for content_type, embeddings in self.embeddings_data.items():
                logger.info(f"Processing {content_type} embeddings...")
                
                for key, embedding_info in embeddings.items():
                    # Parse the key to get university name and source
                    if '_webpage' in key:
                        university_name = key.replace('_webpage', '')
                        source = 'webpage'
                        content_text = self.scraped_content.get(university_name, '')[:2000]  # Limit content
                    elif '_brochure' in key:
                        university_name = key.replace('_brochure', '')
                        source = 'brochure'
                        content_text = f"Brochure content for {university_name}"
                    elif '_info' in key:
                        university_name = key.replace('_info', '')
                        source = 'university_info'
                        # Get structured info from CSV
                        row_data = self.df[self.df['Brand University'] == university_name]
                        if not row_data.empty:
                            row = row_data.iloc[0]
                            content_text = f"Fees: {row.get('Course Fees', 'N/A')} | Specialization: {row.get('Specialization', 'N/A')} | Accreditations: {row.get('Accredations', 'N/A')}"
                        else:
                            content_text = f"Information for {university_name}"
                    else:
                        continue
                    
                    # Get university ID
                    cursor.execute("SELECT id FROM universities WHERE name = %s", (university_name,))
                    result = cursor.fetchone()
                    if not result:
                        logger.warning(f"University not found in database: {university_name}")
                        continue
                    
                    university_id = result[0]
                    
                    # Prepare embedding vector
                    embedding_vector = np.array(embedding_info['embedding'])
                    
                    # Prepare metadata
                    metadata = {
                        'source': content_type,
                        'university': university_name,
                        'content_source': source,
                        'embedding_model': 'all-MiniLM-L6-v2',
                        'vector_dimension': len(embedding_vector)
                    }
                    
                    # Insert embedding
                    cursor.execute("""
                        INSERT INTO mba_embeddings (
                            university_id, content_type, content_source, content_text, 
                            embedding, metadata
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        university_id,
                        content_type,
                        source,
                        content_text,
                        embedding_vector.tolist(),
                        json.dumps(metadata)
                    ))
                    
                    total_embeddings += 1
            
            conn.commit()
            conn.close()
            logger.info(f"Successfully populated {total_embeddings} embeddings!")
            return True
            
        except Exception as e:
            logger.error(f"Error populating embeddings table: {str(e)}")
            return False
    
    def _parse_fees(self, fees_str):
        """Parse fees string to extract numeric value"""
        if not fees_str or pd.isna(fees_str):
            return None
        
        # Extract numbers from the fees string
        import re
        numbers = re.findall(r'\d+', str(fees_str))
        if numbers:
            return float(numbers[0])
        return None
    
    def verify_population(self):
        """Verify that data was populated correctly"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check universities count
            cursor.execute("SELECT COUNT(*) FROM universities;")
            uni_count = cursor.fetchone()[0]
            
            # Check embeddings count
            cursor.execute("SELECT COUNT(*) FROM mba_embeddings;")
            emb_count = cursor.fetchone()[0]
            
            # Check content types distribution
            cursor.execute("""
                SELECT content_type, content_source, COUNT(*) 
                FROM mba_embeddings 
                GROUP BY content_type, content_source
                ORDER BY content_type, content_source;
            """)
            distribution = cursor.fetchall()
            
            conn.close()
            
            logger.info(f"\n{'='*50}")
            logger.info("DATABASE POPULATION VERIFICATION")
            logger.info(f"{'='*50}")
            logger.info(f"Universities: {uni_count}")
            logger.info(f"Total Embeddings: {emb_count}")
            logger.info(f"\nEmbeddings Distribution:")
            for content_type, source, count in distribution:
                logger.info(f"  {content_type} -> {source}: {count}")
            logger.info(f"{'='*50}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during verification: {str(e)}")
            return False
    
    def populate_database(self):
        """Main method to populate the entire database"""
        logger.info("🚀 Starting database population process...")
        
        # Load data files
        if not self.load_data_files():
            return False
        
        # Setup database schema
        if not self.setup_database():
            return False
        
        # Populate universities table
        if not self.populate_universities_table():
            return False
        
        # Populate embeddings table
        if not self.populate_embeddings_table():
            return False
        
        # Verify population
        if not self.verify_population():
            return False
        
        logger.info("✅ Database population completed successfully!")
        logger.info("The database is now ready for the RAG chatbot!")
        return True

def main():
    """Main function"""
    populator = DatabasePopulator()
    success = populator.populate_database()
    
    if success:
        print("\n🎉 SUCCESS! Your PostgreSQL database is now populated with MBA data!")
        print("You can now run the chatbot application.")
    else:
        print("\n❌ FAILED! Please check the logs above for error details.")
        print("Make sure:")
        print("1. PostgreSQL is running with pgvector extension")
        print("2. Database credentials in .env are correct")
        print("3. You have run demo_scraper.py first to generate JSON files")

if __name__ == "__main__":
    main()