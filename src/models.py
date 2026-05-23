from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    department = Column(String, nullable=True)
    position = Column(String, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, server_default=func.now())


class FaceTemplate(Base):
    __tablename__ = "face_templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    embedding = Column(Text, nullable=False)
    embedding_model = Column(String, default="unknown")
    embedding_dim = Column(Integer, default=0)
    quality_score = Column(Float, default=0.0)

    status = Column(String, default="active")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AccessEvent(Base):
    __tablename__ = "access_events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, nullable=True)
    access_point_id = Column(Integer, nullable=True)
    controller_id = Column(String, nullable=True)
    decision = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    similarity = Column(Float, nullable=True)
    liveness_score = Column(Float, nullable=True)
    sync_status = Column(String, default="synced")
