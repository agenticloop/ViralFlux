"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useQuery } from "@tanstack/react-query"
import { Loader2, Copy, Check, Key, User, CreditCard, Mic } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useAuthStore } from "@/store/authStore"
import { plansAPI, authAPI } from "@/lib/api"
import { VOICE_IDS, type VoiceProvider } from "@/types"
import type { UserSubscription } from "@/types"

const profileSchema = z.object({
  full_name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Invalid email"),
})

const passwordSchema = z
  .object({
    current_password: z.string().min(1, "Required"),
    new_password: z.string().min(8, "Min 8 characters"),
    confirm_password: z.string(),
  })
  .refine((d) => d.new_password === d.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  })

type ProfileData = z.infer<typeof profileSchema>
type PasswordData = z.infer<typeof passwordSchema>

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <button
      onClick={handleCopy}
      className="text-[#666666] hover:text-[#FAFAFA] transition-colors p-1"
    >
      {copied ? (
        <Check className="w-4 h-4 text-green-400" />
      ) : (
        <Copy className="w-4 h-4" />
      )}
    </button>
  )
}

export default function SettingsPage() {
  const { user, setUser } = useAuthStore()
  const [profileLoading, setProfileLoading] = useState(false)
  const [passwordLoading, setPasswordLoading] = useState(false)
  const [profileSuccess, setProfileSuccess] = useState(false)
  const [passwordSuccess, setPasswordSuccess] = useState(false)
  const [profileError, setProfileError] = useState<string | null>(null)
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [defaultVoiceProvider, setDefaultVoiceProvider] = useState<VoiceProvider>("elevenlabs")

  const { data: subscription } = useQuery<UserSubscription>({
    queryKey: ["subscription"],
    queryFn: () => plansAPI.current().then((r) => r.data),
  })

  const profileForm = useForm<ProfileData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: user?.full_name ?? "",
      email: user?.email ?? "",
    },
  })

  const passwordForm = useForm<PasswordData>({
    resolver: zodResolver(passwordSchema),
  })

  const onProfileSubmit = async (data: ProfileData) => {
    setProfileError(null)
    setProfileLoading(true)
    try {
      // In a real app, this would call a PATCH /auth/me endpoint
      setUser({ ...user!, full_name: data.full_name, email: data.email })
      setProfileSuccess(true)
      setTimeout(() => setProfileSuccess(false), 3000)
    } catch {
      setProfileError("Failed to update profile.")
    } finally {
      setProfileLoading(false)
    }
  }

  const onPasswordSubmit = async (_data: PasswordData) => {
    setPasswordError(null)
    setPasswordLoading(true)
    try {
      // Would call PATCH /auth/change-password
      setPasswordSuccess(true)
      passwordForm.reset()
      setTimeout(() => setPasswordSuccess(false), 3000)
    } catch {
      setPasswordError("Failed to change password. Check your current password.")
    } finally {
      setPasswordLoading(false)
    }
  }

  const usagePercent = subscription
    ? subscription.plan.shorts_per_month
      ? Math.min(
          100,
          (subscription.videos_used / subscription.plan.shorts_per_month) * 100
        )
      : 0
    : 0

  return (
    <div className="max-w-2xl space-y-6">
      {/* Profile Section */}
      <div className="bg-[#111111] border border-[#222222] rounded-xl p-6">
        <div className="flex items-center gap-2 mb-5">
          <User className="w-5 h-5 text-[#E5192A]" />
          <h2 className="text-[#FAFAFA] font-bold text-lg">Profile</h2>
        </div>

        <form onSubmit={profileForm.handleSubmit(onProfileSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label>Full Name</Label>
            <Input {...profileForm.register("full_name")} />
            {profileForm.formState.errors.full_name && (
              <p className="text-[#E5192A] text-xs">
                {profileForm.formState.errors.full_name.message}
              </p>
            )}
          </div>
          <div className="space-y-1.5">
            <Label>Email Address</Label>
            <Input type="email" {...profileForm.register("email")} />
          </div>

          {profileError && (
            <p className="text-red-400 text-sm">{profileError}</p>
          )}
          {profileSuccess && (
            <p className="text-green-400 text-sm">Profile updated!</p>
          )}

          <Button type="submit" variant="red" size="sm" disabled={profileLoading}>
            {profileLoading ? (
              <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Saving...</>
            ) : "Save Changes"}
          </Button>
        </form>

        <Separator className="my-5" />

        {/* Change Password */}
        <h3 className="text-[#FAFAFA] font-semibold mb-4">Change Password</h3>
        <form onSubmit={passwordForm.handleSubmit(onPasswordSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label>Current Password</Label>
            <Input type="password" {...passwordForm.register("current_password")} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>New Password</Label>
              <Input type="password" {...passwordForm.register("new_password")} />
              {passwordForm.formState.errors.new_password && (
                <p className="text-[#E5192A] text-xs">
                  {passwordForm.formState.errors.new_password.message}
                </p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label>Confirm Password</Label>
              <Input type="password" {...passwordForm.register("confirm_password")} />
              {passwordForm.formState.errors.confirm_password && (
                <p className="text-[#E5192A] text-xs">
                  {passwordForm.formState.errors.confirm_password.message}
                </p>
              )}
            </div>
          </div>

          {passwordError && (
            <p className="text-red-400 text-sm">{passwordError}</p>
          )}
          {passwordSuccess && (
            <p className="text-green-400 text-sm">Password changed!</p>
          )}

          <Button type="submit" variant="outline" size="sm"
            className="border-[#333333] text-[#FAFAFA] hover:border-[#E5192A]"
            disabled={passwordLoading}>
            {passwordLoading ? (
              <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Changing...</>
            ) : "Change Password"}
          </Button>
        </form>
      </div>

      {/* Plan Section */}
      <div className="bg-[#111111] border border-[#222222] rounded-xl p-6">
        <div className="flex items-center gap-2 mb-5">
          <CreditCard className="w-5 h-5 text-[#E5192A]" />
          <h2 className="text-[#FAFAFA] font-bold text-lg">Plan & Usage</h2>
        </div>

        {subscription ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[#FAFAFA] font-semibold">
                  {subscription.plan.name} Plan
                </p>
                <p className="text-[#888888] text-sm">
                  ${subscription.plan.price_usd}/month
                </p>
              </div>
              <Button variant="red" size="sm" asChild>
                <a href="/pricing">Upgrade</a>
              </Button>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-[#888888]">Videos used</span>
                <span className="text-[#FAFAFA]">
                  {subscription.videos_used} / {subscription.plan.shorts_per_month ?? "∞"}
                </span>
              </div>
              <Progress value={usagePercent} className="h-2" />
            </div>
          </div>
        ) : (
          <div className="text-center py-6">
            <p className="text-[#888888] text-sm mb-4">
              You&apos;re on the free trial (3 videos).
            </p>
            <Button variant="red" size="sm" asChild>
              <a href="/pricing">Upgrade to Starter</a>
            </Button>
          </div>
        )}
      </div>

      {/* API Keys Section */}
      <div className="bg-[#111111] border border-[#222222] rounded-xl p-6">
        <div className="flex items-center gap-2 mb-5">
          <Key className="w-5 h-5 text-[#E5192A]" />
          <h2 className="text-[#FAFAFA] font-bold text-lg">API Keys</h2>
        </div>
        <p className="text-[#888888] text-sm mb-4">
          Your configured API keys for AI providers. Keys are stored encrypted.
        </p>
        <div className="space-y-3">
          {[
            { label: "ElevenLabs API Key", key: "el_****************************1a2b" },
            { label: "OpenAI API Key", key: "sk-****************************3c4d" },
            { label: "Google Gemini Key", key: "AI****************************5e6f" },
          ].map(({ label, key }) => (
            <div key={label} className="flex items-center gap-3 p-3 bg-[#0A0A0A] rounded-lg border border-[#1A1A1A]">
              <div className="flex-1">
                <p className="text-[#888888] text-xs mb-0.5">{label}</p>
                <p className="text-[#FAFAFA] font-mono text-sm">{key}</p>
              </div>
              <CopyButton text={key} />
            </div>
          ))}
        </div>
      </div>

      {/* Voice Defaults */}
      <div className="bg-[#111111] border border-[#222222] rounded-xl p-6">
        <div className="flex items-center gap-2 mb-5">
          <Mic className="w-5 h-5 text-[#E5192A]" />
          <h2 className="text-[#FAFAFA] font-bold text-lg">Voice Defaults</h2>
        </div>
        <p className="text-[#888888] text-sm mb-4">
          Set your default voice settings for new channels.
        </p>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label>Default Provider</Label>
            <Select
              value={defaultVoiceProvider}
              onValueChange={(v) => setDefaultVoiceProvider(v as VoiceProvider)}
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
            <Label>Default Voice</Label>
            <Select>
              <SelectTrigger>
                <SelectValue placeholder="Select voice..." />
              </SelectTrigger>
              <SelectContent>
                {VOICE_IDS[defaultVoiceProvider].map((v) => (
                  <SelectItem key={v.id} value={v.id}>
                    {v.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <Button variant="red" size="sm" className="mt-4">
          Save Voice Defaults
        </Button>
      </div>
    </div>
  )
}
