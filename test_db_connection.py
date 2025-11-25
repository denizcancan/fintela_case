"""Test database connection."""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Use same connection logic as the app
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Construct from individual environment variables with local defaults
    db_user = os.getenv("POSTGRES_USER", "fintela")
    db_password = os.getenv("POSTGRES_PASSWORD", "fintela_password")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "fintela")
    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"



print("=" * 50)
print("Testing Database Connection")
print("=" * 50)
print(f"Host: {os.getenv('POSTGRES_HOST', 'localhost')}")
print(f"Database: {os.getenv('POSTGRES_DB', 'postgres')}")
print(f"User: {os.getenv('POSTGRES_USER', 'postgres')}")
print()

try:
    # Test connection
    print("1. Testing connection...")
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"   ✅ Connected successfully!")
        print(f"   PostgreSQL version: {version[:50]}...")
    
    # Check if tables exist
    print("\n2. Checking tables...")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
        
        expected_tables = [
            'portfolios',
            'portfolio_positions', 
            'fund_labels',
            'portfolio_risk_scores',
            'fund_performance_metrics'
        ]
        
        print(f"   Found {len(tables)} tables:")
        for table in tables:
            status = "✅" if table in expected_tables else "ℹ️"
            print(f"   {status} {table}")
        
        missing = [t for t in expected_tables if t not in tables]
        if missing:
            print(f"\n   ⚠️  Missing tables: {', '.join(missing)}")
        else:
            print(f"\n   ✅ All expected tables exist!")
    
    # Check fund_labels data
    print("\n3. Checking fund_labels data...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM fund_labels"))
        count = result.scalar()
        print(f"   ✅ fund_labels: {count} records")
    
    # Check if fund_prices exists (will be created by Dagster)
    print("\n4. Checking fund_prices table...")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'fund_prices'
            )
        """))
        exists = result.scalar()
        if exists:
            result = conn.execute(text("SELECT COUNT(*) FROM fund_prices"))
            count = result.scalar()
            print(f"   ✅ fund_prices exists: {count} records")
        else:
            print(f"   ℹ️  fund_prices doesn't exist yet (will be created by Dagster)")
    
    print("\n" + "=" * 50)
    print("✅ All tests passed! Database connection is working.")
    print("=" * 50)
    
except Exception as e:
    print(f"\n❌ Connection failed!")
    print(f"Error: {e}")
    print("\nPlease check:")
    print("1. Your .env file exists and has correct values")
    print("2. PostgreSQL is running (docker-compose up or local install)")
    print("3. Database connection settings are correct")
    import traceback
    traceback.print_exc()
    exit(1)