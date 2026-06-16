"use client"

import { useEffect, useState } from "react"
import { useParams, useSearchParams } from "next/navigation"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useTheme } from "next-themes"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"
import {
  Youtube,
  Cpu,
  Clock,
  Mic,
  CheckCircle2,
  Loader2,
  Link2Off,
  Calendar,
} from "lucide-react"
import Image from "next/image"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { LoadingSpinner } from "@/components/shared/LoadingSpinner"
import ScheduleConfig from "@/components/dashboard/ScheduleConfig"
import { channelsAPI } from "@/lib/api"
import { getInitials, timeAgo, formatNumber, formatDate } from "@/lib/utils"
import {
  GENRES,
  MODEL_TIERS,
  DURATION_TIERS,
  genreLabel,
  type Channel,
  type Genre,
  type ModelTier,
  type DurationTier,
  type RecommendedVoice,
  type AnalyticsDataPoint,
} from "@/types"

export default function ChannelDetailPage() {
  const params = useParams()
  const searchParams = useSearchParams()
  const queryClient = useQueryClient()
  const channelId = params.id as string
  const justConnected = searchParams.get("connected") === "1"

  const [showConnectedBanner, setShowConnectedBanner] = useState(justConnected)

  const {
    data: channel,
    isLoading,
    refetch,
  } = useQuery<Channel>({
    queryKey: ["channel", channelId],
    queryFn: () => channelsAPI.get(channelId).then((r) => r.data),
  })

  useEffect(() => {
    if (justConnected) {
      refetch()
      setShowConnectedBanner(true)
    }
  }, [justConnected, refetch])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  if (!channel) {
    return (
      <div className="text-center text-muted-foreground mt-16">
        Channel not found.
      </div>
    )
  }

  const genreDef = GENRES.find((g) => g.value === channel.genre)

  return (
    <div className="max-w-5xl space-y-6">
      {showConnectedBanner && (
        <div className="flex items-center gap-2 bg-green-100 text-green-700 border border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800/30 rounded-lg px-4 py-3">
          <CheckCircle2 className="w-4 h-4" />
          <span className="text-sm font-medium">
            YouTube connected successfully!
          </span>
          <button
            onClick={() => setShowConnectedBanner(false)}
            className="ml-auto text-xs underline opacity-70 hover:opacity-100"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Channel Header */}
      <div className="bg-card border border-border rounded-xl p-6 flex items-center gap-5">
        <div className="w-16 h-16 rounded-2xl bg-[#E5192A]/15 border border-[#E5192A]/20 flex items-center justify-center text-2xl font-bold text-[#E5192A]">
          {getInitials(channel.channel_name)}
        </div>
        <div className="flex-1 min-w-0">
          <h1 className="text-foreground font-bold text-2xl truncate">
            {channel.channel_name}
          </h1>
          <div className="flex items-center gap-3 mt-1 flex-wrap">
            <span className="text-xs px-2 py-0.5 rounded-full border border-border bg-muted text-muted-foreground capitalize">
              {genreDef?.emoji} {genreLabel(channel.genre)}
            </span>
            <span
              className={`text-xs px-2 py-0.5 rounded-full border flex items-center gap-1 ${
                channel.youtube_connected
                  ? "bg-green-100 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800/30"
                  : "bg-zinc-100 text-zinc-600 border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700"
              }`}
            >
              <Youtube className="w-3 h-3" />
              {channel.youtube_connected
                ? channel.youtube_channel_title ?? "Connected"
                : "Not Connected"}
            </span>
            {channel.youtube_connected && channel.google_account_email && (
              <span className="text-muted-foreground text-xs truncate">
                {channel.google_account_email}
              </span>
            )}
          </div>
        </div>
        {channel.youtube_connected && channel.youtube_thumbnail_url && (
          <Image
            src={channel.youtube_thumbnail_url}
            alt={channel.youtube_channel_title ?? channel.channel_name}
            width={48}
            height={48}
            unoptimized
            className="w-12 h-12 rounded-full border border-border object-cover"
          />
        )}
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview">
        <TabsList className="mb-4 flex-wrap h-auto">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="content">Content</TabsTrigger>
          <TabsTrigger value="schedule">Schedule</TabsTrigger>
          <TabsTrigger value="connect">Connect YouTube</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <OverviewTab channel={channel} />
        </TabsContent>

        <TabsContent value="content">
          <ContentTab channel={channel} />
        </TabsContent>

        <TabsContent value="schedule">
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="text-foreground font-bold mb-6">
              Schedule Configuration
            </h3>
            <ScheduleConfig
              channelId={channelId}
              initialSchedule={channel.schedule}
              onSaved={() =>
                queryClient.invalidateQueries({
                  queryKey: ["channel", channelId],
                })
              }
            />
          </div>
        </TabsContent>

        <TabsContent value="connect">
          <ConnectTab channel={channel} />
        </TabsContent>

        <TabsContent value="analytics">
          <AnalyticsTab channelId={channelId} />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function OverviewTab({ channel }: { channel: Channel }) {
  const items = [
    {
      label: "Genre",
      value: genreLabel(channel.genre),
      icon: Mic,
    },
    {
      label: "Model Tier",
      value: channel.default_model_tier,
      icon: Cpu,
    },
    {
      label: "Duration",
      value: channel.default_duration,
      icon: Clock,
    },
  ]
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        {items.map(({ label, value, icon: Icon }) => (
          <div key={label} className="bg-card border border-border rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Icon className="w-4 h-4 text-[#E5192A]" />
              <span className="text-muted-foreground text-xs">{label}</span>
            </div>
            <div className="text-foreground font-bold capitalize">{value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Mic className="w-4 h-4 text-[#E5192A]" />
            <span className="text-muted-foreground text-xs">Voice</span>
          </div>
          <div className="text-foreground font-medium">
            {channel.voice_name ?? "Not set"}
          </div>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Calendar className="w-4 h-4 text-[#E5192A]" />
            <span className="text-muted-foreground text-xs">Schedule</span>
          </div>
          <div className="text-foreground font-medium text-sm">
            {channel.schedule?.is_enabled
              ? `Every ${channel.schedule.frequency_days}d at ${channel.schedule.post_time} (${channel.schedule.timezone})`
              : "Not scheduled"}
          </div>
        </div>
      </div>

      <div className="bg-card border border-border rounded-xl p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-muted-foreground text-xs">
            Weekly Seed Prompt
          </span>
          {channel.seed_prompt_updated_at && (
            <span className="text-muted-foreground text-xs">
              Updated {timeAgo(channel.seed_prompt_updated_at)}
            </span>
          )}
        </div>
        <p className="text-foreground/80 text-sm whitespace-pre-wrap">
          {channel.seed_prompt || "No seed prompt set yet."}
        </p>
      </div>

      <p className="text-muted-foreground text-xs">
        Created {formatDate(channel.created_at)}
      </p>
    </div>
  )
}

function ContentTab({ channel }: { channel: Channel }) {
  const queryClient = useQueryClient()
  const [genre, setGenre] = useState<Genre>(channel.genre)
  const [seedPrompt, setSeedPrompt] = useState(channel.seed_prompt ?? "")
  const [voiceId, setVoiceId] = useState(channel.voice_id ?? "")
  const [modelTier, setModelTier] = useState<ModelTier>(
    channel.default_model_tier
  )
  const [duration, setDuration] = useState<DurationTier>(
    channel.default_duration
  )
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { data: voices } = useQuery<RecommendedVoice[]>({
    queryKey: ["channel-voices", channel.id],
    queryFn: () => channelsAPI.voices(channel.id).then((r) => r.data),
  })

  const voiceOptions = voices ?? []

  const onSave = async () => {
    setError(null)
    setSaving(true)
    try {
      const voiceName =
        voiceOptions.find((v) => v.voice_id === voiceId)?.name ?? undefined
      await channelsAPI.update(channel.id, {
        genre,
        seed_prompt: seedPrompt,
        voice_id: voiceId || undefined,
        voice_name: voiceName,
        default_model_tier: modelTier,
        default_duration: duration,
      })
      queryClient.invalidateQueries({ queryKey: ["channel", channel.id] })
      queryClient.invalidateQueries({ queryKey: ["channels"] })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err: unknown) {
      const resp =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string; message?: string } } })
              .response?.data
          : null
      setError(resp?.detail ?? resp?.message ?? "Failed to save changes.")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-card border border-border rounded-xl p-6 space-y-5">
      <h3 className="text-foreground font-bold">Content Settings</h3>

      <div className="space-y-1.5">
        <Label>Genre</Label>
        <Select value={genre} onValueChange={(v) => setGenre(v as Genre)}>
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

      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <Label>Weekly Seed Prompt</Label>
          {channel.seed_prompt_updated_at && (
            <span className="text-muted-foreground text-xs">
              Updated {timeAgo(channel.seed_prompt_updated_at)}
            </span>
          )}
        </div>
        <Textarea
          rows={4}
          placeholder="Describe the theme / direction for this week's videos..."
          value={seedPrompt}
          onChange={(e) => setSeedPrompt(e.target.value)}
        />
      </div>

      <div className="space-y-1.5">
        <Label>Voice</Label>
        <Select value={voiceId} onValueChange={setVoiceId}>
          <SelectTrigger>
            <SelectValue placeholder="Pick a voice..." />
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

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label>Default Model Tier</Label>
          <Select
            value={modelTier}
            onValueChange={(v) => setModelTier(v as ModelTier)}
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
          <Label>Default Duration</Label>
          <Select
            value={duration}
            onValueChange={(v) => setDuration(v as DurationTier)}
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

      {error && (
        <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
      )}
      {saved && (
        <p className="text-green-600 dark:text-green-400 text-sm">
          Changes saved!
        </p>
      )}

      <Button variant="red" onClick={onSave} disabled={saving}>
        {saving ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Saving...
          </>
        ) : (
          "Save Content Settings"
        )}
      </Button>
    </div>
  )
}

function ConnectTab({ channel }: { channel: Channel }) {
  const queryClient = useQueryClient()
  const [connecting, setConnecting] = useState(false)
  const [disconnecting, setDisconnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onConnect = async () => {
    setError(null)
    setConnecting(true)
    try {
      const res = await channelsAPI.connectYouTube(channel.id)
      window.location.href = res.data.auth_url
    } catch {
      setError("Failed to start YouTube connection. Please try again.")
      setConnecting(false)
    }
  }

  const onDisconnect = async () => {
    setError(null)
    setDisconnecting(true)
    try {
      await channelsAPI.disconnectYouTube(channel.id)
      queryClient.invalidateQueries({ queryKey: ["channel", channel.id] })
      queryClient.invalidateQueries({ queryKey: ["channels"] })
    } catch {
      setError("Failed to disconnect. Please try again.")
    } finally {
      setDisconnecting(false)
    }
  }

  return (
    <div className="bg-card border border-border rounded-xl p-6">
      <h3 className="text-foreground font-bold mb-4 flex items-center gap-2">
        <Youtube className="w-5 h-5 text-red-500" />
        YouTube Connection
      </h3>

      {channel.youtube_connected ? (
        <div className="space-y-4">
          <div className="flex items-center gap-4 p-4 bg-background rounded-lg border border-border">
            {channel.youtube_thumbnail_url && (
              <Image
                src={channel.youtube_thumbnail_url}
                alt={channel.youtube_channel_title ?? channel.channel_name}
                width={48}
                height={48}
                unoptimized
                className="w-12 h-12 rounded-full border border-border object-cover"
              />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-foreground font-semibold truncate">
                {channel.youtube_channel_title ?? "YouTube Channel"}
              </p>
              {channel.google_account_email && (
                <p className="text-muted-foreground text-sm truncate">
                  {channel.google_account_email}
                </p>
              )}
            </div>
            <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 border border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800/30 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" />
              Connected
            </span>
          </div>

          {error && (
            <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
          )}

          <Button
            variant="outline"
            onClick={onDisconnect}
            disabled={disconnecting}
            className="border-red-200 text-red-600 hover:bg-red-50 dark:border-red-800/40 dark:text-red-400 dark:hover:bg-red-900/10 flex items-center gap-2"
          >
            {disconnecting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Link2Off className="w-4 h-4" />
            )}
            Disconnect
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-muted-foreground text-sm">
            Connect this channel to YouTube via Google OAuth so we can post Shorts
            on your behalf. We never see your password.
          </p>

          {error && (
            <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
          )}

          <Button
            variant="red"
            onClick={onConnect}
            disabled={connecting}
            className="flex items-center gap-2"
          >
            {connecting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Youtube className="w-4 h-4" />
            )}
            Connect YouTube
          </Button>
        </div>
      )}
    </div>
  )
}

function AnalyticsTab({ channelId }: { channelId: string }) {
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

  const { data } = useQuery<{ data_points?: AnalyticsDataPoint[] }>({
    queryKey: ["channel-analytics", channelId],
    queryFn: () => channelsAPI.analytics(channelId).then((r) => r.data),
  })

  const points = data?.data_points ?? []

  return (
    <div className="bg-card border border-border rounded-xl p-6">
      <h3 className="text-foreground font-bold mb-4">Views Over Time</h3>
      {points.length === 0 ? (
        <div className="text-center text-muted-foreground py-12">
          No analytics data yet. Post some videos first.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={points}>
            <CartesianGrid strokeDasharray="3 3" stroke={chart.grid} />
            <XAxis
              dataKey="date"
              stroke={chart.axis}
              tick={{ fill: chart.tick, fontSize: 11 }}
            />
            <YAxis
              stroke={chart.axis}
              tick={{ fill: chart.tick, fontSize: 11 }}
              tickFormatter={formatNumber}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: chart.tooltipBg,
                border: `1px solid ${chart.tooltipBorder}`,
                borderRadius: "8px",
                color: chart.tooltipText,
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
  )
}
