"use client"

import { useState } from "react"
import { useParams } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { LoadingSpinner } from "@/components/shared/LoadingSpinner"
import { channelsAPI } from "@/lib/api"
import VideoCard from "@/components/dashboard/VideoCard"
import ScheduleConfig from "@/components/dashboard/ScheduleConfig"
import type { Channel, AnalyticsDataPoint } from "@/types"
import { Youtube, Video, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { timeAgo, formatNumber } from "@/lib/utils"

export default function ChannelDetailPage() {
  const params = useParams()
  const channelId = params.id as string

  const { data: channelData, isLoading } = useQuery<Channel>({
    queryKey: ["channel", channelId],
    queryFn: () => channelsAPI.get(channelId).then((r) => r.data),
  })

  const { data: analyticsData } = useQuery<{ data_points: AnalyticsDataPoint[] }>({
    queryKey: ["channel-analytics", channelId],
    queryFn: () => channelsAPI.analytics(channelId).then((r) => r.data),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  if (!channelData) {
    return (
      <div className="text-center text-[#888888] mt-16">Channel not found.</div>
    )
  }

  const channel = channelData
  const analyticsPoints = analyticsData?.data_points ?? []

  return (
    <div className="max-w-5xl space-y-6">
      {/* Channel Header */}
      <div className="bg-[#111111] border border-[#222222] rounded-xl p-6 flex items-center gap-5">
        <div className="w-16 h-16 rounded-2xl bg-[#E5192A]/15 border border-[#E5192A]/20 flex items-center justify-center text-2xl font-bold text-[#E5192A]">
          {channel.channel_name.slice(0, 2).toUpperCase()}
        </div>
        <div className="flex-1">
          <h1 className="text-[#FAFAFA] font-bold text-2xl">
            {channel.channel_name}
          </h1>
          <div className="flex items-center gap-3 mt-1">
            <span
              className={`text-xs px-2 py-0.5 rounded-full border flex items-center gap-1 ${
                channel.youtube_channel_id
                  ? "bg-green-900/20 text-green-400 border-green-800/30"
                  : "bg-zinc-800 text-zinc-400 border-zinc-700"
              }`}
            >
              <Youtube className="w-3 h-3" />
              {channel.youtube_channel_id ? "Connected" : "Not Connected"}
            </span>
            <span className="text-[#666666] text-xs flex items-center gap-1">
              <Video className="w-3 h-3" />
              {channel.total_videos} videos
            </span>
            {channel.last_posted_at && (
              <span className="text-[#666666] text-xs flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Last post {timeAgo(channel.last_posted_at)}
              </span>
            )}
          </div>
        </div>
        {!channel.youtube_channel_id && (
          <Button
            variant="red"
            size="sm"
            onClick={() => channelsAPI.connectYouTube(channelId)}
            className="flex items-center gap-1.5"
          >
            <Youtube className="w-4 h-4" />
            Connect YouTube
          </Button>
        )}
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview">
        <TabsList className="mb-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="schedule">Schedule</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        {/* Overview */}
        <TabsContent value="overview">
          <div className="grid grid-cols-3 gap-4 mb-6">
            {[
              { label: "Total Videos", value: String(channel.total_videos), icon: Video },
              {
                label: "Last Posted",
                value: channel.last_posted_at ? timeAgo(channel.last_posted_at) : "Never",
                icon: Clock,
              },
              {
                label: "Format",
                value: channel.default_format?.replace("_", " ") ?? "Horror Story",
                icon: Video,
              },
            ].map(({ label, value, icon: Icon }) => (
              <div
                key={label}
                className="bg-[#111111] border border-[#222222] rounded-xl p-4"
              >
                <div className="flex items-center gap-2 mb-2">
                  <Icon className="w-4 h-4 text-[#E5192A]" />
                  <span className="text-[#888888] text-xs">{label}</span>
                </div>
                <div className="text-[#FAFAFA] font-bold capitalize">{value}</div>
              </div>
            ))}
          </div>
          <p className="text-[#888888] text-sm">
            Connect this channel to YouTube and configure a schedule to start
            automating.
          </p>
        </TabsContent>

        {/* Analytics */}
        <TabsContent value="analytics">
          <div className="bg-[#111111] border border-[#222222] rounded-xl p-6">
            <h3 className="text-[#FAFAFA] font-bold mb-4">Views Over Time</h3>
            {analyticsPoints.length === 0 ? (
              <div className="text-center text-[#555555] py-12">
                No analytics data yet. Post some videos first.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={analyticsPoints}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1A1A1A" />
                  <XAxis
                    dataKey="date"
                    stroke="#555555"
                    tick={{ fill: "#888888", fontSize: 11 }}
                  />
                  <YAxis
                    stroke="#555555"
                    tick={{ fill: "#888888", fontSize: 11 }}
                    tickFormatter={formatNumber}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#111111",
                      border: "1px solid #222222",
                      borderRadius: "8px",
                      color: "#FAFAFA",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="views"
                    stroke="#E5192A"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </TabsContent>

        {/* Schedule */}
        <TabsContent value="schedule">
          <div className="bg-[#111111] border border-[#222222] rounded-xl p-6">
            <h3 className="text-[#FAFAFA] font-bold mb-6">
              Schedule Configuration
            </h3>
            <ScheduleConfig channelId={channelId} />
          </div>
        </TabsContent>

        {/* Settings */}
        <TabsContent value="settings">
          <div className="bg-[#111111] border border-[#222222] rounded-xl p-6">
            <h3 className="text-[#FAFAFA] font-bold mb-4">Channel Settings</h3>
            <div className="space-y-4">
              <div>
                <p className="text-[#888888] text-sm mb-1">Channel Name</p>
                <p className="text-[#FAFAFA]">{channel.channel_name}</p>
              </div>
              <div>
                <p className="text-[#888888] text-sm mb-1">Voice Provider</p>
                <p className="text-[#FAFAFA] capitalize">
                  {channel.default_voice_provider}
                </p>
              </div>
              <div>
                <p className="text-[#888888] text-sm mb-1">Default Format</p>
                <p className="text-[#FAFAFA] capitalize">
                  {channel.default_format?.replace("_", " ")}
                </p>
              </div>
              <div>
                <p className="text-[#888888] text-sm mb-1">Music Category</p>
                <p className="text-[#FAFAFA] capitalize">
                  {channel.default_music_category}
                </p>
              </div>
              <Button variant="red" size="sm">Edit Settings</Button>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
