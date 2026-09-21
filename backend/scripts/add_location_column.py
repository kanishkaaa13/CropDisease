"""
Script to add the location column to farms table.
Run this if alembic migration fails due to insufficient privileges.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.connection import get_db
from sqlalchemy import text

def add_location_column():
    """Add location column to farms table and backfill data."""
    db = next(get_db())
    
    try:
        print("Adding location column to farms table...")
        
        # Check if column already exists
        check_sql = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'farms' AND column_name = 'location'
        """)
        result = db.execute(check_sql).fetchone()
        
        if result:
            print("✓ Location column already exists")
        else:
            # Add the column
            alter_sql = text("""
                ALTER TABLE farms 
                ADD COLUMN location geometry(POINT, 4326)
            """)
            db.execute(alter_sql)
            print("✓ Added location column")
        
        # Check if index exists
        check_index_sql = text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'farms' AND indexname = 'ix_farms_location_gist'
        """)
        index_result = db.execute(check_index_sql).fetchone()
        
        if index_result:
            print("✓ GIST index already exists")
        else:
            # Create GIST index
            index_sql = text("""
                CREATE INDEX ix_farms_location_gist 
                ON farms USING GIST (location)
            """)
            db.execute(index_sql)
            print("✓ Created GIST index")
        
        # Backfill existing data
        backfill_sql = text("""
            UPDATE farms 
            SET location = ST_SetSRID(ST_MakePoint(gps_lng, gps_lat), 4326)
            WHERE location IS NULL
        """)
        result = db.execute(backfill_sql)
        print(f"✓ Backfilled {result.rowcount} farms with location data")
        
        db.commit()
        print("\n✅ Successfully added location column to farms table")
        
        # Verify the column exists
        verify_sql = text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'farms' AND column_name = 'location'
        """)
        verify_result = db.execute(verify_sql).fetchone()
        if verify_result:
            print(f"Verified: column '{verify_result[0]}' with type '{verify_result[1]}' exists")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_location_column()
