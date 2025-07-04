Agentic Research Paper Intelligence Platform

Overview

Build a fullstack GenAI-powered platform that helps users manage, understand, and learn from research papers. The platform should proactively assist users in their research workflow with intelligent, agentic features. The frontend (Next.js, dark chat UI) is already built. This document details the backend, AI, and integration requirements, explaining the working of each feature and how they interact.



Core Features & Detailed Workflow

1. User Authentication & Profiles
 • Users register/login with email and password (JWT-based).
 • User profile stores preferences, recent activity, and learning goals.
 • Authentication secures all endpoints and personalizes the experience.

2. Paper Upload & Processing
 • Users upload PDFs of research papers.
 • Backend extracts metadata (title, authors, abstract) and full text using ‎`pdfplumber` or ‎`PyMuPDF`.
 • Paper is stored in ‎`/storage` and indexed in SQLite.
 • On upload, the backend:
 ▫ Automatically triggers summarization (LLM via Groq+LangChain).
 ▫ Generates study notes, flashcards, and a mind map.
 ▫ Embeds paper sections into vector store (ChromaDB/Pinecone) for semantic search.

3. My Papers & Paper Management
 • Users see a library of uploaded papers, each with metadata and status.
 • Selecting a paper loads its context into the chat interface.
 • Users can delete, rename, or update papers.
 • All paper data is linked to the user profile.

4. Chat-Based Q&A (with RAG)
 • Users interact with a chat interface to ask questions about any paper or across their entire library.
 • When a question is asked:
 ▫ LangChain retrieves relevant paper chunks (via vector search).
 ▫ Groq LLM answers the question using retrieved context (RAG).
 ▫ Answers are shown as AI chat bubbles.
 • Chat history is stored per user and paper for continuity.

5. Study Planner & Agentic Workflow
 • Users set study goals (e.g., “Master GANs in 2 weeks”).
 • The platform’s agent (via LangChain) analyzes the user’s papers and goals, then:
 ▫ Suggests a reading schedule based on paper complexity and deadlines.
 ▫ Automatically schedules sessions and reminders.
 ▫ Tracks progress and adjusts the plan if the user falls behind or completes tasks early.
 • Planner integrates with the chat: users can ask for updates, reschedule, or get recommendations.

6. Notes, Flashcards, and Mind Maps
 • For each paper, the backend generates:
 ▫ Concise study notes and key takeaways.
 ▫ Flashcards (Q&A pairs) for active recall.
 ▫ A mind map (JSON structure for frontend visualization) showing key concepts and relationships.
 • Users can review, edit, or export these materials.
 • Materials are linked to the study planner (e.g., flashcards for upcoming sessions).

7. Insights & Proactive Agentic Features
 • The platform proactively:
 ▫ Flags novel findings, contradictions, or gaps between papers.
 ▫ Surfaces trends or recurring themes across the user’s library.
 ▫ Sends weekly digest emails with new insights and study progress (optional).
 • Insights appear in a dedicated sidebar section and can be loaded into the chat for discussion.

How Features Work Together
 • Agentic Workflow: The platform is not just reactive; it acts as a research partner. Uploading a paper triggers automatic processing and content generation. Setting a goal activates the agent to plan and guide study sessions, adapting as the user interacts.
 • Chat as the Hub: All major actions—Q&A, planner updates, insight discussions—happen through the chat interface, making the experience unified and intuitive.
 • Semantic Search & RAG: Every Q&A leverages the vector store for context-aware answers, ensuring responses are specific to the user’s library.
 • Proactive Support: The system monitors user activity and research content to offer timely suggestions, reminders, and insights.

Tech Stack
 • Frontend: Next.js (TypeScript, dark chat UI, shadcn/ui or Chakra UI)
 • Backend: FastAPI (Python), SQLite, SQLAlchemy
 • AI/LLM: Groq API (Llama 3/Mistral), LangChain
 • Vector Store: ChromaDB or Pinecone
 • Data Processing: pdfplumber, PyMuPDF
 • Auth: JWT
 • File Storage: Local ‎`/storage`


1. Project Structure
 • ‎`/frontend` — Next.js frontend (already built)
 • ‎`/backend` — FastAPI backend (to be built)
 • ‎`/ai` — AI/ML scripts and utilities (to be built)
 • ‎`/storage` — Uploaded PDFs and assets

2. Backend API
 • Framework: FastAPI (Python)
 • Features:
 ▫ User authentication (JWT-based)
 ▫ File upload (PDFs) with secure local storage
 ▫ Metadata extraction (title, authors, abstract, etc.)
 ▫ Paper management (CRUD)
 ▫ Study planner endpoints (CRUD for goals/sessions)
 ▫ Q&A endpoint (user question, AI answer)
 ▫ Notes, flashcards, mind map endpoints
 ▫ User preferences/settings
 • Persistence: SQLite with SQLAlchemy ORM

3. AI/ML Layer
 • PDF Parsing: ‎`pdfplumber` or ‎`PyMuPDF`
 • Summarization/Notes/Q&A: Groq API (Llama 3/Mistral) via LangChain
 • Vector Embeddings & RAG: sentence-transformers or Groq embeddings; vector store with ChromaDB or Pinecone
 • Agentic Features: LangChain agents to automate study planning, suggest readings, and surface trends/contradictions

4. Integration
 • Document endpoints with OpenAPI
 • All responses as JSON matching frontend expectations
 • Replace frontend mock data with real API calls (JWT auth)
 • File uploads via multipart/form-data
 • Handle loading/error states in frontend

5. Deployment & Local Dev
 • Frontend: Vercel
 • Backend: Render
 • Use environment variables for all secrets

6. Documentation
 • API docs, setup, and usage in ‎`/docs`
 • README in ‎`/backend` and ‎`/ai` with setup instructions

7. Tech Stack
 • Frontend: Next.js (TypeScript, shadcn/ui/Chakra UI, dark chat UI)
 • Backend: FastAPI, SQLite, SQLAlchemy
 • AI/LLM: Groq API, LangChain
 • Vector Store: ChromaDB or Pinecone

  FastAPI backend with all required endpoints and SQLite models
 2. File upload and parsing
 3. LLM-powered features (summarization, Q&A, analytics) via Groq + LangChain
 4. Vector search and RAG
 5. Connect frontend to backend, replacing mock data
 6. Polish UI/UX for chat, planner/reports, and insights
 7. Deploy and document

