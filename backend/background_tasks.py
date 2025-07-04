import asyncio
from typing import Dict, Any
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Paper, Note, Flashcard, MindMap
import sys
import os
from pathlib import Path

# Add parent directory to Python path to import ai modules
sys.path.append(str(Path(__file__).parent.parent))

from pdf_processor import process_uploaded_paper
from ai.llm_processor import LLMProcessor
from ai.vector_store import VectorStore, RAGProcessor, chunk_text, preprocess_text
import os
import json

class PaperProcessor:
    def __init__(self):
        self.llm_processor = LLMProcessor()
        self.vector_store = VectorStore()
        self.rag_processor = RAGProcessor(self.vector_store)
    
    async def process_paper(self, paper_id: int):
        """Process a newly uploaded paper: extract content, generate embeddings, create study materials"""
        db = SessionLocal()
        try:
            # Get paper from database
            paper = db.query(Paper).filter(Paper.id == paper_id).first()
            if not paper:
                print(f"Paper with ID {paper_id} not found")
                return
            
            print(f"Processing paper: {paper.title}")
            
            # Update status to processing
            paper.status = "processing"
            db.commit()
            
            # Extract content from PDF
            extracted_content = process_uploaded_paper(paper.file_path)
            
            # Update paper with extracted content
            paper.title = extracted_content.title or paper.title
            paper.authors = extracted_content.authors
            paper.abstract = extracted_content.abstract
            paper.full_text = extracted_content.full_text
            paper.metadata = extracted_content.metadata
            
            # Generate study materials
            await self._generate_study_materials(paper, extracted_content, db)
            
            # Process for vector search
            await self._process_for_vector_search(paper, extracted_content)
            
            # Update status to ready
            paper.status = "ready"
            db.commit()
            
            print(f"Successfully processed paper: {paper.title}")
            
        except Exception as e:
            print(f"Error processing paper {paper_id}: {str(e)}")
            # Update status to error
            if paper:
                paper.status = "error"
                paper.metadata = {"error": str(e)}
                db.commit()
        finally:
            db.close()
    
    async def _generate_study_materials(self, paper: Paper, extracted_content, db: Session):
        """Generate notes, flashcards, and mind maps"""
        try:
            # Generate study notes
            study_notes = self.llm_processor.generate_study_notes(
                extracted_content.full_text, 
                paper.title
            )
            
            # Create note record
            # Ensure we handle the data properly for database insertion
            summary_data = study_notes.get('main_points', [])[:3] if isinstance(study_notes, dict) else []
            summary_text = "; ".join(summary_data) if isinstance(summary_data, list) else str(summary_data)
            
            takeaways_data = study_notes.get('takeaways', []) if isinstance(study_notes, dict) else []
            
            note = Note(
                paper_id=paper.id,
                title=f"Study Notes: {paper.title}",
                content=json.dumps(study_notes),
                summary=summary_text,
                key_takeaways=json.dumps(takeaways_data)  # Store as JSON string
            )
            db.add(note)
            
            # Generate flashcards
            flashcards_data = self.llm_processor.generate_flashcards(
                extracted_content.full_text,
                paper.title,
                num_cards=8
            )
            
            # Create flashcard records
            for card_data in flashcards_data:
                if isinstance(card_data, dict) and 'question' in card_data:
                    flashcard = Flashcard(
                        paper_id=paper.id,
                        question=card_data['question'],
                        answer=card_data['answer'],
                        difficulty=card_data.get('difficulty', 'medium'),
                        category=card_data.get('category', 'concept')
                    )
                    db.add(flashcard)
            
            # Generate mind map
            mind_map_data = self.llm_processor.generate_mind_map(
                extracted_content.full_text,
                paper.title
            )
            
            # Create mind map record
            mind_map = MindMap(
                paper_id=paper.id,
                title=f"Mind Map: {paper.title}",
                structure=mind_map_data
            )
            db.add(mind_map)
            
            db.commit()
            print(f"Generated study materials for paper: {paper.title}")
            
        except Exception as e:
            print(f"Error generating study materials: {str(e)}")
            db.rollback()
    
    async def _process_for_vector_search(self, paper: Paper, extracted_content):
        """Process paper for vector search and RAG"""
        try:
            # Preprocess text
            full_text = preprocess_text(extracted_content.full_text)
            
            # Create chunks
            chunks = chunk_text(full_text, chunk_size=1000, overlap=200)
            
            # Prepare metadata - ChromaDB doesn't accept None values
            metadata = {
                "authors": paper.authors or "Unknown",
                "abstract": paper.abstract or "No abstract available",
                "upload_date": paper.upload_date.isoformat() if paper.upload_date else "",
                "file_path": paper.file_path or ""
            }
            
            # Add to vector store
            success = self.vector_store.add_paper(
                paper_id=paper.id,
                title=paper.title,
                content=full_text,
                chunks=chunks,
                metadata=metadata
            )
            
            if success:
                print(f"Added paper to vector store: {paper.title}")
            else:
                print(f"Failed to add paper to vector store: {paper.title}")
                
        except Exception as e:
            print(f"Error processing paper for vector search: {str(e)}")

class BackgroundTaskManager:
    def __init__(self):
        self.paper_processor = PaperProcessor()
        self.task_queue = asyncio.Queue()
        self.running = False
    
    async def start(self):
        """Start the background task processor"""
        self.running = True
        while self.running:
            try:
                # Wait for a task with timeout
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Process the task
                if task['type'] == 'process_paper':
                    await self.paper_processor.process_paper(task['paper_id'])
                
                # Mark task as done
                self.task_queue.task_done()
                
            except asyncio.TimeoutError:
                # No tasks in queue, continue
                continue
            except Exception as e:
                print(f"Error in background task: {str(e)}")
    
    async def stop(self):
        """Stop the background task processor"""
        self.running = False
        # Wait for current tasks to complete
        await self.task_queue.join()
    
    async def add_paper_processing_task(self, paper_id: int):
        """Add a paper processing task to the queue"""
        await self.task_queue.put({
            'type': 'process_paper',
            'paper_id': paper_id
        })

# Global task manager instance
task_manager = BackgroundTaskManager()

async def process_paper_background(paper_id: int):
    """Add a paper processing task to the background queue"""
    await task_manager.add_paper_processing_task(paper_id)

def start_background_tasks():
    """Start background task processing"""
    import threading
    
    def run_background_tasks():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(task_manager.start())
    
    background_thread = threading.Thread(target=run_background_tasks, daemon=True)
    background_thread.start()
    return background_thread
