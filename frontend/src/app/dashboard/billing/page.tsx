"use client"

import { useState } from "react"
import Link from "next/link"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import {
  Sparkles,
  Coins,
  Plus,
  ArrowUpRight,
  Loader2,
  Zap,
  Tv2,
  Gauge,
  Receipt,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { LoadingSkeleton } from "@/components/shared/LoadingSpinner"
import { plansAPI, creditsAPI } from "@/lib/api"
import { formatCredits, formatDate, timeAgo, cn } from "@/lib/utils"
import {
  TOPUP_PACKS,
  ADDONS,
  type CurrentPlan,
  type CreditLedgerEntry,
  type PlanName,
  type TopupPack,
} from "@/types"

function Banner({
  message,
  tone,
}: {
  message: string
  tone: "success" | "error"
}) {
  return (
    <div
      className={cn(
        "rounded-lg px-4 py-3 text-sm border",
        tone === "success"
          ? "bg-green-50 border-green-200 text-green-700 dark:bg-green-900/20 dark:border-green-800/40 dark:text-green-400"
          : "bg-red-50 border-red-200 text-red-600 dark:bg-red-900/20 dark:border-red-800/40 dark:text-red-400"
      )}
    >
      {message}
    </div>
  )
}

export default function BillingPage() {
  const queryClient = useQueryClient()
  const [busy, setBusy] = useState<string | null>(null)
  const [notice, setNotice] = useState<{
    tone: "success" | "error"
    message: string
  } | null>(null)

  const { data: current, isLoading: planLoading } = useQuery<CurrentPlan>({
    queryKey: ["current-plan"],
    queryFn: () => plansAPI.current().then((r) => r.data),
  })

  const { data: ledger, isLoading: ledgerLoading } = useQuery<
    CreditLedgerEntry[]
  >({
    queryKey: ["credit-ledger"],
    queryFn: () => creditsAPI.ledger(50).then((r) => r.data.entries),
  })

  const usage = current?.usage
  const planName = current?.plan?.name as PlanName | undefined

  const flash = (tone: "success" | "error", message: string) => {
    setNotice({ tone, message })
    setTimeout(() => setNotice(null), 4000)
  }

  const handleTopup = async (pack: TopupPack) => {
    setBusy(`topup-${pack.name}`)
    try {
      const res = await creditsAPI.topup(pack.name)
      const url = res.data?.url ?? res.data?.checkout_url
      if (url) {
        window.location.href = url
        return
      }
      queryClient.invalidateQueries({ queryKey: ["current-plan"] })
      queryClient.invalidateQueries({ queryKey: ["credit-ledger"] })
      flash("success", `Added ${formatCredits(pack.credits)} credits.`)
    } catch {
      flash("error", "Could not start the top-up. Please try again.")
    } finally {
      setBusy(null)
    }
  }

  const handleAddon = async (addon: string) => {
    setBusy(`addon-${addon}`)
    try {
      const res = await creditsAPI.addon(addon)
      const url = res.data?.url ?? res.data?.checkout_url
      if (url) {
        window.location.href = url
        return
      }
      queryClient.invalidateQueries({ queryKey: ["current-plan"] })
      flash("success", `${addon} added to your plan.`)
    } catch {
      flash("error", "Could not add this add-on. Please try again.")
    } finally {
      setBusy(null)
    }
  }

  const maxQuotaPct =
    usage && usage.max_quota > 0
      ? Math.min(100, (usage.max_quota_used / usage.max_quota) * 100)
      : 0
  const channelsPct =
    usage && usage.channels_limit > 0
      ? Math.min(100, (usage.channels_used / usage.channels_limit) * 100)
      : 0

  return (
    <div className="max-w-5xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-foreground font-bold text-2xl">Billing & Credits</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Track your credit balance, top up, and manage add-ons.
          </p>
        </div>
        <Button variant="red" asChild>
          <Link href="/pricing" className="flex items-center gap-2">
            <ArrowUpRight className="w-4 h-4" />
            Upgrade plan
          </Link>
        </Button>
      </div>

      {notice && <Banner tone={notice.tone} message={notice.message} />}

      {/* Balance + usage */}
      {planLoading ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <LoadingSkeleton key={i} className="h-40 rounded-xl" />
          ))}
        </div>
      ) : usage ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Balance card */}
          <div className="lg:col-span-1 bg-card border border-border rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-9 h-9 rounded-lg bg-[#E5192A]/10 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-[#E5192A]" />
              </div>
              <span className="text-muted-foreground text-sm">
                Credit balance
              </span>
            </div>
            <div className="text-4xl font-black text-foreground mb-1">
              {formatCredits(usage.credits_balance)}
            </div>
            <p className="text-muted-foreground text-xs mb-4">
              {formatCredits(usage.credits_per_month)} credits / mo · resets{" "}
              {formatDate(usage.period_end)}
            </p>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Subscription</span>
                <span className="text-foreground font-medium">
                  {formatCredits(usage.subscription_credits)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Top-up (never expires)</span>
                <span className="text-foreground font-medium">
                  {formatCredits(usage.topup_credits)}
                </span>
              </div>
            </div>
          </div>

          {/* Plan + quotas */}
          <div className="lg:col-span-2 bg-card border border-border rounded-xl p-5 space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-muted-foreground text-xs">Current plan</p>
                <p className="text-foreground font-bold text-lg capitalize">
                  {planName ?? "—"}
                </p>
              </div>
              <Button variant="outline" size="sm" asChild
                className="border-border text-foreground hover:border-[#E5192A]">
                <Link href="/pricing">Compare plans</Link>
              </Button>
            </div>

            {usage.max_quota > 0 && (
              <div>
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="text-muted-foreground flex items-center gap-1.5">
                    <Gauge className="w-3.5 h-3.5" />
                    Max-model generations
                  </span>
                  <span className="text-foreground">
                    {usage.max_quota_used} / {usage.max_quota}
                  </span>
                </div>
                <Progress value={maxQuotaPct} className="h-2" />
                <p className="text-muted-foreground text-xs mt-1.5">
                  After the quota, generation falls back to Balanced — you&apos;re
                  never blocked.
                </p>
              </div>
            )}

            <div>
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-muted-foreground flex items-center gap-1.5">
                  <Tv2 className="w-3.5 h-3.5" />
                  Channels
                </span>
                <span className="text-foreground">
                  {usage.channels_used} / {usage.channels_limit}
                </span>
              </div>
              <Progress value={channelsPct} className="h-2" />
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-card border border-border rounded-xl p-8 text-center text-muted-foreground text-sm">
          Could not load your plan. Please refresh.
        </div>
      )}

      {/* Top-up packs */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Coins className="w-4 h-4 text-[#E5192A]" />
          <h2 className="text-foreground font-bold">Top-up packs</h2>
          <span className="text-muted-foreground text-xs">
            Credits never expire while your account is active.
          </span>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {TOPUP_PACKS.map((pack) => (
            <div
              key={pack.name}
              className="bg-card border border-border rounded-xl p-5 flex flex-col"
            >
              <p className="text-foreground font-bold">{pack.name}</p>
              <p className="text-2xl font-black text-foreground mt-2">
                {formatCredits(pack.credits)}
              </p>
              <p className="text-muted-foreground text-xs mb-4">credits</p>
              <p className="text-foreground font-semibold mb-3">
                ${pack.price_usd}
              </p>
              <Button
                variant="red"
                size="sm"
                className="mt-auto"
                disabled={busy === `topup-${pack.name}`}
                onClick={() => handleTopup(pack)}
              >
                {busy === `topup-${pack.name}` ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <Zap className="w-3.5 h-3.5 mr-1.5 fill-white" />
                    Buy
                  </>
                )}
              </Button>
            </div>
          ))}
        </div>
      </div>

      {/* Add-ons */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Plus className="w-4 h-4 text-[#E5192A]" />
          <h2 className="text-foreground font-bold">Add-ons</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {ADDONS.map((addon) => {
            const available =
              !planName || addon.availableTo.includes(planName)
            return (
              <div
                key={addon.name}
                className="bg-card border border-border rounded-xl p-5 flex flex-col"
              >
                <p className="text-foreground font-bold">{addon.name}</p>
                <p className="text-muted-foreground text-xs mt-1 mb-3 flex-1">
                  {addon.effect}
                </p>
                <p className="text-foreground font-semibold mb-1">
                  +${addon.price_usd}/mo
                </p>
                <p className="text-muted-foreground text-[11px] mb-3 capitalize">
                  {addon.availableTo.join(", ")}
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-auto border-border text-foreground hover:border-[#E5192A]"
                  disabled={!available || busy === `addon-${addon.name}`}
                  onClick={() => handleAddon(addon.name)}
                >
                  {busy === `addon-${addon.name}` ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : available ? (
                    "Add"
                  ) : (
                    "Not on your plan"
                  )}
                </Button>
              </div>
            )
          })}
        </div>
      </div>

      {/* Ledger */}
      <div className="bg-card border border-border rounded-xl p-5">
        <div className="flex items-center gap-2 mb-4">
          <Receipt className="w-4 h-4 text-[#E5192A]" />
          <h2 className="text-foreground font-bold">Credit history</h2>
        </div>
        {ledgerLoading ? (
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <LoadingSkeleton key={i} className="h-10 rounded-lg" />
            ))}
          </div>
        ) : !ledger || ledger.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            No credit activity yet.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b border-border">
                  <th className="text-muted-foreground text-xs font-medium pb-3 pr-4">
                    Type
                  </th>
                  <th className="text-muted-foreground text-xs font-medium pb-3 pr-4">
                    Amount
                  </th>
                  <th className="text-muted-foreground text-xs font-medium pb-3 pr-4">
                    Balance
                  </th>
                  <th className="text-muted-foreground text-xs font-medium pb-3 pr-4">
                    Bucket
                  </th>
                  <th className="text-muted-foreground text-xs font-medium pb-3 pr-4">
                    Note
                  </th>
                  <th className="text-muted-foreground text-xs font-medium pb-3">
                    When
                  </th>
                </tr>
              </thead>
              <tbody>
                {ledger.map((entry, i) => (
                  <tr
                    key={i}
                    className="border-b border-border last:border-0"
                  >
                    <td className="py-3 pr-4 text-foreground capitalize">
                      {entry.kind}
                    </td>
                    <td
                      className={cn(
                        "py-3 pr-4 font-medium",
                        entry.amount >= 0
                          ? "text-green-600 dark:text-green-400"
                          : "text-red-600 dark:text-red-400"
                      )}
                    >
                      {entry.amount >= 0 ? "+" : ""}
                      {formatCredits(entry.amount)}
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground">
                      {formatCredits(entry.balance_after)}
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground capitalize">
                      {entry.bucket}
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground max-w-xs truncate">
                      {entry.note ?? "—"}
                    </td>
                    <td className="py-3 text-muted-foreground whitespace-nowrap">
                      {timeAgo(entry.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
