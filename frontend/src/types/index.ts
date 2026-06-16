// ===========================================================================
// ViralFlux v2 types — mirrors backend /api/v1 contract + pricing.md
// ===========================================================================

export type VideoStatus =
  | "queued"
  | "generating"
  | "pending_approval"
  | "approved"
  | "uploading"
  | "posted"
  | "failed"
  | "rejected"

export type Genre = "horror" | "brainrot" | "custom"
export type ModelTier = "Lite" | "Balanced" | "Max"
export type DurationTier = "20s" | "30s" | "60s" | "120s" | "150s"
export type ScriptSource = "ai" | "seed" | "manual"
export type PlanName = "free" | "starter" | "pro" | "agency"

// --- Channels ---------------------------------------------------------------

export interface ChannelSchedule {
  id?: string
  channel_id?: string
  is_enabled: boolean
  frequency_days: number
  post_time: string // "HH:MM"
  timezone: string
  require_approval: boolean
  approval_email?: string | null
  next_run_at?: string | null
}

export interface Channel {
  id: string
  user_id: string
  channel_name: string
  genre: Genre
  seed_prompt: string | null
  seed_prompt_updated_at: string | null
  default_model_tier: ModelTier
  default_duration: DurationTier
  voice_id: string | null
  voice_name: string | null
  music_bucket: string | null
  youtube_connected: boolean
  youtube_channel_id: string | null
  youtube_channel_title: string | null
  youtube_thumbnail_url: string | null
  google_account_email: string | null
  oauth_expiry: string | null
  is_active: boolean
  created_at: string
  schedule: ChannelSchedule | null
}

export interface RecommendedVoice {
  name: string
  voice_id: string
  desc: string
}

// --- Videos -----------------------------------------------------------------

export interface VideoScene {
  index?: number
  text?: string
  image_prompt?: string
  [key: string]: unknown
}

export interface VideoJob {
  id: string
  channel_id: string
  genre: Genre
  duration_tier: DurationTier
  model_tier: ModelTier
  script_source: ScriptSource
  status: VideoStatus
  topic: string | null
  script: string | null
  scene_plan: VideoScene[] | null
  word_timestamps: unknown | null
  seo_title: string | null
  seo_description: string | null
  seo_tags: string[] | null
  voice_id: string | null
  voice_settings: Record<string, unknown> | null
  video_path: string | null
  youtube_video_id: string | null
  youtube_url: string | null
  credits_cost: number | null
  error_message: string | null
  posted_at: string | null
  scheduled_for: string | null
  created_at: string
}

export interface VideoListResponse {
  items: VideoJob[]
  total: number
  page: number
  page_size: number
}

export interface GenerateResult {
  job: VideoJob
  credits_charged: number
  fell_back_to_balanced: boolean
}

export interface InsufficientCredits {
  message: string
  needed: number
  balance: number
  topup_url: string
}

// --- Plans / Credits --------------------------------------------------------

export interface PlanFeatures {
  models: ModelTier[]
  durations: DurationTier[]
  genres: Genre[]
  max_duration: number
  script_char_limit: number
  community_voices: boolean
  team_seats: number
  max_quota?: number
}

export interface Plan {
  id: string
  name: PlanName
  price_usd: number
  price_yearly_usd: number
  credits_per_month: number
  max_quota: number
  channels_limit: number
  features: PlanFeatures
}

export interface UsageStats {
  credits_balance: number
  subscription_credits: number
  topup_credits: number
  credits_per_month: number
  max_quota: number
  max_quota_used: number
  channels_used: number
  channels_limit: number
  period_start: string
  period_end: string
}

export interface CurrentPlan {
  plan: Plan
  usage: UsageStats
}

export type CreditKind = "grant" | "spend" | "topup" | "refund" | "reset"

export interface CreditLedgerEntry {
  kind: CreditKind | string
  amount: number
  balance_after: number
  bucket: "subscription" | "topup" | string
  note: string | null
  created_at: string
}

// --- Dashboard --------------------------------------------------------------

export interface DashboardStats {
  videos_posted: number
  total_views: number
  credits_balance: number
  credits_used_this_period: number
  active_channels: number
}

export interface ActivityItem {
  id: string
  type:
    | "video_posted"
    | "video_failed"
    | "video_approved"
    | "video_generated"
    | "channel_added"
  message: string
  channel_name: string | null
  video_id: string | null
  created_at: string
}

export interface ChannelHealth {
  channel_id: string
  channel_name: string
  status: "healthy" | "warning" | "error"
  youtube_connected: boolean
  videos_this_week: number
  last_post: string | null
}

export interface AnalyticsDataPoint {
  date: string
  views: number
  videos: number
  credits: number
}

// --- User -------------------------------------------------------------------

export interface User {
  id: string
  email: string
  full_name: string
  is_verified: boolean
  plan_id: string | null
  created_at: string
}

// --- Blog -------------------------------------------------------------------

export interface BlogPost {
  id: string
  title: string
  slug: string
  excerpt: string | null
  content: string
  tags: string[] | null
  reading_time_min: number | null
  author_name: string | null
  cover_image_url: string | null
  published_at: string | null
  created_at: string
  updated_at: string
}

// ===========================================================================
// Constants (mirror pricing.md §10)
// ===========================================================================

export interface GenreDef {
  value: Genre
  name: string
  description: string
  emoji: string
}

export const GENRES: GenreDef[] = [
  {
    value: "horror",
    name: "Horror",
    description: "Terrifying narrated short stories with eerie AI imagery.",
    emoji: "🕯️",
  },
  {
    value: "brainrot",
    name: "Brainrot",
    description: "Chaotic Gen-Z narration over satisfying CC0 loops.",
    emoji: "🧠",
  },
  {
    value: "custom",
    name: "Custom",
    description: "Your own genre prompt — Pro & Agency only.",
    emoji: "✨",
  },
]

export interface DurationDef {
  value: DurationTier
  seconds: number
  label: string
}

export const DURATION_TIERS: DurationDef[] = [
  { value: "20s", seconds: 20, label: "20 sec" },
  { value: "30s", seconds: 30, label: "30 sec" },
  { value: "60s", seconds: 60, label: "60 sec" },
  { value: "120s", seconds: 120, label: "120 sec" },
  { value: "150s", seconds: 150, label: "150 sec" },
]

export interface ModelTierDef {
  value: ModelTier
  name: string
  description: string
  unlockPlan: PlanName | null // null = available on free
}

export const MODEL_TIERS: ModelTierDef[] = [
  {
    value: "Lite",
    name: "Lite",
    description: "Maximum efficiency. High-throughput scripts.",
    unlockPlan: null,
  },
  {
    value: "Balanced",
    name: "Balanced",
    description: "Everyday workhorse. Great quality, low cost.",
    unlockPlan: "starter",
  },
  {
    value: "Max",
    name: "Max",
    description: "Frontier reasoning. Best, most creative scripts.",
    unlockPlan: "pro",
  },
]

// Credit math (pricing.md §3 / §10)
export const VIDEO_CREDITS_BASE: Record<DurationTier, number> = {
  "20s": 20,
  "30s": 25,
  "60s": 40,
  "120s": 65,
  "150s": 80,
}

export const MODEL_MULTIPLIER: Record<ModelTier, number> = {
  Lite: 0.7,
  Balanced: 0.85,
  Max: 1.0,
}

export function creditsForVideo(
  duration: DurationTier,
  model: ModelTier
): number {
  return Math.round(VIDEO_CREDITS_BASE[duration] * MODEL_MULTIPLIER[model])
}

// Script character limit per duration (pricing.md DURATION_CHARS)
export const DURATION_CHARS: Record<DurationTier, number> = {
  "20s": 300,
  "30s": 450,
  "60s": 900,
  "120s": 1800,
  "150s": 2250,
}

// Top-up packs (pricing.md §6)
export interface TopupPack {
  name: "Spark" | "Boost" | "Surge" | "Blitz"
  credits: number
  price_usd: number
}

export const TOPUP_PACKS: TopupPack[] = [
  { name: "Spark", credits: 500, price_usd: 12 },
  { name: "Boost", credits: 1500, price_usd: 32 },
  { name: "Surge", credits: 4000, price_usd: 78 },
  { name: "Blitz", credits: 10000, price_usd: 180 },
]

// Add-on packs (pricing.md §7)
export interface AddonDef {
  name: string
  price_usd: number
  effect: string
  availableTo: PlanName[]
}

export const ADDONS: AddonDef[] = [
  {
    name: "Voice Vault",
    price_usd: 9,
    effect: "Full ElevenLabs community voice library",
    availableTo: ["starter"],
  },
  {
    name: "Max Booster",
    price_usd: 15,
    effect: "+50 Max generations before fallback",
    availableTo: ["pro", "agency"],
  },
  {
    name: "Extra Channel",
    price_usd: 6,
    effect: "+1 channel beyond plan limit",
    availableTo: ["starter", "pro"],
  },
  {
    name: "Priority Queue",
    price_usd: 12,
    effect: "Jump the generation queue",
    availableTo: ["starter", "pro"],
  },
]

// Plan display metadata (mirror pricing.md §5 — backend is source of truth at runtime)
export interface PlanDisplay {
  name: PlanName
  label: string
  price_usd: number
  price_yearly_usd: number
  credits_per_month: number
  approx_videos: string
  channels: number
  max_duration: string
  models: string
  custom_genre: boolean
  community_voices: string
  team_seats: number
  highlight?: boolean
  tagline: string
}

export const PLAN_DISPLAY: PlanDisplay[] = [
  {
    name: "free",
    label: "Free",
    price_usd: 0,
    price_yearly_usd: 0,
    credits_per_month: 30,
    approx_videos: "~2 videos (20s)",
    channels: 1,
    max_duration: "20s",
    models: "Lite only",
    custom_genre: false,
    community_voices: "—",
    team_seats: 1,
    tagline: "Kick the tires.",
  },
  {
    name: "starter",
    label: "Starter",
    price_usd: 19,
    price_yearly_usd: 190,
    credits_per_month: 850,
    approx_videos: "~21 videos (60s)",
    channels: 2,
    max_duration: "60s",
    models: "Lite + Balanced",
    custom_genre: false,
    community_voices: "Add-on",
    team_seats: 1,
    tagline: "For solo creators getting serious.",
  },
  {
    name: "pro",
    label: "Pro",
    price_usd: 49,
    price_yearly_usd: 490,
    credits_per_month: 2600,
    approx_videos: "~40 videos (120s)",
    channels: 5,
    max_duration: "120s",
    models: "All · 30 Max/mo",
    custom_genre: true,
    community_voices: "Full library",
    team_seats: 1,
    highlight: true,
    tagline: "Scale across channels.",
  },
  {
    name: "agency",
    label: "Agency",
    price_usd: 129,
    price_yearly_usd: 1290,
    credits_per_month: 8000,
    approx_videos: "~100 videos (150s)",
    channels: 15,
    max_duration: "150s",
    models: "All · 120 Max/mo",
    custom_genre: true,
    community_voices: "Full + community",
    team_seats: 3,
    tagline: "Run a content operation.",
  },
]

// Plan ordering for lock comparisons (free < starter < pro < agency)
export const PLAN_RANK: Record<PlanName, number> = {
  free: 0,
  starter: 1,
  pro: 2,
  agency: 3,
}

// Recommended ElevenLabs voices per genre (fallback when /voices not loaded)
export const GENRE_VOICES: Record<Genre, RecommendedVoice[]> = {
  horror: [
    { name: "Hollow", voice_id: "ErXwobaYiN019PkySvjV", desc: "Deep, ominous male narrator" },
    { name: "Whisper", voice_id: "pNInz6obpgDQGcFmaJgB", desc: "Breathy, unsettling tone" },
    { name: "Crypt", voice_id: "VR6AewLTigWG4xSOukaG", desc: "Gravelly storyteller" },
  ],
  brainrot: [
    { name: "Hype", voice_id: "TxGEqnHWrfWFTfGW9XjX", desc: "Energetic, fast-paced male" },
    { name: "Sparkle", voice_id: "EXAVITQu4vr4xnSDxMaL", desc: "Bubbly Gen-Z female" },
    { name: "Chill", voice_id: "21m00Tcm4TlvDq8ikWAM", desc: "Casual, relaxed narrator" },
  ],
  custom: [
    { name: "Neutral", voice_id: "21m00Tcm4TlvDq8ikWAM", desc: "Versatile balanced voice" },
    { name: "Warm", voice_id: "AZnzlk1XvdvUeBnXmlld", desc: "Warm, friendly female" },
  ],
}

export const TIMEZONES = [
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "America/Toronto",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Asia/Tokyo",
  "Asia/Singapore",
  "Asia/Kolkata",
  "Australia/Sydney",
  "UTC",
]

export function genreLabel(genre: Genre): string {
  return GENRES.find((g) => g.value === genre)?.name ?? genre
}
