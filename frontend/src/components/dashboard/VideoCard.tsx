"use client"

import Link from "next/link"
import { Play, Check, X, Eye, Clock, DollarSign } from "lucide-react"
import { Button } from "@/components/ui/button"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { formatCost, timeAgo } from "@/lib/utils"
import type { VideoJob } from "@/types"
import { videosAPI } from "@/lib/api"
import { useQueryClient } from "@tanstack/react-query"

interface VideoCardProps {
  video: VideoJob
  channelName?: string
}

export default function VideoCard({ video, channelName }: VideoCardProps) {
  const queryClient = useQueryClient()

  const handleApprove = async (e: React.MouseEvent) => {
    e.preventDefault()
    try {
      await videosAPI.approve(video.id)
      queryClient.invalidateQueries({ queryKey: ["videos"] })
    } catch {
      // Handle error
    }
  }

  const handleReject = async (e: React.MouseEvent) => {
    e.preventDefault()
    try {
      await videosAPI.reject(video.id)
      queryClient.invalidateQueries({ queryKey: ["videos"] })
    } catch {
      // Handle error
    }
  }

  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden hover:border-border transition-all duration-200 group">
      {/* Thumbnail */}
      <div className="relative aspect-[9/16] max-h-48 bg-muted overflow-hidden flex items-center justify-center">
        {video.video_path ? (
          <video
            src={video.video_path}
            className="w-full h-full object-cover"
            muted
            preload="metadata"
          />
        ) : (
          <div className="flex flex-col items-center gap-2 text-foreground/60">
            <Play className="w-8 h-8" />
            <span className="text-xs text-foreground/70 capitalize">
              {video.status}
            </span>
          </div>
        )}

        {/* Status overlay */}
        <div className="absolute top-2 left-2">
          <StatusBadge status={video.status} />
        </div>

        {/* Format badge */}
        <div className="absolute top-2 right-2">
          <span className="text-xs bg-black/70 text-muted-foreground/70 px-2 py-0.5 rounded-full">
            {video.format_slug?.replace("_", " ") ?? "Unknown"}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Title */}
        <h3 className="text-foreground font-semibold text-sm mb-1 truncate">
          {video.seo_title ?? video.topic ?? "Untitled Short"}
        </h3>

        {/* Channel */}
        {channelName && (
          <p className="text-muted-foreground text-xs mb-2">{channelName}</p>
        )}

        {/* Meta */}
        <div className="flex items-center gap-3 text-xs text-muted-foreground mb-3">
          {video.cost_usd !== null && (
            <span className="flex items-center gap-1">
              <DollarSign className="w-3 h-3" />
              {formatCost(video.cost_usd)}
            </span>
          )}
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {timeAgo(video.created_at)}
          </span>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" className="flex-1 text-xs h-8" asChild>
            <Link href={`/dashboard/videos/${video.id}`} className="flex items-center gap-1">
              <Eye className="w-3 h-3" />
              View
            </Link>
          </Button>

          {video.status === "pending_approval" && (
            <>
              <Button
                variant="ghost"
                size="sm"
                className="text-green-600 hover:bg-green-100 dark:text-green-400 dark:hover:bg-green-900/20 h-8 px-3"
                onClick={handleApprove}
              >
                <Check className="w-3 h-3" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="text-red-600 hover:bg-red-100 dark:text-red-400 dark:hover:bg-red-900/20 h-8 px-3"
                onClick={handleReject}
              >
                <X className="w-3 h-3" />
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
