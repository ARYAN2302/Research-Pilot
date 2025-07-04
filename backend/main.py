import sys
import os
import json
from pathlib import Path

os.environ['ANONYMIZED_TELEMETRY'] = 'false'
os.environ['CHROMA_TELEMETRY'] = 'false'
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
from datetime import datetime

from database import engine, get_db
from models import Base, User, Paper, Note, Flashcard, MindMap, StudyPlan, StudySession, ChatSession, ChatMessage, Insight
from schemas import (
    UserCreate, UserLogin, User as UserSchema, Token,
    PaperCreate, Paper as PaperSchema,
    NoteCreate, Note as NoteSchema,
    FlashcardCreate, Flashcard as FlashcardSchema,
    MindMapCreate, MindMap as MindMapSchema,
    StudyPlanCreate, StudyPlan as StudyPlanSchema,
    StudySessionCreate, StudySession as StudySessionSchema,
    ChatSessionCreate, ChatSession as ChatSessionSchema,
    ChatMessageCreate, ChatMessage as ChatMessageSchema,
    InsightCreate, Insight as InsightSchema,
    QuestionAnswerRequest, QuestionAnswerResponse
)
from auth import verify_password, get_password_hash, create_access_token, verify_token
from background_tasks import process_paper_background, start_background_tasks
from ai.llm_processor import LLMProcessor
from ai.vector_store import VectorStore, RAGProcessor

Base.metadata.create_all(bind=engine)

llm_processor = LLMProcessor()
vector_store = VectorStore()
rag_processor = RAGProcessor(vector_store)

start_background_tasks()

app = FastAPI(
    title="Research Pilot API",
    description="Agentic Research Paper Intelligence Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Storage configuration
STORAGE_PATH = os.getenv("STORAGE_PATH", "../storage")
os.makedirs(STORAGE_PATH, exist_ok=True)

# Dependency to get current user
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials
    email = verify_token(token, credentials_exception)
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# Authentication endpoints
@app.post("/auth/register", response_model=UserSchema)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        learning_goals=user.learning_goals,
        preferences=user.preferences
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/auth/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# User endpoints
@app.get("/users/me", response_model=UserSchema)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@app.put("/users/me", response_model=UserSchema)
def update_current_user(
    full_name: Optional[str] = None,
    learning_goals: Optional[str] = None,
    preferences: Optional[dict] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if full_name is not None:
        current_user.full_name = full_name
    if learning_goals is not None:
        current_user.learning_goals = learning_goals
    if preferences is not None:
        current_user.preferences = preferences
    
    db.commit()
    db.refresh(current_user)
    return current_user

# Paper endpoints
@app.post("/papers/upload", response_model=PaperSchema)
async def upload_paper(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save file
    file_path = os.path.join(STORAGE_PATH, f"{current_user.id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create paper record
    db_paper = Paper(
        title=file.filename,
        file_path=file_path,
        file_size=os.path.getsize(file_path),
        owner_id=current_user.id,
        status="processing"
    )
    db.add(db_paper)
    db.commit()
    db.refresh(db_paper)
    
    # TODO: Process paper in background
    # Trigger background processing
    await process_paper_background(db_paper.id)
    
    return db_paper

@app.get("/papers", response_model=List[PaperSchema])
def get_papers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Paper).filter(Paper.owner_id == current_user.id).all()

@app.get("/papers/{paper_id}", response_model=PaperSchema)
def get_paper(paper_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.owner_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

@app.delete("/papers/{paper_id}")
def delete_paper(paper_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.owner_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Delete file
    if os.path.exists(paper.file_path):
        os.remove(paper.file_path)
    
    db.delete(paper)
    db.commit()
    return {"message": "Paper deleted successfully"}

# Notes endpoints
@app.post("/papers/{paper_id}/notes", response_model=NoteSchema)
def create_note(
    paper_id: int,
    note: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.owner_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    db_note = Note(**note.dict(), paper_id=paper_id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

@app.get("/papers/{paper_id}/notes", response_model=List[NoteSchema])
def get_notes(paper_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.owner_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return db.query(Note).filter(Note.paper_id == paper_id).all()

# Flashcards endpoints
@app.post("/papers/{paper_id}/flashcards", response_model=FlashcardSchema)
def create_flashcard(
    paper_id: int,
    flashcard: FlashcardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.owner_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    db_flashcard = Flashcard(**flashcard.dict(), paper_id=paper_id)
    db.add(db_flashcard)
    db.commit()
    db.refresh(db_flashcard)
    return db_flashcard

@app.get("/papers/{paper_id}/flashcards", response_model=List[FlashcardSchema])
def get_flashcards(paper_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.owner_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return db.query(Flashcard).filter(Flashcard.paper_id == paper_id).all()

# Mind Maps endpoints
@app.post("/papers/{paper_id}/mindmaps", response_model=MindMapSchema)
def create_mindmap(
    paper_id: int,
    mindmap: MindMapCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.owner_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    db_mindmap = MindMap(**mindmap.dict(), paper_id=paper_id)
    db.add(db_mindmap)
    db.commit()
    db.refresh(db_mindmap)
    return db_mindmap

@app.get("/papers/{paper_id}/mindmaps", response_model=List[MindMapSchema])
def get_mindmaps(paper_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.owner_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return db.query(MindMap).filter(MindMap.paper_id == paper_id).all()

# Study Plan endpoints
@app.post("/study-plans", response_model=StudyPlanSchema)
def create_study_plan(
    plan: StudyPlanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_plan = StudyPlan(**plan.dict(), user_id=current_user.id)
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

@app.post("/study-plans/generate", response_model=StudyPlanSchema)
def generate_study_plan(
    goal: str,
    deadline: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate an AI-powered study plan based on user's papers and goals"""
    try:
        # Get user's papers
        papers = db.query(Paper).filter(Paper.owner_id == current_user.id).all()
        papers_data = [
            {
                "title": paper.title,
                "abstract": paper.abstract,
                "authors": paper.authors,
                "id": paper.id
            }
            for paper in papers
        ]
        
        # Generate study plan using LLM
        plan_data = llm_processor.generate_study_plan(goal, papers_data, deadline)
        
        # Create study plan record
        db_plan = StudyPlan(
            user_id=current_user.id,
            title=plan_data.get("plan_title", f"Study Plan: {goal}"),
            description=f"AI-generated study plan for: {goal}",
            goal=goal,
            deadline=deadline,
            schedule=plan_data.get("weekly_schedule", []),
            progress={"completed_weeks": 0, "total_weeks": len(plan_data.get("weekly_schedule", []))},
            status="active"
        )
        db.add(db_plan)
        db.commit()
        db.refresh(db_plan)
        
        # Create study sessions from the plan
        for week_data in plan_data.get("weekly_schedule", []):
            session = StudySession(
                plan_id=db_plan.id,
                title=f"Week {week_data.get('week', 1)}: {week_data.get('focus', 'Study Session')}",
                description=f"Tasks: {', '.join(week_data.get('tasks', []))}",
                scheduled_date=datetime.utcnow(),  # You might want to calculate actual dates
                status="scheduled"
            )
            db.add(session)
        
        db.commit()
        return db_plan
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating study plan: {str(e)}")

@app.get("/study-plans", response_model=List[StudyPlanSchema])
def get_study_plans(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(StudyPlan).filter(StudyPlan.user_id == current_user.id).all()

@app.get("/study-plans/{plan_id}", response_model=StudyPlanSchema)
def get_study_plan(plan_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    plan = db.query(StudyPlan).filter(StudyPlan.id == plan_id, StudyPlan.user_id == current_user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Study plan not found")
    return plan

# Generate insights endpoint
@app.post("/insights/generate")
def generate_insights(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate insights from user's papers"""
    try:
        # Get user's papers
        papers = db.query(Paper).filter(Paper.owner_id == current_user.id).all()
        papers_data = []
        
        for paper in papers:
            paper_data = {
                "title": paper.title or "Untitled Paper",
                "abstract": paper.abstract or "No abstract available", 
                "authors": paper.authors or "Unknown",
                "id": paper.id
            }
            papers_data.append(paper_data)
        
        if not papers_data:
            return {"message": "No papers found for analysis"}
        
        # Generate insights using LLM
        insights_data = llm_processor.analyze_insights(papers_data)
        
        # Ensure insights_data is not None and is a list
        if not insights_data or not isinstance(insights_data, list):
            insights_data = [
                {
                    "type": "trend",
                    "title": "Research Portfolio Analysis",
                    "description": f"Analysis of {len(papers_data)} research papers in your collection.",
                    "relevance_score": 5,
                    "related_papers": [p["title"] for p in papers_data]
                }
            ]
        
        # Store insights in database
        stored_count = 0
        for insight_data in insights_data:
            if isinstance(insight_data, dict) and "title" in insight_data:
                # Ensure related_papers is properly serialized
                related_papers = insight_data.get("related_papers", [])
                if not isinstance(related_papers, list):
                    related_papers = []
                
                insight = Insight(
                    user_id=current_user.id,
                    title=insight_data.get("title", "Research Insight"),
                    content=insight_data.get("description", "Generated insight"),
                    type=insight_data.get("type", "trend"),
                    relevance_score=min(max(insight_data.get("relevance_score", 5), 1), 10),  # Ensure 1-10 range
                    related_papers=json.dumps(related_papers),  # Store as JSON string
                    is_read=False
                )
                db.add(insight)
                stored_count += 1
        
        db.commit()
        return {"message": f"Generated {stored_count} insights"}
        
    except Exception as e:
        import traceback
        print(f"Insights generation error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")

# Get paper analysis endpoint
@app.get("/papers/{paper_id}/analysis")
def get_paper_analysis(paper_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get comprehensive analysis of a paper"""
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.owner_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get notes, flashcards, and mind maps
    notes = db.query(Note).filter(Note.paper_id == paper_id).all()
    flashcards = db.query(Flashcard).filter(Flashcard.paper_id == paper_id).all()
    mind_maps = db.query(MindMap).filter(MindMap.paper_id == paper_id).all()
    
    return {
        "paper": paper,
        "notes": notes,
        "flashcards": flashcards,
        "mind_maps": mind_maps,
        "analysis_complete": paper.status == "ready"
    }

# Study Session endpoints
@app.post("/study-sessions", response_model=StudySessionSchema)
def create_study_session(
    session: StudySessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = db.query(StudyPlan).filter(StudyPlan.id == session.plan_id, StudyPlan.user_id == current_user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Study plan not found")
    
    db_session = StudySession(**session.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@app.get("/study-sessions", response_model=List[StudySessionSchema])
def get_study_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_plan_ids = [plan.id for plan in db.query(StudyPlan).filter(StudyPlan.user_id == current_user.id).all()]
    return db.query(StudySession).filter(StudySession.plan_id.in_(user_plan_ids)).all()

# Chat endpoints
@app.post("/chat/sessions", response_model=ChatSessionSchema)
def create_chat_session(
    session: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if session.paper_id:
        paper = db.query(Paper).filter(Paper.id == session.paper_id, Paper.owner_id == current_user.id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
    
    db_session = ChatSession(**session.dict(), user_id=current_user.id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@app.get("/chat/sessions", response_model=List[ChatSessionSchema])
def get_chat_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(ChatSession).filter(ChatSession.user_id == current_user.id).all()

@app.post("/chat/message", response_model=ChatMessageSchema)
def create_chat_message(
    message: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(ChatSession.id == message.session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    db_message = ChatMessage(**message.dict())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

@app.get("/chat/sessions/{session_id}/messages", response_model=List[ChatMessageSchema])
def get_chat_messages(session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()

# Q&A endpoint with RAG
@app.post("/chat/ask", response_model=QuestionAnswerResponse)
def ask_question(
    request: QuestionAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Get chat history if session_id provided
        chat_history = []
        if request.session_id:
            session = db.query(ChatSession).filter(
                ChatSession.id == request.session_id, 
                ChatSession.user_id == current_user.id
            ).first()
            if session:
                messages = db.query(ChatMessage).filter(
                    ChatMessage.session_id == request.session_id
                ).order_by(ChatMessage.timestamp.desc()).limit(6).all()
                chat_history = [
                    {"role": msg.role, "content": msg.content} 
                    for msg in reversed(messages)
                ]
        
        # Use RAG to get answer
        result = rag_processor.answer_with_context(
            query=request.question,
            llm_processor=llm_processor,
            paper_id=request.paper_id,
            chat_history=chat_history
        )
        
        # Store the conversation if session_id provided
        if request.session_id:
            # Store user message
            user_message = ChatMessage(
                session_id=request.session_id,
                role="user",
                content=request.question
            )
            db.add(user_message)
            
            # Store assistant message
            assistant_message = ChatMessage(
                session_id=request.session_id,
                role="assistant",
                content=result["answer"],
                context={"sources": result["sources"], "num_sources": result["num_sources"]}
            )
            db.add(assistant_message)
            db.commit()
        
        return QuestionAnswerResponse(
            answer=result["answer"],
            context=result["context"],
            sources=result["sources"]
        )
        
    except Exception as e:
        return QuestionAnswerResponse(
            answer=f"Error processing question: {str(e)}",
            context=[],
            sources=[]
        )

# Insights endpoints
@app.get("/insights", response_model=List[InsightSchema])
def get_insights(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    insights = db.query(Insight).filter(Insight.user_id == current_user.id).all()
    
    # Process insights to handle JSON fields properly
    processed_insights = []
    for insight in insights:
        # Parse related_papers JSON if it's a string
        related_papers = insight.related_papers
        if isinstance(related_papers, str):
            try:
                related_papers = json.loads(related_papers)
            except (json.JSONDecodeError, TypeError):
                related_papers = []
        elif related_papers is None:
            related_papers = []
        
        # Create processed insight
        processed_insight = {
            "id": insight.id,
            "title": insight.title,
            "content": insight.content,
            "type": insight.type,
            "relevance_score": insight.relevance_score,
            "related_papers": related_papers,
            "user_id": insight.user_id,
            "created_at": insight.created_at,
            "is_read": insight.is_read
        }
        processed_insights.append(processed_insight)
    
    return processed_insights

@app.post("/insights/{insight_id}/read")
def mark_insight_read(insight_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    insight = db.query(Insight).filter(Insight.id == insight_id, Insight.user_id == current_user.id).first()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    insight.is_read = True
    db.commit()
    return {"message": "Insight marked as read"}

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
