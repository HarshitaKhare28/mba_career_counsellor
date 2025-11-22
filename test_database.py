#!/usr/bin/env python3
"""
Quick Database Setup Test
Tests if the database can be created and connected to
"""
import os
import sys
from pathlib import Path

# Add the project directory to Python path
sys.path.append(str(Path(__file__).parent))

from setup import create_database_if_not_exists, test_database_connection
from dotenv import load_dotenv

def main():
    print("🧪 Database Setup Test")
    print("=" * 40)
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("💡 Please create .env file from .env.template")
        return False
    
    load_dotenv()
    
    # Check environment variables
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ Environment variables configured")
    print(f"   Host: {os.getenv('DB_HOST')}")
    print(f"   Database: {os.getenv('DB_NAME')}")
    print(f"   User: {os.getenv('DB_USER')}")
    print(f"   Port: {os.getenv('DB_PORT')}")
    
    # Test database creation
    print("\n🔨 Testing database creation...")
    if create_database_if_not_exists():
        print("✅ Database creation successful")
        
        # Test connection
        print("\n🔌 Testing database connection...")
        if test_database_connection():
            print("✅ Database connection successful")
            print("\n🎉 Database setup test passed!")
            print("💡 You can now run: python scraper.py")
            return True
        else:
            print("❌ Database connection failed")
            return False
    else:
        print("❌ Database creation failed")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n💥 Database setup test failed")
        print("💡 Check your PostgreSQL installation and .env configuration")
        sys.exit(1)