"use client"

import { useRouter } from "next/navigation"
import { useQueryClient } from "@tanstack/react-query"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"
import GenerateForm from "@/components/dashboard/GenerateForm"
import { useUIStore } from "@/store/uiStore"

export default function NewVideoPage() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const { selectedChannelId } = useUIStore()

  return (
    <div className="max-w-2xl">
      {/* Back */}
      <Link
        href="/dashboard/videos"
        className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground text-sm mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Videos
      </Link>

      <div className="mb-6">
        <h1 className="text-foreground font-bold text-2xl">Create New Short</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Configure and queue a new AI-generated YouTube Short. Billed in
          credits.
        </p>
      </div>

      <div className="bg-card border border-border rounded-xl p-6">
        <GenerateForm
          initialChannelId={selectedChannelId}
          onSuccess={(jobId) => {
            queryClient.invalidateQueries({ queryKey: ["videos"] })
            queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] })
            queryClient.invalidateQueries({ queryKey: ["plan-current"] })
            router.push(`/dashboard/videos/${jobId}`)
          }}
        />
      </div>
    </div>
  )
}
