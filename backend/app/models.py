from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True)
    source_url = Column(String(500))
    filename = Column(String(255))
    duration_sec = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    analyses = relationship("Analysis", back_populates="video", cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    risk_score = Column(Float)
    category = Column(String(32))
    transcript = Column(Text, default="")
    ocr_text = Column(Text, default="")
    text_score = Column(Float, default=0.0)
    vision_score = Column(Float, default=0.0)
    processing_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    video = relationship("Video", back_populates="analyses")
    signals = relationship("Signal", back_populates="analysis", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="analysis", cascade="all, delete-orphan")
    model_prediction = relationship("ModelPrediction", back_populates="analysis", uselist=False, cascade="all, delete-orphan")


class ModelPrediction(Base):
    """Separate table adds ML history without altering existing analyses."""
    __tablename__ = 'model_predictions'

    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey('analyses.id'), unique=True, nullable=False)
    payload = Column(JSON, nullable=False)
    analysis = relationship('Analysis', back_populates='model_prediction')


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"))
    source = Column(String(16))
    description = Column(String(300))

    analysis = relationship("Analysis", back_populates="signals")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"))
    is_correct = Column(Boolean)
    true_category = Column(String(32))
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    analysis = relationship("Analysis", back_populates="feedback")
