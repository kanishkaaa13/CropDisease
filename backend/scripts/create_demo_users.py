"""
Create demo users (farmer and officer) without clearing existing data.
Run this to add demo credentials for testing authentication.
"""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.db.connection import get_db
from app.db.models import User, UserRole
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_demo_users():
    """Create demo farmer and officer users if they don't exist."""
    db: Session = next(get_db())
    
    try:
        # Check if demo users already exist
        existing_farmer = db.query(User).filter(User.email == "farmer@krushirakshak.in").first()
        existing_officer = db.query(User).filter(User.email == "officer@krushirakshak.in").first()
        
        if existing_farmer and existing_officer:
            print("✓ Demo users already exist")
            print("  Farmer: farmer@krushirakshak.in / farmer123")
            print("  Officer: officer@krushirakshak.in / officer123")
            return
        
        # Create demo farmer
        if not existing_farmer:
            demo_farmer = User(
                name="Demo Farmer",
                email="farmer@krushirakshak.in",
                password_hash=pwd_context.hash("farmer123"),
                phone="+919876543210",
                role=UserRole.farmer,
                district="Nashik",
                state="Maharashtra",
                language_pref="en",
                created_at=datetime.now(timezone.utc) - timedelta(days=30)
            )
            db.add(demo_farmer)
            db.flush()
            print("✓ Created demo farmer (farmer@krushirakshak.in / farmer123)")
        else:
            print("✓ Demo farmer already exists")
        
        # Create demo officer
        if not existing_officer:
            demo_officer = User(
                name="Demo Officer",
                email="officer@krushirakshak.in",
                password_hash=pwd_context.hash("officer123"),
                phone="+919876543211",
                role=UserRole.officer,
                district="Nashik",
                state="Maharashtra",
                language_pref="en",
                created_at=datetime.now(timezone.utc) - timedelta(days=30)
            )
            db.add(demo_officer)
            db.flush()
            print("✓ Created demo officer (officer@krushirakshak.in / officer123)")
        else:
            print("✓ Demo officer already exists")
        
        db.commit()
        print("\n✅ Demo users created successfully!")
        print("\nDemo Credentials:")
        print("  Farmer: farmer@krushirakshak.in / farmer123")
        print("  Officer: officer@krushirakshak.in / officer123")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Failed to create demo users: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    create_demo_users()
