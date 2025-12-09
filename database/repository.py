"""Repository for benchmark data operations."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
import logging

from database.models import BenchmarkDocument, BenchmarkStatus
from database.connection import Database

logger = logging.getLogger(__name__)


class BenchmarkRepository:
    """Repository for benchmark CRUD operations."""
    
    def __init__(self):
        self.collection_name = "benchmarks"
    
    def _get_collection(self) -> AsyncIOMotorCollection:
        """Get the benchmarks collection."""
        db = Database.get_database()
        return db[self.collection_name]
    
    async def create(self, benchmark: BenchmarkDocument) -> str:
        """Create a new benchmark document."""
        collection = self._get_collection()
        benchmark.updated_at = datetime.utcnow()
        
        # Get the document as dict, ensuring _id is None for new documents
        # so MongoDB can auto-generate it
        doc_dict = benchmark.to_dict()
        # Remove _id if it's None or not set, so MongoDB generates it
        if "_id" in doc_dict and (doc_dict["_id"] is None or doc_dict["_id"] == ""):
            del doc_dict["_id"]
        
        result = await collection.insert_one(doc_dict)
        logger.info(f"Created benchmark with id: {result.inserted_id}")
        return str(result.inserted_id)
    
    async def get_by_id(self, benchmark_id: str) -> Optional[BenchmarkDocument]:
        """Get a benchmark by ID."""
        collection = self._get_collection()
        try:
            # Validate ObjectId format
            try:
                object_id = ObjectId(benchmark_id)
            except Exception as e:
                logger.error(f"Invalid ObjectId format: {benchmark_id} - {e}")
                return None
            
            # Try to find with ObjectId first (correct format)
            doc = await collection.find_one({"_id": object_id})
            
            # If not found, try with string (for backwards compatibility with old data)
            if not doc:
                doc = await collection.find_one({"_id": benchmark_id})
            
            if doc:
                return BenchmarkDocument.from_dict(doc)
            logger.warning(f"Benchmark not found with ID: {benchmark_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting benchmark {benchmark_id}: {e}", exc_info=True)
            return None
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[BenchmarkDocument]:
        """Get all benchmarks with optional filtering."""
        collection = self._get_collection()
        query = {}
        if status:
            query["status"] = status
        
        cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        benchmarks = []
        async for doc in cursor:
            benchmarks.append(BenchmarkDocument.from_dict(doc))
        return benchmarks
    
    async def update(
        self, 
        benchmark_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update a benchmark document."""
        collection = self._get_collection()
        updates["updated_at"] = datetime.utcnow()
        
        try:
            object_id = ObjectId(benchmark_id)
            # Try with ObjectId first
            result = await collection.update_one(
                {"_id": object_id},
                {"$set": updates}
            )
            # If not found, try with string (for backwards compatibility)
            if result.matched_count == 0:
                result = await collection.update_one(
                    {"_id": benchmark_id},
                    {"$set": updates}
                )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating benchmark {benchmark_id}: {e}")
            return False
    
    async def update_status(
        self, 
        benchmark_id: str, 
        status: str,
        error_message: Optional[str] = None,
        error_traceback: Optional[str] = None
    ) -> bool:
        """Update benchmark status."""
        updates = {"status": status}
        
        if status == BenchmarkStatus.RUNNING and not error_message:
            updates["started_at"] = datetime.utcnow()
        elif status in [BenchmarkStatus.COMPLETED, BenchmarkStatus.FAILED]:
            updates["completed_at"] = datetime.utcnow()
        
        if error_message:
            updates["error_message"] = error_message
        if error_traceback:
            updates["error_traceback"] = error_traceback
        
        return await self.update(benchmark_id, updates)
    
    async def save_result(
        self, 
        benchmark_id: str, 
        result_data: Dict[str, Any]
    ) -> bool:
        """Save benchmark result data."""
        updates = {
            "result_data": result_data,
            "status": BenchmarkStatus.COMPLETED,
            "completed_at": datetime.utcnow()
        }
        return await self.update(benchmark_id, updates)
    
    async def delete(self, benchmark_id: str) -> bool:
        """Delete a benchmark document."""
        collection = self._get_collection()
        try:
            object_id = ObjectId(benchmark_id)
            # Try with ObjectId first
            result = await collection.delete_one({"_id": object_id})
            # If not found, try with string (for backwards compatibility)
            if result.deleted_count == 0:
                result = await collection.delete_one({"_id": benchmark_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting benchmark {benchmark_id}: {e}")
            return False
    
    async def count(self, status: Optional[str] = None) -> int:
        """Count benchmarks, optionally filtered by status."""
        collection = self._get_collection()
        query = {}
        if status:
            query["status"] = status
        return await collection.count_documents(query)

