"use client"

import { useParams, useRouter } from "next/navigation"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import {
  ArrowLeft,
  Check,
  X,
  ExternalLink,
  DollarSign,
  Clock,
  Youtube,
  FileText,
  Tag,
  Loader2,
} from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { LoadingSpinner } from "@/components/shared/LoadingSpinner"
import VideoPlayer from "@/components/dashboard/VideoPlayer"
import { videosAPI } from "@/lib/api"
import { formatCost, timeAgo, formatDate } from "@/lib/utils"
import type { VideoJob } from "@/types"
import { useState } from "react"

export default function VideoDetailPage() {
  const params = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const videoId = params.id as string
  const [isApproving, setIsApproving] = useState(false)
  const [isRejecting, setIsRejecting] = useState(false)

  const { data: video, isLoading } = useQuery<VideoJob>({
    queryKey: ["video", videoId],
    queryFn: () => videosAPI.get(videoId).then((r) => r.data),
    refetchInterval: (query) => {
      const status = (query.state.data as VideoJob | undefined)?.status
      return status === "generating" || status === "uploading" ? 5000 : false
    },
  })

  const handleApprove = async () => {
    setIsApproving(true)
    try {
      await videosAPI.approve(videoId)
      queryClient.invalidateQueries({ queryKey: ["video", videoId] })
    } finally {
      setIsApproving(false)
    }
  }

  const handleReject = async () => {
    setIsRejecting(true)
    try {
      await videosAPI.reject(videoId)
      queryClient.invalidateQueries({ queryKey: ["video", videoId] })
    } finally {
      setIsRejecting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  if (!video) {
    return (
      <div className="text-center text-muted-foreground mt-16">Video not found.</div>
    )
  }

  return (
    <div className="max-w-5xl">
      {/* Back */}
      <Link
        href="/dashboard/videos"
        className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground text-sm mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Videos
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Video + Actions */}
        <div className="space-y-4">
          {/* Video Preview */}
          <div className="bg-card border border-border rounded-xl overflow-hidden">
            {video.video_path ? (
              <VideoPlayer
                src={video.video_path}
                className="w-full aspect-[9/16]"
              />
            ) : (
              <div className="aspect-[9/16] bg-muted flex flex-col items-center justify-center text-center p-6">
                <StatusBadge status={video.status} className="mb-3" />
                <p className="text-muted-foreground text-sm">
                  {video.status === "generating"
                    ? "Video is being generated..."
                    : video.status === "queued"
                    ? "Waiting in queue..."
                    : video.status === "failed"
                    ? "Generation failed"
                    : "Video not available"}
                </p>
                {video.status === "generating" && (
                  <Loader2 className="w-6 h-6 text-[#E5192A] animate-spin mt-3" />
                )}
              </div>
            )}
          </div>

          {/* Actions */}
          {video.status === "pending_approval" && (
            <div className="space-y-2">
              <p className="text-muted-foreground text-xs text-center">
                Review and approve or reject this Short
              </p>
              <Button
                variant="red"
                className="w-full flex items-center gap-2"
                onClick={handleApprove}
                disabled={isApproving}
              >
                {isApproving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Check className="w-4 h-4" />
                )}
                Approve & Post
              </Button>
              <Button
                variant="outline"
                className="w-full border-red-800/40 text-red-400 hover:bg-red-900/10 flex items-center gap-2"
                onClick={handleReject}
                disabled={isRejecting}
              >
                {isRejecting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <X className="w-4 h-4" />
                )}
                Reject
              </Button>
            </div>
          )}

          {video.youtube_url && (
            <Button
              variant="outline"
              className="w-full border-border text-foreground hover:border-[#E5192A] flex items-center gap-2"
              asChild
            >
              <a href={video.youtube_url} target="_blank" rel="noopener noreferrer">
                <Youtube className="w-4 h-4 text-red-500" />
                View on YouTube
                <ExternalLink className="w-3 h-3 ml-auto" />
              </a>
            </Button>
          )}
        </div>

        {/* Right: Details */}
        <div className="lg:col-span-2 space-y-4">
          {/* Status + Meta */}
          <div className="bg-card border border-border rounded-xl p-5">
            <div className="flex items-center gap-3 mb-4">
              <StatusBadge status={video.status} />
              <span className="text-muted-foreground text-xs capitalize">
                {video.format_slug?.replace("_", " ")}
              </span>
            </div>

            <h1 className="text-foreground font-bold text-xl mb-1">
              {video.seo_title ?? video.topic ?? "Untitled Short"}
            </h1>

            <div className="flex flex-wrap gap-4 text-sm text-muted-foreground mt-3">
              {video.cost_usd !== null && (
                <span className="flex items-center gap-1.5">
                  <DollarSign className="w-3.5 h-3.5 text-green-400" />
                  {formatCost(video.cost_usd)} cost
                </span>
              )}
              <span className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5" />
                Created {timeAgo(video.created_at)}
              </span>
              {video.posted_at && (
                <span className="flex items-center gap-1.5">
                  <Check className="w-3.5 h-3.5 text-green-400" />
                  Posted {formatDate(video.posted_at)}
                </span>
              )}
            </div>
          </div>

          {/* SEO Metadata */}
          {(video.seo_title || video.seo_description) && (
            <div className="bg-card border border-border rounded-xl p-5">
              <h3 className="text-foreground font-semibold mb-4 flex items-center gap-2">
                <Tag className="w-4 h-4 text-[#E5192A]" />
                SEO Metadata
              </h3>
              {video.seo_title && (
                <div className="mb-3">
                  <p className="text-muted-foreground text-xs mb-1">Title</p>
                  <p className="text-muted-foreground/70 text-sm">{video.seo_title}</p>
                </div>
              )}
              {video.seo_description && (
                <div className="mb-3">
                  <p className="text-muted-foreground text-xs mb-1">Description</p>
                  <p className="text-muted-foreground/70 text-sm leading-relaxed">
                    {video.seo_description}
                  </p>
                </div>
              )}
              {video.seo_tags && video.seo_tags.length > 0 && (
                <div>
                  <p className="text-muted-foreground text-xs mb-2">Tags</p>
                  <div className="flex flex-wrap gap-2">
                    {video.seo_tags.map((tag) => (
                      <span
                        key={tag}
                        className="text-xs bg-muted text-muted-foreground px-2 py-1 rounded-md"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Script */}
          {video.script && (
            <div className="bg-card border border-border rounded-xl p-5">
              <h3 className="text-foreground font-semibold mb-4 flex items-center gap-2">
                <FileText className="w-4 h-4 text-[#E5192A]" />
                Script
              </h3>
              <div className="bg-background rounded-lg p-4 border border-border">
                <p className="text-muted-foreground/70 text-sm leading-relaxed whitespace-pre-wrap font-mono">
                  {video.script}
                </p>
              </div>
            </div>
          )}

          {/* Error message */}
          {video.error_message && (
            <div className="bg-red-900/20 border border-red-800/40 rounded-xl p-5">
              <h3 className="text-red-400 font-semibold mb-2">
                Error Details
              </h3>
              <p className="text-red-300/80 text-sm font-mono">
                {video.error_message}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
