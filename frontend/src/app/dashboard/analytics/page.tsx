"use client"

import { useState } from "react"
import { useTheme } from "next-themes"
import { useQuery } from "@tanstack/react-query"
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts"
import {
  Eye,
  Video,
  DollarSign,
  TrendingUp,
  Trophy,
} from "lucide-react"
import StatsCard from "@/components/dashboard/StatsCard"
import { LoadingSkeleton } from "@/components/shared/LoadingSpinner"
import { dashboardAPI, videosAPI } from "@/lib/api"
import { formatCost, formatNumber, timeAgo } from "@/lib/utils"
import type { DashboardStats, VideoJob } from "@/types"
import { StatusBadge } from "@/components/shared/StatusBadge"

const DATE_RANGES = [
  { label: "7 days", value: 7 },
  { label: "30 days", value: 30 },
  { label: "90 days", value: 90 },
]

// Mock analytics data points
const generateMockData = (days: number) => {
  return Array.from({ length: days }, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - (days - 1 - i))
    return {
      date: date.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      views: Math.floor(Math.random() * 50000) + 5000,
      videos: Math.floor(Math.random() * 5) + 1,
      cost: parseFloat((Math.random() * 0.5 + 0.3).toFixed(2)),
    }
  })
}

const FORMAT_DATA = [
  { format: "Horror Story", count: 48, views: 385000 },
  { format: "Brainrot", count: 0, views: 0 },
  { format: "Listicle", count: 0, views: 0 },
]

export default function AnalyticsPage() {
  const [dateRange, setDateRange] = useState(30)
  const { resolvedTheme } = useTheme()
  const isDark = resolvedTheme === "dark"
  const chart = {
    grid: isDark ? "#1A1A1A" : "#E5E5E5",
    axis: isDark ? "#555555" : "#AAAAAA",
    tick: isDark ? "#888888" : "#666666",
    tooltipBg: isDark ? "#111111" : "#FFFFFF",
    tooltipBorder: isDark ? "#222222" : "#E5E5E5",
    tooltipText: isDark ? "#FAFAFA" : "#111111",
  }

  const { data: stats, isLoading: statsLoading } = useQuery<DashboardStats>({
    queryKey: ["dashboard-stats"],
    queryFn: () => dashboardAPI.stats().then((r) => r.data),
  })

  const { data: topVideosData, isLoading: videosLoading } = useQuery<{
    videos: VideoJob[]
  }>({
    queryKey: ["videos", { status: "posted", limit: 5 }],
    queryFn: () =>
      videosAPI.list({ status: "posted", limit: 5 }).then((r) => r.data),
  })

  const chartData = generateMockData(dateRange)
  const topVideos = topVideosData?.videos ?? []

  return (
    <div className="max-w-7xl space-y-6">
      {/* Header + Date Range */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-foreground font-bold text-2xl">Analytics</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Performance overview across all channels
          </p>
        </div>
        <div className="flex items-center gap-2 bg-card border border-border rounded-lg p-1">
          {DATE_RANGES.map((r) => (
            <button
              key={r.value}
              onClick={() => setDateRange(r.value)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                dateRange === r.value
                  ? "bg-[#E5192A] text-white"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        {statsLoading ? (
          [...Array(4)].map((_, i) => (
            <LoadingSkeleton key={i} className="h-28 rounded-xl" />
          ))
        ) : (
          <>
            <StatsCard
              icon={Eye}
              label="Total Views"
              value={formatNumber(stats?.total_views ?? 0)}
              change={stats?.views_change_pct}
              iconColor="text-blue-600 dark:text-blue-400"
              iconBg="bg-blue-100 dark:bg-blue-900/20"
            />
            <StatsCard
              icon={Video}
              label="Videos Posted"
              value={formatNumber(stats?.videos_posted ?? 0)}
              change={stats?.videos_change_pct}
              iconColor="text-purple-600 dark:text-purple-400"
              iconBg="bg-purple-100 dark:bg-purple-900/20"
            />
            <StatsCard
              icon={DollarSign}
              label="Total Spend"
              value={formatCost(stats?.cost_this_month ?? 0)}
              change={stats?.cost_change_pct}
              iconColor="text-green-600 dark:text-green-400"
              iconBg="bg-green-100 dark:bg-green-900/20"
            />
            <StatsCard
              icon={TrendingUp}
              label="Avg Views/Video"
              value={
                stats?.videos_posted
                  ? formatNumber(
                      Math.round(
                        (stats.total_views ?? 0) / stats.videos_posted
                      )
                    )
                  : "0"
              }
              iconColor="text-[#E5192A]"
              iconBg="bg-[#E5192A]/10"
            />
          </>
        )}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Views Over Time */}
        <div className="lg:col-span-2 bg-card border border-border rounded-xl p-5">
          <h3 className="text-foreground font-bold mb-4">
            Views Over Time ({dateRange}d)
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke={chart.grid} />
              <XAxis
                dataKey="date"
                stroke={chart.axis}
                tick={{ fill: chart.tick, fontSize: 10 }}
                interval={Math.floor(dateRange / 7)}
              />
              <YAxis
                stroke={chart.axis}
                tick={{ fill: chart.tick, fontSize: 10 }}
                tickFormatter={formatNumber}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: chart.tooltipBg,
                  border: `1px solid ${chart.tooltipBorder}`,
                  borderRadius: "8px",
                  color: chart.tooltipText,
                  fontSize: "12px",
                }}
              />
              <Line
                type="monotone"
                dataKey="views"
                stroke="#E5192A"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: "#E5192A" }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Videos by Format */}
        <div className="bg-card border border-border rounded-xl p-5">
          <h3 className="text-foreground font-bold mb-4">Videos by Format</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={FORMAT_DATA} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke={chart.grid} />
              <XAxis
                type="number"
                stroke={chart.axis}
                tick={{ fill: chart.tick, fontSize: 10 }}
              />
              <YAxis
                type="category"
                dataKey="format"
                stroke={chart.axis}
                tick={{ fill: chart.tick, fontSize: 10 }}
                width={70}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: chart.tooltipBg,
                  border: `1px solid ${chart.tooltipBorder}`,
                  borderRadius: "8px",
                  color: chart.tooltipText,
                  fontSize: "12px",
                }}
              />
              <Bar dataKey="count" fill="#E5192A" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Cost Over Time */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-foreground font-bold mb-4">
          Daily Spend ({dateRange}d)
        </h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke={chart.grid} />
            <XAxis
              dataKey="date"
              stroke={chart.axis}
              tick={{ fill: chart.tick, fontSize: 10 }}
              interval={Math.floor(dateRange / 7)}
            />
            <YAxis
              stroke={chart.axis}
              tick={{ fill: chart.tick, fontSize: 10 }}
              tickFormatter={(v) => `$${v}`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: chart.tooltipBg,
                border: `1px solid ${chart.tooltipBorder}`,
                borderRadius: "8px",
                color: chart.tooltipText,
                fontSize: "12px",
              }}
              formatter={(v: number) => [`$${v}`, "Cost"]}
            />
            <Bar dataKey="cost" fill="#22C55E" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Top Videos */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-foreground font-bold mb-4 flex items-center gap-2">
          <Trophy className="w-4 h-4 text-yellow-500 dark:text-yellow-400" />
          Top Performing Videos
        </h3>
        {videosLoading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <LoadingSkeleton key={i} className="h-14 rounded-lg" />
            ))}
          </div>
        ) : topVideos.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            No posted videos yet. Post some Shorts to see performance data.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left border-b border-border">
                  <th className="text-muted-foreground text-xs font-medium pb-3 pr-4">
                    Video
                  </th>
                  <th className="text-muted-foreground text-xs font-medium pb-3 pr-4">
                    Status
                  </th>
                  <th className="text-muted-foreground text-xs font-medium pb-3 pr-4">
                    Cost
                  </th>
                  <th className="text-muted-foreground text-xs font-medium pb-3">
                    Posted
                  </th>
                </tr>
              </thead>
              <tbody>
                {topVideos.map((video) => (
                  <tr
                    key={video.id}
                    className="border-b border-border last:border-0"
                  >
                    <td className="py-3 pr-4">
                      <a
                        href={`/dashboard/videos/${video.id}`}
                        className="text-foreground text-sm hover:text-[#E5192A] transition-colors truncate max-w-xs block"
                      >
                        {video.seo_title ?? video.topic ?? "Untitled"}
                      </a>
                    </td>
                    <td className="py-3 pr-4">
                      <StatusBadge status={video.status} />
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground text-sm">
                      {video.cost_usd !== null
                        ? formatCost(video.cost_usd)
                        : "—"}
                    </td>
                    <td className="py-3 text-muted-foreground text-sm">
                      {video.posted_at ? timeAgo(video.posted_at) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
