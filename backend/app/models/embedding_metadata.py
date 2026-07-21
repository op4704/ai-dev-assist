from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class EmbeddingMetadata(Base):
    __tablename__ = "embeddings_metadata"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("chunks.id", ondelete="CASCADE"), unique=True)
    vector_id: Mapped[str] = mapped_column(String(255))
    embedding_model: Mapped[str] = mapped_column(String(100))
    dimension: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    chunk: Mapped["Chunk"] = relationship(back_populates="embedding_metadata")
