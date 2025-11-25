"""Script to create 50+ test portfolios directly in database."""

import random
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Database connection - use environment variables or construct from them
import os
from dotenv import load_dotenv

# Load .env file
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
SessionLocal = sessionmaker(bind=engine)


def get_available_fund_codes():
    """Get available fund codes from the database."""
    with engine.connect() as conn:
        # Try fund_labels first (preferred), then fund_prices as fallback
        try:
            result = conn.execute(text("SELECT DISTINCT code FROM fund_labels LIMIT 200"))
            codes = [row[0] for row in result]
            if codes:
                print(f"✅ Found {len(codes)} fund codes from fund_labels table")
                return codes
        except Exception as e:
            print(f"⚠️  Could not read from fund_labels: {e}")
        
        # Fallback to fund_prices
        try:
            result = conn.execute(text("SELECT DISTINCT code FROM fund_prices LIMIT 200"))
            codes = [row[0] for row in result]
            if codes:
                print(f"✅ Found {len(codes)} fund codes from fund_prices table")
                return codes
        except Exception as e:
            print(f"⚠️  Could not read from fund_prices: {e}")
    
    return []


def create_portfolios_direct(num_portfolios=60):
    """Create portfolios directly in database."""
    print(f"Fetching available fund codes...")
    fund_codes = get_available_fund_codes()
    
    if not fund_codes:
        print("❌ No fund codes found in database.")
        print("   Make sure you've loaded fund_labels or run the Dagster ingestion job.")
        return
    
    if len(fund_codes) < 2:
        print(f"❌ Need at least 2 fund codes, but only found {len(fund_codes)}")
        return
    
    print(f"Creating {num_portfolios} portfolios...\n")
    
    db = SessionLocal()
    created = 0
    
    try:
        for i in range(1, num_portfolios + 1):
            # Vary number of funds per portfolio (2-5 funds)
            num_funds = random.randint(2, min(5, len(fund_codes)))
            selected_funds = random.sample(fund_codes, num_funds)
            
            # Generate random weights that sum to 1.0
            weights = [random.random() for _ in range(len(selected_funds))]
            total_weight = sum(weights)
            normalized_weights = [round(w / total_weight, 4) for w in weights]
            
            # Ensure last weight accounts for rounding
            total = sum(normalized_weights)
            if abs(total - 1.0) > 0.001:
                normalized_weights[-1] = round(normalized_weights[-1] + (1.0 - total), 4)
            
            # Insert portfolio
            now = datetime.now()
            db.execute(text("""
                INSERT INTO portfolios (id, name, created_at, updated_at)
                VALUES (:id, :name, :created_at, :updated_at)
            """), {
                "id": i,
                "name": f"Test Portfolio {i}",
                "created_at": now,
                "updated_at": now
            })
            
            # Insert positions
            for fund, weight in zip(selected_funds, normalized_weights):
                db.execute(text("""
                    INSERT INTO portfolio_positions (portfolio_id, fund_code, weight, created_at)
                    VALUES (:portfolio_id, :fund_code, :weight, :created_at)
                """), {
                    "portfolio_id": i,
                    "fund_code": fund,
                    "weight": weight,
                    "created_at": now
                })
            
            created += 1
            
            # Print progress every 10 portfolios
            if created % 10 == 0:
                print(f"✅ Created {created}/{num_portfolios} portfolios...")
        
        db.commit()
        print(f"\n✅ Successfully created {created} portfolios!")
        
        # Verify
        result = db.execute(text("SELECT COUNT(*) FROM portfolios"))
        count = result.scalar()
        print(f"✅ Total portfolios in database: {count}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating portfolios: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    # Create 60 portfolios (more than 50 as requested)
    create_portfolios_direct(60)