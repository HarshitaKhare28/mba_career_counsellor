# MBA Career Counselor Bot

A comprehensive AI-powered MBA career counseling application that scrapes MBA program data, analyzes reviews, provides alumni status information, and offers personalized recommendations through an intelligent chatbot interface.

## Features

### 🎓 Core Data Processing
1. **CSV Data Processing**: Reads and processes MBA program data from CSV files
2. **Web Scraping**: Scrapes landing pages of MBA programs to extract detailed content
3. **Brochure Download**: Downloads PDF brochures from university websites
4. **Embedding Creation**: Creates vector embeddings for all content using SentenceTransformers
5. **Database Storage**: Stores all embeddings in PostgreSQL with pgvector for efficient similarity search
6. **Content Processing**: Uses Unstructured API for PDF processing

### ⭐ New Enhanced Features
7. **Google Reviews Integration**: Scrapes and analyzes university reviews with sentiment analysis
8. **Alumni Status Tracking**: Determines and tracks alumni status for each university
9. **Rating System**: 5-star rating system with review counts and sentiment analysis
10. **Intelligent Chatbot**: AI-powered career counselor with university recommendations
11. **Responsive UI**: Modern web interface with university cards and detailed information

## Prerequisites

### Software Requirements
- Python 3.8 or higher
- **Database**: Choose one of the following:
  - **Option 1: Supabase** (Recommended - Cloud PostgreSQL with pgvector)
  - **Option 2: Local PostgreSQL** with pgvector extension
- Git (optional)

### Database Setup

#### Option A: Supabase (Recommended for Production)

**Why Supabase?**
- ✅ No local PostgreSQL installation needed
- ✅ Built-in pgvector extension
- ✅ Free tier with 500MB storage
- ✅ Automatic backups
- ✅ Managed and scalable

**Quick Setup:**
1. **Create account**: Go to [supabase.com](https://supabase.com) and sign up
2. **Create project**: Click "New Project" and fill in details
3. **Get credentials**: Go to Settings → Database → Connection string
4. **Update .env**: Copy connection details to your `.env` file

```env
DB_HOST=aws-0-us-east-1.pooler.supabase.com
DB_NAME=postgres
DB_USER=postgres.xxxxxxxxxxxxx
DB_PASSWORD=your_supabase_password
DB_PORT=6543  # Connection pooling port
```

5. **Enable pgvector**: Run in Supabase SQL Editor:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

6. **Run setup**: 
   ```bash
   python setup_supabase.py  # Verify Supabase setup
   python scraper.py         # Populate data
   ```

📖 **Detailed Guide**: See [`supabase_setup.md`](supabase_setup.md) for complete migration instructions

#### Option B: Local PostgreSQL with pgvector

1. **Install PostgreSQL**:
   - Windows: Download from [postgresql.org](https://www.postgresql.org/download/windows/)
   - macOS: `brew install postgresql`
   - Ubuntu: `sudo apt-get install postgresql postgresql-contrib`

2. **Install pgvector extension**:
   ```bash
   # Clone the pgvector repository
   git clone https://github.com/pgvector/pgvector.git
   cd pgvector
   
   # Build and install (Linux/macOS)
   make
   sudo make install
   
   # For Windows, use the pre-built binaries or Docker
   ```

3. **Database Setup**:
   ```sql
   -- The setup script will create this automatically, but if needed manually:
   CREATE DATABASE mba_data;
   \c mba_data
   CREATE EXTENSION vector;
   ```

## Quick Start

### Option 1: Supabase (Cloud Database - Recommended)

```bash
# Clone the repository
git clone https://github.com/Ankit0431/MBA_Career_Counceller.git
cd MBA_Career_Counceller

# Install dependencies
python setup.py

# Configure Supabase credentials in .env
# Get from: Supabase Dashboard → Settings → Database
cp .env.template .env
# Edit .env with your Supabase credentials

# Verify Supabase connection
python setup_supabase.py

# Populate database
python scraper.py
python reviews_scraper.py

# Start the application
python app.py
```

### Option 2: Local PostgreSQL

```bash
# Clone the repository
git clone https://github.com/Ankit0431/MBA_Career_Counceller.git
cd MBA_Career_Counceller

# Run complete setup (installs dependencies, sets up database, processes data)
python full_setup.py

# Start the application
python app.py
```

### Option 3: Complete Automatic Setup (Local DB)

```bash
# Install dependencies and set up environment
python setup.py
```

#### Step 2: Database Configuration
```bash
# Update database schema with new fields
python update_schema.py
```

#### Step 3: Data Processing
```bash
# Process MBA data and create embeddings
python scraper.py

# Add reviews and alumni status (optional but recommended)
python reviews_scraper.py
```

#### Step 4: Validation and Launch
```bash
# Validate setup
python validate_setup.py

# Start the application
python app.py
```

## Configuration

### Environment Variables
Copy `.env.template` to `.env` and update with your settings:

DB_NAME=mba_data
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_PORT=5432

# Application Settings (optional)
FLASK_ENV=development
FLASK_DEBUG=true
```

### Required Files
- `Online MBA Website with All Data.csv` in the project root directory

## Usage

### Running Individual Components

```bash
# Set up environment and dependencies
python setup.py

# Update database schema with new fields
python update_schema.py

# Process data and create embeddings
python scraper.py

# Add reviews and alumni status
python reviews_scraper.py

# Start the web application
python app.py

# Validate setup
python validate_setup.py
```

### Application Components

#### 1. Data Processing (`scraper.py`)
- **Load CSV Data**: Reads MBA programs from CSV into pandas DataFrame
- **Web Scraping**: Extracts content from university landing pages
- **Brochure Processing**: Downloads and processes PDF brochures
- **Embedding Creation**: Generates vector embeddings using SentenceTransformers
- **Database Population**: Creates and populates universities table
- **Vector Storage**: Stores embeddings in pgvector for similarity search

#### 2. Reviews Integration (`reviews_scraper.py`)  
- **Review Scraping**: Simulates Google reviews collection (demo implementation)
- **Sentiment Analysis**: Analyzes review sentiments and ratings
- **Alumni Status**: Determines alumni benefits for each university
- **Database Updates**: Updates universities with review data

#### 3. Web Application (`app.py`)
- **Chatbot Interface**: AI-powered MBA career counselor
- **University Cards**: Interactive cards with detailed information
- **Search & Filter**: Advanced filtering by rating, fees, location
- **Responsive Design**: Modern web interface for all devices

## Project Structure

```
MBABOT/
├── app.py                    # Flask web application
├── chatbot.py               # AI chatbot logic
├── scraper.py               # Data processing and embeddings
├── reviews_scraper.py       # Reviews and alumni status scraper
├── update_schema.py         # Database schema updates
├── setup.py                 # Environment setup script
├── full_setup.py           # Complete automated setup
├── validate_setup.py       # Setup validation script
├── populate_database.py    # Database population utilities
├── requirements.txt        # Python dependencies
├── .env.template           # Environment configuration template
├── Online MBA Website with All Data.csv  # Input data
├── brochures/              # Downloaded PDF brochures
│   ├── Jain_University_Online_abc123.pdf
│   ├── Amity_University_Online_def456.pdf
│   └── ...
├── static/                 # Web assets
│   ├── css/style.css      # Stylesheets
│   ├── js/chat.js         # JavaScript for chatbot
│   └── images/            # Static images
├── templates/              # HTML templates
│   ├── index.html         # Main chat interface
│   ├── 404.html          # Error pages
│   └── 500.html
├── results/               # Processing results
├── logs/                  # Application logs
└── summaries and tests/   # Documentation and tests
```

### Database Schema

The application creates the following table structure:

```sql
-- Universities table with reviews and alumni status
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
    alumni_status BOOLEAN DEFAULT TRUE,
    review_rating DECIMAL(2,1) DEFAULT 0.0,
    review_count INTEGER DEFAULT 0,
    review_sentiment TEXT[],
    review_source TEXT DEFAULT 'Not Available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vector embeddings table
CREATE TABLE mba_embeddings (
    id SERIAL PRIMARY KEY,
    university_id INTEGER REFERENCES universities(id),
    content_type VARCHAR(50),      -- 'webpage', 'brochure', 'info'
    university_name VARCHAR(255),  -- University name
    content_text TEXT,             -- Original text content
    embedding vector(384),         -- Vector embedding (384 dimensions)
    metadata JSONB,               -- Additional metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversation history for chatbot
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    context JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Features in Detail

### Web Scraping
- Respectful scraping with delays
- User-agent rotation
- Error handling and retries
- Content cleaning (removes scripts, styles, navigation)

### Brochure Processing
- Automatic PDF download
- Duplicate detection (hash-based)
- Text extraction using Unstructured API
- Error handling for corrupted files

### Embedding Creation
- Uses SentenceTransformers (all-MiniLM-L6-v2 model)
- 384-dimensional embeddings
- Batch processing for efficiency
- Memory optimization

### Database Operations
- Automatic table creation
- Vector similarity indexing
- Metadata storage
- Transaction safety

## Querying the Database

### Example Similarity Searches

```python
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer

# Connect to database
conn = psycopg2.connect(
    host="localhost",
    database="mba_data",
    user="postgres",
    password="your_password"
)

# Create embedding for search query
model = SentenceTransformer('all-MiniLM-L6-v2')
query = "affordable MBA with finance specialization"
query_embedding = model.encode(query)

# Search for similar content
cursor = conn.cursor()
cursor.execute("""
    SELECT university_name, content_type, content_text,
           1 - (embedding <=> %s::vector) as similarity
    FROM mba_embeddings
    ORDER BY embedding <=> %s::vector
    LIMIT 5;
""", (query_embedding.tolist(), query_embedding.tolist()))

results = cursor.fetchall()
for result in results:
    print(f"University: {result[0]}")
    print(f"Type: {result[1]}")
    print(f"Similarity: {result[3]:.4f}")
    print(f"Content: {result[2][:200]}...")
    print("-" * 50)
```

## Database Migration

### Migrating from Local PostgreSQL to Supabase

If you have an existing local database and want to move to Supabase:

```bash
# Run the migration script
python migrate_to_supabase.py
```

The script will:
1. Connect to your local PostgreSQL database
2. Export all data (universities, embeddings, conversations)
3. Connect to Supabase
4. Import all data to Supabase
5. Verify the migration

**Alternative: Manual Migration**
```bash
# Export from local
pg_dump -h localhost -U postgres mba_data > local_backup.sql

# Import to Supabase (get connection string from Supabase dashboard)
psql "postgresql://postgres.xxx:password@aws-0-region.pooler.supabase.com:6543/postgres" < local_backup.sql
```

### Starting Fresh with Supabase

If you don't have existing data:

```bash
# Just run the scrapers with Supabase credentials in .env
python scraper.py
python reviews_scraper.py
```

## Troubleshooting

### Supabase-Specific Issues

1. **SSL Connection Error**:
   - Supabase requires SSL connections
   - The scripts automatically add `sslmode=require` for Supabase
   - If issues persist, try direct connection (port 5432)

2. **Connection Timeout**:
   - Check your internet connection
   - Verify Supabase project is active (not paused)
   - Try switching between pooling (6543) and direct (5432) ports

3. **Too Many Connections** (Free tier limit):
   - Use connection pooling (port 6543)
   - Ensure connections are being closed properly
   - Free tier: max 15 pooled connections

4. **Storage Limit** (Free tier: 500MB):
   - Check usage in Supabase Dashboard → Database
   - Optimize by removing unnecessary data
   - Upgrade to paid tier if needed

### Common Issues

1. **Database Connection Error**:
   - **Local**: Verify PostgreSQL is running
   - **Supabase**: Check credentials and internet connection
   - Check credentials in `.env` file
   - Ensure pgvector extension is installed

2. **Import Errors**:
   - Run `pip install -r requirements.txt`
   - Check Python version compatibility

3. **PDF Processing Errors**:
   - Some PDFs might be corrupted or protected
   - The script continues processing other files

4. **Memory Issues**:
   - Large CSV files might require more RAM
   - Consider processing in batches for very large datasets

### Performance Optimization

1. **Batch Processing**: Process embeddings in batches
2. **Database Indexing**: Ensure vector indexes are created
3. **Content Limiting**: Truncate very long text content
4. **Parallel Processing**: Use threading for I/O operations

## New Features (v2.0)

### 🌟 Reviews and Alumni Status Integration

#### Reviews Scraper (`reviews_scraper.py`)
- **Intelligent Review Simulation**: Generates realistic review data based on university prestige
- **5-Star Rating System**: Comprehensive rating with review counts
- **Sentiment Analysis**: Positive and negative sentiment extraction
- **Multi-Source Support**: Designed for Google Reviews, expandable to other platforms

#### Alumni Status Tracking
- **Smart Detection**: Determines alumni benefits for each MBA program  
- **Database Integration**: Seamlessly integrated with university profiles
- **Career Benefits**: Helps students understand post-graduation networking opportunities

#### Enhanced Web Interface
- **University Cards**: Beautiful, responsive cards with all key information
- **Review Display**: Star ratings, review counts, and sentiment highlights
- **Alumni Badge**: Clear indication of alumni status benefits
- **Advanced Filtering**: Filter by ratings, fees, alumni status, and more

### 🚀 Setup Automation

#### Complete Setup Script (`full_setup.py`)
- **One-Command Setup**: Automated installation and configuration
- **Progress Tracking**: Step-by-step progress with clear status updates
- **Error Handling**: Graceful error handling with helpful messages
- **Validation**: Automatic validation of each setup step

#### Validation Tools (`validate_setup.py`)
- **Database Health Check**: Comprehensive database structure validation
- **Data Verification**: Ensures all required data is properly loaded
- **Performance Check**: Validates indexes and query performance
- **Summary Reports**: Detailed reports on database contents

### 🎯 User Experience Improvements

#### Smart Career Counseling
- **Context-Aware Responses**: AI understands user preferences and constraints
- **University Recommendations**: Personalized suggestions based on user criteria
- **Review Integration**: Recommendations include peer review insights
- **Alumni Network Consideration**: Factors in alumni networking opportunities

## Development

### Class Structure
```
MBADataProcessor (scraper.py)
├── load_csv_data()                    # Load and validate CSV data
├── scrape_landing_pages()             # Extract university website content  
├── create_embeddings_for_scraped_content()  # Generate web content embeddings
├── download_brochures()               # Download and store PDF brochures
├── create_embeddings_for_brochures()  # Process PDF content into embeddings
├── populate_universities_table()      # Create and populate universities table
├── scrape_and_update_reviews()       # Integrate review data
└── store_embeddings_in_database()    # Store all embeddings with references

ReviewsScraper (reviews_scraper.py)
├── scrape_google_reviews()           # Extract review data (simulated)
├── determine_alumni_status()         # Analyze alumni benefits
├── update_university_reviews()       # Update individual university data
└── scrape_all_universities()         # Process all universities in batch
```

### Contributing

We welcome contributions! Here's how you can help:

1. **Real Review Integration**: Replace simulated reviews with actual Google Reviews API
2. **Additional Data Sources**: Add support for more review platforms (Glassdoor, LinkedIn, etc.)
3. **Enhanced AI**: Improve the chatbot's conversation capabilities
4. **UI/UX Improvements**: Enhance the web interface design
5. **Performance Optimization**: Optimize database queries and embedding operations

### Roadmap

- [ ] **Real Google Reviews API Integration**
- [ ] **Multi-language Support** 
- [ ] **Mobile App Development**
- [ ] **Advanced Analytics Dashboard**
- [ ] **Social Media Integration**
- [ ] **Video Content Processing**
- [ ] **Career Outcome Tracking**

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **SentenceTransformers** for embedding generation
- **pgvector** for efficient vector similarity search  
- **Unstructured** for PDF processing capabilities
- **Flask** for the web application framework
- **Beautiful Soup** for web scraping capabilities

## Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Run `python validate_setup.py` to diagnose problems  
3. Review the logs in the `logs/` directory
4. Open an issue on GitHub with detailed error information

---

**🎓 Ready to help students find their perfect MBA program!** 🚀
│   ├── create_embeddings_for_brochures()  # Step 6: PDF embeddings
│   ├── create_embeddings_for_csv_data()   # Step 7: CSV embeddings
│   ├── setup_database()          # Database setup
│   ├── store_embeddings_in_database()  # Step 8: Store embeddings
│   └── process_all_data()        # Main orchestrator
```

### Extending the Application

1. **Add New Content Types**: Modify embedding creation methods
2. **Different Embedding Models**: Change the SentenceTransformers model
3. **Additional Metadata**: Extend the metadata JSON structure
4. **Custom Scrapers**: Add domain-specific scraping logic

## License

This project is open-source. Please ensure you comply with the terms of service of the websites you're scraping.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review error logs in the `logs/` directory
3. Ensure all dependencies are correctly installed
4. Verify database setup and connections