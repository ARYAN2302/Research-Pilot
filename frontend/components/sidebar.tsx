"use client"

import { useState, useEffect } from "react"
import {
  FileText,
  Calendar,
  Lightbulb,
  Settings,
  MessageSquare,
  Plus,
  Search,
  Upload,
  LogOut,
  User,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { PaperDetailsModal } from "@/components/paper-details-modal"
import { StudyPlannerModal } from "@/components/study-planner-modal"
import { useSidebar } from "@/components/ui/sidebar"
import { useAuth } from "@/lib/auth-context"
import { apiClient, Paper, StudyPlan, Insight } from "@/lib/api"

interface SidebarProps {
  activeSection: string
  setActiveSection: (section: string) => void
  selectedPaper: string | null
  setSelectedPaper: (paperId: string | null) => void
}

export function Sidebar({ activeSection, setActiveSection, selectedPaper, setSelectedPaper }: SidebarProps) {
  const [selectedPaperDetails, setSelectedPaperDetails] = useState<Paper | null>(null)
  const [showStudyPlanner, setShowStudyPlanner] = useState(false)
  const [papers, setPapers] = useState<Paper[]>([])
  const [studyPlans, setStudyPlans] = useState<StudyPlan[]>([])
  const [insights, setInsights] = useState<Insight[]>([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")
  const { user, logout } = useAuth()

  const sidebarItems = [
    { id: "chat", label: "Chat", icon: MessageSquare },
    { id: "papers", label: "My Papers", icon: FileText },
    { id: "planner", label: "Study Planner", icon: Calendar },
    { id: "insights", label: "Insights", icon: Lightbulb },
    { id: "settings", label: "Settings", icon: Settings },
  ]

  // Load data based on active section
  useEffect(() => {
    loadData()
  }, [activeSection])

  const loadData = async () => {
    setLoading(true)
    try {
      switch (activeSection) {
        case "papers":
          const papersData = await apiClient.getPapers()
          setPapers(papersData)
          break
        case "planner":
          const plansData = await apiClient.getStudyPlans()
          setStudyPlans(plansData)
          break
        case "insights":
          const insightsData = await apiClient.getInsights()
          setInsights(insightsData)
          break
      }
    } catch (error) {
      console.error("Failed to load data:", error)
    } finally {
      setLoading(false)
    }
  }

  const handlePaperClick = (paper: Paper) => {
    setSelectedPaper(paper.id.toString())
    setSelectedPaperDetails(paper)
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (file.type !== "application/pdf") {
      alert("Please upload a PDF file")
      return
    }

    try {
      setLoading(true)
      await apiClient.uploadPaper(file)
      // Refresh papers list
      const papersData = await apiClient.getPapers()
      setPapers(papersData)
    } catch (error) {
      console.error("Failed to upload paper:", error)
      alert("Failed to upload paper. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const generateStudyPlan = async (goal: string, deadline?: string) => {
    try {
      setLoading(true)
      await apiClient.generateStudyPlan(goal, deadline)
      // Refresh study plans
      const plansData = await apiClient.getStudyPlans()
      setStudyPlans(plansData)
    } catch (error) {
      console.error("Failed to generate study plan:", error)
      alert("Failed to generate study plan. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const generateInsights = async () => {
    try {
      setLoading(true)
      await apiClient.generateInsights()
      // Refresh insights
      const insightsData = await apiClient.getInsights()
      setInsights(insightsData)
    } catch (error) {
      console.error("Failed to generate insights:", error)
      alert("Failed to generate insights. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const filteredPapers = papers.filter((paper: Paper) =>
    paper.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (paper.authors && paper.authors.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-32">
          <div className="text-gray-400">Loading...</div>
        </div>
      )
    }

    switch (activeSection) {
      case "papers":
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">My Papers</h3>
              <div className="flex gap-2">
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="paper-upload"
                />
                <Button
                  size="sm"
                  onClick={() => document.getElementById("paper-upload")?.click()}
                  disabled={loading}
                >
                  <Upload className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search papers..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-gray-800/50 border-gray-700"
              />
            </div>
            <ScrollArea className="h-[calc(100vh-200px)]">
              <div className="space-y-3">
                {filteredPapers.map((paper) => (
                  <div
                    key={paper.id}
                    className={`p-3 rounded-lg cursor-pointer border transition-colors ${
                      selectedPaper === paper.id.toString()
                        ? "bg-blue-600/20 border-blue-500"
                        : "bg-gray-800/50 border-gray-700 hover:bg-gray-800"
                    }`}
                    onClick={() => handlePaperClick(paper)}
                  >
                    <div className="flex items-start gap-3">
                      <FileText className="h-5 w-5 text-gray-400 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm truncate">{paper.title}</h4>
                        {paper.authors && (
                          <p className="text-xs text-gray-400 truncate">{paper.authors}</p>
                        )}
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant={paper.status === "ready" ? "default" : "secondary"}>
                            {paper.status}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            {new Date(paper.upload_date).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                {filteredPapers.length === 0 && (
                  <div className="text-center py-8 text-gray-400">
                    No papers found. Upload your first paper to get started.
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>
        )

      case "planner":
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Study Plans</h3>
              <Button size="sm" onClick={() => setShowStudyPlanner(true)}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <ScrollArea className="h-[calc(100vh-200px)]">
              <div className="space-y-3">
                {studyPlans.map((plan) => (
                  <div key={plan.id} className="p-3 bg-gray-800/50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-sm">{plan.title}</h4>
                      <Badge variant={plan.status === "completed" ? "default" : "secondary"}>
                        {plan.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-400 mb-2">{plan.description}</p>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>{new Date(plan.created_at).toLocaleDateString()}</span>
                      {plan.deadline && (
                        <span>Due: {new Date(plan.deadline).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                ))}
                {studyPlans.length === 0 && (
                  <div className="text-center py-8 text-gray-400">
                    No study plans yet. Create your first plan to get started.
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>
        )

      case "insights":
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">AI Insights</h3>
              <Button size="sm" onClick={generateInsights} disabled={loading}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <ScrollArea className="h-[calc(100vh-200px)]">
              <div className="space-y-3">
                {insights.map((insight) => (
                  <div
                    key={insight.id}
                    className="p-3 bg-gray-800/50 rounded-lg cursor-pointer hover:bg-gray-800 transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <div
                        className={`p-1 rounded ${
                          insight.type === "trend"
                            ? "bg-green-600/20 text-green-400"
                            : insight.type === "contradiction"
                              ? "bg-red-600/20 text-red-400"
                              : "bg-blue-600/20 text-blue-400"
                        }`}
                      >
                        <Lightbulb className="h-4 w-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm">{insight.title}</h4>
                        <p className="text-xs text-gray-400 mt-1">{insight.content}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant="outline">{insight.type}</Badge>
                          <span className="text-xs text-gray-500">
                            {new Date(insight.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                {insights.length === 0 && (
                  <div className="text-center py-8 text-gray-400">
                    No insights yet. Generate insights from your papers to see patterns and trends.
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>
        )

      case "settings":
        return (
          <div className="space-y-4">
            <h3 className="font-semibold">Settings</h3>
            <div className="space-y-3">
              <div className="p-3 bg-gray-800/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <User className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="font-medium">{user?.full_name || "User"}</p>
                    <p className="text-sm text-gray-400">{user?.email}</p>
                  </div>
                </div>
              </div>
              <Button
                variant="outline"
                onClick={logout}
                className="w-full justify-start"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Sign Out
              </Button>
            </div>
          </div>
        )

      default:
        return (
          <div className="space-y-4">
            <h3 className="font-semibold">Welcome to Research Pilot</h3>
            <p className="text-sm text-gray-400">
              Select a section from the sidebar to get started.
            </p>
          </div>
        )
    }
  }

  return (
    <>
      <div className="w-80 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <h1 className="text-lg font-bold text-blue-400">Research Pilot</h1>
          <p className="text-xs text-gray-500">Intelligent Paper Analysis</p>
        </div>

        <nav className="p-4">
          <div className="space-y-1">
            {sidebarItems.map((item) => (
              <Button
                key={item.id}
                variant={activeSection === item.id ? "secondary" : "ghost"}
                className={`w-full justify-start ${
                  activeSection === item.id
                    ? "bg-blue-600/20 text-blue-400 hover:bg-blue-600/30"
                    : "text-gray-300 hover:text-white hover:bg-gray-800"
                }`}
                onClick={() => setActiveSection(item.id)}
              >
                <item.icon className="h-4 w-4 mr-3" />
                {item.label}
              </Button>
            ))}
          </div>
        </nav>

        <Separator className="bg-gray-800" />

        <div className="flex-1 p-4">{renderContent()}</div>
      </div>

      <PaperDetailsModal
        paper={selectedPaperDetails}
        isOpen={!!selectedPaperDetails}
        onClose={() => setSelectedPaperDetails(null)}
      />

      <StudyPlannerModal 
        isOpen={showStudyPlanner} 
        onClose={() => setShowStudyPlanner(false)}
        onCreatePlan={generateStudyPlan}
      />
    </>
  )
}
