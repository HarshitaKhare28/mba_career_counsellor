#!/usr/bin/env python3
"""
Setup script for MBA Bot Scraper
This script helps set up the environment and dependencies
"""

import subprocess
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

def run_command(command):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    try:
        load_dotenv()
        
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD'),
            'port': int(os.getenv('DB_PORT', '5432'))
        }
        
        # Add SSL mode for Supabase support
        if 'supabase' in db_config.get('host', '').lower():
            db_config['sslmode'] = 'require'
            print("ℹ️ Detected Supabase - Using SSL connection")
        
        database_name = os.getenv('DB_NAME', 'mba_data')
        
        if not db_config['password']:
            print("❌ DB_PASSWORD not found in .env file")
            return False
        
        # Check if this is Supabase (database already exists)
        if 'supabase' in db_config.get('host', '').lower():
            print("ℹ️ Supabase detected - Database 'postgres' is pre-created")
            # Just test connection and enable pgvector
            try:
                db_config['database'] = database_name
                conn = psycopg2.connect(**db_config)
                cursor = conn.cursor()
                
                # Enable pgvector extension
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                print("✅ pgvector extension enabled on Supabase")
                
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"❌ Error connecting to Supabase: {e}")
                return False
        
        # Local PostgreSQL - create database if needed
        try:
            conn = psycopg2.connect(**db_config)
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute("""
                SELECT 1 FROM pg_database WHERE datname = %s;
            """, (database_name,))
            
            if cursor.fetchone():
                print(f"✅ Database '{database_name}' already exists")
                conn.close()
                return True
            else:
                # Create the database
                cursor.execute(f'CREATE DATABASE "{database_name}";')
                print(f"✅ Created database '{database_name}'")
                conn.close()
                
                # Now connect to the new database and enable pgvector
                db_config['database'] = database_name
                conn = psycopg2.connect(**db_config)
                cursor = conn.cursor()
                
                # Enable pgvector extension
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                print("✅ Enabled pgvector extension")
                
                conn.commit()
                conn.close()
                return True
                
        except psycopg2.Error as e:
            if "already exists" in str(e):
                print(f"✅ Database '{database_name}' already exists")
                return True
            else:
                print(f"❌ Error creating database: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        return False

def test_database_connection():
    """Test database connection using environment variables"""
    try:
        load_dotenv()
        
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'mba_data'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD'),
            'port': int(os.getenv('DB_PORT', '5432'))
        }
        
        # Add SSL mode for Supabase support
        if 'supabase' in db_config.get('host', '').lower():
            db_config['sslmode'] = 'require'
        
        if not db_config['password']:
            print("❌ DB_PASSWORD not found in .env file")
            return False
            
        conn = psycopg2.connect(**db_config)
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def run_schema_update():
    """Run the schema update script"""
    try:
        success, output = run_command(f"{sys.executable} update_schema.py")
        if success:
            return True
        else:
            print(f"Schema update error: {output}")
            return False
    except Exception as e:
        print(f"Error running schema update: {e}")
        return False

def create_env_template():
    """Create .env.template file if it doesn't exist"""
    template_path = Path('.env.template')
    if not template_path.exists():
        template_content = """# Database Configuration
DB_HOST=localhost
DB_NAME=mba_data
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_PORT=5432

# Application Settings
FLASK_ENV=development
FLASK_DEBUG=true
"""
        template_path.write_text(template_content)
        print("✓ Created .env.template file")

def create_database_setup_script():
    """Create a manual database setup script as fallback"""
    script_path = Path('create_database.sql')
    if not script_path.exists():
        sql_content = """-- Manual Database Setup Script for MBA Bot
-- Run this in PostgreSQL if automatic database creation fails

-- Create the database
CREATE DATABASE mba_data;

-- Connect to the database
\\c mba_data;

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify setup
SELECT version();
SELECT * FROM pg_extension WHERE extname = 'vector';

-- You can now run: python scraper.py
"""
        script_path.write_text(sql_content)
        print("✓ Created create_database.sql for manual setup")

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("\n🔍 Checking Prerequisites:")
    print("-" * 30)
    
    issues = []
    
    # Check CSV file
    if os.path.exists("Online MBA Website with All Data.csv"):
        print("✓ CSV data file found")
    else:
        print("❌ 'Online MBA Website with All Data.csv' not found")
        issues.append("CSV data file missing")
    
    # Check .env file
    if os.path.exists(".env"):
        print("✓ .env file found")
        load_dotenv()
        if os.getenv('DB_PASSWORD'):
            print("✓ Database password configured")
        else:
            print("⚠️ Database password not set in .env")
            issues.append("Database password not configured")
    else:
        print("⚠️ .env file not found (using .env.template)")
        issues.append(".env file needs to be created")
    
    # Check PostgreSQL (try connection)
    try:
        import psycopg2
        print("✓ psycopg2 (PostgreSQL driver) available")
    except ImportError:
        print("❌ psycopg2 not installed")
        issues.append("PostgreSQL driver missing")
    
    return issues

def main():
    print("🚀 Setting up MBA Bot Scraper Environment")
    print("=" * 50)
    
    # Check Python version
    print(f"✓ Python version: {sys.version}")
    
    # Install pip if not available
    print("\n📦 Installing dependencies...")
    
    # Upgrade pip
    success, output = run_command(f"{sys.executable} -m pip install --upgrade pip")
    if success:
        print("✓ Pip upgraded successfully")
    else:
        print(f"❌ Failed to upgrade pip: {output}")
        return False
    
    # Install requirements
    success, output = run_command(f"{sys.executable} -m pip install -r requirements.txt")
    if success:
        print("✓ Dependencies installed successfully")
        print("✓ Core packages: pandas, requests, beautifulsoup4, psycopg2-binary")
        print("✓ AI packages: sentence-transformers, numpy, unstructured[pdf]")
        print("✓ Utility packages: python-dotenv, lxml")
    else:
        print(f"❌ Failed to install dependencies: {output}")
        print("Try installing individually:")
        print("pip install pandas requests beautifulsoup4 psycopg2-binary")
        print("pip install sentence-transformers numpy python-dotenv lxml")
        print("pip install 'unstructured[pdf]' openai")
        return False
    
    # Create directories
    print("\n📁 Creating directories...")
    os.makedirs("brochures", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    os.makedirs("static/css", exist_ok=True)
    os.makedirs("static/js", exist_ok=True)
    os.makedirs("static/images", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    print("✓ Directories created")
    
    # Create environment template and database setup script
    print("\n⚙️ Setting up environment configuration...")
    create_env_template()
    create_database_setup_script()
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️ Please create a .env file based on .env.template")
        print("Update the database credentials and other settings")
    
    # Setup database if .env exists
    env_path = Path('.env')
    if env_path.exists():
        print("\n�️ Setting up database...")
        if create_database_if_not_exists():
            print("✓ Database setup successful")
            
            print("\n�🔌 Testing database connection...")
            if test_database_connection():
                print("✓ Database connection successful")
                
                # Run schema update
                print("\n📊 Updating database schema...")
                if run_schema_update():
                    print("✓ Database schema updated with reviews and alumni status support")
                else:
                    print("⚠️ Schema update failed - you may need to run update_schema.py manually")
            else:
                print("❌ Database connection failed after creation - please check your .env settings")
        else:
            print("❌ Database creation failed - please check your PostgreSQL setup and .env settings")
            print("💡 Alternative: Run the SQL commands in 'create_database.sql' manually")
    
    print("\n🎯 Setup Complete! Next Steps:")
    print("=" * 50)
    print("1. 📁 Ensure 'Online MBA Website with All Data.csv' is in the project directory")
    print("2. 🔧 Configure .env file with your database credentials:")
    print("   - Copy .env.template to .env")
    print("   - Update DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT")
    print("3. 🐘 Install PostgreSQL with pgvector extension:")
    print("   - PostgreSQL: https://www.postgresql.org/download/")
    print("   - pgvector: https://github.com/pgvector/pgvector")
    print("   - Database will be created automatically!")
    print("4. 🚀 Run the scraper: python scraper.py")
    print("5. 📝 Run reviews scraper: python reviews_scraper.py (optional)")
    print("6. 🤖 Start the chatbot: python app.py")
    
    # Final prerequisite check
    issues = check_prerequisites()
    
    if issues:
        print(f"\n⚠️ Setup completed with {len(issues)} issue(s) to resolve:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print("\nPlease resolve these issues before running the scraper.")
    else:
        print("\n🎉 Setup completed successfully!")
        print("✅ All prerequisites met - ready to run!")
    
    print(f"\n📋 Summary:")
    print(f"   • Python version: {sys.version.split()[0]}")
    print(f"   • Working directory: {os.getcwd()}")
    print(f"   • Dependencies: Installed")
    print(f"   • Database schema: {'✓ Updated' if not issues else '⚠️ Needs configuration'}")
    
    return len(issues) == 0

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎯 Ready to proceed! Run these commands in order:")
        print("   1. python scraper.py          # Process MBA data and create embeddings")
        print("   2. python reviews_scraper.py  # Add reviews and alumni status (optional)")
        print("   3. python app.py              # Start the chatbot application")
    else:
        print("\n❌ Setup incomplete. Please resolve the issues above.")