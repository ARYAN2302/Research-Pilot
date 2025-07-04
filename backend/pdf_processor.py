import pdfplumber
import fitz  # PyMuPDF
import os
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ExtractedPaper:
    title: str
    authors: str
    abstract: str
    full_text: str
    metadata: Dict
    sections: List[Dict]

class PDFProcessor:
    def __init__(self):
        self.title_patterns = [
            r'^([A-Z][^.!?]*[.!?]?)$',  # Title case sentences
            r'^([A-Z][A-Z\s]+)$',        # All caps
            r'^(.{10,100})$'              # Reasonable length
        ]
        
    def extract_paper_content(self, file_path: str) -> ExtractedPaper:
        """Extract content from PDF using pdfplumber and PyMuPDF"""
        try:
            # Use pdfplumber for text extraction
            with pdfplumber.open(file_path) as pdf:
                full_text = ""
                pages_text = []
                
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        pages_text.append(page_text)
                        full_text += page_text + "\n"
                
                # Extract metadata using PyMuPDF
                metadata = self._extract_metadata_pymupdf(file_path)
                
                # Extract structured content
                title = self._extract_title(pages_text, metadata)
                authors = self._extract_authors(pages_text, metadata)
                abstract = self._extract_abstract(pages_text)
                sections = self._extract_sections(pages_text)
                
                return ExtractedPaper(
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    full_text=full_text,
                    metadata=metadata,
                    sections=sections
                )
                
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
    
    def _extract_metadata_pymupdf(self, file_path: str) -> Dict:
        """Extract metadata using PyMuPDF"""
        try:
            doc = fitz.open(file_path)
            metadata = doc.metadata
            doc.close()
            
            return {
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'creator': metadata.get('creator', ''),
                'producer': metadata.get('producer', ''),
                'creation_date': metadata.get('creationDate', ''),
                'modification_date': metadata.get('modDate', ''),
                'pages': len(doc) if doc else 0
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _extract_title(self, pages_text: List[str], metadata: Dict) -> str:
        """Extract paper title from first page or metadata"""
        # Try metadata first
        if metadata.get('title') and len(metadata['title']) > 3:
            return metadata['title'].strip()
        
        # Try extracting from first page
        if not pages_text:
            return "Unknown Title"
        
        first_page = pages_text[0]
        lines = first_page.split('\n')
        
        # Look for title patterns in first few lines
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            if len(line) > 10 and len(line) < 200:
                # Check if it looks like a title
                if self._is_likely_title(line):
                    return line
        
        # Fallback to first substantial line
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 10:
                return line
        
        return "Unknown Title"
    
    def _extract_authors(self, pages_text: List[str], metadata: Dict) -> str:
        """Extract authors from paper"""
        # Try metadata first
        if metadata.get('author') and len(metadata['author']) > 2:
            return metadata['author'].strip()
        
        if not pages_text:
            return "Unknown Authors"
        
        first_page = pages_text[0]
        lines = first_page.split('\n')
        
        # Look for author patterns
        author_patterns = [
            r'^([A-Z][a-z]+ [A-Z][a-z]+(?:, [A-Z][a-z]+ [A-Z][a-z]+)*)',
            r'^([A-Z]\. [A-Z][a-z]+(?:, [A-Z]\. [A-Z][a-z]+)*)',
            r'(?:Authors?|By):?\s*([A-Z][^.!?]*)',
        ]
        
        for line in lines[:20]:
            line = line.strip()
            for pattern in author_patterns:
                match = re.search(pattern, line)
                if match:
                    return match.group(1).strip()
        
        return "Unknown Authors"
    
    def _extract_abstract(self, pages_text: List[str]) -> str:
        """Extract abstract from paper"""
        if not pages_text:
            return ""
        
        # Look in first few pages
        text_to_search = ""
        for i, page in enumerate(pages_text[:3]):
            text_to_search += page + "\n"
            if i > 0 and len(text_to_search) > 5000:  # Don't search too far
                break
        
        # Abstract patterns
        abstract_patterns = [
            r'Abstract[:\s]+(.*?)(?=\n\n|\nKeywords?|\nIntroduction|\n1\.)',
            r'ABSTRACT[:\s]+(.*?)(?=\n\n|\nKEYWORDS?|\nINTRODUCTION|\n1\.)',
            r'Summary[:\s]+(.*?)(?=\n\n|\nKeywords?|\nIntroduction|\n1\.)',
        ]
        
        for pattern in abstract_patterns:
            match = re.search(pattern, text_to_search, re.DOTALL | re.IGNORECASE)
            if match:
                abstract = match.group(1).strip()
                # Clean up the abstract
                abstract = re.sub(r'\s+', ' ', abstract)
                if len(abstract) > 50 and len(abstract) < 2000:
                    return abstract
        
        return ""
    
    def _extract_sections(self, pages_text: List[str]) -> List[Dict]:
        """Extract paper sections"""
        sections = []
        full_text = "\n".join(pages_text)
        
        # Common section patterns
        section_patterns = [
            r'\n(\d+\.?\s+[A-Z][^.!?]*[.!?]?)\n',
            r'\n([A-Z][A-Z\s]+)\n',
            r'\n(Introduction|Method|Results|Discussion|Conclusion|References)[:\s]*\n',
        ]
        
        for pattern in section_patterns:
            matches = re.finditer(pattern, full_text, re.IGNORECASE)
            for match in matches:
                section_title = match.group(1).strip()
                start_pos = match.end()
                
                # Find next section or end of text
                next_match = None
                for next_pattern in section_patterns:
                    next_matches = re.finditer(next_pattern, full_text[start_pos:], re.IGNORECASE)
                    for next_match_candidate in next_matches:
                        if next_match is None or next_match_candidate.start() < next_match.start():
                            next_match = next_match_candidate
                        break
                
                if next_match:
                    section_content = full_text[start_pos:start_pos + next_match.start()]
                else:
                    section_content = full_text[start_pos:start_pos + 2000]  # Limit section length
                
                sections.append({
                    'title': section_title,
                    'content': section_content.strip(),
                    'start_pos': start_pos
                })
        
        return sections
    
    def _is_likely_title(self, text: str) -> bool:
        """Determine if text looks like a paper title"""
        # Check length
        if len(text) < 10 or len(text) > 200:
            return False
        
        # Check for title-like characteristics
        title_indicators = [
            text[0].isupper(),  # Starts with capital
            not text.endswith('.'),  # Doesn't end with period
            text.count(' ') > 1,  # Multiple words
            not re.search(r'\d{4}', text),  # No years
            not re.search(r'@|\.com|\.org', text),  # No emails/URLs
        ]
        
        return sum(title_indicators) >= 3
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Chunk text for vector embeddings"""
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

def process_uploaded_paper(file_path: str) -> ExtractedPaper:
    """Main function to process uploaded PDF"""
    processor = PDFProcessor()
    return processor.extract_paper_content(file_path)
