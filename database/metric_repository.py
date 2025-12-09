"""Repository for metric data operations."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
import logging

from database.models import MetricDocument, MetricType
from database.connection import Database

logger = logging.getLogger(__name__)


class MetricRepository:
    """Repository for metric CRUD operations."""
    
    def __init__(self):
        self.collection_name = "metrics"
    
    def _get_collection(self) -> AsyncIOMotorCollection:
        """Get the metrics collection."""
        db = Database.get_database()
        return db[self.collection_name]
    
    async def create(self, metric: MetricDocument) -> str:
        """Create a new metric document."""
        collection = self._get_collection()
        metric.updated_at = datetime.utcnow()
        result = await collection.insert_one(metric.to_dict())
        logger.info(f"Created metric with id: {result.inserted_id}")
        return str(result.inserted_id)
    
    async def get_by_id(self, metric_id: str) -> Optional[MetricDocument]:
        """Get a metric by ID."""
        collection = self._get_collection()
        try:
            doc = await collection.find_one({"_id": ObjectId(metric_id)})
            if doc:
                return MetricDocument.from_dict(doc)
            return None
        except Exception as e:
            logger.error(f"Error getting metric {metric_id}: {e}")
            return None
    
    async def get_by_name(self, name: str) -> Optional[MetricDocument]:
        """Get a metric by name."""
        collection = self._get_collection()
        try:
            doc = await collection.find_one({"name": name})
            if doc:
                return MetricDocument.from_dict(doc)
            return None
        except Exception as e:
            logger.error(f"Error getting metric by name {name}: {e}")
            return None
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 1000,
        metric_type: Optional[str] = None,
        enabled_only: bool = False
    ) -> List[MetricDocument]:
        """Get all metrics with optional filtering."""
        collection = self._get_collection()
        query = {}
        if metric_type:
            query["type"] = metric_type
        if enabled_only:
            query["enabled"] = True
        
        cursor = collection.find(query).sort("name", 1).skip(skip).limit(limit)
        metrics = []
        async for doc in cursor:
            metrics.append(MetricDocument.from_dict(doc))
        return metrics
    
    async def update(
        self, 
        metric_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update a metric document."""
        collection = self._get_collection()
        updates["updated_at"] = datetime.utcnow()
        
        try:
            result = await collection.update_one(
                {"_id": ObjectId(metric_id)},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating metric {metric_id}: {e}")
            return False
    
    async def delete(self, metric_id: str) -> bool:
        """Delete a metric document."""
        collection = self._get_collection()
        try:
            result = await collection.delete_one({"_id": ObjectId(metric_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting metric {metric_id}: {e}")
            return False
    
    async def count(self, metric_type: Optional[str] = None, enabled_only: bool = False) -> int:
        """Count metrics, optionally filtered by type."""
        collection = self._get_collection()
        query = {}
        if metric_type:
            query["type"] = metric_type
        if enabled_only:
            query["enabled"] = True
        return await collection.count_documents(query)
    
    async def upsert_by_name(self, metric: MetricDocument) -> str:
        """Insert or update a metric by name."""
        collection = self._get_collection()
        metric.updated_at = datetime.utcnow()
        
        existing = await self.get_by_name(metric.name)
        if existing:
            # Update existing
            await self.update(str(existing.id), metric.model_dump(exclude={"id", "_id", "created_at"}))
            return str(existing.id)
        else:
            # Insert new
            result = await collection.insert_one(metric.to_dict())
            return str(result.inserted_id)

