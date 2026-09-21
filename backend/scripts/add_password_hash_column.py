"""
Manual migration script to add password_hash column to users table.
Run this if Alembic migration fails due to permission issues.
"""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.connection import engine
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def add_password_hash_column():
    """Add password_hash column to users table and backfill existing users."""
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'password_hash'
        """))
        
        if result.fetchone():
            print("✓ password_hash column already exists")
            return
        
        print("Adding password_hash column to users table...")
        
        # Add password_hash column (nullable initially)
        conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
        print("✓ Added password_hash column")
        
        # Make email non-nullable
        conn.execute(text("ALTER TABLE users ALTER COLUMN email SET NOT NULL"))
        print("✓ Made email non-nullable")
        
        # Make phone nullable
        conn.execute(text("ALTER TABLE users ALTER COLUMN phone DROP NOT NULL"))
        print("✓ Made phone nullable")
        
        # Backfill password_hash for existing users
        default_hash = pwd_context.hash("changeme123")
        conn.execute(text("UPDATE users SET password_hash = :hash WHERE password_hash IS NULL"), {"hash": default_hash})
        print("✓ Backfilled password_hash for existing users")
        
        # Now make password_hash non-nullable
        conn.execute(text("ALTER TABLE users ALTER COLUMN password_hash SET NOT NULL"))
        print("✓ Made password_hash non-nullable")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")

if __name__ == "__main__":
    try:
        add_password_hash_column()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
