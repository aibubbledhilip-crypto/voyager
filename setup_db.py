#!/usr/bin/env python
"""
Database setup script
Initializes the database and creates admin user
"""
from backend.database import init_db, SessionLocal
from backend.auth import init_admin_user

def main():
    print("🚀 Setting up database...")

    # Initialize database tables
    print("📊 Creating database tables...")
    init_db()

    # Create admin user
    print("👤 Creating admin user...")
    db = SessionLocal()
    try:
        init_admin_user(db)
    finally:
        db.close()

    print("\n✅ Database setup complete!")
    print("\n📝 Next steps:")
    print("1. Edit .env file and add your API keys")
    print("2. Run 'python run_gui.py' to start the application")
    print("3. Login with username='admin', password='admin123'")
    print("4. ⚠️  IMPORTANT: Change the admin password immediately!")


if __name__ == "__main__":
    main()
