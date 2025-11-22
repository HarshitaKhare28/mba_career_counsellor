# What this file does:
# 1. Reads the file 'Online MBA Website with All Data.csv' and stores it in a dataframe.
# 2. Scrapes the URLs in the 'Landing Page Link' column of the dataframe.
# 3. Creates embeddings for the scraped content for storange in pgvector.
# 5. Downloads and stores the brouchers given in 'Brouchure Link' column in a local folder.
# 6. Creates embeddings for the brouchers for storage in pgvector using unstructured API.
# 7. Created embeddings for the remaining columns in the dataframe for storage in pgvector.
# 8. Stores all the embeddings in a pgvector database.

import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import logging
from urllib.parse import urljoin, urlparse
import time
import hashlib
import re
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from azure_embeddings import AzureEmbeddings
import numpy as np
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.auto import partition
import json
from pathlib import Path
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore")

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MBADataProcessor:
    def __init__(self, csv_file_path: str, brochures_folder: str = "brochures", 
                 db_config: Optional[Dict] = None):
        """
        Initialize the MBA Data Processor
        
        Args:
            csv_file_path: Path to the CSV file
            brochures_folder: Folder to store downloaded brochures
            db_config: Database configuration for pgvector
        """
        self.csv_file_path = csv_file_path
        self.brochures_folder = brochures_folder
        self.db_config = db_config or {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'mba_data'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password'),
            'port': int(os.getenv('DB_PORT', '5432'))
        }
        
        # Add SSL mode for Supabase support
        if 'supabase' in self.db_config.get('host', '').lower():
            self.db_config['sslmode'] = 'require'
            logger.info("Detected Supabase connection - SSL enabled")
        
        # Initialize Azure OpenAI embedding model
        self.embedding_model = AzureEmbeddings()
        logger.info("Using Azure OpenAI Embeddings (text-embedding-ada-002)")
        
        # Create directories
        os.makedirs(self.brochures_folder, exist_ok=True)
        
        # Initialize dataframe
        self.df = None
        
        # Session for web scraping
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def load_csv_data(self) -> pd.DataFrame:
        """
        Step 1: Read the CSV file and store it in a dataframe
        """
        try:
            logger.info(f"Loading CSV data from {self.csv_file_path}")
            self.df = pd.read_csv(self.csv_file_path)
            logger.info(f"Successfully loaded {len(self.df)} records")
            
            # Clean and prepare data
            self.df = self.df.fillna('')
            self.df['id'] = range(1, len(self.df) + 1)
            
            return self.df
        except Exception as e:
            logger.error(f"Error loading CSV file: {str(e)}")
            raise
    
    def scrape_landing_pages(self) -> Dict[str, str]:
        """
        Step 2: Scrape the URLs in the 'Landing Page Link' column
        """
        scraped_content = {}
        
        for index, row in self.df.iterrows():
            landing_page_url = row['Landing Page Link']
            if not landing_page_url or pd.isna(landing_page_url):
                continue
                
            try:
                logger.info(f"Scraping: {landing_page_url}")
                
                # Add delay to be respectful
                time.sleep(1)
                
                response = self.session.get(landing_page_url, timeout=30)
                response.raise_for_status()
                
                # Parse content with BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer"]):
                    script.decompose()
                
                # Extract text content
                text_content = soup.get_text()
                
                # Clean up text
                lines = (line.strip() for line in text_content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                # Store content with university name as key
                university_name = row['Brand University']
                scraped_content[university_name] = text[:5000]  # Limit content length
                
                logger.info(f"Successfully scraped content for {university_name}")
                
            except Exception as e:
                logger.error(f"Error scraping {landing_page_url}: {str(e)}")
                continue
        
        return scraped_content
    
    def download_brochures(self) -> Dict[str, str]:
        """
        Step 5: Download and store brochures from 'Brouchure Link' column
        """
        downloaded_files = {}
        
        for index, row in self.df.iterrows():
            brochure_url = row['Brouchure Link']
            university_name = row['Brand University']
            
            if not brochure_url or pd.isna(brochure_url):
                continue
            
            try:
                logger.info(f"Downloading brochure for {university_name}")
                
                # Generate filename
                url_hash = hashlib.md5(brochure_url.encode()).hexdigest()[:8]
                filename = f"{university_name.replace(' ', '_')}_{url_hash}.pdf"
                file_path = os.path.join(self.brochures_folder, filename)
                
                # Check if already downloaded
                if os.path.exists(file_path):
                    logger.info(f"Brochure already exists: {filename}")
                    downloaded_files[university_name] = file_path
                    continue
                
                # Download file
                response = self.session.get(brochure_url, timeout=60)
                response.raise_for_status()
                
                # Save file
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                downloaded_files[university_name] = file_path
                logger.info(f"Successfully downloaded brochure: {filename}")
                
                time.sleep(1)  # Be respectful
                
            except Exception as e:
                logger.error(f"Error downloading brochure for {university_name}: {str(e)}")
                continue
        
        return downloaded_files
    
    def create_embeddings_for_scraped_content(self, scraped_content: Dict[str, str]) -> Dict[str, np.ndarray]:
        """
        Step 3: Create embeddings for scraped content
        """
        embeddings = {}
        
        for university_name, content in scraped_content.items():
            if content:
                try:
                    logger.info(f"Creating embeddings for {university_name} scraped content")
                    embedding = self.embedding_model.encode(content)
                    embeddings[f"{university_name}_webpage"] = embedding
                except Exception as e:
                    logger.error(f"Error creating embeddings for {university_name}: {str(e)}")
        
        return embeddings
    
    def create_embeddings_for_brochures(self, downloaded_files: Dict[str, str]) -> Dict[str, np.ndarray]:
        """
        Step 6: Create embeddings for brochures using unstructured API
        """
        embeddings = {}
        
        for university_name, file_path in downloaded_files.items():
            try:
                logger.info(f"Processing brochure for {university_name}")
                
                # Extract text from PDF using unstructured
                elements = partition_pdf(filename=file_path)
                
                # Combine text elements
                text_content = ""
                for element in elements:
                    if hasattr(element, 'text'):
                        text_content += element.text + " "
                
                # Create embeddings if content exists
                if text_content.strip():
                    text_content = text_content[:8000]  # Limit content length
                    embedding = self.embedding_model.encode(text_content)
                    embeddings[f"{university_name}_brochure"] = embedding
                    logger.info(f"Created embeddings for {university_name} brochure")
                
            except Exception as e:
                logger.error(f"Error processing brochure for {university_name}: {str(e)}")
                continue
        
        return embeddings
    
    def create_embeddings_for_csv_data(self) -> Dict[str, np.ndarray]:
        """
        Step 7: Create embeddings for remaining columns in the dataframe
        """
        embeddings = {}
        
        # Columns to create embeddings for
        text_columns = ['Courses', 'Specialization', 'Brand University', 'Course Fees', 
                       'Subsidy Cashback on Full Payment', 'Accredations']
        
        for index, row in self.df.iterrows():
            university_name = row['Brand University']
            
            # Combine relevant text data
            combined_text = []
            for col in text_columns:
                if col in row and pd.notna(row[col]) and str(row[col]).strip():
                    combined_text.append(f"{col}: {str(row[col])}")
            
            if combined_text:
                text_content = " | ".join(combined_text)
                try:
                    embedding = self.embedding_model.encode(text_content)
                    embeddings[f"{university_name}_info"] = embedding
                    logger.info(f"Created embeddings for {university_name} information")
                except Exception as e:
                    logger.error(f"Error creating embeddings for {university_name} info: {str(e)}")
        
        return embeddings
    
    def setup_database(self):
        """
        Setup pgvector database and tables with reviews and alumni status support
        """
        try:
            # Connect to database
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Enable pgvector extension
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Create universities table with all required fields
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
            
            # Create embeddings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mba_embeddings (
                    id SERIAL PRIMARY KEY,
                    university_id INTEGER REFERENCES universities(id),
                    content_type VARCHAR(50),
                    university_name VARCHAR(255),
                    content_text TEXT,
                    embedding vector(384),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create conversations table for chatbot memory
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
            
            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS mba_embeddings_vector_idx 
                ON mba_embeddings USING ivfflat (embedding vector_cosine_ops) 
                WITH (lists = 100);
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_universities_name ON universities(name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_universities_rating ON universities(review_rating);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);")
            
            conn.commit()
            conn.close()
            logger.info("Database setup completed with reviews and alumni status support")
            
        except Exception as e:
            logger.error(f"Database setup error: {str(e)}")
            raise
    
    def populate_universities_table(self, scraped_content: Dict[str, str], 
                                  downloaded_files: Dict[str, str]) -> Dict[str, int]:
        """
        Populate universities table with CSV data and return university name to ID mapping
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Clear existing universities data
            cursor.execute("DELETE FROM universities;")
            
            university_ids = {}
            
            for index, row in self.df.iterrows():
                university_name = row['Brand University']
                
                # Extract fees (assuming format like "₹X per semester")
                fees_text = str(row.get('Course Fees', '0'))
                fees_per_semester = 0
                if fees_text and fees_text != 'nan':
                    # Extract numeric value from fees text
                    import re
                    fees_match = re.search(r'[\d,]+', fees_text.replace('₹', '').replace(',', ''))
                    if fees_match:
                        try:
                            fees_per_semester = float(fees_match.group())
                        except:
                            fees_per_semester = 0
                
                # Determine brochure file path
                brochure_file_path = downloaded_files.get(university_name, '')
                
                # Insert university data
                cursor.execute("""
                    INSERT INTO universities 
                    (name, specialization, fees_per_semester, subsidy_cashback, accreditations, 
                     landing_page_url, brochure_url, brochure_file_path, raw_data,
                     alumni_status, review_rating, review_count, review_sentiment, review_source)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    university_name,
                    str(row.get('Specialization', '')),
                    fees_per_semester,
                    str(row.get('Subsidy Cashback on Full Payment', '')),
                    str(row.get('Accredations', '')),
                    str(row.get('Landing Page Link', '')),
                    str(row.get('Brouchure Link', '')),
                    brochure_file_path,
                    json.dumps(row.to_dict(), default=str),
                    True,  # Default alumni_status to True for MBA programs
                    0.0,   # Default review_rating
                    0,     # Default review_count
                    [],    # Empty review_sentiment array
                    'Not Available'  # Default review_source
                ))
                
                university_id = cursor.fetchone()[0]
                university_ids[university_name] = university_id
                
            conn.commit()
            conn.close()
            logger.info(f"Successfully populated universities table with {len(university_ids)} universities")
            return university_ids
            
        except Exception as e:
            logger.error(f"Error populating universities table: {str(e)}")
            raise

    def scrape_and_update_reviews(self, university_ids: Dict[str, int]):
        """
        Scrape reviews and update universities with review data
        """
        try:
            # Import reviews scraper functionality
            from reviews_scraper import ReviewsScraper
            
            reviews_scraper = ReviewsScraper()
            
            for university_name, university_id in university_ids.items():
                logger.info(f"Updating reviews for {university_name}")
                reviews_scraper.update_university_reviews(university_id, university_name)
                time.sleep(1)  # Be respectful to servers
                
            logger.info("Successfully updated all university reviews")
            
        except ImportError:
            logger.warning("reviews_scraper.py not found. Skipping review updates.")
        except Exception as e:
            logger.error(f"Error updating reviews: {str(e)}")

    def store_embeddings_in_database(self, all_embeddings: Dict[str, Dict[str, np.ndarray]], 
                                   scraped_content: Dict[str, str], 
                                   downloaded_files: Dict[str, str],
                                   university_ids: Dict[str, int]):
        """
        Step 8: Store all embeddings in pgvector database with university references
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Clear existing embeddings data
            cursor.execute("DELETE FROM mba_embeddings;")
            
            for content_type, embeddings in all_embeddings.items():
                for key, embedding in embeddings.items():
                    # Parse key to get university name and type
                    if '_webpage' in key:
                        university_name = key.replace('_webpage', '')
                        data_type = 'webpage'
                        content_text = scraped_content.get(university_name, '')
                    elif '_brochure' in key:
                        university_name = key.replace('_brochure', '')
                        data_type = 'brochure'
                        content_text = f"Brochure content for {university_name}"
                    elif '_info' in key:
                        university_name = key.replace('_info', '')
                        data_type = 'info'
                        # Get info from dataframe
                        if self.df is not None:
                            row_data = self.df[self.df['Brand University'] == university_name]
                            if not row_data.empty:
                                content_text = str(row_data.iloc[0].to_dict())
                            else:
                                content_text = f"Information for {university_name}"
                        else:
                            content_text = f"Information for {university_name}"
                    else:
                        continue
                    
                    # Get university ID
                    university_id = university_ids.get(university_name)
                    if not university_id:
                        logger.warning(f"University ID not found for {university_name}")
                        continue
                    
                    # Prepare metadata
                    metadata = {
                        'source': content_type,
                        'university': university_name,
                        'data_type': data_type
                    }
                    
                    # Insert into database
                    cursor.execute("""
                        INSERT INTO mba_embeddings (university_id, content_type, university_name, content_text, embedding, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (university_id, data_type, university_name, content_text, embedding.tolist(), json.dumps(metadata)))
            
            conn.commit()
            conn.close()
            logger.info("Successfully stored all embeddings in database")
            
        except Exception as e:
            logger.error(f"Error storing embeddings in database: {str(e)}")
            raise
    
    def process_all_data(self):
        """
        Execute all steps in sequence with reviews and alumni status support
        """
        try:
            # Step 1: Load CSV data
            self.load_csv_data()
            if self.df is None:
                raise ValueError("Failed to load CSV data")
            
            # Step 2: Scrape landing pages
            logger.info("Starting web scraping...")
            scraped_content = self.scrape_landing_pages()
            
            # Step 3: Create embeddings for scraped content
            logger.info("Creating embeddings for scraped content...")
            webpage_embeddings = self.create_embeddings_for_scraped_content(scraped_content)
            
            # Step 5: Download brochures
            logger.info("Downloading brochures...")
            downloaded_files = self.download_brochures()
            
            # Step 6: Create embeddings for brochures
            logger.info("Creating embeddings for brochures...")
            brochure_embeddings = self.create_embeddings_for_brochures(downloaded_files)
            
            # Step 7: Create embeddings for CSV data
            logger.info("Creating embeddings for CSV data...")
            csv_embeddings = self.create_embeddings_for_csv_data()
            
            # Step 8: Setup database and populate universities
            logger.info("Setting up database...")
            self.setup_database()
            
            logger.info("Populating universities table...")
            university_ids = self.populate_universities_table(scraped_content, downloaded_files)
            
            # Step 9: Update universities with review data
            logger.info("Updating university reviews and alumni status...")
            self.scrape_and_update_reviews(university_ids)
            
            # Combine all embeddings
            all_embeddings = {
                'webpage': webpage_embeddings,
                'brochure': brochure_embeddings,
                'csv_data': csv_embeddings
            }
            
            logger.info("Storing embeddings in database...")
            self.store_embeddings_in_database(all_embeddings, scraped_content, downloaded_files, university_ids)
            
            logger.info("Data processing completed successfully!")
            
            # Print summary
            print(f"\nProcessing Summary:")
            print(f"- Total universities processed: {len(self.df)}")
            print(f"- Webpages scraped: {len(scraped_content)}")
            print(f"- Brochures downloaded: {len(downloaded_files)}")
            print(f"- Universities with reviews: {len(university_ids)}")
            print(f"- Total embeddings created: {sum(len(emb) for emb in all_embeddings.values())}")
            print(f"- Database tables: universities, mba_embeddings, conversations")
            
        except Exception as e:
            logger.error(f"Error in data processing: {str(e)}")
            raise

def main():
    """
    Main function to run the MBA data processor
    """
    # Configuration
    csv_file_path = "Online MBA Website with All Data.csv"
    
    # Check if CSV file exists
    if not os.path.exists(csv_file_path):
        logger.error(f"CSV file not found: {csv_file_path}")
        print(f"❌ Please ensure '{csv_file_path}' exists in the current directory")
        return False
    
    # Database configuration from environment variables
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'mba_data'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD'),
        'port': int(os.getenv('DB_PORT', '5432'))
    }
    
    # Check if database password is provided
    if not db_config['password']:
        logger.error("Database password not found in environment variables")
        print("❌ Please set DB_PASSWORD in your .env file")
        return False
    
    try:
        # Initialize processor
        processor = MBADataProcessor(
            csv_file_path=csv_file_path,
            brochures_folder="brochures",
            db_config=db_config
        )
        
        # Process all data
        processor.process_all_data()
        
        print("\n🎉 MBA data processing completed successfully!")
        print("✅ Database is ready for the chatbot application")
        return True
        
    except psycopg2.OperationalError as e:
        if "database" in str(e).lower() and "does not exist" in str(e).lower():
            logger.error(f"Database does not exist: {str(e)}")
            print("❌ Database does not exist!")
            print("💡 Run 'python setup.py' first to create the database")
            print("💡 Or manually run the SQL commands in 'create_database.sql'")
        else:
            logger.error(f"Database connection error: {str(e)}")
            print(f"❌ Database connection error: {str(e)}")
            print("💡 Check your database configuration in .env file")
        return False
    except Exception as e:
        logger.error(f"Main execution error: {str(e)}")
        print(f"❌ Error: {str(e)}")
        if "database" in str(e).lower():
            print("💡 This might be a database issue. Try running 'python setup.py' first")
        return False

if __name__ == "__main__":
    main()
