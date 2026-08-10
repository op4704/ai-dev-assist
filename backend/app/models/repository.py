import enum
from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class RepositoryStatus(str, enum.Enum):
    PENDING = "pending"
    CLONING = "cloning"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

class Repository(Base):
    __tablename__ = "repositories"
    __table_args__ = (UniqueConstraint("user_id", "github_url", name="uq_repo_user_url"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    github_url: Mapped[str] = mapped_column(String(500))
    owner: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    default_branch: Mapped[str] = mapped_column(String(100), default="main")
    local_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[RepositoryStatus] = mapped_column(Enum(RepositoryStatus, native_enum=False, length=20), default=RepositoryStatus.PENDING)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user: Mapped["User"] = relationship(back_populates="repositories")
    files: Mapped[list["File"]] = relationship(back_populates="repository", cascade="all, delete-orphan")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="repository", cascade="all, delete-orphan")
    agent_logs: Mapped[list["AgentLog"]] = relationship(back_populates="repository", cascade="all, delete-orphan")
    security_findings: Mapped[list["SecurityFinding"]] = relationship(back_populates="repository", cascade="all, delete-orphan")
    generated_docs: Mapped[list["GeneratedDoc"]] = relationship(back_populates="repository", cascade="all, delete-orphan")