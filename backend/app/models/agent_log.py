from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class AgentLog(Base):
    __tablename__ = "agent_logs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    repository_id: Mapped[int | None] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True)
    agent_name: Mapped[str] = mapped_column(String(100))
    input_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="success")
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    repository: Mapped["Repository"] = relationship(back_populates="agent_logs")
