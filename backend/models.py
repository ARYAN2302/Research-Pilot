from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    learning_goals = Column(Text)
    preferences = Column(JSON)
    
    # Relationships
    papers = relationship("Paper", back_populates="owner")
    study_plans = relationship("StudyPlan", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")

class Paper(Base):
    __tablename__ = "papers"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    authors = Column(Text)
    abstract = Column(Text)
    full_text = Column(Text)
    file_path = Column(String)
    file_size = Column(Integer)
    upload_date = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="processing")  # processing, ready, error
    paper_metadata = Column(JSON)  # Renamed from 'metadata' to avoid conflict
    
    # Relationships
    owner = relationship("User", back_populates="papers")
    notes = relationship("Note", back_populates="paper")
    flashcards = relationship("Flashcard", back_populates="paper")
    mind_maps = relationship("MindMap", back_populates="paper")
    chat_sessions = relationship("ChatSession", back_populates="paper")

class Note(Base):
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"))
    title = Column(String)
    content = Column(Text)
    summary = Column(Text)
    key_takeaways = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    paper = relationship("Paper", back_populates="notes")

class Flashcard(Base):
    __tablename__ = "flashcards"
    
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"))
    question = Column(Text)
    answer = Column(Text)
    difficulty = Column(String, default="medium")
    category = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    paper = relationship("Paper", back_populates="flashcards")

class MindMap(Base):
    __tablename__ = "mind_maps"
    
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"))
    title = Column(String)
    structure = Column(JSON)  # JSON structure for frontend visualization
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    paper = relationship("Paper", back_populates="mind_maps")

class StudyPlan(Base):
    __tablename__ = "study_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    description = Column(Text)
    goal = Column(Text)
    deadline = Column(DateTime)
    status = Column(String, default="active")  # active, completed, paused
    schedule = Column(JSON)
    progress = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="study_plans")
    sessions = relationship("StudySession", back_populates="plan")

class StudySession(Base):
    __tablename__ = "study_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("study_plans.id"))
    title = Column(String)
    description = Column(Text)
    scheduled_date = Column(DateTime)
    completed_date = Column(DateTime)
    status = Column(String, default="scheduled")  # scheduled, completed, skipped
    notes = Column(Text)
    
    # Relationships
    plan = relationship("StudyPlan", back_populates="sessions")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=True)
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    paper = relationship("Paper", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String)  # user, assistant
    content = Column(Text)
    context = Column(JSON)  # Retrieved context for RAG
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class Insight(Base):
    __tablename__ = "insights"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    content = Column(Text)
    type = Column(String)  # novel_finding, contradiction, trend, gap
    relevance_score = Column(Integer, default=0)
    related_papers = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
