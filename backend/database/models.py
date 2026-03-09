from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sessions = relationship("AnalysisSession", back_populates="user", cascade="all, delete")

class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    company_name = Column(String, nullable=True)
    gstin = Column(String, nullable=True)
    location = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="sessions")
    messages = relationship("AnalysisMessage", back_populates="session", cascade="all, delete")

class AnalysisMessage(Base):
    __tablename__ = "analysis_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("analysis_sessions.id"))
    message_type = Column(String, nullable=False) # e.g., user_upload, extracted_data, analysis_result, system_message
    content = Column(Text, nullable=False) # Store JSON string
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("AnalysisSession", back_populates="messages")
