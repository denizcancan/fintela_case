"""Test script to see what the TEFAS crawler returns."""

from datetime import date, timedelta
from case_study.tefas_parser import TefasCrawler

# Create crawler instance
crawler = TefasCrawler()

# Fetch data for yesterday (more likely to have data than today)
yesterday = date.today() - timedelta(days=1)

print(f"Fetching data for {yesterday}...")
print("-" * 50)

try:
    data = crawler.fetch_historical_data(
        start_date=yesterday.strftime("%Y-%m-%d"),
        end_date=yesterday.strftime("%Y-%m-%d")
    )
    
    print(f"\n✅ Successfully fetched data!")
    print(f"Shape: {data.shape} (rows, columns)")
    print(f"\nColumns:")
    print(data.columns.tolist())
    print(f"\nFirst few rows:")
    print(data.head())
    print(f"\nData types:")
    print(data.dtypes)
    print(f"\nSample data (first row):")
    print(data.iloc[0] if len(data) > 0 else "No data")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()