"""Database models for benchmark storage."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId for Pydantic v2."""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )
    
    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return ObjectId(v)
            raise ValueError("Invalid ObjectId string")
        raise ValueError("Invalid ObjectId")


class BenchmarkStatus:
    """Status constants for a benchmark run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BenchmarkDocument(BaseModel):
    """MongoDB document model for benchmark results."""
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    status: str = Field(default=BenchmarkStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Benchmark configuration
    model_name: Optional[str] = None
    dataset_name: Optional[str] = None
    dataset_id: Optional[str] = None  # Reference to dataset document
    metrics: List[str] = Field(default_factory=list)
    metric_ids: List[str] = Field(default_factory=list)  # References to metric documents
    metric_type: Optional[str] = None  # "standard" or "mcp"
    evaluator_models: List[str] = Field(default_factory=list)
    
    # MCP-specific configuration
    mcp_tools: Optional[List[Dict[str, Any]]] = None  # MCP tool configurations
    
    # Benchmark results (stored as JSON-serializable dict)
    result_data: Optional[Dict[str, Any]] = None
    
    # Error information
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    
    # Progress information
    progress: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage.
        
        Note: Keeps ObjectId as ObjectId for MongoDB operations.
        MongoDB expects ObjectId objects, not strings.
        Pydantic v2's model_dump() preserves Python objects by default.
        """
        data = self.model_dump(by_alias=True, exclude_none=True)
        # Ensure _id is ObjectId if present and is a string (shouldn't happen, but safety check)
        if "_id" in data and isinstance(data["_id"], str):
            # If somehow it's a string, convert back to ObjectId for MongoDB
            try:
                data["_id"] = ObjectId(data["_id"])
            except Exception:
                pass  # Keep as string if conversion fails
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkDocument":
        """Create from dictionary (e.g., from MongoDB)."""
        if "_id" in data and isinstance(data["_id"], str):
            data["_id"] = ObjectId(data["_id"])
        return cls(**data)


class MetricType:
    """Metric type constants."""
    STANDARD = "standard"
    MCP = "mcp"


class MetricDocument(BaseModel):
    """MongoDB document model for metrics."""
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str = Field(..., min_length=1)
    type: str = Field(..., description="standard or mcp")
    description: str = ""
    class_path: Optional[str] = None  # Python class path for dynamic loading
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Metric configuration
    evaluation_instructions: str = ""  # The evaluation prompt/instructions
    scale_min: int = Field(default=0, description="Minimum score value")
    scale_max: int = Field(default=10, description="Maximum score value")
    custom_format: Optional[str] = None  # Custom response format
    additional_context: Optional[str] = None  # Additional context for evaluation
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage.
        
        Note: Keeps ObjectId as ObjectId for MongoDB operations.
        MongoDB expects ObjectId objects, not strings.
        Pydantic v2's model_dump() preserves Python objects by default.
        """
        data = self.model_dump(by_alias=True, exclude_none=True)
        # Ensure _id is ObjectId if present and is a string (shouldn't happen, but safety check)
        if "_id" in data and isinstance(data["_id"], str):
            # If somehow it's a string, convert back to ObjectId for MongoDB
            try:
                data["_id"] = ObjectId(data["_id"])
            except Exception:
                pass  # Keep as string if conversion fails
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricDocument":
        """Create from dictionary (e.g., from MongoDB)."""
        if "_id" in data and isinstance(data["_id"], str):
            data["_id"] = ObjectId(data["_id"])
        return cls(**data)


class DatasetDocument(BaseModel):
    """MongoDB document model for datasets."""
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str = Field(..., min_length=1)
    description: str = ""
    questions: List[Dict[str, Any]] = Field(default_factory=list)  # Question data as dicts
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage.
        
        Note: Keeps ObjectId as ObjectId for MongoDB operations.
        MongoDB expects ObjectId objects, not strings.
        Pydantic v2's model_dump() preserves Python objects by default.
        """
        data = self.model_dump(by_alias=True, exclude_none=True)
        # Ensure _id is ObjectId if present and is a string (shouldn't happen, but safety check)
        if "_id" in data and isinstance(data["_id"], str):
            # If somehow it's a string, convert back to ObjectId for MongoDB
            try:
                data["_id"] = ObjectId(data["_id"])
            except Exception:
                pass  # Keep as string if conversion fails
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetDocument":
        """Create from dictionary (e.g., from MongoDB)."""
        if "_id" in data and isinstance(data["_id"], str):
            data["_id"] = ObjectId(data["_id"])
        return cls(**data)
