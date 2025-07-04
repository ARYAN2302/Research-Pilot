"use client"

import { useState } from "react"
import { useAuth } from "@/lib/auth-context"
import { LoginForm } from "@/components/login-form"
import { Sidebar } from "@/components/sidebar"
import { ChatInterface } from "@/components/chat-interface"
import { SidebarProvider } from "@/components/ui/sidebar"

export default function Home() {
  const [selectedPaper, setSelectedPaper] = useState<string | null>(null)
  const [activeSection, setActiveSection] = useState("chat")
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-gray-100">Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <LoginForm />
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <SidebarProvider defaultOpen={true}>
        <div className="flex h-screen">
          <Sidebar
            activeSection={activeSection}
            setActiveSection={setActiveSection}
            selectedPaper={selectedPaper}
            setSelectedPaper={setSelectedPaper}
          />
          <main className="flex-1 flex flex-col">
            <ChatInterface selectedPaper={selectedPaper} activeSection={activeSection} />
          </main>
        </div>
      </SidebarProvider>
    </div>
  )
}
