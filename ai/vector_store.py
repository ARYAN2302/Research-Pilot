import os
os.environ['ANONYMIZED_TELEMETRY'] = 'false'
os.environ['CHROMA_TELEMETRY'] = 'false'

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import logging

logging.getLogger('chromadb.telemetry').setLevel(logging.CRITICAL)

class VectorStore:
    def __init__(self, persist_directory: str = "./vector_store"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        try:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False, allow_reset=True)
            )
        except Exception as e:
            self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="research_papers",
            metadata={"description": "Research paper embeddings"}
        )
    
    def add_paper(self, paper_id: int, title: str, content: str, chunks: List[str], metadata: Dict[str, Any] = None):
        """Add a paper's chunks to the vector store"""
        try:
            # Generate embeddings for all chunks
            embeddings = self.embedding_model.encode(chunks).tolist()
            
            # Create unique IDs for each chunk
            chunk_ids = [f"paper_{paper_id}_chunk_{i}" for i in range(len(chunks))]
            
            # Prepare metadata for each chunk
            chunk_metadata = []
            for i, chunk in enumerate(chunks):
                chunk_meta = {
                    "paper_id": paper_id,
                    "title": title,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "timestamp": datetime.utcnow().isoformat(),
                    "content_length": len(chunk)
                }
                if metadata:
                    chunk_meta.update(metadata)
                chunk_metadata.append(chunk_meta)
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=chunks,
                metadatas=chunk_metadata,
                ids=chunk_ids
            )
            
            return True
        except Exception as e:
            print(f"Error adding paper to vector store: {str(e)}")
            return False
    
    def search_similar(self, query: str, n_results: int = 5, paper_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for similar content using vector similarity"""
        try:
            # Generate embedding for query
            query_embedding = self.embedding_model.encode([query]).tolist()
            
            # Prepare where clause for filtering
            where_clause = None
            if paper_id:
                where_clause = {"paper_id": paper_id}
            
            # Search in collection
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                where=where_clause
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['documents'][0])):
                result = {
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else 0.0,
                    "id": results['ids'][0][i]
                }
                formatted_results.append(result)
            
            return formatted_results
        except Exception as e:
            print(f"Error searching vector store: {str(e)}")
            return []
    
    def search_by_paper(self, paper_id: int, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Search within a specific paper"""
        return self.search_similar(query, n_results, paper_id)
    
    def get_paper_chunks(self, paper_id: int) -> List[Dict[str, Any]]:
        """Get all chunks for a specific paper"""
        try:
            results = self.collection.get(
                where={"paper_id": paper_id}
            )
            
            formatted_results = []
            for i in range(len(results['documents'])):
                result = {
                    "content": results['documents'][i],
                    "metadata": results['metadatas'][i],
                    "id": results['ids'][i]
                }
                formatted_results.append(result)
            
            # Sort by chunk index
            formatted_results.sort(key=lambda x: x['metadata'].get('chunk_index', 0))
            return formatted_results
        except Exception as e:
            print(f"Error getting paper chunks: {str(e)}")
            return []
    
    def delete_paper(self, paper_id: int):
        """Delete all chunks for a specific paper"""
        try:
            # Get all chunk IDs for this paper
            results = self.collection.get(
                where={"paper_id": paper_id}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
            
            return True
        except Exception as e:
            print(f"Error deleting paper from vector store: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection.name,
                "embedding_model": "all-MiniLM-L6-v2"
            }
        except Exception as e:
            return {"error": str(e)}

class RAGProcessor:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
    
    def retrieve_context(self, query: str, paper_id: Optional[int] = None, max_chunks: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant context for a query"""
        if paper_id:
            # Search within specific paper
            results = self.vector_store.search_by_paper(paper_id, query, max_chunks)
        else:
            # Search across all papers
            results = self.vector_store.search_similar(query, max_chunks)
        
        return results
    
    def format_context_for_llm(self, context_chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved context for LLM consumption"""
        if not context_chunks:
            return "No relevant context found."
        
        formatted_context = "Relevant context from research papers:\n\n"
        
        for i, chunk in enumerate(context_chunks, 1):
            paper_title = chunk['metadata'].get('title', 'Unknown Paper')
            content = chunk['content']
            
            formatted_context += f"Context {i} (from '{paper_title}'):\n"
            formatted_context += f"{content}\n\n"
        
        return formatted_context
    
    def get_sources(self, context_chunks: List[Dict[str, Any]]) -> List[str]:
        """Extract source information from context chunks"""
        sources = []
        seen_papers = set()
        
        for chunk in context_chunks:
            paper_title = chunk['metadata'].get('title', 'Unknown Paper')
            paper_id = chunk['metadata'].get('paper_id', 'unknown')
            
            if paper_id not in seen_papers:
                sources.append(f"{paper_title} (Paper ID: {paper_id})")
                seen_papers.add(paper_id)
        
        return sources
    
    def answer_with_context(self, query: str, llm_processor, paper_id: Optional[int] = None, chat_history: List[Dict] = None) -> Dict[str, Any]:
        """Complete RAG pipeline: retrieve context and generate answer"""
        # Retrieve relevant context
        context_chunks = self.retrieve_context(query, paper_id)
        
        # Format context for LLM
        formatted_context = self.format_context_for_llm(context_chunks)
        
        # Generate answer using LLM
        answer = llm_processor.answer_question(query, formatted_context, chat_history)
        
        # Get sources
        sources = self.get_sources(context_chunks)
        
        return {
            "answer": answer,
            "context": [chunk['content'] for chunk in context_chunks],
            "sources": sources,
            "num_sources": len(context_chunks)
        }

# Utility functions for text processing
def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to end at a sentence boundary
        if end < len(text):
            # Look for sentence endings
            sentence_end = text.rfind('.', start, end)
            if sentence_end != -1 and sentence_end > start + chunk_size // 2:
                end = sentence_end + 1
            else:
                # Look for word boundaries
                space_pos = text.rfind(' ', start, end)
                if space_pos != -1 and space_pos > start + chunk_size // 2:
                    end = space_pos
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

def preprocess_text(text: str) -> str:
    """Preprocess text for better embeddings"""
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Remove special characters that might interfere with embeddings
    # Keep basic punctuation and alphanumeric characters
    import re
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)]', ' ', text)
    
    return text.strip()
