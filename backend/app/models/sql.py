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

from sqlalchemy import UniqueConstraint, Integer, JSON

class KizunaChronicleModel(Base):
    """
    Kizuna's Eternal Memory — immune to purge_all_memories().
    Records the relational dynamics Kizuna observes between users and agents.
    Survives all wipes. This is Kizuna's private truth.
    """
    __tablename__ = "kizuna_chronicle"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, nullable=False, index=True)
    agent_id = Column(String, nullable=False, index=True)
    agent_name = Column(String, nullable=False)  # stored separately — agent JSON may be deleted
    relationship_summary = Column(String, nullable=True)  # "Siempre discutían pero se buscaban"
    dominant_topics = Column(JSON, default=list)  # ["anime", "música", "filosofía"]
    emotional_tone = Column(String, nullable=True)  # "tensa_cercana" / "admiración" / "dependencia"
    interaction_count = Column(Integer, default=0)
    survived_wipes = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'agent_id', name='uq_user_agent_chronicle'),
    )
