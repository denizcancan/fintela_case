"""Script to load fund_labels CSV into PostgreSQL."""

import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection - use DATABASE_URL or construct from individual env vars
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

# Read CSV file
csv_path = os.path.join(os.path.dirname(__file__), "fund_labels_202511180330.csv")
print(f"Reading CSV from {csv_path}...")

df = pd.read_csv(csv_path)

print(f"Loaded {len(df)} records from CSV")
print(f"Columns: {df.columns.tolist()}")
print(f"\nFirst few rows:")
print(df.head())

# Load into database
print(f"\nLoading into database...")
df.to_sql(
    'fund_labels',
    engine,
    if_exists='replace',  # Use 'append' if you want to keep existing data
    index=False,
    method='multi'
)

print(f"✅ Successfully loaded {len(df)} records into fund_labels table!")

# Verify
result = pd.read_sql("SELECT COUNT(*) as count FROM fund_labels", engine)
print(f"✅ Verified: {result['count'].iloc[0]} records in database")