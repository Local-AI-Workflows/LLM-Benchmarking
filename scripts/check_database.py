#!/usr/bin/env python3
"""Script to check database contents and verify data integrity."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import Database
from database.repository import BenchmarkRepository
from bson import ObjectId


async def check_benchmarks():
    """Check benchmark documents in the database."""
    await Database.connect()
    
    try:
        repository = BenchmarkRepository()
        db = Database.get_database()
        collection = db["benchmarks"]
        
        print("=" * 80)
        print("CHECKING BENCHMARK DOCUMENTS IN DATABASE")
        print("=" * 80)
        
        # Get all benchmarks
        cursor = collection.find({})
        benchmarks = await cursor.to_list(length=None)
        
        print(f"\nTotal benchmarks in database: {len(benchmarks)}")
        print("\n" + "-" * 80)
        
        if not benchmarks:
            print("No benchmarks found in database.")
            return
        
        for i, doc in enumerate(benchmarks, 1):
            print(f"\nBenchmark #{i}:")
            print(f"  _id (type: {type(doc.get('_id'))}): {doc.get('_id')}")
            print(f"  _id as string: {str(doc.get('_id'))}")
            print(f"  Status: {doc.get('status')}")
            print(f"  Model: {doc.get('model_name')}")
            print(f"  Created: {doc.get('created_at')}")
            
            # Check if _id is ObjectId or string
            _id = doc.get('_id')
            if isinstance(_id, ObjectId):
                print(f"  ✓ _id is ObjectId (correct)")
            elif isinstance(_id, str):
                print(f"  ⚠ _id is string (should be ObjectId)")
                try:
                    # Try to convert to ObjectId
                    obj_id = ObjectId(_id)
                    print(f"  ✓ String is valid ObjectId format")
                except Exception as e:
                    print(f"  ✗ String is NOT valid ObjectId: {e}")
            else:
                print(f"  ✗ _id has unexpected type: {type(_id)}")
        
        print("\n" + "=" * 80)
        print("TESTING REPOSITORY METHODS")
        print("=" * 80)
        
        # Test get_all
        all_benchmarks = await repository.get_all()
        print(f"\nRepository.get_all() returned {len(all_benchmarks)} benchmarks")
        
        for benchmark in all_benchmarks[:3]:  # Show first 3
            print(f"\n  ID: {benchmark.id}")
            print(f"  ID type: {type(benchmark.id)}")
            print(f"  ID as string: {str(benchmark.id)}")
            print(f"  Status: {benchmark.status}")
            
            # Test get_by_id with string ID
            string_id = str(benchmark.id)
            print(f"\n  Testing get_by_id('{string_id}')...")
            found = await repository.get_by_id(string_id)
            if found:
                print(f"  ✓ Found benchmark with ID: {found.id}")
            else:
                print(f"  ✗ NOT FOUND!")
        
        # Test with a specific ID from the error message
        test_id = "6925bf8217a05652af24558d"
        print(f"\n" + "-" * 80)
        print(f"Testing with ID from error: {test_id}")
        print("-" * 80)
        
        # Check if it's a valid ObjectId
        try:
            obj_id = ObjectId(test_id)
            print(f"✓ ID is valid ObjectId format")
        except Exception as e:
            print(f"✗ ID is NOT valid ObjectId: {e}")
            return
        
        # Try to find it directly in collection
        doc = await collection.find_one({"_id": obj_id})
        if doc:
            print(f"✓ Found document directly in collection")
            print(f"  _id: {doc.get('_id')}")
            print(f"  Status: {doc.get('status')}")
        else:
            print(f"✗ Document NOT found in collection")
        
        # Try with repository
        found = await repository.get_by_id(test_id)
        if found:
            print(f"✓ Found via repository.get_by_id()")
            print(f"  ID: {found.id}")
            print(f"  Status: {found.status}")
        else:
            print(f"✗ NOT found via repository.get_by_id()")
        
    finally:
        await Database.disconnect()


if __name__ == "__main__":
    asyncio.run(check_benchmarks())

