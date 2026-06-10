"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useQuery } from "@tanstack/react-query"
import { Loader2, DollarSign, Zap, ArrowLeft } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { channelsAPI, videosAPI } from "@/lib/api"
import { VIDEO_FORMATS, VOICE_IDS, type VoiceProvider } from "@/types"
import type { Channel } from "@/types"

const schema = z.object({
  channel_id: z.string().min(1, "Select a channel"),
  format_slug: z.string().min(1, "Select a format"),
  topic: z.string().optional(),
  voice_provider: z.string().optional(),
  voice_id: z.string().optional(),
  post_immediately: z.boolean().default(false),
  scheduled_for: z.string().optional(),
})

type FormData = z.infer<typeof schema>

const COST_MAP: Record<string, number> = {
  horror_story: 0.08,
  brainrot_dialogue: 0.07,
  ranking_listicle: 0.06,
  motivational_quotes: 0.05,
  clip_stitch: 0.09,
}

export default function NewVideoPage() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [overrideVoice, setOverrideVoice] = useState(false)

  const { data: channelsData } = useQuery<{ channels: Channel[] }>({
    queryKey: ["channels"],
    queryFn: () => channelsAPI.list().then((r) => r.data),
  })

  const channels = channelsData?.channels ?? []

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      format_slug: "horror_story",
      post_immediately: false,
    },
  })

  const selectedFormat = watch("format_slug")
  const selectedVoiceProvider = watch("voice_provider") as VoiceProvider | undefined
  const postImmediately = watch("post_immediately")
  const estimatedCost = COST_MAP[selectedFormat] ?? 0.08

  const onSubmit = async (data: FormData) => {
    setError(null)
    setIsLoading(true)
    try {
      const { data: result } = await videosAPI.generate({
        channel_id: data.channel_id,
        format_slug: data.format_slug,
        topic: data.topic || undefined,
        voice_provider: overrideVoice ? data.voice_provider : undefined,
        voice_id: overrideVoice ? data.voice_id : undefined,
        post_immediately: data.post_immediately,
        schedule_for: !data.post_immediately && data.scheduled_for
          ? data.scheduled_for
          : undefined,
      })
      router.push(`/dashboard/videos/${result.id}`)
    } catch (err: unknown) {
      const message =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null
      setError(message ?? "Failed to create video. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="max-w-2xl">
      {/* Back */}
      <Link
        href="/dashboard/videos"
        className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground text-sm mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Videos
      </Link>

      <div className="mb-6">
        <h1 className="text-foreground font-bold text-2xl">
          Create New Short
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Configure and queue a new AI-generated YouTube Short.
        </p>
      </div>

      <form
        onSubmit={handleSubmit(onSubmit)}
        className="bg-card border border-border rounded-xl p-6 space-y-5"
      >
        {/* Channel */}
        <div className="space-y-1.5">
          <Label>Channel</Label>
          <Select
            value={watch("channel_id") ?? ""}
            onValueChange={(v) => setValue("channel_id", v)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select a channel..." />
            </SelectTrigger>
            <SelectContent>
              {channels.map((ch) => (
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

        {/* Topic */}
        <div className="space-y-1.5">
          <Label>
            Topic{" "}
            <span className="text-muted-foreground text-xs">(optional)</span>
          </Label>
          <Input
            placeholder="e.g. The abandoned hospital in Chicago..."
            {...register("topic")}
          />
          <p className="text-muted-foreground text-xs">
            Leave empty to let AI pick a trending topic automatically.
          </p>
        </div>

        {/* Voice Override */}
        <div className="space-y-3 p-4 bg-background rounded-lg border border-border">
          <div className="flex items-center justify-between">
            <Label>Override Voice Settings</Label>
            <Switch
              checked={overrideVoice}
              onCheckedChange={setOverrideVoice}
            />
          </div>

          {overrideVoice && (
            <div className="grid grid-cols-2 gap-3 pt-2">
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
                    {(VOICE_IDS[selectedVoiceProvider ?? "elevenlabs"] ?? []).map(
                      (v) => (
                        <SelectItem key={v.id} value={v.id}>
                          {v.name}
                        </SelectItem>
                      )
                    )}
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
        </div>

        {/* Post schedule */}
        <div className="space-y-3 p-4 bg-background rounded-lg border border-border">
          <div className="flex items-center justify-between">
            <div>
              <Label>Post Immediately When Ready</Label>
              <p className="text-muted-foreground text-xs mt-0.5">
                Post as soon as generation completes, skipping approval
              </p>
            </div>
            <Switch
              checked={postImmediately}
              onCheckedChange={(v) => setValue("post_immediately", v)}
            />
          </div>

          {!postImmediately && (
            <div className="space-y-1.5 pt-2">
              <Label className="text-xs">Schedule For (optional)</Label>
              <Input
                type="datetime-local"
                {...register("scheduled_for")}
                className="text-foreground"
              />
            </div>
          )}
        </div>

        {/* Cost Estimate */}
        <div className="flex items-center gap-3 p-3 bg-green-50 border border-green-200 dark:bg-green-900/10 dark:border-green-900/20 rounded-lg">
          <DollarSign className="w-5 h-5 text-green-600 dark:text-green-400" />
          <div>
            <p className="text-foreground text-sm">
              Estimated cost:{" "}
              <strong className="text-green-600 dark:text-green-400">
                ~${estimatedCost.toFixed(2)}
              </strong>
            </p>
            <p className="text-muted-foreground text-xs">
              Includes AI script + voice generation
            </p>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 dark:bg-red-900/20 dark:border-red-800/40 rounded-lg px-4 py-3">
            <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
          </div>
        )}

        {/* Submit */}
        <Button
          type="submit"
          variant="red"
          className="w-full"
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Queuing Generation...
            </>
          ) : (
            <>
              <Zap className="w-4 h-4 mr-2 fill-white" />
              Queue Generation
            </>
          )}
        </Button>
      </form>
    </div>
  )
}
