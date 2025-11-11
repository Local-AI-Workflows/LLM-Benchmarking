"""Database models for benchmark storage."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId for Pydantic."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class BenchmarkStatus:
    """Status constants for a benchmark run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BenchmarkDocument(BaseModel):
    """MongoDB document model for benchmark results."""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    status: str = Field(default=BenchmarkStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Benchmark configuration
    model_name: Optional[str] = None
    dataset_name: Optional[str] = None
    metrics: List[str] = Field(default_factory=list)
    evaluator_models: List[str] = Field(default_factory=list)
    
    # Benchmark results (stored as JSON-serializable dict)
    result_data: Optional[Dict[str, Any]] = None
    
    # Error information
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    
    # Progress information
    progress: Optional[Dict[str, Any]] = None
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        data = self.dict(by_alias=True, exclude_none=True)
        if "_id" in data and isinstance(data["_id"], ObjectId):
            data["_id"] = str(data["_id"])
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkDocument":
        """Create from dictionary (e.g., from MongoDB)."""
        if "_id" in data and isinstance(data["_id"], str):
            data["_id"] = ObjectId(data["_id"])
        return cls(**data)

