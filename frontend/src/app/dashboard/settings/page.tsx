"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useQuery } from "@tanstack/react-query"
import { Loader2, User, CreditCard } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { useAuthStore } from "@/store/authStore"
import { plansAPI } from "@/lib/api"
import { formatCredits } from "@/lib/utils"
import type { CurrentPlan } from "@/types"

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

export default function SettingsPage() {
  const { user, setUser } = useAuthStore()
  const [profileLoading, setProfileLoading] = useState(false)
  const [passwordLoading, setPasswordLoading] = useState(false)
  const [profileSuccess, setProfileSuccess] = useState(false)
  const [passwordSuccess, setPasswordSuccess] = useState(false)
  const [profileError, setProfileError] = useState<string | null>(null)
  const [passwordError, setPasswordError] = useState<string | null>(null)

  const { data: current } = useQuery<CurrentPlan>({
    queryKey: ["current-plan"],
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
      setPasswordSuccess(true)
      passwordForm.reset()
      setTimeout(() => setPasswordSuccess(false), 3000)
    } catch {
      setPasswordError("Failed to change password. Check your current password.")
    } finally {
      setPasswordLoading(false)
    }
  }

  const usage = current?.usage
  const creditsUsed = usage
    ? Math.max(0, usage.credits_per_month - usage.subscription_credits)
    : 0
  const creditsPercent =
    usage && usage.credits_per_month > 0
      ? Math.min(100, (creditsUsed / usage.credits_per_month) * 100)
      : 0

  return (
    <div className="max-w-2xl space-y-6">
      {/* Profile Section */}
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex items-center gap-2 mb-5">
          <User className="w-5 h-5 text-[#E5192A]" />
          <h2 className="text-foreground font-bold text-lg">Profile</h2>
        </div>

        <form
          onSubmit={profileForm.handleSubmit(onProfileSubmit)}
          className="space-y-4"
        >
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
            <p className="text-red-600 dark:text-red-400 text-sm">
              {profileError}
            </p>
          )}
          {profileSuccess && (
            <p className="text-green-600 dark:text-green-400 text-sm">
              Profile updated!
            </p>
          )}

          <Button type="submit" variant="red" size="sm" disabled={profileLoading}>
            {profileLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              "Save Changes"
            )}
          </Button>
        </form>

        <Separator className="my-5" />

        {/* Change Password */}
        <h3 className="text-foreground font-semibold mb-4">Change Password</h3>
        <form
          onSubmit={passwordForm.handleSubmit(onPasswordSubmit)}
          className="space-y-4"
        >
          <div className="space-y-1.5">
            <Label>Current Password</Label>
            <Input
              type="password"
              {...passwordForm.register("current_password")}
            />
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
              <Input
                type="password"
                {...passwordForm.register("confirm_password")}
              />
              {passwordForm.formState.errors.confirm_password && (
                <p className="text-[#E5192A] text-xs">
                  {passwordForm.formState.errors.confirm_password.message}
                </p>
              )}
            </div>
          </div>

          {passwordError && (
            <p className="text-red-600 dark:text-red-400 text-sm">
              {passwordError}
            </p>
          )}
          {passwordSuccess && (
            <p className="text-green-600 dark:text-green-400 text-sm">
              Password changed!
            </p>
          )}

          <Button
            type="submit"
            variant="outline"
            size="sm"
            className="border-border text-foreground hover:border-[#E5192A]"
            disabled={passwordLoading}
          >
            {passwordLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Changing...
              </>
            ) : (
              "Change Password"
            )}
          </Button>
        </form>
      </div>

      {/* Plan & Credits Section */}
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex items-center gap-2 mb-5">
          <CreditCard className="w-5 h-5 text-[#E5192A]" />
          <h2 className="text-foreground font-bold text-lg">Plan & Credits</h2>
        </div>

        {current ? (
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-foreground font-semibold capitalize">
                  {current.plan.name} Plan
                </p>
                <p className="text-muted-foreground text-sm">
                  ${current.plan.price_usd}/month
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="border-border text-foreground hover:border-[#E5192A]"
                  asChild
                >
                  <a href="/dashboard/billing">Manage billing</a>
                </Button>
                <Button variant="red" size="sm" asChild>
                  <a href="/pricing">Upgrade</a>
                </Button>
              </div>
            </div>

            {/* Credits */}
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-muted-foreground">
                  Subscription credits used
                </span>
                <span className="text-foreground">
                  {formatCredits(creditsUsed)} /{" "}
                  {formatCredits(usage?.credits_per_month ?? 0)}
                </span>
              </div>
              <Progress value={creditsPercent} className="h-2" />
              <p className="text-muted-foreground text-xs mt-2">
                Balance: {formatCredits(usage?.credits_balance ?? 0)} credits
                {(usage?.topup_credits ?? 0) > 0 && (
                  <> · {formatCredits(usage?.topup_credits ?? 0)} top-up</>
                )}
              </p>
            </div>

            {/* Max quota */}
            {(usage?.max_quota ?? 0) > 0 && (
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-muted-foreground">
                    Max-model generations
                  </span>
                  <span className="text-foreground">
                    {usage?.max_quota_used ?? 0} / {usage?.max_quota ?? 0}
                  </span>
                </div>
                <Progress
                  value={
                    usage && usage.max_quota > 0
                      ? Math.min(
                          100,
                          (usage.max_quota_used / usage.max_quota) * 100
                        )
                      : 0
                  }
                  className="h-2"
                />
              </div>
            )}

            {/* Channels */}
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-muted-foreground">Channels</span>
                <span className="text-foreground">
                  {usage?.channels_used ?? 0} / {usage?.channels_limit ?? 0}
                </span>
              </div>
              <Progress
                value={
                  usage && usage.channels_limit > 0
                    ? Math.min(
                        100,
                        (usage.channels_used / usage.channels_limit) * 100
                      )
                    : 0
                }
                className="h-2"
              />
            </div>
          </div>
        ) : (
          <div className="text-center py-6">
            <p className="text-muted-foreground text-sm mb-4">
              Loading your plan...
            </p>
            <Button variant="red" size="sm" asChild>
              <a href="/pricing">View plans</a>
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
