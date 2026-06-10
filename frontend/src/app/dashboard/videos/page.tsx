"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { Video, Plus, Filter } from "lucide-react"
import VideoCard from "@/components/dashboard/VideoCard"
import { LoadingSkeleton } from "@/components/shared/LoadingSpinner"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { videosAPI, channelsAPI } from "@/lib/api"
import type { VideoJob, Channel } from "@/types"
import { useUIStore } from "@/store/uiStore"

const STATUS_OPTIONS = [
  { value: "all", label: "All Statuses" },
  { value: "queued", label: "Queued" },
  { value: "generating", label: "Generating" },
  { value: "pending_approval", label: "Pending Approval" },
  { value: "approved", label: "Approved" },
  { value: "uploading", label: "Uploading" },
  { value: "posted", label: "Posted" },
  { value: "failed", label: "Failed" },
]

export default function VideosPage() {
  const { openGenerateModal } = useUIStore()
  const [statusFilter, setStatusFilter] = useState("all")
  const [channelFilter, setChannelFilter] = useState("all")
  const [page, setPage] = useState(1)
  const pageSize = 12

  const { data: channelsData } = useQuery<{ channels: Channel[] }>({
    queryKey: ["channels"],
    queryFn: () => channelsAPI.list().then((r) => r.data),
  })

  const { data, isLoading } = useQuery<{
    videos: VideoJob[]
    total: number
    page: number
  }>({
    queryKey: ["videos", statusFilter, channelFilter, page],
    queryFn: () =>
      videosAPI
        .list({
          status: statusFilter === "all" ? undefined : statusFilter,
          channel_id: channelFilter === "all" ? undefined : channelFilter,
          page,
          limit: pageSize,
        })
        .then((r) => r.data),
  })

  const channels = channelsData?.channels ?? []
  const videos = data?.videos ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / pageSize)

  const channelMap = Object.fromEntries(
    channels.map((c) => [c.id, c.channel_name])
  )

  return (
    <div className="max-w-7xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-foreground font-bold text-2xl">Videos</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {total} video{total !== 1 ? "s" : ""} total
          </p>
        </div>
        <Button
          variant="red"
          onClick={() => openGenerateModal()}
          className="flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Generate New
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Filter className="w-4 h-4" />
          <span className="text-sm">Filter:</span>
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-44 h-9">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STATUS_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={channelFilter} onValueChange={setChannelFilter}>
          <SelectTrigger className="w-44 h-9">
            <SelectValue placeholder="All Channels" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Channels</SelectItem>
            {channels.map((ch) => (
              <SelectItem key={ch.id} value={ch.id}>
                {ch.channel_name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <LoadingSkeleton key={i} className="h-64 rounded-xl" />
          ))}
        </div>
      ) : videos.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-16 text-center">
          <Video className="w-12 h-12 text-foreground/60 mx-auto mb-4" />
          <h3 className="text-muted-foreground font-semibold text-lg mb-2">
            No videos found
          </h3>
          <p className="text-muted-foreground text-sm mb-6">
            {statusFilter !== "all" || channelFilter !== "all"
              ? "Try adjusting your filters."
              : "Generate your first Short to get started."}
          </p>
          <Button variant="red" onClick={() => openGenerateModal()}>
            Generate New Short
          </Button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {videos.map((video) => (
              <VideoCard
                key={video.id}
                video={video}
                channelName={channelMap[video.channel_id]}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page === 1}
                onClick={() => setPage((p) => p - 1)}
                className="border-border text-muted-foreground"
              >
                Previous
              </Button>
              <span className="text-muted-foreground text-sm px-4">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page === totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="border-border text-muted-foreground"
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
