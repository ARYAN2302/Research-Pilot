"use client"

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { FileText, Calendar, Users, ExternalLink } from "lucide-react"
import { Paper } from "@/lib/api"

interface PaperDetailsModalProps {
  paper: Paper | null
  isOpen: boolean
  onClose: () => void
  onAnalyze?: () => void
}

export function PaperDetailsModal({ paper, isOpen, onClose, onAnalyze }: PaperDetailsModalProps) {
  if (!paper) return null

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'default'
      case 'processing':
        return 'secondary'
      case 'failed':
        return 'destructive'
      default:
        return 'secondary'
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl bg-gray-900 border-gray-800">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-blue-400">{paper.title}</DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          <div className="flex items-center gap-4 text-sm text-gray-400">
            {paper.authors && (
              <div className="flex items-center gap-1">
                <Users className="h-4 w-4" />
                <span>{paper.authors}</span>
              </div>
            )}
            <div className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              <span>{formatDate(paper.upload_date)}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant={getStatusColor(paper.status) as any}>{paper.status}</Badge>
            <Badge variant="outline">{(paper.file_size / 1024 / 1024).toFixed(1)} MB</Badge>
          </div>

          <Separator className="bg-gray-800" />

          {paper.abstract && (
            <>
              <div>
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Abstract
                </h3>
                <p className="text-sm text-gray-300 leading-relaxed">{paper.abstract}</p>
              </div>
              <Separator className="bg-gray-800" />
            </>
          )}

          <div>
            <h3 className="font-semibold mb-3">File Information</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Size:</span>
                <p className="font-medium">{(paper.file_size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
              <div>
                <span className="text-gray-400">Uploaded:</span>
                <p className="font-medium">{formatDate(paper.upload_date)}</p>
              </div>
              <div>
                <span className="text-gray-400">Status:</span>
                <p className="font-medium capitalize">{paper.status}</p>
              </div>
              <div>
                <span className="text-gray-400">ID:</span>
                <p className="font-medium">{paper.id}</p>
              </div>
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <Button 
              className="flex-1 bg-blue-600 hover:bg-blue-700"
              onClick={() => {
                onAnalyze?.()
                onClose()
              }}
              disabled={paper.status !== 'ready'}
            >
              <FileText className="h-4 w-4 mr-2" />
              Analyze in Chat
            </Button>
            <Button variant="outline" className="flex-1 bg-transparent">
              <ExternalLink className="h-4 w-4 mr-2" />
              Download
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
