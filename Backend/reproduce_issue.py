import sys
import os
import asyncio
import json

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.query_extraction import QueryExtractor
from app.database import DatabaseManager

async def test():
    extractor = QueryExtractor()
    db = DatabaseManager()

    query = "PROFIT QUARTERS PIECHART"
    print(f"Testing Query: {query}")

    # 1. Extraction
    params = extractor.extract_parameters(query)
    print("\n--- Extracted Parameters ---")
    print(json.dumps(params, indent=2))

    # 2. Database Query
    print("\n--- Database Execution ---")
    try:
        results = db.query_dynamic(params)
        print(f"Result Type: {type(results)}")
        if isinstance(results, list):
            print(f"Row Count: {len(results)}")
            if len(results) > 0:
                print("First Row:", results[0])
        else:
            print("Result:", results)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
