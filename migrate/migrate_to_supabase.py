#!/usr/bin/env python3
"""
Migration Script: Local PostgreSQL to Supabase
Exports data from local database and imports to Supabase
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self):
        load_dotenv()
        
    def get_local_config(self):
        """Get local database configuration"""
        print("\n📍 Local Database Configuration")
        
        # Try to get from .env first (if using local PostgreSQL)
        env_host = os.getenv('DB_HOST', 'localhost')
        env_name = os.getenv('DB_NAME', 'mba_data')
        env_user = os.getenv('DB_USER', 'postgres')
        env_password = os.getenv('DB_PASSWORD', '')
        env_port = os.getenv('DB_PORT', '5432')
        
        # Check if .env has local PostgreSQL credentials
        if env_host in ['localhost', '127.0.0.1'] and env_name != 'postgres':
            print("✅ Found local database credentials in .env file")
            print(f"   Host: {env_host}")
            print(f"   Database: {env_name}")
            print(f"   User: {env_user}")
            print(f"   Port: {env_port}\n")
            
            use_env = input("Use these credentials? [Y/n]: ").strip().lower()
            if use_env != 'n':
                return {
                    'host': env_host,
                    'database': env_name,
                    'user': env_user,
                    'password': env_password,
                    'port': int(env_port)
                }
        
        # Manual input with defaults
        database = input(f"Local database name (default: {env_name}): ").strip() or env_name
        user = input(f"Local database user (default: {env_user}): ").strip() or env_user
        password = input("Local database password: ").strip() or env_password
        
        return {
            'host': 'localhost',
            'database': database,
            'user': user,
            'password': password,
            'port': 5432
        }
    
    def get_supabase_config(self):
        """Get Supabase configuration from .env or user input"""
        print("\n📋 Supabase Configuration")
        
        # Try to get from .env first
        env_host = os.getenv('DB_HOST', '')
        env_user = os.getenv('DB_USER', '')
        env_password = os.getenv('DB_PASSWORD', '')
        env_port = os.getenv('DB_PORT', '6543')
        
        # Check if .env has Supabase credentials (contains 'supabase' in host)
        if 'supabase' in env_host.lower():
            print("✅ Found Supabase credentials in .env file")
            print(f"   Host: {env_host}")
            print(f"   User: {env_user}")
            print(f"   Port: {env_port}\n")
            
            use_env = input("Use these credentials? [Y/n]: ").strip().lower()
            if use_env != 'n':
                return {
                    'host': env_host,
                    'database': 'postgres',
                    'user': env_user,
                    'password': env_password,
                    'port': int(env_port),
                    'sslmode': 'require'
                }
        
        # Manual input
        print("You can find these in: Supabase Dashboard → Settings → Database\n")
        
        host = input(f"Supabase host (default: {env_host or 'db.xxxxx.supabase.co'}): ").strip() or env_host
        user = input(f"Supabase user (default: {env_user or 'postgres.xxxxx'}): ").strip() or env_user
        password = input(f"Supabase password: ").strip() or env_password
        port = input(f"Supabase port (default: {env_port}): ").strip() or env_port
        
        return {
            'host': host,
            'database': 'postgres',  # Supabase always uses 'postgres'
            'user': user,
            'password': password,
            'port': int(port),
            'sslmode': 'require'
        }
    
    def export_table_data(self, conn, table_name):
        """Export data from a table"""
        try:
            cursor = conn.cursor()
            
            # Get column names
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position;
            """)
            columns = [row[0] for row in cursor.fetchall()]
            
            # Get all data
            cursor.execute(f"SELECT * FROM {table_name};")
            rows = cursor.fetchall()
            
            logger.info(f"Exported {len(rows)} rows from {table_name}")
            
            return {
                'columns': columns,
                'rows': rows,
                'row_count': len(rows)
            }
            
        except Exception as e:
            logger.error(f"Error exporting {table_name}: {e}")
            return None
    
    def import_table_data(self, conn, table_name, data):
        """Import data into a table"""
        try:
            cursor = conn.cursor()
            
            if data['row_count'] == 0:
                logger.info(f"No data to import for {table_name}")
                return True
            
            # Clear existing data
            cursor.execute(f"TRUNCATE TABLE {table_name} CASCADE;")
            
            # Prepare insert statement with JSONB type casting
            columns = data['columns']
            
            # Get column types to handle JSONB properly
            cursor.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position;
            """)
            column_types = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Build placeholders with type casting for JSONB columns
            placeholders = []
            for col in columns:
                if column_types.get(col) == 'jsonb':
                    placeholders.append('%s::jsonb')
                else:
                    placeholders.append('%s')
            
            columns_str = ', '.join(columns)
            placeholders_str = ', '.join(placeholders)
            insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders_str})"
            
            # Convert dict/list columns to JSON strings for JSONB columns
            def prepare_row(row):
                prepared = []
                for i, value in enumerate(row):
                    col_name = columns[i]
                    if column_types.get(col_name) == 'jsonb' and value is not None:
                        # Convert dict/list to JSON string
                        if isinstance(value, (dict, list)):
                            prepared.append(json.dumps(value))
                        else:
                            prepared.append(value)
                    else:
                        prepared.append(value)
                return tuple(prepared)
            
            # Import data in batches
            batch_size = 100
            total_rows = len(data['rows'])
            
            for i in range(0, total_rows, batch_size):
                batch = data['rows'][i:i+batch_size]
                prepared_batch = [prepare_row(row) for row in batch]
                cursor.executemany(insert_sql, prepared_batch)
                logger.info(f"Imported {min(i+batch_size, total_rows)}/{total_rows} rows into {table_name}")
            
            conn.commit()
            logger.info(f"✅ Successfully imported {total_rows} rows into {table_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error importing {table_name}: {e}")
            conn.rollback()
            return False
    
    def migrate_database(self):
        """Main migration function"""
        print("🚀 Database Migration: Local PostgreSQL → Supabase")
        print("=" * 60)
        
        # Get configurations
        print("\n📍 Local Database Configuration")
        local_config = self.get_local_config()
        
        supabase_config = self.get_supabase_config()
        
        # Test connections
        print("\n🔌 Testing connections...")
        
        try:
            local_conn = psycopg2.connect(**local_config)
            print("✅ Connected to local database")
        except Exception as e:
            print(f"❌ Failed to connect to local database: {e}")
            return False
        
        try:
            supabase_conn = psycopg2.connect(**supabase_config)
            print("✅ Connected to Supabase")
        except Exception as e:
            print(f"❌ Failed to connect to Supabase: {e}")
            local_conn.close()
            return False
        
        # Get tables to migrate
        tables = ['universities', 'mba_embeddings', 'conversations']
        
        print(f"\n📦 Migrating {len(tables)} tables...")
        
        migration_data = {}
        
        # Export from local
        print("\n📤 Exporting data from local database...")
        for table in tables:
            data = self.export_table_data(local_conn, table)
            if data is not None:
                migration_data[table] = data
            else:
                print(f"⚠️ Skipping {table} due to export error")
        
        local_conn.close()
        
        # Import to Supabase
        print("\n📥 Importing data to Supabase...")
        success_count = 0
        
        for table, data in migration_data.items():
            if self.import_table_data(supabase_conn, table, data):
                success_count += 1
        
        supabase_conn.close()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Migration Summary")
        print(f"   Tables migrated: {success_count}/{len(tables)}")
        
        for table, data in migration_data.items():
            print(f"   • {table}: {data['row_count']} rows")
        
        if success_count == len(tables):
            print("\n🎉 Migration completed successfully!")
            print("\n📋 Next Steps:")
            print("   1. Update your .env file with Supabase credentials")
            print("   2. Run: python validate_setup.py")
            print("   3. Run: python app.py")
            return True
        else:
            print("\n⚠️ Migration completed with errors")
            print("   Please check the logs above for details")
            return False

def main():
    """Main execution"""
    print("⚠️ Important: This will TRUNCATE tables in Supabase!")
    print("Make sure you have backups before proceeding.\n")
    
    response = input("Continue with migration? [y/N]: ").strip().lower()
    if response != 'y':
        print("Migration cancelled")
        return False
    
    migrator = DatabaseMigrator()
    return migrator.migrate_database()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
