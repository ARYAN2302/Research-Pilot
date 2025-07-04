# Agentic Research Paper Intelligence Platform

An AI-powered platform that helps researchers manage, understand, and learn from research papers through intelligent conversation and automated study planning.

## Features

- **PDF Processing**: Upload and automatically process research papers
- **AI Chat**: Intelligent Q&A with your research papers using RAG
- **Study Planning**: AI-generated personalized study plans and schedules
- **Smart Insights**: Automated insights and trend analysis across papers
- **Study Materials**: Auto-generated notes, flashcards, and mind maps
- **Vector Search**: Semantic search across your research library

## Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI, SQLAlchemy, SQLite
- **AI/LLM**: Groq API, LangChain
- **Vector Database**: ChromaDB
- **Authentication**: JWT

## Setup

### Prerequisites

- Node.js 18+
- Python 3.8+
- Groq API key

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file:
```env
SECRET_KEY=your-secret-key-here
GROQ_API_KEY=your-groq-api-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL=sqlite:///./research_pilot.db
STORAGE_PATH=../storage
VECTOR_STORE_PATH=./vector_store
ANONYMIZED_TELEMETRY=false
CHROMA_TELEMETRY=false
```

4. Start the backend server:
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

## Usage

1. Open http://localhost:3000 in your browser
2. Register a new account or login
3. Upload PDF research papers
4. Start chatting with your papers or explore AI-generated insights
5. Create study plans and track your progress

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.

## License

MIT License
