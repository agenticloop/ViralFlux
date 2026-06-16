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
import {
  GENRES,
  MODEL_TIERS,
  DURATION_TIERS,
  GENRE_VOICES,
  type Channel,
  type Genre,
  type ModelTier,
  type DurationTier,
} from "@/types"

const schema = z.object({
  channel_name: z.string().min(2, "Channel name must be at least 2 characters"),
  genre: z.enum(["horror", "brainrot", "custom"]),
  default_model_tier: z.enum(["Lite", "Balanced", "Max"]),
  default_duration: z.enum(["20s", "30s", "60s", "120s", "150s"]),
  voice_id: z.string().optional(),
})

type FormData = z.infer<typeof schema>

export default function ChannelsPage() {
  const queryClient = useQueryClient()
  const [addOpen, setAddOpen] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  const { data, isLoading } = useQuery<Channel[]>({
    queryKey: ["channels"],
    queryFn: () => channelsAPI.list().then((r) => r.data),
  })

  const channels = data ?? []

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
      genre: "horror",
      default_model_tier: "Lite",
      default_duration: "30s",
      voice_id: "",
    },
  })

  const selectedGenre = watch("genre") as Genre
  const voiceOptions = GENRE_VOICES[selectedGenre] ?? []

  const onSubmit = async (values: FormData) => {
    setCreateError(null)
    setIsCreating(true)
    try {
      await channelsAPI.create({
        channel_name: values.channel_name,
        genre: values.genre,
        default_model_tier: values.default_model_tier,
        default_duration: values.default_duration,
        voice_id: values.voice_id || undefined,
      })
      queryClient.invalidateQueries({ queryKey: ["channels"] })
      reset()
      setAddOpen(false)
    } catch (err: unknown) {
      const resp =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string; message?: string } } })
              .response?.data
          : null
      setCreateError(resp?.detail ?? resp?.message ?? "Failed to create channel.")
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <div className="max-w-6xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-foreground font-bold text-2xl">Channels</h1>
          <p className="text-muted-foreground text-sm mt-1">
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
        <div className="bg-card border border-border rounded-xl p-16 text-center">
          <Tv2 className="w-12 h-12 text-foreground/60 mx-auto mb-4" />
          <h3 className="text-muted-foreground font-semibold text-lg mb-2">
            No channels yet
          </h3>
          <p className="text-muted-foreground text-sm mb-6">
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
              Configure a new channel — pick a genre, voice, and defaults.
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
              <Label>Genre</Label>
              <Select
                value={watch("genre")}
                onValueChange={(v) => {
                  setValue("genre", v as Genre)
                  setValue("voice_id", "")
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {GENRES.map((g) => (
                    <SelectItem key={g.value} value={g.value}>
                      {g.emoji} {g.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Model Tier</Label>
                <Select
                  value={watch("default_model_tier")}
                  onValueChange={(v) =>
                    setValue("default_model_tier", v as ModelTier)
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {MODEL_TIERS.map((m) => (
                      <SelectItem key={m.value} value={m.value}>
                        {m.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Duration</Label>
                <Select
                  value={watch("default_duration")}
                  onValueChange={(v) =>
                    setValue("default_duration", v as DurationTier)
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {DURATION_TIERS.map((d) => (
                      <SelectItem key={d.value} value={d.value}>
                        {d.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-1.5">
              <Label>
                Voice{" "}
                <span className="text-muted-foreground text-xs">(optional)</span>
              </Label>
              <Select
                value={watch("voice_id") || ""}
                onValueChange={(v) => setValue("voice_id", v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Pick a recommended voice..." />
                </SelectTrigger>
                <SelectContent>
                  {voiceOptions.map((v) => (
                    <SelectItem key={v.voice_id} value={v.voice_id}>
                      {v.name} — {v.desc}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {createError && (
              <div className="bg-red-50 border border-red-200 dark:bg-red-900/20 dark:border-red-800/40 rounded-lg px-4 py-3">
                <p className="text-red-600 dark:text-red-400 text-sm">
                  {createError}
                </p>
              </div>
            )}

            <DialogFooter>
              <Button
                type="button"
                variant="ghost"
                onClick={() => setAddOpen(false)}
                className="text-muted-foreground"
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
