from pydantic import BaseModel
from typing import Optional, List

class UserCreate(BaseModel):
    full_name: str
    department: Optional[str] = None
    position: Optional[str] = None
    status: str = "active"

class UserOut(BaseModel):
    id: int
    full_name: str
    department: Optional[str] = None
    position: Optional[str] = None
    status: str

    model_config = {"from_attributes": True}


class FaceCreate(BaseModel):
    embedding: List[float]
    embedding_model: str = "unknown"
    quality_score: float = 1.0


class AccessCheckRequest(BaseModel):
    controller_id: str
    access_point_id: int = 1
    embedding: List[float]
    liveness_score: Optional[float] = None


class AccessCheckResponse(BaseModel):
    decision: str
    reason: str
    user_id: Optional[int] = None
    full_name: Optional[str] = None
    similarity: float
    unlock_duration_sec: int = 0


class EventCreate(BaseModel):
    user_id: Optional[int] = None
    access_point_id: Optional[int] = None
    controller_id: Optional[str] = None
    decision: str
    reason: Optional[str] = None
    similarity: Optional[float] = None
    liveness_score: Optional[float] = None
