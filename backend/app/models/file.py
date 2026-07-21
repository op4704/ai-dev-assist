from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class File(Base):
    __tablename__ = "files"
    __table_args__ = (UniqueConstraint("repository_id", "path", name="uq_file_repo_path"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"))
    path: Mapped[str] = mapped_column(String(1000))
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    content_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    repository: Mapped["Repository"] = relationship(back_populates="files")
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="file", cascade="all, delete-orphan")
