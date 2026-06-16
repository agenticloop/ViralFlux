"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useQuery } from "@tanstack/react-query"
import { Loader2, Zap, Sparkles, AlertTriangle, Lock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { channelsAPI, videosAPI, plansAPI } from "@/lib/api"
import {
  GENRES,
  DURATION_TIERS,
  MODEL_TIERS,
  GENRE_VOICES,
  DURATION_CHARS,
  PLAN_RANK,
  creditsForVideo,
} from "@/types"
import type {
  Channel,
  Genre,
  ModelTier,
  DurationTier,
  ScriptSource,
  RecommendedVoice,
  CurrentPlan,
} from "@/types"
import { cn } from "@/lib/utils"

interface GenerateFormProps {
  initialChannelId?: string | null
  onSuccess?: (jobId: string) => void
  submitLabel?: string
}

interface Insufficient {
  needed: number
  balance: number
  topup_url: string
}

export default function GenerateForm({
  initialChannelId,
  onSuccess,
  submitLabel = "Queue Generation",
}: GenerateFormProps) {
  const [channelId, setChannelId] = useState<string>(initialChannelId ?? "")
  const [genre, setGenre] = useState<Genre>("horror")
  const [duration, setDuration] = useState<DurationTier>("30s")
  const [modelTier, setModelTier] = useState<ModelTier>("Lite")
  const [voiceId, setVoiceId] = useState<string>("")
  const [scriptSource, setScriptSource] = useState<ScriptSource>("seed")
  const [topic, setTopic] = useState("")
  const [script, setScript] = useState("")

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [insufficient, setInsufficient] = useState<Insufficient | null>(null)
  const [fellBack, setFellBack] = useState(false)
  const [touchedChannel, setTouchedChannel] = useState(false)

  const { data: channels } = useQuery<Channel[]>({
    queryKey: ["channels"],
    queryFn: () => channelsAPI.list().then((r) => r.data),
  })

  const { data: currentPlan } = useQuery<CurrentPlan>({
    queryKey: ["plan-current"],
    queryFn: () => plansCurrent(),
  })

  const { data: channelVoices } = useQuery<RecommendedVoice[]>({
    queryKey: ["channel-voices", channelId],
    queryFn: () => channelsAPI.voices(channelId).then((r) => r.data),
    enabled: !!channelId,
  })

  const selectedChannel = useMemo(
    () => channels?.find((c) => c.id === channelId) ?? null,
    [channels, channelId]
  )

  // Default channel selection
  useEffect(() => {
    if (channelId || !channels || channels.length === 0) return
    setChannelId(initialChannelId ?? channels[0].id)
  }, [channels, channelId, initialChannelId])

  // When channel changes, seed defaults from it
  useEffect(() => {
    if (!selectedChannel || touchedChannel) return
    setGenre(selectedChannel.genre)
    setDuration(selectedChannel.default_duration)
    setModelTier(selectedChannel.default_model_tier)
    if (selectedChannel.voice_id) setVoiceId(selectedChannel.voice_id)
  }, [selectedChannel, touchedChannel])

  const voices: RecommendedVoice[] =
    channelVoices && channelVoices.length > 0
      ? channelVoices
      : GENRE_VOICES[genre] ?? []

  const planName = currentPlan?.plan.name ?? "free"
  const balance = currentPlan?.usage.credits_balance ?? 0
  const cost = creditsForVideo(duration, modelTier)
  const overBudget = cost > balance

  const charLimit = DURATION_CHARS[duration]

  const isModelLocked = (tierUnlock: string | null) => {
    if (!tierUnlock) return false
    return PLAN_RANK[planName] < PLAN_RANK[tierUnlock as keyof typeof PLAN_RANK]
  }

  const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setInsufficient(null)
    setFellBack(false)

    if (!channelId) {
      setError("Please select a channel.")
      return
    }
    if (scriptSource === "manual" && !script.trim()) {
      setError("Please enter a script.")
      return
    }

    setIsLoading(true)
    try {
      const { data: result } = await videosAPI.generate({
        channel_id: channelId,
        genre,
        duration_tier: duration,
        model_tier: modelTier,
        script_source: scriptSource,
        script: scriptSource === "manual" ? script : undefined,
        topic:
          scriptSource === "ai" || scriptSource === "seed"
            ? topic || undefined
            : undefined,
        voice_id: voiceId || undefined,
      })
      if (result.fell_back_to_balanced) setFellBack(true)
      onSuccess?.(result.job.id)
    } catch (err: unknown) {
      const resp =
        err && typeof err === "object" && "response" in err
          ? (err as {
              response?: {
                status?: number
                data?: {
                  message?: string
                  detail?: string
                  needed?: number
                  balance?: number
                  topup_url?: string
                }
              }
            }).response
          : undefined
      if (resp?.status === 402 && resp.data) {
        setInsufficient({
          needed: resp.data.needed ?? cost,
          balance: resp.data.balance ?? balance,
          topup_url: resp.data.topup_url ?? "/dashboard/billing",
        })
      } else {
        setError(
          resp?.data?.message ??
            resp?.data?.detail ??
            "Failed to queue video. Please try again."
        )
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <TooltipProvider delayDuration={150}>
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Channel */}
        <div className="space-y-1.5">
          <Label>Channel</Label>
          <Select
            value={channelId}
            onValueChange={(v) => {
              setChannelId(v)
              setTouchedChannel(false)
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select a channel..." />
            </SelectTrigger>
            <SelectContent>
              {(channels ?? []).map((ch) => (
                <SelectItem key={ch.id} value={ch.id}>
                  {ch.channel_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Genre */}
        <div className="space-y-1.5">
          <Label>Genre</Label>
          <Select
            value={genre}
            onValueChange={(v) => {
              setGenre(v as Genre)
              setTouchedChannel(true)
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

        {/* Duration tier */}
        <div className="space-y-1.5">
          <Label>Duration</Label>
          <div className="flex flex-wrap gap-2">
            {DURATION_TIERS.map((d) => (
              <button
                key={d.value}
                type="button"
                onClick={() => {
                  setDuration(d.value)
                  setTouchedChannel(true)
                }}
                className={cn(
                  "px-3 py-1.5 rounded-lg border text-sm font-medium transition-all",
                  duration === d.value
                    ? "bg-[#E5192A] text-white border-[#E5192A]"
                    : "bg-background text-muted-foreground border-border hover:border-[#E5192A]/50"
                )}
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>

        {/* Model tier with locks */}
        <div className="space-y-1.5">
          <Label>Model Tier</Label>
          <div className="grid grid-cols-3 gap-2">
            {MODEL_TIERS.map((m) => {
              const locked = isModelLocked(m.unlockPlan)
              const selected = modelTier === m.value
              const btn = (
                <button
                  key={m.value}
                  type="button"
                  disabled={locked}
                  onClick={() => {
                    setModelTier(m.value)
                    setTouchedChannel(true)
                  }}
                  className={cn(
                    "w-full rounded-lg border p-2.5 text-left transition-all",
                    locked && "opacity-50 cursor-not-allowed",
                    !locked && selected
                      ? "bg-[#E5192A]/10 border-[#E5192A]"
                      : "bg-background border-border hover:border-[#E5192A]/50"
                  )}
                >
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm font-semibold text-foreground">
                      {m.name}
                    </span>
                    {locked && <Lock className="w-3 h-3 text-muted-foreground" />}
                  </div>
                  <p className="text-[11px] text-muted-foreground leading-tight mt-0.5">
                    {m.description}
                  </p>
                </button>
              )
              return locked ? (
                <Tooltip key={m.value}>
                  <TooltipTrigger asChild>
                    <span>{btn}</span>
                  </TooltipTrigger>
                  <TooltipContent>
                    Unlock with {cap(m.unlockPlan ?? "")}
                  </TooltipContent>
                </Tooltip>
              ) : (
                btn
              )
            })}
          </div>
        </div>

        {/* Voice */}
        <div className="space-y-1.5">
          <Label>Voice</Label>
          <Select value={voiceId} onValueChange={setVoiceId}>
            <SelectTrigger>
              <SelectValue placeholder="Select a voice..." />
            </SelectTrigger>
            <SelectContent>
              {voices.map((v) => (
                <SelectItem key={v.voice_id} value={v.voice_id}>
                  {v.name} — {v.desc}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Script source */}
        <div className="space-y-2">
          <Label>Script Source</Label>
          <div className="grid grid-cols-3 gap-2">
            {(
              [
                { value: "seed", label: "AI · from seed" },
                { value: "ai", label: "AI · from idea" },
                { value: "manual", label: "Manual script" },
              ] as { value: ScriptSource; label: string }[]
            ).map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setScriptSource(opt.value)}
                className={cn(
                  "px-2 py-2 rounded-lg border text-xs font-medium transition-all",
                  scriptSource === opt.value
                    ? "bg-[#E5192A]/10 border-[#E5192A] text-foreground"
                    : "bg-background text-muted-foreground border-border hover:border-[#E5192A]/50"
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>

          {scriptSource === "seed" && (
            <p className="text-muted-foreground text-xs">
              Uses this channel&apos;s weekly seed prompt to generate the script.
              Optionally nudge it with an idea below.
            </p>
          )}

          {(scriptSource === "ai" || scriptSource === "seed") && (
            <div className="space-y-1.5">
              <Label className="text-xs">
                {scriptSource === "ai" ? "Idea / Topic" : "Idea (optional)"}
              </Label>
              <Input
                placeholder="e.g. The abandoned hospital in Chicago..."
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
              />
            </div>
          )}

          {scriptSource === "manual" && (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label className="text-xs">Script</Label>
                <span
                  className={cn(
                    "text-[11px]",
                    script.length > charLimit
                      ? "text-red-500"
                      : "text-muted-foreground"
                  )}
                >
                  {script.length} / {charLimit}
                </span>
              </div>
              <Textarea
                placeholder="Write your narration script here..."
                value={script}
                maxLength={charLimit}
                onChange={(e) => setScript(e.target.value)}
                className="min-h-[120px]"
              />
            </div>
          )}
        </div>

        {/* Credit preview */}
        <div
          className={cn(
            "flex items-center gap-3 p-3 rounded-lg border",
            overBudget
              ? "bg-red-50 border-red-200 dark:bg-red-900/10 dark:border-red-900/30"
              : "bg-background border-border"
          )}
        >
          <Sparkles className="w-5 h-5 text-[#E5192A] flex-shrink-0" />
          <div className="flex-1">
            <p className="text-foreground text-sm">
              Cost:{" "}
              <strong className="text-[#E5192A]">{cost} credits</strong>
            </p>
            <p className="text-muted-foreground text-xs">
              Balance: {balance} credits
              {overBudget && " — not enough to generate"}
            </p>
          </div>
        </div>

        {/* Fell back notice */}
        {fellBack && (
          <div className="bg-yellow-50 border border-yellow-200 dark:bg-yellow-900/10 dark:border-yellow-900/30 rounded-lg px-4 py-3">
            <p className="text-yellow-700 dark:text-yellow-400 text-sm">
              Your Max quota is used up — this video fell back to the Balanced
              model.
            </p>
          </div>
        )}

        {/* Insufficient credits */}
        {insufficient && (
          <div className="bg-red-50 border border-red-200 dark:bg-red-900/20 dark:border-red-800/40 rounded-lg px-4 py-3">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-red-600 dark:text-red-400 text-sm font-medium">
                  Insufficient credits — need {insufficient.needed}, have{" "}
                  {insufficient.balance}.
                </p>
                <Button
                  variant="red"
                  size="sm"
                  className="mt-2"
                  asChild
                >
                  <Link href="/dashboard/billing">Top up credits</Link>
                </Button>
              </div>
            </div>
          </div>
        )}

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
          disabled={isLoading || overBudget}
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Queuing Generation...
            </>
          ) : (
            <>
              <Zap className="w-4 h-4 mr-2 fill-white" />
              {submitLabel}
            </>
          )}
        </Button>
      </form>
    </TooltipProvider>
  )
}

async function plansCurrent(): Promise<CurrentPlan> {
  const r = await plansAPI.current()
  return r.data
}
