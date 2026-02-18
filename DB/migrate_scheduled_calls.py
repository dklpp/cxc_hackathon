"""
Migration script to make scheduled_time nullable in scheduled_calls table

Note: This migration is now handled automatically by DatabaseManager.create_tables().
This script is kept for backward compatibility and uses PostgreSQL-compatible SQL.
"""
import os
from sqlalchemy import create_engine, text, inspect

def migrate_scheduled_calls_table():
    """Migrate scheduled_calls table to allow NULL scheduled_time (PostgreSQL)"""
    database_url = os.environ.get('DATABASE_URL')
    if database_url is None:
        print("DATABASE_URL environment variable is not set.")
        print("Please set it to a PostgreSQL connection string, e.g.:")
        print("  postgresql://username:password@localhost:5432/banking_system")
        return
    
    engine = create_engine(database_url, echo=False)
    
    try:
        inspector = inspect(engine)
        if 'scheduled_calls' not in inspector.get_table_names():
            print("Table scheduled_calls does not exist yet.")
            return
        
        # Check if migration is needed
        columns = inspector.get_columns('scheduled_calls')
        scheduled_time_col = next((col for col in columns if col['name'] == 'scheduled_time'), None)
        
        if scheduled_time_col and not scheduled_time_col.get('nullable', False):
            print("Migrating scheduled_calls table to allow NULL scheduled_time...")
            
            with engine.connect() as conn:
                # PostgreSQL supports ALTER COLUMN directly
                conn.execute(text("""
                    ALTER TABLE scheduled_calls 
                    ALTER COLUMN scheduled_time DROP NOT NULL
                """))
                conn.commit()
                print("✓ Migration completed successfully!")
        else:
            print("✓ Table already migrated or scheduled_time is already nullable")
            
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    migrate_scheduled_calls_table()
