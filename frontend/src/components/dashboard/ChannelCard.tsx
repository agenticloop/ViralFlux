"use client"

import Link from "next/link"
import { Settings, Youtube, Video } from "lucide-react"
import { Button } from "@/components/ui/button"
import { getInitials, timeAgo } from "@/lib/utils"
import type { Channel } from "@/types"

interface ChannelCardProps {
  channel: Channel
}

export default function ChannelCard({ channel }: ChannelCardProps) {
  const isConnected = !!channel.youtube_channel_id

  return (
    <div className="bg-[#111111] border border-[#222222] rounded-xl p-5 hover:border-[#333333] transition-all duration-200">
      {/* Header */}
      <div className="flex items-start gap-3 mb-4">
        {/* Avatar */}
        <div className="w-12 h-12 rounded-xl bg-[#E5192A]/15 border border-[#E5192A]/20 flex items-center justify-center flex-shrink-0">
          <span className="text-[#E5192A] font-bold text-lg">
            {getInitials(channel.channel_name)}
          </span>
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <h3 className="text-[#FAFAFA] font-semibold truncate">
            {channel.channel_name}
          </h3>
          <div className="flex items-center gap-2 mt-1">
            <span
              className={`text-xs px-2 py-0.5 rounded-full border flex items-center gap-1 ${
                isConnected
                  ? "bg-green-900/20 text-green-400 border-green-800/30"
                  : "bg-zinc-800 text-zinc-400 border-zinc-700"
              }`}
            >
              <Youtube className="w-3 h-3" />
              {isConnected ? "Connected" : "Not Connected"}
            </span>
            {!channel.is_active && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400 border border-zinc-700">
                Inactive
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-[#1A1A1A] rounded-lg p-3">
          <div className="flex items-center gap-1.5 mb-1">
            <Video className="w-3 h-3 text-[#555555]" />
            <span className="text-[#555555] text-xs">Total Videos</span>
          </div>
          <span className="text-[#FAFAFA] font-bold">
            {channel.total_videos}
          </span>
        </div>
        <div className="bg-[#1A1A1A] rounded-lg p-3">
          <div className="flex items-center gap-1.5 mb-1">
            <span className="text-[#555555] text-xs">Last Post</span>
          </div>
          <span className="text-[#FAFAFA] font-bold text-xs">
            {channel.last_posted_at ? timeAgo(channel.last_posted_at) : "Never"}
          </span>
        </div>
      </div>

      {/* Format + Voice */}
      <div className="flex gap-2 mb-4 text-xs text-[#666666]">
        <span className="bg-[#1A1A1A] px-2 py-1 rounded-md capitalize">
          {channel.default_format?.replace("_", " ") ?? "horror story"}
        </span>
        <span className="bg-[#1A1A1A] px-2 py-1 rounded-md capitalize">
          {channel.default_voice_provider}
        </span>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <Button variant="ghost" size="sm" className="flex-1 text-xs h-8" asChild>
          <Link href={`/dashboard/channels/${channel.id}`}>View</Link>
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 px-3 text-[#888888] hover:text-[#FAFAFA]"
          asChild
        >
          <Link href={`/dashboard/channels/${channel.id}`}>
            <Settings className="w-3.5 h-3.5" />
          </Link>
        </Button>
        {!isConnected && (
          <Button variant="red" size="sm" className="flex-1 text-xs h-8 flex items-center gap-1">
            <Youtube className="w-3 h-3" />
            Connect
          </Button>
        )}
      </div>
    </div>
  )
}
