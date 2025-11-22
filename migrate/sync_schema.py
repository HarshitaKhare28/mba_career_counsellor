#!/usr/bin/env python3
"""
Schema Sync Script: Sync schema from local PostgreSQL to Supabase
Detects and creates missing tables/columns automatically
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SchemaSync:
    def __init__(self):
        load_dotenv()
        
    def get_local_config(self):
        """Get local database configuration"""
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'mba_data'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': int(os.getenv('DB_PORT', '5432'))
        }
    
    def get_supabase_config(self):
        """Get Supabase configuration"""
        return {
            'host': os.getenv('SUPABASE_HOST') or os.getenv('DB_HOST'),
            'database': 'postgres',
            'user': os.getenv('SUPABASE_USER') or os.getenv('DB_USER'),
            'password': os.getenv('SUPABASE_PASSWORD') or os.getenv('DB_PASSWORD'),
            'port': int(os.getenv('SUPABASE_PORT', '6543')),
            'sslmode': 'require'
        }
    
    def get_table_schema(self, conn, table_name):
        """Get complete schema for a table"""
        try:
            cursor = conn.cursor()
            
            # Get column definitions
            cursor.execute(f"""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    column_default,
                    is_nullable,
                    udt_name
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position;
            """)
            
            columns = []
            for row in cursor.fetchall():
                col_name, data_type, max_length, default, nullable, udt_name = row
                columns.append({
                    'name': col_name,
                    'type': data_type,
                    'max_length': max_length,
                    'default': default,
                    'nullable': nullable,
                    'udt_name': udt_name
                })
            
            cursor.close()
            return columns
            
        except Exception as e:
            logger.error(f"Error getting schema for {table_name}: {e}")
            return None
    
    def create_column_sql(self, column):
        """Generate SQL to create a column"""
        col_def = f"{column['name']} "
        
        # Handle special types
        if column['udt_name'] == 'vector':
            col_def += "vector(384)"
        elif column['type'] == 'ARRAY':
            col_def += f"{column['udt_name']}[]"
        elif column['type'] == 'USER-DEFINED':
            if column['udt_name'] == 'jsonb':
                col_def += "JSONB"
            else:
                col_def += column['udt_name']
        elif column['type'] == 'character varying':
            if column['max_length']:
                col_def += f"VARCHAR({column['max_length']})"
            else:
                col_def += "VARCHAR(255)"
        elif column['type'] == 'numeric':
            col_def += "NUMERIC"
        else:
            col_def += column['type'].upper()
        
        # Add constraints
        if column['nullable'] == 'NO':
            col_def += " NOT NULL"
        
        if column['default']:
            # Clean up default value
            default_val = column['default']
            if not default_val.startswith('nextval'):  # Skip sequence defaults
                col_def += f" DEFAULT {default_val}"
        
        return col_def
    
    def sync_table_schema(self, local_conn, supabase_conn, table_name):
        """Sync schema for a single table"""
        logger.info(f"Syncing schema for table: {table_name}")
        
        # Get schemas from both databases
        local_schema = self.get_table_schema(local_conn, table_name)
        supabase_schema = self.get_table_schema(supabase_conn, table_name)
        
        if not local_schema:
            logger.warning(f"Table {table_name} not found in local database")
            return False
        
        if not supabase_schema:
            logger.info(f"Table {table_name} doesn't exist in Supabase. Creating...")
            # Table doesn't exist, create it
            return self.create_table(supabase_conn, table_name, local_schema)
        
        # Find missing columns
        local_cols = {col['name'] for col in local_schema}
        supabase_cols = {col['name'] for col in supabase_schema}
        missing_cols = local_cols - supabase_cols
        
        if not missing_cols:
            logger.info(f"✅ Table {table_name} schema is in sync")
            return True
        
        # Add missing columns
        logger.info(f"Adding {len(missing_cols)} missing columns to {table_name}: {missing_cols}")
        
        cursor = supabase_conn.cursor()
        for col_name in missing_cols:
            col_def = next(col for col in local_schema if col['name'] == col_name)
            col_sql = self.create_column_sql(col_def)
            
            try:
                alter_sql = f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {col_sql};"
                logger.info(f"   Adding column: {col_sql}")
                cursor.execute(alter_sql)
                supabase_conn.commit()
                logger.info(f"   ✅ Column {col_name} added")
            except Exception as e:
                logger.error(f"   ❌ Failed to add column {col_name}: {e}")
                supabase_conn.rollback()
                return False
        
        cursor.close()
        logger.info(f"✅ Table {table_name} schema synced successfully")
        return True
    
    def create_table(self, conn, table_name, schema):
        """Create a new table with given schema"""
        try:
            cursor = conn.cursor()
            
            # Build CREATE TABLE statement
            col_defs = []
            for col in schema:
                if col['name'] == 'id' and 'nextval' in str(col['default']):
                    col_defs.append(f"{col['name']} SERIAL PRIMARY KEY")
                else:
                    col_defs.append(self.create_column_sql(col))
            
            create_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    {', '.join(col_defs)}
                );
            """
            
            logger.info(f"Creating table {table_name}...")
            cursor.execute(create_sql)
            conn.commit()
            cursor.close()
            
            logger.info(f"✅ Table {table_name} created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating table {table_name}: {e}")
            conn.rollback()
            return False
    
    def sync_all_tables(self):
        """Sync schema for all tables"""
        print("🔄 Schema Synchronization: Local PostgreSQL → Supabase")
        print("=" * 60)
        
        # Get configurations
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
        
        # Enable pgvector extension
        print("\n📦 Enabling pgvector extension...")
        try:
            cursor = supabase_conn.cursor()
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            supabase_conn.commit()
            cursor.close()
            print("✅ pgvector extension enabled")
        except Exception as e:
            print(f"⚠️ Could not enable pgvector: {e}")
        
        # Sync tables
        tables = ['universities', 'mba_embeddings', 'conversations']
        
        print(f"\n🔄 Syncing {len(tables)} tables...")
        success_count = 0
        
        for table in tables:
            if self.sync_table_schema(local_conn, supabase_conn, table):
                success_count += 1
        
        local_conn.close()
        supabase_conn.close()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Schema Sync Summary")
        print(f"   Tables synced: {success_count}/{len(tables)}")
        
        if success_count == len(tables):
            print("\n✅ Schema synchronization completed successfully!")
            print("\n📋 Next Steps:")
            print("   1. Run: python migrate_to_supabase.py")
            print("   2. Verify: python validate_setup.py")
            return True
        else:
            print("\n⚠️ Schema sync completed with errors")
            return False

def main():
    """Main execution"""
    print("⚠️ This will modify Supabase database schema!")
    print("This script will add missing columns/tables to match local database.\n")
    
    response = input("Continue with schema sync? [y/N]: ").strip().lower()
    if response != 'y':
        print("Schema sync cancelled")
        return False
    
    syncer = SchemaSync()
    return syncer.sync_all_tables()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
