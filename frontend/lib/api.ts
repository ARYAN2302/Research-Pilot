const API_BASE_URL = typeof window !== 'undefined' && (window as any).location?.origin 
  ? 'http://localhost:8000' 
  : 'http://localhost:8000'

// Types
export interface User {
  id: number
  email: string
  full_name: string | null
  is_active: boolean
  created_at: string
  learning_goals: string | null
  preferences: any
}

export interface Paper {
  id: number
  title: string
  authors: string | null
  abstract: string | null
  full_text: string | null
  file_path: string
  file_size: number
  upload_date: string
  owner_id: number
  status: string
  paper_metadata: any
}

export interface Note {
  id: number
  paper_id: number
  title: string
  content: string
  summary: string | null
  key_takeaways: string[] | null
  created_at: string
  updated_at: string
}

export interface Flashcard {
  id: number
  paper_id: number
  question: string
  answer: string
  difficulty: string
  category: string | null
  created_at: string
}

export interface MindMap {
  id: number
  paper_id: number
  title: string
  structure: any
  created_at: string
}

export interface StudyPlan {
  id: number
  user_id: number
  title: string
  description: string | null
  goal: string
  deadline: string | null
  status: string
  schedule: any
  progress: any
  created_at: string
  updated_at: string
}

export interface ChatSession {
  id: number
  user_id: number
  paper_id: number | null
  title: string
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: number
  session_id: number
  role: string
  content: string
  context: any
  timestamp: string
}

export interface Insight {
  id: number
  user_id: number
  title: string
  content: string
  type: string
  relevance_score: number
  related_papers: number[] | null
  created_at: string
  is_read: boolean
}

export interface QuestionAnswerResponse {
  answer: string
  context: string[]
  sources: string[]
}

// API utility functions
class ApiClient {
  private token: string | null = null

  constructor() {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('token')
    }
  }

  setToken(token: string) {
    this.token = token
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', token)
    }
  }

  removeToken() {
    this.token = null
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token')
    }
  }

  isAuthenticated(): boolean {
    return this.token !== null
  }

  getToken(): string | null {
    return this.token
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    // Add any existing headers
    if (options.headers) {
      Object.entries(options.headers as Record<string, string>).forEach(([key, value]) => {
        headers[key] = value
      })
    }

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`
    }

    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      // If unauthorized, clear token and redirect to login
      if (response.status === 401) {
        this.removeToken()
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
      }
      
      const error = await response.json().catch(() => ({ detail: 'An error occurred' }))
      throw new Error(error.detail || `HTTP error! status: ${response.status}`)
    }

    return response.json()
  }

  // Authentication
  async register(email: string, password: string, full_name?: string) {
    const response = await this.request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name }),
    })
    return response
  }

  async login(email: string, password: string) {
    const response = await this.request<{ access_token: string; token_type: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    this.setToken(response.access_token)
    return response
  }

  async logout() {
    this.removeToken()
    if (typeof window !== 'undefined') {
      window.location.href = '/'
    }
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/users/me')
  }

  async updateUser(updates: Partial<User>): Promise<User> {
    return this.request<User>('/users/me', {
      method: 'PUT',
      body: JSON.stringify(updates),
    })
  }

  // Papers
  async uploadPaper(file: File): Promise<Paper> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE_URL}/papers/upload`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${this.token}`,
      },
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
      throw new Error(error.detail || `HTTP error! status: ${response.status}`)
    }

    return response.json()
  }

  async getPapers(): Promise<Paper[]> {
    return this.request<Paper[]>('/papers')
  }

  async getPaper(id: number): Promise<Paper> {
    return this.request<Paper>(`/papers/${id}`)
  }

  async deletePaper(id: number): Promise<void> {
    await this.request(`/papers/${id}`, { method: 'DELETE' })
  }

  async getPaperAnalysis(id: number): Promise<{
    paper: Paper
    notes: Note[]
    flashcards: Flashcard[]
    mind_maps: MindMap[]
    analysis_complete: boolean
  }> {
    return this.request(`/papers/${id}/analysis`)
  }

  // Notes
  async createNote(paperId: number, note: { title: string; content: string; summary?: string; key_takeaways?: string[] }): Promise<Note> {
    return this.request<Note>(`/papers/${paperId}/notes`, {
      method: 'POST',
      body: JSON.stringify(note),
    })
  }

  async getNotes(paperId: number): Promise<Note[]> {
    return this.request<Note[]>(`/papers/${paperId}/notes`)
  }

  // Flashcards
  async getFlashcards(paperId: number): Promise<Flashcard[]> {
    return this.request<Flashcard[]>(`/papers/${paperId}/flashcards`)
  }

  // Mind Maps
  async getMindMaps(paperId: number): Promise<MindMap[]> {
    return this.request<MindMap[]>(`/papers/${paperId}/mindmaps`)
  }

  // Study Plans
  async createStudyPlan(plan: { title: string; description?: string; goal: string; deadline?: string }): Promise<StudyPlan> {
    return this.request<StudyPlan>('/study-plans', {
      method: 'POST',
      body: JSON.stringify(plan),
    })
  }

  async generateStudyPlan(goal: string, deadline?: string): Promise<StudyPlan> {
    const params = new URLSearchParams({ goal })
    if (deadline) params.append('deadline', deadline)

    return this.request<StudyPlan>(`/study-plans/generate?${params}`, {
      method: 'POST',
    })
  }

  async getStudyPlans(): Promise<StudyPlan[]> {
    return this.request<StudyPlan[]>('/study-plans')
  }

  async getStudyPlan(id: number): Promise<StudyPlan> {
    return this.request<StudyPlan>(`/study-plans/${id}`)
  }

  // Chat
  async createChatSession(title: string, paperId?: number): Promise<ChatSession> {
    return this.request<ChatSession>('/chat/sessions', {
      method: 'POST',
      body: JSON.stringify({ title, paper_id: paperId }),
    })
  }

  async getChatSessions(): Promise<ChatSession[]> {
    return this.request<ChatSession[]>('/chat/sessions')
  }

  async getChatMessages(sessionId: number): Promise<ChatMessage[]> {
    return this.request<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`)
  }

  async askQuestion(question: string, paperId?: number, sessionId?: number): Promise<QuestionAnswerResponse> {
    return this.request<QuestionAnswerResponse>('/chat/ask', {
      method: 'POST',
      body: JSON.stringify({ question, paper_id: paperId, session_id: sessionId }),
    })
  }

  // Insights
  async getInsights(): Promise<Insight[]> {
    return this.request<Insight[]>('/insights')
  }

  async generateInsights(): Promise<{ message: string }> {
    return this.request<{ message: string }>('/insights/generate', {
      method: 'POST',
    })
  }

  async markInsightRead(id: number): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/insights/${id}/read`, {
      method: 'POST',
    })
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request<{ status: string; timestamp: string }>('/health')
  }
}

export const apiClient = new ApiClient()
