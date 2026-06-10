export type VideoStatus =
  | "queued"
  | "generating"
  | "pending_approval"
  | "approved"
  | "uploading"
  | "posted"
  | "failed"

export interface VideoJob {
  id: string
  user_id: string
  channel_id: string
  format_slug: string
  status: VideoStatus
  topic: string | null
  source_url: string | null
  script: string | null
  seo_title: string | null
  seo_description: string | null
  seo_tags: string[] | null
  voice_provider: string | null
  voice_id: string | null
  video_path: string | null
  youtube_video_id: string | null
  youtube_url: string | null
  cost_usd: number | null
  error_message: string | null
  posted_at: string | null
  scheduled_for: string | null
  created_at: string
  updated_at: string
}

export interface Channel {
  id: string
  user_id: string
  channel_name: string
  youtube_channel_id: string | null
  youtube_channel_name: string | null
  default_voice_provider: string
  default_voice_id: string
  default_music_category: string
  default_format: string
  is_active: boolean
  total_videos: number
  last_posted_at: string | null
  created_at: string
  updated_at: string
}

export interface ChannelSchedule {
  id: string
  channel_id: string
  enabled: boolean
  frequency_days: number
  time_of_day: string
  timezone: string
  require_approval: boolean
  approval_email: string | null
  auto_topic: boolean
  topic_queue: string[]
  next_run_at: string | null
}

export interface Plan {
  id: string
  name: string
  price_usd: number
  shorts_per_month: number | null
  channels_limit: number | null
  features: Record<string, boolean | string | number>
}

export interface UserSubscription {
  plan: Plan
  videos_used: number
  period_start: string
  period_end: string
}

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

export interface DashboardStats {
  videos_posted: number
  total_views: number
  cost_this_month: number
  active_channels: number
  videos_this_month: number
  videos_change_pct: number
  views_change_pct: number
  cost_change_pct: number
}

export interface ActivityItem {
  id: string
  type: "video_posted" | "video_failed" | "video_approved" | "channel_added"
  message: string
  channel_name: string | null
  video_id: string | null
  created_at: string
}

export interface TrendingTopic {
  topic: string
  score: number
  source: string
  category: string
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
  cost: number
}

export interface User {
  id: string
  email: string
  full_name: string
  is_verified: boolean
  plan_id: string | null
  created_at: string
}

export interface VideoFormat {
  slug: string
  name: string
  description: string
  is_active: boolean
  coming_soon: boolean
}

export const VIDEO_FORMATS: VideoFormat[] = [
  {
    slug: "horror_story",
    name: "Horror Story",
    description: "Terrifying 60-second horror narratives",
    is_active: true,
    coming_soon: false,
  },
  {
    slug: "brainrot_dialogue",
    name: "Brainrot Dialogue",
    description: "Chaotic Gen Z conversation style",
    is_active: false,
    coming_soon: true,
  },
  {
    slug: "ranking_listicle",
    name: "Ranking / Listicle",
    description: "Top 5/10 countdown videos",
    is_active: false,
    coming_soon: true,
  },
  {
    slug: "motivational_quotes",
    name: "Motivational Quotes",
    description: "Inspirational quote compilations",
    is_active: false,
    coming_soon: true,
  },
  {
    slug: "clip_stitch",
    name: "Clip Stitch",
    description: "Stitched clip compilations",
    is_active: false,
    coming_soon: true,
  },
]

export const VOICE_PROVIDERS = ["elevenlabs", "openai"] as const
export type VoiceProvider = (typeof VOICE_PROVIDERS)[number]

export const VOICE_IDS: Record<VoiceProvider, { id: string; name: string }[]> =
  {
    elevenlabs: [
      { id: "21m00Tcm4TlvDq8ikWAM", name: "Rachel" },
      { id: "AZnzlk1XvdvUeBnXmlld", name: "Domi" },
      { id: "EXAVITQu4vr4xnSDxMaL", name: "Bella" },
      { id: "ErXwobaYiN019PkySvjV", name: "Antoni" },
      { id: "MF3mGyEYCl7XYWbV9V6O", name: "Elli" },
      { id: "TxGEqnHWrfWFTfGW9XjX", name: "Josh" },
      { id: "VR6AewLTigWG4xSOukaG", name: "Arnold" },
      { id: "pNInz6obpgDQGcFmaJgB", name: "Adam" },
    ],
    openai: [
      { id: "alloy", name: "Alloy" },
      { id: "echo", name: "Echo" },
      { id: "fable", name: "Fable" },
      { id: "onyx", name: "Onyx" },
      { id: "nova", name: "Nova" },
      { id: "shimmer", name: "Shimmer" },
    ],
  }

export const MUSIC_CATEGORIES = [
  "horror",
  "ambient",
  "upbeat",
  "cinematic",
  "lofi",
  "none",
] as const
export type MusicCategory = (typeof MUSIC_CATEGORIES)[number]

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
