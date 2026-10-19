import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

CATEGORIES = ["investment_platform", "pyramid", "betting", "giveaway", "job_offer", "none"]
STATUSES = ["queued", "running", "done", "failed"]
STAGES = ["queued", "downloading", "listening", "reading_screen", "scoring", "finished"]


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    analyses: Mapped[list["Analysis"]] = relationship(back_populates="user", passive_deletes=True)

    def __str__(self) -> str:
        return self.email


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_type: Mapped[str] = mapped_column(String(10))
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    stored_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    analyses: Mapped[list["Analysis"]] = relationship(back_populates="video")

    def __str__(self) -> str:
        if self.source_url:
            return self.source_url
        return self.original_filename or "video " + str(self.id)


class Analysis(Base):
    __tablename__ = "analyses"
    __table_args__ = (
        Index("ix_analyses_user_created", "user_id", "created_at"),
        Index("ix_analyses_client_created", "client_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    client_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(10), default="queued", index=True)
    stage: Mapped[str] = mapped_column(String(20), default="queued")
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript_language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    links: Mapped[list] = mapped_column(JSON, default=list)
    phones: Mapped[list] = mapped_column(JSON, default=list)
    qr_codes: Mapped[list] = mapped_column(JSON, default=list)
    text_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    vision_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    processing_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User | None] = relationship(back_populates="analyses")
    video: Mapped[Video] = relationship(back_populates="analyses")
    signals: Mapped[list["Signal"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    feedback: Mapped[list["Feedback"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )

    def __str__(self) -> str:
        return self.id


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(20))
    kind: Mapped[str] = mapped_column(String(30), index=True)
    value: Mapped[str] = mapped_column(String(500))
    weight: Mapped[float] = mapped_column(Float, default=0.0)

    analysis: Mapped[Analysis] = relationship(back_populates="signals")

    def __str__(self) -> str:
        return self.kind + ": " + self.value


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), unique=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    true_category: Mapped[str | None] = mapped_column(String(30), nullable=True)
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    analysis: Mapped[Analysis] = relationship(back_populates="feedback")

    def __str__(self) -> str:
        return "feedback " + str(self.id)
