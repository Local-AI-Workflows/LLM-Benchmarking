"""Repository for dataset data operations."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
import logging

from database.models import DatasetDocument
from database.connection import Database

logger = logging.getLogger(__name__)


class DatasetRepository:
    """Repository for dataset CRUD operations."""
    
    def __init__(self):
        self.collection_name = "datasets"
    
    def _get_collection(self) -> AsyncIOMotorCollection:
        """Get the datasets collection."""
        db = Database.get_database()
        return db[self.collection_name]
    
    async def create(self, dataset: DatasetDocument) -> str:
        """Create a new dataset document."""
        collection = self._get_collection()
        dataset.updated_at = datetime.utcnow()
        result = await collection.insert_one(dataset.to_dict())
        logger.info(f"Created dataset with id: {result.inserted_id}")
        return str(result.inserted_id)
    
    async def get_by_id(self, dataset_id: str) -> Optional[DatasetDocument]:
        """Get a dataset by ID."""
        collection = self._get_collection()
        try:
            doc = await collection.find_one({"_id": ObjectId(dataset_id)})
            if doc:
                return DatasetDocument.from_dict(doc)
            return None
        except Exception as e:
            logger.error(f"Error getting dataset {dataset_id}: {e}")
            return None
    
    async def get_by_name(self, name: str) -> Optional[DatasetDocument]:
        """Get a dataset by name."""
        collection = self._get_collection()
        try:
            doc = await collection.find_one({"name": name})
            if doc:
                return DatasetDocument.from_dict(doc)
            return None
        except Exception as e:
            logger.error(f"Error getting dataset by name {name}: {e}")
            return None
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 1000,
        enabled_only: bool = False
    ) -> List[DatasetDocument]:
        """Get all datasets with optional filtering."""
        collection = self._get_collection()
        query = {}
        if enabled_only:
            query["enabled"] = True
        
        cursor = collection.find(query).sort("name", 1).skip(skip).limit(limit)
        datasets = []
        async for doc in cursor:
            datasets.append(DatasetDocument.from_dict(doc))
        return datasets
    
    async def update(
        self, 
        dataset_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update a dataset document."""
        collection = self._get_collection()
        updates["updated_at"] = datetime.utcnow()
        
        try:
            result = await collection.update_one(
                {"_id": ObjectId(dataset_id)},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating dataset {dataset_id}: {e}")
            return False
    
    async def delete(self, dataset_id: str) -> bool:
        """Delete a dataset document."""
        collection = self._get_collection()
        try:
            result = await collection.delete_one({"_id": ObjectId(dataset_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting dataset {dataset_id}: {e}")
            return False
    
    async def count(self, enabled_only: bool = False) -> int:
        """Count datasets."""
        collection = self._get_collection()
        query = {}
        if enabled_only:
            query["enabled"] = True
        return await collection.count_documents(query)
    
    async def upsert_by_name(self, dataset: DatasetDocument) -> str:
        """Insert or update a dataset by name."""
        collection = self._get_collection()
        dataset.updated_at = datetime.utcnow()
        
        existing = await self.get_by_name(dataset.name)
        if existing:
            # Update existing
            await self.update(str(existing.id), dataset.dict(exclude={"id", "_id", "created_at"}))
            return str(existing.id)
        else:
            # Insert new
            result = await collection.insert_one(dataset.to_dict())
            return str(result.inserted_id)

