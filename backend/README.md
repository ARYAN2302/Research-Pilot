# Backend API

FastAPI backend for the Research Paper Intelligence Platform.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and update with your API keys

3. Start the server:
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Visit http://localhost:8000/docs for interactive API documentation.

## Environment Variables

- `SECRET_KEY`: JWT secret key
- `GROQ_API_KEY`: Groq API key for LLM
- `DATABASE_URL`: SQLite database URL
- `STORAGE_PATH`: Path for uploaded files
- `VECTOR_STORE_PATH`: Path for vector database
