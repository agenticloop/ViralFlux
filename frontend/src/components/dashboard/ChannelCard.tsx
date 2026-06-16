"use client"

import Link from "next/link"
import { Youtube, Mic, Cpu, Clock, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { getInitials } from "@/lib/utils"
import { GENRES, genreLabel } from "@/types"
import type { Channel } from "@/types"

interface ChannelCardProps {
  channel: Channel
}

export default function ChannelCard({ channel }: ChannelCardProps) {
  const isConnected = channel.youtube_connected
  const genreDef = GENRES.find((g) => g.value === channel.genre)
  const connectedLabel =
    channel.youtube_channel_title ?? channel.google_account_email ?? "Connected"

  return (
    <div className="bg-card border border-border rounded-xl p-5 hover:border-[#E5192A]/40 transition-all duration-200">
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
          <h3 className="text-foreground font-semibold truncate">
            {channel.channel_name}
          </h3>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs px-2 py-0.5 rounded-full border border-border bg-muted text-muted-foreground capitalize">
              {genreDef?.emoji} {genreLabel(channel.genre)}
            </span>
            {!channel.is_active && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-zinc-100 text-zinc-600 border border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700">
                Inactive
              </span>
            )}
          </div>
        </div>
      </div>

      {/* YouTube status */}
      <div
        className={`flex items-center gap-2 mb-4 text-xs px-3 py-2 rounded-lg border ${
          isConnected
            ? "bg-green-100 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800/30"
            : "bg-zinc-100 text-zinc-600 border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700"
        }`}
      >
        <span
          className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
            isConnected ? "bg-green-500 dark:bg-green-400" : "bg-zinc-400"
          }`}
        />
        <Youtube className="w-3.5 h-3.5 flex-shrink-0" />
        <span className="truncate">
          {isConnected ? connectedLabel : "Not Connected"}
        </span>
      </div>

      {/* Config chips */}
      <div className="flex flex-wrap gap-2 mb-4 text-xs">
        <span className="flex items-center gap-1 bg-muted text-muted-foreground px-2 py-1 rounded-md">
          <Cpu className="w-3 h-3" />
          {channel.default_model_tier}
        </span>
        <span className="flex items-center gap-1 bg-muted text-muted-foreground px-2 py-1 rounded-md">
          <Clock className="w-3 h-3" />
          {channel.default_duration}
        </span>
        {channel.voice_name && (
          <span className="flex items-center gap-1 bg-muted text-muted-foreground px-2 py-1 rounded-md">
            <Mic className="w-3 h-3" />
            {channel.voice_name}
          </span>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <Button variant="ghost" size="sm" className="flex-1 text-xs h-8" asChild>
          <Link
            href={`/dashboard/channels/${channel.id}`}
            className="flex items-center gap-1"
          >
            View
            <ArrowRight className="w-3 h-3" />
          </Link>
        </Button>
        {!isConnected && (
          <Button
            variant="red"
            size="sm"
            className="flex-1 text-xs h-8 flex items-center gap-1"
            asChild
          >
            <Link href={`/dashboard/channels/${channel.id}`}>
              <Youtube className="w-3 h-3" />
              Connect
            </Link>
          </Button>
        )}
      </div>
    </div>
  )
}
