#!/usr/bin/env python3
import requests
import json

try:
    # Make request to the database API
    response = requests.get('http://localhost:8000/api/database/data')
    response.raise_for_status()
    
    data = response.json()
    
    print("Database Table Row Counts:")
    print("=" * 30)
    
    # Extract row counts for each table
    for table_name, count in data.items():
        if table_name == '_summary':
            continue
        if isinstance(count, int):
            print(f"{table_name}: {count} rows")
    
    # Print summary if available
    if '_summary' in data:
        summary = data['_summary']
        print("\nSummary:")
        print(f"Total tables: {summary.get('total_tables', 'N/A')}")
        print(f"Total records: {summary.get('total_records', 'N/A')}")
        
except requests.exceptions.RequestException as e:
    print(f"Error connecting to API: {e}")
except json.JSONDecodeError as e:
    print(f"Error parsing JSON response: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")