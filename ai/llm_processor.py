from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
import json

load_dotenv()

class LLMProcessor:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.llm = ChatGroq(
            groq_api_key=self.groq_api_key,
            model_name="llama3-70b-8192",
            temperature=0.1
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
    
    def generate_summary(self, paper_content: str, title: str = "") -> str:
        system_prompt = """You are an expert research assistant. Create a comprehensive summary of the research paper that includes:
        1. Main research question or objective
        2. Key methodology used
        3. Major findings and results
        4. Significance and implications
        5. Limitations (if mentioned)
        
        Make the summary clear, concise, and accessible to someone familiar with the research domain."""
        
        user_prompt = f"""Please summarize this research paper:
        
        Title: {title}
        
        Content: {paper_content[:4000]}...
        
        Provide a structured summary covering the key aspects mentioned in the instructions."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def generate_study_notes(self, paper_content: str, title: str = "") -> Dict[str, Any]:
        """Generate structured study notes"""
        system_prompt = """You are an expert study assistant. Create structured study notes that help students learn and remember the key concepts from this research paper. 
        
        Format your response as a JSON object with the following structure:
        {
            "key_concepts": ["concept1", "concept2", ...],
            "main_points": ["point1", "point2", ...],
            "important_definitions": {"term1": "definition1", "term2": "definition2"},
            "takeaways": ["takeaway1", "takeaway2", ...],
            "study_questions": ["question1", "question2", ...]
        }"""
        
        user_prompt = f"""Create study notes for this research paper:
        
        Title: {title}
        Content: {paper_content[:3000]}...
        
        Focus on the most important concepts that a student should understand and remember."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            # Try to parse JSON response
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                # If JSON parsing fails, return structured text
                return {
                    "key_concepts": [],
                    "main_points": [response.content],
                    "important_definitions": {},
                    "takeaways": [],
                    "study_questions": []
                }
        except Exception as e:
            return {"error": f"Error generating study notes: {str(e)}"}
    
    def generate_flashcards(self, paper_content: str, title: str = "", num_cards: int = 10) -> List[Dict[str, str]]:
        """Generate flashcards for active recall"""
        system_prompt = f"""You are an expert educator. Create {num_cards} flashcards for active recall and spaced repetition based on this research paper.
        
        Format your response as a JSON array of objects with this structure:
        [
            {{"question": "Q1", "answer": "A1", "difficulty": "easy|medium|hard", "category": "concept|definition|application"}},
            {{"question": "Q2", "answer": "A2", "difficulty": "easy|medium|hard", "category": "concept|definition|application"}},
            ...
        ]
        
        Make questions clear and answers concise but complete. Include a mix of difficulties and categories."""
        
        user_prompt = f"""Create flashcards for this research paper:
        
        Title: {title}
        Content: {paper_content[:3000]}...
        
        Focus on key concepts, definitions, methods, and findings that students should memorize."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            # Try to parse JSON response
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                # If JSON parsing fails, create basic flashcards
                return [
                    {
                        "question": "What is the main contribution of this paper?",
                        "answer": response.content[:200],
                        "difficulty": "medium",
                        "category": "concept"
                    }
                ]
        except Exception as e:
            return [{"error": f"Error generating flashcards: {str(e)}"}]
    
    def generate_mind_map(self, paper_content: str, title: str = "") -> Dict[str, Any]:
        """Generate a mind map structure"""
        system_prompt = """You are an expert knowledge visualizer. Create a mind map structure for this research paper that shows the relationships between key concepts.
        
        Format your response as a JSON object representing a hierarchical mind map:
        {
            "title": "Paper Title",
            "central_concept": "Main Concept",
            "branches": [
                {
                    "name": "Branch 1",
                    "children": [
                        {"name": "Sub-concept 1", "children": []},
                        {"name": "Sub-concept 2", "children": []}
                    ]
                },
                {
                    "name": "Branch 2",
                    "children": [...]
                }
            ]
        }
        
        Create a logical hierarchy that helps visualize the paper's structure and key relationships."""
        
        user_prompt = f"""Create a mind map for this research paper:
        
        Title: {title}
        Content: {paper_content[:3000]}...
        
        Show the main concepts and their relationships in a hierarchical structure."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            # Try to parse JSON response
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                # If JSON parsing fails, create basic structure
                return {
                    "title": title,
                    "central_concept": "Research Paper",
                    "branches": [
                        {
                            "name": "Main Content",
                            "children": [
                                {"name": "Key Findings", "children": []},
                                {"name": "Methodology", "children": []},
                                {"name": "Conclusions", "children": []}
                            ]
                        }
                    ]
                }
        except Exception as e:
            return {"error": f"Error generating mind map: {str(e)}"}
    
    def answer_question(self, question: str, context: str, chat_history: List[Dict] = None) -> str:
        """Answer a question based on the provided context"""
        system_prompt = """You are an expert research assistant. Answer the user's question based on the provided context from research papers. 
        
        Guidelines:
        1. Base your answer primarily on the provided context
        2. Be specific and cite relevant information
        3. If the context doesn't contain enough information, say so
        4. Provide clear, well-structured answers
        5. Use technical terms appropriately but explain them if needed"""
        
        # Include chat history if provided
        history_text = ""
        if chat_history:
            history_text = "\n\nPrevious conversation:\n"
            for msg in chat_history[-3:]:  # Include last 3 messages for context
                history_text += f"{msg['role']}: {msg['content']}\n"
        
        user_prompt = f"""Question: {question}
        
        Context from research papers:
        {context}
        {history_text}
        
        Please provide a comprehensive answer based on the context provided."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"Error answering question: {str(e)}"
    
    def generate_study_plan(self, user_goal: str, papers: List[Dict], deadline: str = None) -> Dict[str, Any]:
        """Generate a personalized study plan"""
        system_prompt = """You are an expert study planner. Create a detailed study plan based on the user's goal and available papers.
        
        Format your response as a JSON object:
        {
            "plan_title": "Study Plan Title",
            "total_duration": "X weeks",
            "weekly_schedule": [
                {
                    "week": 1,
                    "focus": "Week focus",
                    "tasks": ["task1", "task2", ...],
                    "papers_to_read": ["paper1", "paper2"],
                    "estimated_hours": 10
                }
            ],
            "milestones": [
                {"week": 2, "milestone": "Complete foundational reading"},
                {"week": 4, "milestone": "Understand key concepts"}
            ],
            "study_tips": ["tip1", "tip2", ...]
        }"""
        
        papers_info = "\n".join([f"- {paper.get('title', 'Unknown')}: {paper.get('abstract', 'No abstract')[:200]}..." for paper in papers])
        
        user_prompt = f"""Create a study plan for this goal: {user_goal}
        
        Available papers:
        {papers_info}
        
        Deadline: {deadline if deadline else 'No specific deadline'}
        
        Create a realistic, progressive plan that builds knowledge systematically."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            # Try to parse JSON response
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                # If JSON parsing fails, create basic plan
                return {
                    "plan_title": f"Study Plan: {user_goal}",
                    "total_duration": "4 weeks",
                    "weekly_schedule": [
                        {
                            "week": 1,
                            "focus": "Getting started",
                            "tasks": ["Read available papers", "Take notes"],
                            "papers_to_read": [paper.get('title', 'Unknown') for paper in papers[:2]],
                            "estimated_hours": 8
                        }
                    ],
                    "milestones": [{"week": 1, "milestone": "Complete initial reading"}],
                    "study_tips": ["Take regular breaks", "Make notes while reading"]
                }
        except Exception as e:
            return {"error": f"Error generating study plan: {str(e)}"}
    
    def analyze_insights(self, papers: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze papers to generate insights"""
        system_prompt = """You are an expert research analyst. Analyze the provided papers to identify:
        1. Novel findings or breakthroughs
        2. Contradictions between papers
        3. Emerging trends or patterns
        4. Research gaps or opportunities
        
        Format your response as a JSON array of insights:
        [
            {
                "type": "novel_finding|contradiction|trend|gap",
                "title": "Insight Title",
                "description": "Detailed description",
                "relevance_score": 1-10,
                "related_papers": ["paper1", "paper2"]
            }
        ]"""
        
        papers_info = "\n".join([
            f"Paper: {paper.get('title', 'Unknown')}\nAbstract: {paper.get('abstract', 'No abstract')[:300]}...\n"
            for paper in papers
        ])
        
        user_prompt = f"""Analyze these research papers for insights:
        
        {papers_info}
        
        Look for patterns, contradictions, novel findings, and research gaps."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            # Try to parse JSON response
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                # If JSON parsing fails, create basic insight
                return [
                    {
                        "type": "trend",
                        "title": "Research Analysis",
                        "description": response.content[:500],
                        "relevance_score": 5,
                        "related_papers": [paper.get('title', 'Unknown') for paper in papers]
                    }
                ]
        except Exception as e:
            return [{"error": f"Error analyzing insights: {str(e)}"}]
