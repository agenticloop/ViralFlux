"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Loader2, Zap, DollarSign } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
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
import { Switch } from "@/components/ui/switch"
import { useUIStore } from "@/store/uiStore"
import { videosAPI } from "@/lib/api"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { channelsAPI } from "@/lib/api"
import { VIDEO_FORMATS, VOICE_IDS, type VoiceProvider } from "@/types"

const schema = z.object({
  channel_id: z.string().min(1, "Please select a channel"),
  format_slug: z.string().min(1, "Please select a format"),
  topic: z.string().optional(),
  voice_provider: z.string().optional(),
  voice_id: z.string().optional(),
  post_immediately: z.boolean().default(false),
})

type FormData = z.infer<typeof schema>

const ESTIMATED_COSTS: Record<string, number> = {
  horror_story: 0.08,
  brainrot_dialogue: 0.07,
  ranking_listicle: 0.06,
  motivational_quotes: 0.05,
  clip_stitch: 0.09,
}

export default function GenerateModal() {
  const { generateModalOpen, closeGenerateModal, selectedChannelId } = useUIStore()
  const queryClient = useQueryClient()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [overrideVoice, setOverrideVoice] = useState(false)

  const { data: channelsData } = useQuery({
    queryKey: ["channels"],
    queryFn: () => channelsAPI.list().then((r) => r.data),
    enabled: generateModalOpen,
  })

  const channels = channelsData?.channels ?? []

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
      channel_id: selectedChannelId ?? "",
      format_slug: "horror_story",
      post_immediately: false,
    },
  })

  const selectedFormat = watch("format_slug")
  const selectedVoiceProvider = watch("voice_provider") as VoiceProvider | undefined
  const estimatedCost = ESTIMATED_COSTS[selectedFormat] ?? 0.08

  const activeFormats = VIDEO_FORMATS.filter((f) => f.is_active)

  const onSubmit = async (data: FormData) => {
    setError(null)
    setIsLoading(true)
    try {
      await videosAPI.generate({
        channel_id: data.channel_id,
        format_slug: data.format_slug,
        topic: data.topic || undefined,
        voice_provider: overrideVoice ? data.voice_provider : undefined,
        voice_id: overrideVoice ? data.voice_id : undefined,
        post_immediately: data.post_immediately,
      })
      queryClient.invalidateQueries({ queryKey: ["videos"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard-activity"] })
      reset()
      closeGenerateModal()
    } catch (err: unknown) {
      const message =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null
      setError(message ?? "Failed to queue video. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={generateModalOpen} onOpenChange={closeGenerateModal}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-[#E5192A] fill-[#E5192A]" />
            Generate New Short
          </DialogTitle>
          <DialogDescription>
            Queue a new AI-generated YouTube Short.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mt-4">
          {/* Channel */}
          <div className="space-y-1.5">
            <Label>Channel</Label>
            <Select
              value={watch("channel_id")}
              onValueChange={(v) => setValue("channel_id", v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select channel..." />
              </SelectTrigger>
              <SelectContent>
                {channels.map((ch: { id: string; channel_name: string }) => (
                  <SelectItem key={ch.id} value={ch.id}>
                    {ch.channel_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.channel_id && (
              <p className="text-[#E5192A] text-xs">{errors.channel_id.message}</p>
            )}
          </div>

          {/* Format */}
          <div className="space-y-1.5">
            <Label>Format</Label>
            <Select
              value={watch("format_slug")}
              onValueChange={(v) => setValue("format_slug", v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select format..." />
              </SelectTrigger>
              <SelectContent>
                {activeFormats.map((f) => (
                  <SelectItem key={f.slug} value={f.slug}>
                    {f.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Topic (optional) */}
          <div className="space-y-1.5">
            <Label>
              Topic{" "}
              <span className="text-[#555555] text-xs">(optional — AI picks if empty)</span>
            </Label>
            <Input
              placeholder="e.g. The haunted hotel in Denver..."
              {...register("topic")}
            />
          </div>

          {/* Voice Override */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>Override Voice</Label>
              <Switch
                checked={overrideVoice}
                onCheckedChange={setOverrideVoice}
              />
            </div>

            {overrideVoice && (
              <div className="grid grid-cols-2 gap-3 pl-2 border-l-2 border-[#E5192A]/30">
                <div className="space-y-1.5">
                  <Label className="text-xs">Provider</Label>
                  <Select
                    onValueChange={(v) => {
                      setValue("voice_provider", v)
                      setValue("voice_id", "")
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Provider" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="elevenlabs">ElevenLabs</SelectItem>
                      <SelectItem value="openai">OpenAI</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Voice</Label>
                  <Select onValueChange={(v) => setValue("voice_id", v)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Voice" />
                    </SelectTrigger>
                    <SelectContent>
                      {(
                        VOICE_IDS[selectedVoiceProvider ?? "elevenlabs"] ?? []
                      ).map((v) => (
                        <SelectItem key={v.id} value={v.id}>
                          {v.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            )}
          </div>

          {/* Post Immediately */}
          <div className="flex items-center justify-between p-3 bg-[#1A1A1A] rounded-lg border border-[#222222]">
            <div>
              <p className="text-[#FAFAFA] text-sm font-medium">
                Post Immediately
              </p>
              <p className="text-[#666666] text-xs">
                Skip approval and post when ready
              </p>
            </div>
            <Switch
              checked={watch("post_immediately")}
              onCheckedChange={(v) => setValue("post_immediately", v)}
            />
          </div>

          {/* Cost estimate */}
          <div className="flex items-center gap-2 p-3 bg-[#0A0A0A] rounded-lg border border-[#1A1A1A]">
            <DollarSign className="w-4 h-4 text-green-400" />
            <div>
              <span className="text-[#FAFAFA] text-sm">
                Estimated cost:{" "}
                <strong className="text-green-400">
                  ~${estimatedCost.toFixed(2)}
                </strong>
              </span>
              <p className="text-[#555555] text-xs">
                AI + voice generation fees
              </p>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-900/20 border border-red-800/40 rounded-lg px-4 py-3">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={closeGenerateModal}
              className="text-[#888888]"
            >
              Cancel
            </Button>
            <Button type="submit" variant="red" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Queuing...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 mr-2 fill-white" />
                  Queue Generation
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
