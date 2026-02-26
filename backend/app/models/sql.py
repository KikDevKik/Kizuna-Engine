from sqlalchemy import Column, String, Integer, JSON, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base
from uuid import uuid4

class NodeModel(Base):
    __tablename__ = "nodes"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    label = Column(String, index=True) # e.g., 'User', 'Agent', 'MemoryEpisode'
    data = Column(JSON) # Stores the Pydantic model
    vector_embedding_id = Column(String, nullable=True) # Future-proofing
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_nodes_label_id", "label", "id"),
    )

class EdgeModel(Base):
    __tablename__ = "edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String, ForeignKey("nodes.id"), nullable=False)
    target_id = Column(String, ForeignKey("nodes.id"), nullable=False)
    type = Column(String, nullable=False, index=True) # e.g., 'interactedWith'
    properties = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_edges_source_target_type", "source_id", "target_id", "type"),
    )
