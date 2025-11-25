#!/usr/bin/env python3
"""Initialize database with fund_labels CSV data.

This script loads the fund_labels CSV into the database.
It's safe to run multiple times - it will check if data already exists.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

# Get database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Construct from individual environment variables with local defaults
    db_user = os.getenv("POSTGRES_USER", "fintela")
    db_password = os.getenv("POSTGRES_PASSWORD", "fintela_password")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "fintela")
    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

engine = create_engine(DATABASE_URL)

# Check if fund_labels table exists and has data
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM fund_labels"))
        count = result.scalar()
        
        if count > 0:
            print(f"✅ fund_labels already has {count} records. Skipping CSV load.")
            print("   To reload, delete the table first or use if_exists='replace' in the script.")
            sys.exit(0)
except Exception as e:
    print(f"⚠️  Could not check fund_labels table: {e}")
    print("   Table might not exist yet. Will attempt to create it.")

# Load CSV
print("📊 Loading fund_labels CSV...")
import pandas as pd

csv_path = project_root / "data" / "fund_labels_202511180330.csv"
if not csv_path.exists():
    print(f"❌ CSV file not found at {csv_path}")
    sys.exit(1)

print(f"Reading CSV from {csv_path}...")
df = pd.read_csv(csv_path)

print(f"Loaded {len(df)} records from CSV")
print(f"Columns: {df.columns.tolist()}")

# Load into database
print(f"\nLoading into database...")
df.to_sql(
    'fund_labels',
    engine,
    if_exists='replace',  # Replace existing data
    index=False,
    method='multi'
)

print(f"✅ Successfully loaded {len(df)} records into fund_labels table!")

# Verify
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM fund_labels"))
    count = result.scalar()
    print(f"✅ Verified: {count} records in database")

print("\n✅ Database initialization complete!")

