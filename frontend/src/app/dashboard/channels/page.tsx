"use client"

import { useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, Tv2, Loader2 } from "lucide-react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import ChannelCard from "@/components/dashboard/ChannelCard"
import { LoadingSkeleton } from "@/components/shared/LoadingSpinner"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { channelsAPI } from "@/lib/api"
import { MUSIC_CATEGORIES, VIDEO_FORMATS } from "@/types"
import type { Channel } from "@/types"

const schema = z.object({
  channel_name: z.string().min(2, "Channel name must be at least 2 characters"),
  default_format: z.string().min(1),
  default_voice_provider: z.string().min(1),
  default_voice_id: z.string().min(1),
  default_music_category: z.string().min(1),
})

type FormData = z.infer<typeof schema>

export default function ChannelsPage() {
  const queryClient = useQueryClient()
  const [addOpen, setAddOpen] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  const { data, isLoading } = useQuery<{ channels: Channel[] }>({
    queryKey: ["channels"],
    queryFn: () => channelsAPI.list().then((r) => r.data),
  })

  const channels = data?.channels ?? []

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      default_format: "horror_story",
      default_voice_provider: "elevenlabs",
      default_voice_id: "21m00Tcm4TlvDq8ikWAM",
      default_music_category: "horror",
    },
  })

  const onSubmit = async (data: FormData) => {
    setCreateError(null)
    setIsCreating(true)
    try {
      await channelsAPI.create(data)
      queryClient.invalidateQueries({ queryKey: ["channels"] })
      reset()
      setAddOpen(false)
    } catch (err: unknown) {
      const message =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null
      setCreateError(message ?? "Failed to create channel.")
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <div className="max-w-6xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[#FAFAFA] font-bold text-2xl">Channels</h1>
          <p className="text-[#888888] text-sm mt-1">
            {channels.length} channel{channels.length !== 1 ? "s" : ""} configured
          </p>
        </div>
        <Button
          variant="red"
          onClick={() => setAddOpen(true)}
          className="flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Add Channel
        </Button>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {[...Array(3)].map((_, i) => (
            <LoadingSkeleton key={i} className="h-52 rounded-xl" />
          ))}
        </div>
      ) : channels.length === 0 ? (
        <div className="bg-[#111111] border border-[#222222] rounded-xl p-16 text-center">
          <Tv2 className="w-12 h-12 text-[#333333] mx-auto mb-4" />
          <h3 className="text-[#888888] font-semibold text-lg mb-2">
            No channels yet
          </h3>
          <p className="text-[#555555] text-sm mb-6">
            Add your first channel to start generating Shorts.
          </p>
          <Button variant="red" onClick={() => setAddOpen(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Add Your First Channel
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {channels.map((channel) => (
            <ChannelCard key={channel.id} channel={channel} />
          ))}
        </div>
      )}

      {/* Add Channel Modal */}
      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Add New Channel</DialogTitle>
            <DialogDescription>
              Configure a new YouTube channel for automation.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mt-2">
            <div className="space-y-1.5">
              <Label>Channel Name</Label>
              <Input
                placeholder="My Horror Channel"
                {...register("channel_name")}
              />
              {errors.channel_name && (
                <p className="text-[#E5192A] text-xs">
                  {errors.channel_name.message}
                </p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label>Default Format</Label>
              <Select
                value={watch("default_format")}
                onValueChange={(v) => setValue("default_format", v)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {VIDEO_FORMATS.filter((f) => f.is_active).map((f) => (
                    <SelectItem key={f.slug} value={f.slug}>
                      {f.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Voice Provider</Label>
                <Select
                  value={watch("default_voice_provider")}
                  onValueChange={(v) => setValue("default_voice_provider", v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="elevenlabs">ElevenLabs</SelectItem>
                    <SelectItem value="openai">OpenAI</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Voice ID</Label>
                <Input
                  placeholder="Rachel"
                  {...register("default_voice_id")}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label>Background Music</Label>
              <Select
                value={watch("default_music_category")}
                onValueChange={(v) => setValue("default_music_category", v)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MUSIC_CATEGORIES.map((cat) => (
                    <SelectItem key={cat} value={cat} className="capitalize">
                      {cat}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {createError && (
              <div className="bg-red-900/20 border border-red-800/40 rounded-lg px-4 py-3">
                <p className="text-red-400 text-sm">{createError}</p>
              </div>
            )}

            <DialogFooter>
              <Button
                type="button"
                variant="ghost"
                onClick={() => setAddOpen(false)}
                className="text-[#888888]"
              >
                Cancel
              </Button>
              <Button type="submit" variant="red" disabled={isCreating}>
                {isCreating ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  "Create Channel"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
