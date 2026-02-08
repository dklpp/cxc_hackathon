"""
Migration script to make scheduled_time nullable in scheduled_calls table
"""
import sqlite3
import os

def migrate_scheduled_calls_table():
    """Migrate scheduled_calls table to allow NULL scheduled_time"""
    db_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(db_dir, 'banking_system.db')
    
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # SQLite doesn't support ALTER COLUMN, so we need to:
        # 1. Create a new table with the correct schema
        # 2. Copy data from old table
        # 3. Drop old table
        # 4. Rename new table
        
        # Check if migration is needed
        cursor.execute("PRAGMA table_info(scheduled_calls)")
        columns = cursor.fetchall()
        scheduled_time_col = next((col for col in columns if col[1] == 'scheduled_time'), None)
        
        if scheduled_time_col and scheduled_time_col[3] == 0:  # 0 means NOT NULL
            print("Migrating scheduled_calls table to allow NULL scheduled_time...")
            
            # Create new table with nullable scheduled_time
            cursor.execute("""
                CREATE TABLE scheduled_calls_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    scheduled_time DATETIME,
                    status VARCHAR(50) NOT NULL DEFAULT 'pending',
                    agent_id VARCHAR(100),
                    notes TEXT,
                    communication_log_id INTEGER,
                    created_at DATETIME,
                    updated_at DATETIME,
                    FOREIGN KEY (customer_id) REFERENCES customers(id),
                    FOREIGN KEY (communication_log_id) REFERENCES communication_logs(id)
                )
            """)
            
            # Copy data from old table
            cursor.execute("""
                INSERT INTO scheduled_calls_new 
                (id, customer_id, scheduled_time, status, agent_id, notes, 
                 communication_log_id, created_at, updated_at)
                SELECT 
                    id, customer_id, scheduled_time, status, agent_id, notes,
                    communication_log_id, created_at, updated_at
                FROM scheduled_calls
            """)
            
            # Drop old table
            cursor.execute("DROP TABLE scheduled_calls")
            
            # Rename new table
            cursor.execute("ALTER TABLE scheduled_calls_new RENAME TO scheduled_calls")
            
            conn.commit()
            print("✓ Migration completed successfully!")
        else:
            print("✓ Table already migrated or scheduled_time is already nullable")
            
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_scheduled_calls_table()
