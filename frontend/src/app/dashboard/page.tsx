"use client"

import { useQuery } from "@tanstack/react-query"
import {
  Video,
  Eye,
  Sparkles,
  Tv2,
  Zap,
  Clock,
  AlertCircle,
  Coins,
} from "lucide-react"
import StatsCard from "@/components/dashboard/StatsCard"
import VideoCard from "@/components/dashboard/VideoCard"
import { LoadingSkeleton } from "@/components/shared/LoadingSpinner"
import { Button } from "@/components/ui/button"
import { dashboardAPI, videosAPI } from "@/lib/api"
import { useUIStore } from "@/store/uiStore"
import { formatCredits, formatNumber, timeAgo } from "@/lib/utils"
import type { DashboardStats, ActivityItem, VideoJob } from "@/types"

export default function DashboardPage() {
  const { openGenerateModal } = useUIStore()

  const { data: stats, isLoading: statsLoading } = useQuery<DashboardStats>({
    queryKey: ["dashboard-stats"],
    queryFn: () => dashboardAPI.stats().then((r) => r.data),
  })

  const { data: activityData, isLoading: activityLoading } = useQuery<{
    items: ActivityItem[]
  }>({
    queryKey: ["dashboard-activity"],
    queryFn: () => dashboardAPI.activity().then((r) => r.data),
  })

  const { data: recentVideos } = useQuery<{ items: VideoJob[] }>({
    queryKey: ["videos", { page_size: 6 }],
    queryFn: () => videosAPI.list({ page_size: 6 }).then((r) => r.data),
  })

  const activity = activityData?.items ?? []
  const videos = recentVideos?.items ?? []

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Stats Row */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        {statsLoading ? (
          [...Array(4)].map((_, i) => (
            <LoadingSkeleton key={i} className="h-28 rounded-xl" />
          ))
        ) : (
          <>
            <StatsCard
              icon={Video}
              label="Videos Posted"
              value={formatNumber(stats?.videos_posted ?? 0)}
              iconColor="text-purple-600 dark:text-purple-400"
              iconBg="bg-purple-100 dark:bg-purple-900/20"
            />
            <StatsCard
              icon={Eye}
              label="Total Views"
              value={formatNumber(stats?.total_views ?? 0)}
              iconColor="text-blue-600 dark:text-blue-400"
              iconBg="bg-blue-100 dark:bg-blue-900/20"
            />
            <StatsCard
              icon={Coins}
              label="Credits Balance"
              value={formatCredits(stats?.credits_balance ?? 0)}
              changeLabel={`${formatCredits(
                stats?.credits_used_this_period ?? 0
              )} used this period`}
              iconColor="text-amber-600 dark:text-amber-400"
              iconBg="bg-amber-100 dark:bg-amber-900/20"
            />
            <StatsCard
              icon={Tv2}
              label="Active Channels"
              value={String(stats?.active_channels ?? 0)}
              iconColor="text-[#E5192A]"
              iconBg="bg-[#E5192A]/10"
            />
          </>
        )}
      </div>

      {/* Middle Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Videos */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-foreground font-bold text-lg">Recent Videos</h2>
            <Button
              variant="red"
              size="sm"
              onClick={() => openGenerateModal()}
              className="flex items-center gap-1.5"
            >
              <Zap className="w-3.5 h-3.5 fill-white" />
              Generate
            </Button>
          </div>

          {videos.length === 0 ? (
            <div className="bg-card border border-border rounded-xl p-12 text-center">
              <Video className="w-10 h-10 text-foreground/60 mx-auto mb-3" />
              <h3 className="text-muted-foreground font-medium mb-1">
                No videos yet
              </h3>
              <p className="text-muted-foreground text-sm mb-4">
                Generate your first Short to get started.
              </p>
              <Button
                variant="red"
                size="sm"
                onClick={() => openGenerateModal()}
              >
                Generate First Short
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {videos.map((video) => (
                <VideoCard key={video.id} video={video} />
              ))}
            </div>
          )}
        </div>

        {/* Sidebar Panels */}
        <div className="space-y-4">
          {/* Credits summary */}
          <div className="bg-card border border-border rounded-xl p-5">
            <h3 className="text-foreground font-bold mb-4 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-500" />
              Credits
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground text-sm">Balance</span>
                <span className="text-foreground font-bold">
                  {formatCredits(stats?.credits_balance ?? 0)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground text-sm">
                  Used this period
                </span>
                <span className="text-foreground font-semibold">
                  {formatCredits(stats?.credits_used_this_period ?? 0)}
                </span>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="w-full border-border text-foreground hover:border-[#E5192A]"
                asChild
              >
                <a href="/dashboard/billing">Top up credits</a>
              </Button>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-card border border-border rounded-xl p-5">
            <h3 className="text-foreground font-bold mb-4 flex items-center gap-2">
              <Clock className="w-4 h-4 text-muted-foreground" />
              Recent Activity
            </h3>
            {activityLoading ? (
              <div className="space-y-2">
                {[...Array(4)].map((_, i) => (
                  <LoadingSkeleton key={i} className="h-12 rounded-lg" />
                ))}
              </div>
            ) : activity.length === 0 ? (
              <p className="text-muted-foreground text-sm">No recent activity.</p>
            ) : (
              <div className="space-y-2">
                {activity.slice(0, 8).map((item) => (
                  <div key={item.id} className="flex items-start gap-2 py-2">
                    <div className="mt-0.5">
                      {item.type === "video_failed" ? (
                        <AlertCircle className="w-3.5 h-3.5 text-red-500 dark:text-red-400" />
                      ) : item.type === "video_posted" ? (
                        <div className="w-3.5 h-3.5 rounded-full bg-green-400/20 flex items-center justify-center">
                          <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
                        </div>
                      ) : (
                        <div className="w-3.5 h-3.5 rounded-full bg-secondary flex items-center justify-center">
                          <div className="w-1.5 h-1.5 rounded-full bg-muted-foreground" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-muted-foreground/70 text-xs leading-tight">
                        {item.message}
                      </p>
                      <p className="text-muted-foreground text-xs mt-0.5">
                        {timeAgo(item.created_at)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
