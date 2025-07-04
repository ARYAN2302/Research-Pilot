"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Bot, User, Sparkles, FileText, Calendar, Lightbulb } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/lib/auth-context"
import { apiClient, Paper, ChatSession, ChatMessage } from "@/lib/api"
import ReactMarkdown from "react-markdown"

interface ChatInterfaceProps {
  selectedPaper: string | null
  activeSection: string
}

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  suggestions?: string[]
  sources?: string[]
}

export function ChatInterface({ selectedPaper, activeSection }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null)
  const [selectedPaperData, setSelectedPaperData] = useState<Paper | null>(null)
  const { user } = useAuth()
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  // Initialize chat session and load messages
  useEffect(() => {
    initializeChat()
  }, [selectedPaper])

  // Scroll to bottom when messages change
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])

  const initializeChat = async () => {
    try {
      // Load selected paper data if available
      if (selectedPaper) {
        const paperData = await apiClient.getPaper(parseInt(selectedPaper))
        setSelectedPaperData(paperData)
      } else {
        setSelectedPaperData(null)
      }

      // Create or get chat session
      const sessionTitle = selectedPaper 
        ? `Chat with ${selectedPaperData?.title || 'Paper'}` 
        : "General Chat"
      
      const session = await apiClient.createChatSession(
        sessionTitle, 
        selectedPaper ? parseInt(selectedPaper) : undefined
      )
      setCurrentSession(session)

      // Load existing messages for this session
      const sessionMessages = await apiClient.getChatMessages(session.id)
      const formattedMessages: Message[] = sessionMessages.map(msg => ({
        id: msg.id.toString(),
        role: msg.role as "user" | "assistant",
        content: msg.content,
        timestamp: new Date(msg.timestamp),
        sources: msg.context?.sources || []
      }))

      setMessages(formattedMessages)

      // Add welcome message if no existing messages
      if (formattedMessages.length === 0) {
        const welcomeMessage: Message = {
          id: "welcome",
          role: "assistant",
          content: selectedPaper 
            ? `Hello! I'm ready to help you analyze and understand "${selectedPaperData?.title}". What would you like to know about this paper?`
            : "Hello! I'm your research assistant. I can help you analyze papers, plan study sessions, and discover insights. What would you like to explore today?",
          timestamp: new Date(),
          suggestions: selectedPaper 
            ? [
                "Summarize the main findings",
                "Explain the methodology",
                "What are the key contributions?",
                "Generate study notes"
              ]
            : [
                "Upload a research paper",
                "Create a study plan",
                "Show my recent insights"
              ]
        }
        setMessages([welcomeMessage])
      }
    } catch (error) {
      console.error("Failed to initialize chat:", error)
      // Add error message
      const errorMessage: Message = {
        id: "error",
        role: "assistant",
        content: "Sorry, I encountered an error setting up the chat. Please try again.",
        timestamp: new Date()
      }
      setMessages([errorMessage])
    }
  }

  const handleSendMessage = async () => {
    if (!input.trim() || !currentSession) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      // Send question to API
      const response = await apiClient.askQuestion(
        input,
        selectedPaper ? parseInt(selectedPaper) : undefined,
        currentSession.id
      )

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.answer,
        timestamp: new Date(),
        sources: response.sources,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error("Failed to send message:", error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "I apologize, but I encountered an error processing your question. Please try again.",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const getSectionIcon = () => {
    switch (activeSection) {
      case "papers":
        return <FileText className="h-5 w-5" />
      case "planner":
        return <Calendar className="h-5 w-5" />
      case "insights":
        return <Lightbulb className="h-5 w-5" />
      default:
        return <Sparkles className="h-5 w-5" />
    }
  }

  const getSectionTitle = () => {
    if (selectedPaperData) {
      return selectedPaperData.title
    }
    
    switch (activeSection) {
      case "papers":
        return "Paper Analysis"
      case "planner":
        return "Study Planning"
      case "insights":
        return "Research Insights"
      default:
        return "Research Assistant"
    }
  }

  return (
    <div className="flex flex-col h-full bg-gray-950">
      {/* Header */}
      <div className="p-4 border-b border-gray-800 bg-gray-900/50">
        <div className="flex items-center gap-3">
          {getSectionIcon()}
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-gray-100">{getSectionTitle()}</h2>
            {selectedPaperData && (
              <div className="flex items-center gap-2 mt-1">
                <Badge variant={selectedPaperData.status === "ready" ? "default" : "secondary"}>
                  {selectedPaperData.status}
                </Badge>
                {selectedPaperData.authors && (
                  <span className="text-sm text-gray-400">by {selectedPaperData.authors}</span>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
        <div className="space-y-6 max-w-4xl mx-auto">
          {messages.map((message) => (
            <div key={message.id} className="flex gap-4">
              <div className="flex-shrink-0">
                {message.role === "user" ? (
                  <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                    <User className="h-4 w-4 text-white" />
                  </div>
                ) : (
                  <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
                    <Bot className="h-4 w-4 text-white" />
                  </div>
                )}
              </div>
              <div className="flex-1 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-200">
                    {message.role === "user" ? user?.full_name || "You" : "Research Assistant"}
                  </span>
                  <span className="text-xs text-gray-500">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                <div className="prose prose-invert prose-sm max-w-none">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs text-gray-400 mb-1">Sources:</p>
                    <div className="flex flex-wrap gap-1">
                      {message.sources.map((source, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {source}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                {message.suggestions && message.suggestions.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {message.suggestions.map((suggestion, index) => (
                      <Button
                        key={index}
                        variant="outline"
                        size="sm"
                        onClick={() => handleSuggestionClick(suggestion)}
                        className="text-xs"
                      >
                        {suggestion}
                      </Button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex gap-4">
              <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
                <Bot className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-200">Research Assistant</span>
                  <span className="text-xs text-gray-500">thinking...</span>
                </div>
                <div className="space-y-2">
                  <Skeleton className="h-4 w-full bg-gray-800" />
                  <Skeleton className="h-4 w-3/4 bg-gray-800" />
                </div>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-800 bg-gray-900/50">
        <div className="flex gap-3 max-w-4xl mx-auto">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              selectedPaper 
                ? "Ask anything about this paper..." 
                : "Ask me anything about your research..."
            }
            className="flex-1 bg-gray-800 border-gray-700 text-gray-100 placeholder-gray-400"
            disabled={isLoading}
          />
          <Button 
            onClick={handleSendMessage} 
            disabled={!input.trim() || isLoading}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
