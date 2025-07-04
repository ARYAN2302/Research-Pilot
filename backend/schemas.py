from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    learning_goals: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Paper schemas
class PaperBase(BaseModel):
    title: Optional[str] = None
    authors: Optional[str] = None
    abstract: Optional[str] = None

class PaperCreate(PaperBase):
    pass

class Paper(PaperBase):
    id: int
    file_path: str
    file_size: int
    upload_date: datetime
    owner_id: int
    status: str
    paper_metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

# Note schemas
class NoteBase(BaseModel):
    title: str
    content: str
    summary: Optional[str] = None
    key_takeaways: Optional[List[str]] = None

class NoteCreate(NoteBase):
    paper_id: int

class Note(NoteBase):
    id: int
    paper_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Flashcard schemas
class FlashcardBase(BaseModel):
    question: str
    answer: str
    difficulty: str = "medium"
    category: Optional[str] = None

class FlashcardCreate(FlashcardBase):
    paper_id: int

class Flashcard(FlashcardBase):
    id: int
    paper_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Mind Map schemas
class MindMapBase(BaseModel):
    title: str
    structure: Dict[str, Any]

class MindMapCreate(MindMapBase):
    paper_id: int

class MindMap(MindMapBase):
    id: int
    paper_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Study Plan schemas
class StudyPlanBase(BaseModel):
    title: str
    description: Optional[str] = None
    goal: str
    deadline: Optional[datetime] = None
    schedule: Optional[Dict[str, Any]] = None

class StudyPlanCreate(StudyPlanBase):
    pass

class StudyPlan(StudyPlanBase):
    id: int
    user_id: int
    status: str
    progress: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Study Session schemas
class StudySessionBase(BaseModel):
    title: str
    description: Optional[str] = None
    scheduled_date: datetime
    notes: Optional[str] = None

class StudySessionCreate(StudySessionBase):
    plan_id: int

class StudySession(StudySessionBase):
    id: int
    plan_id: int
    completed_date: Optional[datetime] = None
    status: str
    
    class Config:
        from_attributes = True

# Chat schemas
class ChatSessionBase(BaseModel):
    title: str
    paper_id: Optional[int] = None

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSession(ChatSessionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ChatMessageBase(BaseModel):
    role: str
    content: str
    context: Optional[Dict[str, Any]] = None

class ChatMessageCreate(ChatMessageBase):
    session_id: int

class ChatMessage(ChatMessageBase):
    id: int
    session_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

# Insight schemas
class InsightBase(BaseModel):
    title: str
    content: str
    type: str
    relevance_score: int = 0
    related_papers: Optional[List[str]] = None  # Changed to List[str] for paper titles

class InsightCreate(InsightBase):
    user_id: int

class Insight(InsightBase):
    id: int
    user_id: int
    created_at: datetime
    is_read: bool
    
    class Config:
        from_attributes = True

# API Response schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class QuestionAnswerRequest(BaseModel):
    question: str
    paper_id: Optional[int] = None
    session_id: Optional[int] = None

class QuestionAnswerResponse(BaseModel):
    answer: str
    context: Optional[List[str]] = None
    sources: Optional[List[str]] = None
