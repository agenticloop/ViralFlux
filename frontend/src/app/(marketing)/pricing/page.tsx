"use client"

import { useState } from "react"
import Link from "next/link"
import { Check, Minus, Sparkles, Loader2, ChevronDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { cn, formatCredits } from "@/lib/utils"
import { plansAPI } from "@/lib/api"
import { PLAN_DISPLAY, TOPUP_PACKS, ADDONS } from "@/types"

const COMPARISON_ROWS: {
  label: string
  get: (p: (typeof PLAN_DISPLAY)[number]) => string | boolean
}[] = [
  { label: "Monthly price", get: (p) => (p.price_usd === 0 ? "Free" : `$${p.price_usd}/mo`) },
  { label: "Credits / mo", get: (p) => formatCredits(p.credits_per_month) },
  { label: "≈ Videos / mo", get: (p) => p.approx_videos.replace(/^~/, "") },
  { label: "Channels", get: (p) => String(p.channels) },
  { label: "Max duration", get: (p) => p.max_duration },
  { label: "Models", get: (p) => p.models },
  { label: "Custom genre", get: (p) => p.custom_genre },
  { label: "Community voices", get: (p) => p.community_voices },
  { label: "Team seats", get: (p) => String(p.team_seats) },
  { label: "Top-ups", get: () => true },
]

const SCHEDULING: Record<string, string> = {
  free: "15-day manual",
  starter: "Monthly auto",
  pro: "Continuous",
  agency: "Continuous + bulk",
}

const FAQS = [
  {
    q: "What is a credit?",
    a: "Credits are the single currency for everything you generate. Each video costs credits based on its duration and model tier — you never deal with tokens, characters, or API bills. A 20s Lite video is ~14 credits; a 150s Max video is ~80.",
  },
  {
    q: "What are Lite, Balanced, and Max?",
    a: "Three model tiers for the script/SEO brain. Lite is fast and efficient, Balanced is the everyday workhorse, and Max is frontier-quality for the most creative writing. Higher tiers cost a small credit premium. Availability scales with your plan.",
  },
  {
    q: "What's the Max quota?",
    a: "Pro and Agency include a fixed number of Max-model generations per month (30 and 120). Once used up, generation automatically falls back to Balanced for the rest of the cycle — you're notified but never blocked.",
  },
  {
    q: "Do top-up credits expire?",
    a: "No. Top-up credits never expire while your account is active. Subscription credits reset every month (Pro and Agency carry a one-month rollover).",
  },
  {
    q: "Can I change plans anytime?",
    a: "Yes. Upgrades take effect immediately; downgrades apply at the end of your billing cycle. You can also stack add-ons like an extra channel or priority queue.",
  },
]

export default function PricingPage() {
  const [yearly, setYearly] = useState(false)
  const [customOpen, setCustomOpen] = useState(false)

  return (
    <div className="bg-background min-h-screen pt-24 pb-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-4xl sm:text-5xl font-black text-foreground mb-4">
            Pay in credits, not guesswork
          </h1>
          <p className="text-muted-foreground text-lg max-w-xl mx-auto">
            Start free with 30 credits. Top up or upgrade whenever you scale.
          </p>
        </div>

        {/* Billing toggle */}
        <div className="flex items-center justify-center gap-3 mb-12">
          <span className={cn("text-sm font-medium", !yearly ? "text-foreground" : "text-muted-foreground")}>
            Monthly
          </span>
          <button
            onClick={() => setYearly((v) => !v)}
            className="relative w-12 h-6 rounded-full bg-muted border border-border"
            aria-label="Toggle yearly billing"
          >
            <span
              className={cn(
                "absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-[#E5192A] transition-transform",
                yearly && "translate-x-6"
              )}
            />
          </button>
          <span className={cn("text-sm font-medium", yearly ? "text-foreground" : "text-muted-foreground")}>
            Yearly <span className="text-[#E5192A] text-xs font-semibold">save ~17%</span>
          </span>
        </div>

        {/* Plan cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto mb-20">
          {PLAN_DISPLAY.map((plan) => {
            const price = yearly ? plan.price_yearly_usd : plan.price_usd
            const isFree = plan.name === "free"
            return (
              <div
                key={plan.name}
                className={cn(
                  "relative rounded-2xl p-7 border flex flex-col",
                  plan.highlight
                    ? "border-[#E5192A] bg-gradient-to-b from-[#E5192A]/8 to-card"
                    : "border-border bg-card"
                )}
              >
                {plan.highlight && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                    <span className="bg-[#E5192A] text-white text-xs font-bold px-3 py-1 rounded-full">
                      MOST POPULAR
                    </span>
                  </div>
                )}
                <h2 className="text-foreground font-bold text-xl">{plan.label}</h2>
                <p className="text-muted-foreground text-sm mb-4 min-h-[2.5rem]">
                  {plan.tagline}
                </p>
                <div className="flex items-end gap-1 mb-1">
                  <span className="text-4xl font-black text-foreground">${price}</span>
                  <span className="text-muted-foreground text-sm mb-1">
                    {isFree ? "" : yearly ? "/yr" : "/mo"}
                  </span>
                </div>
                {!isFree && yearly && (
                  <p className="text-[#E5192A] text-xs font-semibold mb-3">
                    ${plan.price_usd}/mo billed annually
                  </p>
                )}
                <div className="flex items-center gap-1.5 text-foreground font-semibold mb-1 mt-2">
                  <Sparkles className="w-4 h-4 text-[#E5192A]" />
                  {formatCredits(plan.credits_per_month)} credits/mo
                </div>
                <p className="text-muted-foreground text-xs mb-5">{plan.approx_videos}</p>

                <Button
                  variant={plan.highlight ? "red" : "outline"}
                  className={cn(
                    "w-full mb-6",
                    !plan.highlight && "border-border text-foreground hover:border-[#E5192A]"
                  )}
                  asChild
                >
                  <Link href="/register">{isFree ? "Start free" : `Get ${plan.label}`}</Link>
                </Button>

                <ul className="space-y-2.5 text-sm">
                  <Feat label={`${plan.channels} channel${plan.channels > 1 ? "s" : ""}`} />
                  <Feat label={`Up to ${plan.max_duration} videos`} />
                  <Feat label={plan.models} />
                  <Feat label="Custom genre" on={plan.custom_genre} />
                  <Feat
                    label={`Community voices: ${plan.community_voices}`}
                    on={plan.community_voices !== "—"}
                  />
                  <Feat label={`${plan.team_seats} team seat${plan.team_seats > 1 ? "s" : ""}`} />
                </ul>
              </div>
            )
          })}
        </div>

        {/* Comparison table */}
        <div className="max-w-5xl mx-auto mb-20">
          <h2 className="text-2xl font-bold text-foreground mb-8 text-center">
            Full plan comparison
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className="text-left text-muted-foreground text-sm font-medium py-3 px-4 w-1/3">
                    Feature
                  </th>
                  {PLAN_DISPLAY.map((p) => (
                    <th
                      key={p.name}
                      className={cn(
                        "text-center text-sm font-bold py-3 px-4",
                        p.highlight ? "text-[#E5192A]" : "text-foreground"
                      )}
                    >
                      {p.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {COMPARISON_ROWS.map((row, i) => (
                  <tr
                    key={row.label}
                    className={cn("border-t border-border", i % 2 && "bg-card/40")}
                  >
                    <td className="text-muted-foreground/80 text-sm py-3 px-4">
                      {row.label}
                    </td>
                    {PLAN_DISPLAY.map((p) => {
                      const v = row.get(p)
                      return (
                        <td key={p.name} className="text-center py-3 px-4">
                          {v === true ? (
                            <Check className="w-4 h-4 text-[#E5192A] mx-auto" />
                          ) : v === false ? (
                            <Minus className="w-4 h-4 text-muted-foreground/50 mx-auto" />
                          ) : (
                            <span className="text-foreground text-sm font-medium">{v}</span>
                          )}
                        </td>
                      )
                    })}
                  </tr>
                ))}
                <tr className="border-t border-border">
                  <td className="text-muted-foreground/80 text-sm py-3 px-4">Scheduling</td>
                  {PLAN_DISPLAY.map((p) => (
                    <td key={p.name} className="text-center py-3 px-4 text-foreground text-sm font-medium">
                      {SCHEDULING[p.name]}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Custom plan inline form */}
        <div id="custom" className="max-w-3xl mx-auto mb-20">
          <div className="rounded-2xl border border-border bg-card overflow-hidden">
            <button
              onClick={() => setCustomOpen((v) => !v)}
              className="w-full flex items-center justify-between p-6 text-left"
            >
              <div>
                <h2 className="text-foreground font-bold text-xl">Custom plan</h2>
                <p className="text-muted-foreground text-sm">
                  15+ channels, white-label, or custom volume — get a quote.
                </p>
              </div>
              <ChevronDown
                className={cn(
                  "w-5 h-5 text-muted-foreground transition-transform",
                  customOpen && "rotate-180"
                )}
              />
            </button>
            {customOpen && (
              <div className="px-6 pb-6 border-t border-border pt-6">
                <CustomForm />
              </div>
            )}
          </div>
        </div>

        {/* Top-ups */}
        <div className="max-w-5xl mx-auto mb-16">
          <h2 className="text-2xl font-bold text-foreground mb-6 text-center">
            Top-up packs
          </h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {TOPUP_PACKS.map((pack) => (
              <div key={pack.name} className="rounded-xl border border-border bg-card p-5 text-center">
                <p className="text-foreground font-bold">{pack.name}</p>
                <p className="text-2xl font-black text-foreground mt-2">
                  {formatCredits(pack.credits)}
                </p>
                <p className="text-muted-foreground text-xs mb-2">credits</p>
                <p className="text-[#E5192A] font-bold">${pack.price_usd}</p>
              </div>
            ))}
          </div>
          <p className="text-center text-muted-foreground text-sm mt-4">
            Top-up credits never expire while your account is active.
          </p>
        </div>

        {/* Add-ons */}
        <div className="max-w-5xl mx-auto mb-20">
          <h2 className="text-2xl font-bold text-foreground mb-6 text-center">Add-ons</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {ADDONS.map((addon) => (
              <div key={addon.name} className="rounded-xl border border-border bg-card p-5">
                <p className="text-foreground font-bold">{addon.name}</p>
                <p className="text-muted-foreground text-xs mt-1 mb-3">{addon.effect}</p>
                <p className="text-[#E5192A] font-bold">+${addon.price_usd}/mo</p>
                <p className="text-muted-foreground text-[11px] mt-1 capitalize">
                  {addon.availableTo.join(", ")}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* FAQ */}
        <div className="max-w-3xl mx-auto mb-20">
          <h2 className="text-2xl font-bold text-foreground mb-8 text-center">
            Frequently asked questions
          </h2>
          <div className="space-y-4">
            {FAQS.map((faq) => (
              <div key={faq.q} className="bg-card border border-border rounded-xl p-6">
                <h3 className="text-foreground font-semibold mb-2">{faq.q}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="text-center">
          <h2 className="text-2xl font-bold text-foreground mb-4">
            Ready to start automating?
          </h2>
          <p className="text-muted-foreground mb-6">
            30 free credits. No credit card. Set up in under 5 minutes.
          </p>
          <Button variant="red" size="lg" asChild className="px-10">
            <Link href="/register">Get started free</Link>
          </Button>
        </div>
      </div>
    </div>
  )
}

function Feat({ label, on = true }: { label: string; on?: boolean }) {
  return (
    <li className="flex items-start gap-2">
      {on ? (
        <Check className="w-4 h-4 text-[#E5192A] mt-0.5 flex-shrink-0" />
      ) : (
        <Minus className="w-4 h-4 text-muted-foreground/60 mt-0.5 flex-shrink-0" />
      )}
      <span className={on ? "text-muted-foreground/80" : "text-muted-foreground/50"}>{label}</span>
    </li>
  )
}

function CustomForm() {
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState({
    name: "",
    email: "",
    channels_needed: 20,
    videos_per_month: 200,
    max_duration: 150,
    team_seats: 3,
    genres: "Horror, Brainrot, Custom",
    notes: "",
  })

  const set = (k: keyof typeof form, v: string | number) =>
    setForm((f) => ({ ...f, [k]: v }))

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await plansAPI.customRequest({
        name: form.name,
        email: form.email,
        channels_needed: Number(form.channels_needed),
        videos_per_month: Number(form.videos_per_month),
        max_duration: Number(form.max_duration),
        team_seats: Number(form.team_seats),
        genres: form.genres,
        notes: form.notes || undefined,
      })
      setDone(true)
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string; message?: string } } })
              .response?.data?.detail ??
            (err as { response?: { data?: { message?: string } } }).response?.data
              ?.message
          : null
      setError(msg ?? "Could not submit your request. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  if (done) {
    return (
      <div className="text-center py-6">
        <Check className="w-8 h-8 text-green-600 dark:text-green-400 mx-auto mb-3" />
        <p className="text-foreground font-semibold">Request received.</p>
        <p className="text-muted-foreground text-sm">
          We&apos;ll email you a custom quote shortly.
        </p>
      </div>
    )
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label>Name</Label>
          <Input value={form.name} onChange={(e) => set("name", e.target.value)} required />
        </div>
        <div className="space-y-1.5">
          <Label>Email</Label>
          <Input type="email" value={form.email} onChange={(e) => set("email", e.target.value)} required />
        </div>
        <div className="space-y-1.5">
          <Label>Channels needed</Label>
          <Input type="number" min={1} value={form.channels_needed} onChange={(e) => set("channels_needed", e.target.valueAsNumber || 0)} />
        </div>
        <div className="space-y-1.5">
          <Label>Videos / month</Label>
          <Input type="number" min={1} value={form.videos_per_month} onChange={(e) => set("videos_per_month", e.target.valueAsNumber || 0)} />
        </div>
        <div className="space-y-1.5">
          <Label>Max duration (s)</Label>
          <Input type="number" min={20} max={150} value={form.max_duration} onChange={(e) => set("max_duration", e.target.valueAsNumber || 0)} />
        </div>
        <div className="space-y-1.5">
          <Label>Team seats</Label>
          <Input type="number" min={1} value={form.team_seats} onChange={(e) => set("team_seats", e.target.valueAsNumber || 0)} />
        </div>
      </div>
      <div className="space-y-1.5">
        <Label>Genres</Label>
        <Input value={form.genres} onChange={(e) => set("genres", e.target.value)} />
      </div>
      <div className="space-y-1.5">
        <Label>Notes</Label>
        <Textarea
          rows={3}
          placeholder="Anything else we should know?"
          value={form.notes}
          onChange={(e) => set("notes", e.target.value)}
        />
      </div>
      {error && <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>}
      <Button type="submit" variant="red" disabled={loading}>
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Submitting...
          </>
        ) : (
          "Request a quote"
        )}
      </Button>
    </form>
  )
}
