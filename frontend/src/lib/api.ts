import axios, {
  type AxiosInstance,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from "axios"
import type {
  ActivityItem,
  AnalyticsDataPoint,
  Channel,
  CurrentPlan,
  DashboardStats,
  GenerateResult,
  Plan,
  PlanFeatures,
  RecommendedVoice,
  User,
  VideoJob,
} from "@/types"

/*
 * ViralFlux API client (v2).
 *
 * Talks to the FastAPI backend (routes under /api/v1). The browser reaches it
 * same-origin through the host nginx (NEXT_PUBLIC_API_URL = https://<host>/api),
 * so this client appends "/v1".
 *
 * Auth model: short-lived access token in localStorage (Bearer header) +
 * httpOnly refresh_token cookie. On a 401 we transparently hit /auth/refresh
 * (cookie-based) once and retry the original request.
 *
 * The v2 backend schemas (ChannelOut, VideoJobOut, CurrentPlanOut, …) mirror the
 * frontend types in @/types almost 1:1, so the normalizers below are thin: they
 * coerce a couple of numeric/Decimal fields and fill the few UI-only fields the
 * backend doesn't carry with an HONEST empty (0 / null / "" / []). They never
 * fabricate metrics.
 */

const API_ROOT = process.env.NEXT_PUBLIC_API_URL ?? "/api"
const BASE_URL = `${API_ROOT.replace(/\/$/, "")}/v1`

const TOKEN_KEY = "access_token"

function getToken(): string | null {
  if (typeof window === "undefined") return null
  return window.localStorage.getItem(TOKEN_KEY)
}
function setToken(token: string): void {
  if (typeof window === "undefined") return
  window.localStorage.setItem(TOKEN_KEY, token)
}
function clearToken(): void {
  if (typeof window === "undefined") return
  window.localStorage.removeItem(TOKEN_KEY)
}

export const http: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  withCredentials: true, // send/receive the refresh_token cookie
  headers: { "Content-Type": "application/json" },
})

http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Transparent refresh-on-401 (single retry, no loop on the refresh call itself).
let refreshing: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  try {
    const res = await axios.post<{ access_token: string }>(
      `${BASE_URL}/auth/refresh`,
      {},
      { withCredentials: true }
    )
    const token = res.data?.access_token ?? null
    if (token) setToken(token)
    return token
  } catch {
    return null
  }
}

http.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
    const status = error.response?.status
    const isAuthCall = typeof original?.url === "string" && original.url.includes("/auth/")

    if (status === 401 && original && !original._retry && !isAuthCall) {
      original._retry = true
      refreshing = refreshing ?? refreshAccessToken()
      const token = await refreshing
      refreshing = null
      if (token) {
        original.headers = original.headers ?? {}
        original.headers.Authorization = `Bearer ${token}`
        return http(original)
      }
      // Refresh failed → drop session and bounce to login.
      clearToken()
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        window.location.href = "/login"
      }
    }
    return Promise.reject(error)
  }
)

// ── helpers ──────────────────────────────────────────────────────────────────

const num = (v: unknown): number => {
  const n = typeof v === "string" ? parseFloat(v) : (v as number)
  return Number.isFinite(n) ? n : 0
}
const wrap = <T>(data: T): { data: T } => ({ data })

/** Backend VideoJobOut → frontend VideoJob (field names already match). */
function normalizeVideo(v: any): VideoJob {
  return { ...v } as VideoJob
}

/** Backend ChannelOut → frontend Channel (field names already match; the list
 *  endpoint omits the schedule, so default it to null). */
function normalizeChannel(c: any): Channel {
  return { ...c, schedule: c?.schedule ?? null } as Channel
}

const STATUS_TO_ACTIVITY: Record<string, ActivityItem["type"]> = {
  posted: "video_posted",
  approved: "video_approved",
  generated: "video_generated",
  pending_approval: "video_generated",
  rejected: "video_failed",
  failed: "video_failed",
  error: "video_failed",
}

// ── auth ─────────────────────────────────────────────────────────────────────

export const authAPI = {
  login: (body: { email: string; password: string }) =>
    http.post<{ access_token: string; user: User }>("/auth/login", body) as Promise<
      AxiosResponse<{ access_token: string; user: User }>
    >,
  logout: () => http.post("/auth/logout", {}),
  me: () => http.get<User>("/auth/me") as Promise<AxiosResponse<User>>,
  register: (body: { full_name: string; email: string; password: string }) =>
    http.post("/auth/register", body),
  verifyOtp: (body: { email: string; otp: string }) => http.post("/auth/verify-otp", body),
  forgotPassword: (email: string) => http.post("/auth/forgot-password", { email }),
  resetPassword: (body: { email: string; otp: string; new_password: string }) =>
    http.post("/auth/reset-password", body),
}

// ── dashboard ─────────────────────────────────────────────────────────────────

export const dashboardAPI = {
  async stats(): Promise<{ data: DashboardStats }> {
    const { data } = await http.get<any>("/dashboard/stats")
    return wrap<DashboardStats>({
      videos_posted: data.videos_posted ?? 0,
      total_views: data.total_views ?? 0,
      credits_balance: data.credits_balance ?? 0,
      credits_used_this_period: data.credits_used_this_period ?? 0,
      active_channels: data.active_channels ?? 0,
    })
  },

  async activity(): Promise<{ data: { items: ActivityItem[] } }> {
    const { data } = await http.get<any[]>("/dashboard/activity")
    const items: ActivityItem[] = (data ?? []).map((a) => ({
      id: a.id,
      type: STATUS_TO_ACTIVITY[a.status] ?? "video_generated",
      message: a.title || a.topic || `Video ${a.status}`,
      channel_name: null, // backend returns channel_id only on this endpoint
      video_id: a.id,
      created_at: a.created_at,
    }))
    return wrap({ items })
  },
}

// ── videos ─────────────────────────────────────────────────────────────────────

export const videosAPI = {
  async list(params?: {
    status?: string
    channel_id?: string
    genre?: string
    page?: number
    page_size?: number
  }): Promise<{ data: { items: VideoJob[]; total: number; page: number; page_size: number } }> {
    const { data } = await http.get<any>("/videos/", {
      params: {
        status: params?.status,
        channel_id: params?.channel_id,
        genre: params?.genre,
        page: params?.page,
        page_size: params?.page_size,
      },
    })
    return wrap({
      items: (data.items ?? []).map(normalizeVideo),
      total: data.total ?? 0,
      page: data.page ?? 1,
      page_size: data.page_size ?? params?.page_size ?? 20,
    })
  },

  async get(videoId: string): Promise<{ data: VideoJob }> {
    const { data } = await http.get<any>(`/videos/${videoId}`)
    return wrap(normalizeVideo(data))
  },

  // Returns the job + billing info (GenerateResult): { job, credits_charged,
  // fell_back_to_balanced }. Field names match the backend VideoGenerateRequest.
  generate: (body: {
    channel_id: string
    genre?: string
    duration_tier: string
    model_tier: string
    script_source: string
    script?: string
    topic?: string
    voice_id?: string
    schedule_for?: string
  }) => http.post<GenerateResult>("/videos/generate", body),

  approve: (videoId: string) => http.post(`/videos/${videoId}/approve`, {}),
  reject: (videoId: string) => http.post(`/videos/${videoId}/reject`, {}),

  // Absolute URL to the rendered MP4 (backend streams via GET /videos/{id}/preview).
  // Appends ?token= so <video src> works — browsers can't set auth headers on media elements.
  previewUrl: (videoId: string): string => {
    const tok = typeof window !== "undefined" ? window.localStorage.getItem("access_token") : null
    const qs = tok ? `?token=${encodeURIComponent(tok)}` : ""
    return `${BASE_URL}/videos/${videoId}/preview${qs}`
  },
}

// ── channels ─────────────────────────────────────────────────────────────────

export const channelsAPI = {
  async list(): Promise<{ data: Channel[] }> {
    const { data } = await http.get<any[]>("/channels/")
    return wrap((data ?? []).map(normalizeChannel))
  },

  async get(channelId: string): Promise<{ data: Channel }> {
    const { data } = await http.get<any>(`/channels/${channelId}`)
    return wrap(normalizeChannel(data))
  },

  async analytics(channelId: string): Promise<{ data: { data_points: AnalyticsDataPoint[] } }> {
    // Backend exposes an aggregate summary, not a per-day series. Return an empty
    // series (honest "no time-series available") rather than fabricating points.
    await http.get(`/channels/${channelId}/analytics`)
    return wrap({ data_points: [] as AnalyticsDataPoint[] })
  },

  create: (body: {
    channel_name: string
    genre: string
    default_model_tier?: string
    default_duration?: string
    voice_id?: string
    voice_name?: string
    seed_prompt?: string
    music_bucket?: string
  }) => http.post("/channels/", body),

  async update(
    channelId: string,
    body: {
      channel_name?: string
      genre?: string
      seed_prompt?: string
      voice_id?: string
      voice_name?: string
      default_model_tier?: string
      default_duration?: string | number
      music_bucket?: string
    }
  ): Promise<{ data: Channel }> {
    const { data } = await http.put<any>(`/channels/${channelId}`, body)
    return wrap(normalizeChannel(data))
  },

  setSchedule: (
    channelId: string,
    body: {
      is_enabled: boolean
      frequency_days: number
      post_time: string
      timezone: string
      require_approval: boolean
      approval_email?: string
      topics_queue?: string[]
    }
  ) => http.post(`/channels/${channelId}/schedule`, body),

  // Recommended ElevenLabs voices for the channel's genre. Backend returns
  // { voices: [...] }; the UI consumes the bare array.
  async voices(channelId: string): Promise<{ data: RecommendedVoice[] }> {
    const { data } = await http.get<{ voices?: RecommendedVoice[] }>(
      `/channels/${channelId}/voices`
    )
    return wrap(data?.voices ?? [])
  },

  // Begins the direct Google OAuth flow; backend returns { auth_url }. The
  // caller redirects the browser to res.data.auth_url.
  connectYouTube: (channelId: string) =>
    http.post<{ auth_url: string }>(`/channels/${channelId}/connect-youtube`, {}),

  disconnectYouTube: (channelId: string) =>
    http.post(`/channels/${channelId}/disconnect-youtube`, {}),
}

// ── plans ─────────────────────────────────────────────────────────────────────

export const plansAPI = {
  async current(): Promise<{ data: CurrentPlan }> {
    const { data } = await http.get<any>("/plans/current")
    const plan: Plan = {
      id: data.plan.id,
      name: data.plan.name,
      price_usd: num(data.plan.price_usd),
      price_yearly_usd: num(data.plan.price_yearly_usd),
      credits_per_month: data.plan.credits_per_month ?? 0,
      max_quota: data.plan.max_quota ?? 0,
      channels_limit: data.plan.channels_limit ?? 0,
      features: (data.plan.features ?? {}) as PlanFeatures,
    }
    return wrap<CurrentPlan>({ plan, usage: data.usage })
  },

  // Public lead form for the "Custom" plan tier → POST /plans/custom-request.
  customRequest: (body: {
    name: string
    email: string
    channels_needed: number
    videos_per_month: number
    max_duration: number
    team_seats: number
    genres: string
    notes?: string
  }) => http.post("/plans/custom-request", body),
}

// ── credits ───────────────────────────────────────────────────────────────────
// Credit ledger + top-up/add-on purchases. The purchase endpoints will return a
// Stripe checkout `url` once billing is wired; today (Stripe deferred) they
// provision immediately and return no url, so the UI just refreshes balances.

export const creditsAPI = {
  async ledger(limit = 50): Promise<{ data: { entries: any[] } }> {
    const { data } = await http.get<any[]>("/plans/credits/ledger", {
      params: { limit },
    })
    return wrap({ entries: Array.isArray(data) ? data : [] })
  },
  topup: (pack: string) => http.post<any>("/plans/topup", { pack }),
  addon: (addon: string) => http.post<any>("/plans/addons", { addon }),
}

export default http
