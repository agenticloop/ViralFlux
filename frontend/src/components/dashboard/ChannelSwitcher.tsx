"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import { ChevronsUpDown, Plus, Check, Tv2 } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import { channelsAPI } from "@/lib/api"
import { useUIStore } from "@/store/uiStore"
import { cn, getInitials } from "@/lib/utils"
import { genreLabel } from "@/types"
import type { Channel } from "@/types"

export default function ChannelSwitcher() {
  const router = useRouter()
  const { selectedChannelId, setSelectedChannelId } = useUIStore()

  const { data: channels } = useQuery<Channel[]>({
    queryKey: ["channels"],
    queryFn: () => channelsAPI.list().then((r) => r.data),
  })

  // Default-select the first channel once channels load and none is chosen
  useEffect(() => {
    if (!channels || channels.length === 0) return
    if (!selectedChannelId || !channels.some((c) => c.id === selectedChannelId)) {
      setSelectedChannelId(channels[0].id)
    }
  }, [channels, selectedChannelId, setSelectedChannelId])

  const active = channels?.find((c) => c.id === selectedChannelId) ?? null

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex items-center gap-2.5 rounded-lg border border-border bg-background px-3 py-1.5 hover:border-[#E5192A]/50 transition-colors min-w-[180px] max-w-[260px]">
          <div className="w-7 h-7 rounded-md bg-[#E5192A]/15 border border-[#E5192A]/20 flex items-center justify-center flex-shrink-0">
            <span className="text-[#E5192A] text-xs font-bold">
              {active ? getInitials(active.channel_name) : <Tv2 className="w-3.5 h-3.5" />}
            </span>
          </div>
          <div className="flex-1 min-w-0 text-left">
            <p className="text-foreground text-sm font-semibold truncate leading-tight">
              {active ? active.channel_name : "No channel"}
            </p>
            {active && (
              <p className="text-muted-foreground text-[11px] truncate leading-tight capitalize">
                {genreLabel(active.genre)}
              </p>
            )}
          </div>
          {active && (
            <span
              className={cn(
                "w-2 h-2 rounded-full flex-shrink-0",
                active.youtube_connected ? "bg-green-500" : "bg-zinc-400"
              )}
              title={active.youtube_connected ? "YouTube connected" : "Not connected"}
            />
          )}
          <ChevronsUpDown className="w-4 h-4 text-muted-foreground flex-shrink-0" />
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="start" className="w-[260px]">
        <DropdownMenuLabel className="text-muted-foreground text-xs">
          Switch channel
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {(channels ?? []).map((ch) => (
          <DropdownMenuItem
            key={ch.id}
            onClick={() => {
              setSelectedChannelId(ch.id)
              router.push(`/dashboard/channels/${ch.id}`)
            }}
            className="gap-2.5"
          >
            <div className="w-6 h-6 rounded-md bg-[#E5192A]/15 flex items-center justify-center flex-shrink-0">
              <span className="text-[#E5192A] text-[10px] font-bold">
                {getInitials(ch.channel_name)}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm truncate leading-tight">{ch.channel_name}</p>
              <p className="text-muted-foreground text-[11px] truncate capitalize leading-tight">
                {genreLabel(ch.genre)}
              </p>
            </div>
            <span
              className={cn(
                "w-1.5 h-1.5 rounded-full",
                ch.youtube_connected ? "bg-green-500" : "bg-zinc-400"
              )}
            />
            {ch.id === selectedChannelId && (
              <Check className="w-3.5 h-3.5 text-[#E5192A]" />
            )}
          </DropdownMenuItem>
        ))}
        {(channels ?? []).length === 0 && (
          <p className="px-2 py-3 text-muted-foreground text-xs text-center">
            No channels yet.
          </p>
        )}
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={() => router.push("/dashboard/channels")}
          className="text-[#E5192A] gap-2.5"
        >
          <Plus className="w-4 h-4" />
          Add / manage channels
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
