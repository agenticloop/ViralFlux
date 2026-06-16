"use client"

import { useState } from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import { Check, Minus, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn, formatCredits } from "@/lib/utils"
import { PLAN_DISPLAY, TOPUP_PACKS } from "@/types"

export default function PricingSection() {
  const [yearly, setYearly] = useState(false)

  return (
    <section id="pricing" className="py-20 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-10"
        >
          <span className="text-[#E5192A] text-sm font-semibold uppercase tracking-wider mb-3 block">
            Pricing
          </span>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-foreground mb-4">
            Pay in <span className="text-gradient-red">credits</span>, not guesswork
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Every plan includes monthly credits. Start free, scale when you&apos;re
            ready, top up anytime.
          </p>
        </motion.div>

        {/* Billing toggle */}
        <div className="flex items-center justify-center gap-3 mb-12">
          <span
            className={cn(
              "text-sm font-medium",
              !yearly ? "text-foreground" : "text-muted-foreground"
            )}
          >
            Monthly
          </span>
          <button
            onClick={() => setYearly((v) => !v)}
            className="relative w-12 h-6 rounded-full bg-muted border border-border transition-colors"
            aria-label="Toggle yearly billing"
          >
            <span
              className={cn(
                "absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-[#E5192A] transition-transform",
                yearly && "translate-x-6"
              )}
            />
          </button>
          <span
            className={cn(
              "text-sm font-medium",
              yearly ? "text-foreground" : "text-muted-foreground"
            )}
          >
            Yearly{" "}
            <span className="text-[#E5192A] text-xs font-semibold">save ~17%</span>
          </span>
        </div>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
          {PLAN_DISPLAY.map((plan, i) => {
            const price = yearly ? plan.price_yearly_usd : plan.price_usd
            const isFree = plan.name === "free"
            return (
              <motion.div
                key={plan.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className={cn(
                  "relative rounded-2xl p-7 border transition-all duration-300 flex flex-col",
                  plan.highlight
                    ? "border-[#E5192A] bg-gradient-to-b from-[#E5192A]/8 to-card shadow-xl shadow-[#E5192A]/10"
                    : "border-border bg-card hover:border-border hover:shadow-md dark:hover:shadow-none"
                )}
              >
                {plan.highlight && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                    <span className="bg-[#E5192A] text-white text-xs font-bold px-3 py-1 rounded-full">
                      MOST POPULAR
                    </span>
                  </div>
                )}

                <h3 className="text-foreground font-bold text-xl">{plan.label}</h3>
                <p className="text-muted-foreground text-sm mb-4 min-h-[2.5rem]">
                  {plan.tagline}
                </p>

                <div className="flex items-end gap-1 mb-1">
                  <span className="text-4xl font-black text-foreground">
                    ${price}
                  </span>
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
                <p className="text-muted-foreground text-xs mb-5">
                  {plan.approx_videos}
                </p>

                <Button
                  variant={plan.highlight ? "red" : "outline"}
                  className={cn(
                    "w-full mb-6",
                    !plan.highlight &&
                      "border-border text-foreground hover:border-[#E5192A]"
                  )}
                  asChild
                >
                  <Link href="/register">
                    {isFree ? "Start free" : `Get ${plan.label}`}
                  </Link>
                </Button>

                <ul className="space-y-2.5 text-sm">
                  <Feature label={`${plan.channels} channel${plan.channels > 1 ? "s" : ""}`} />
                  <Feature label={`Up to ${plan.max_duration} videos`} />
                  <Feature label={plan.models} />
                  <Feature label="Custom genre" on={plan.custom_genre} />
                  <Feature
                    label={`Community voices: ${plan.community_voices}`}
                    on={plan.community_voices !== "—"}
                  />
                  <Feature
                    label={`${plan.team_seats} team seat${plan.team_seats > 1 ? "s" : ""}`}
                  />
                </ul>
              </motion.div>
            )
          })}
        </div>

        {/* Custom + top-up teaser */}
        <div className="max-w-6xl mx-auto mt-10 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-2xl border border-border bg-card p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h4 className="text-foreground font-bold">Need more scale?</h4>
              <p className="text-muted-foreground text-sm">
                15+ channels, white-label, custom volume — we&apos;ll build a quote.
              </p>
            </div>
            <Button variant="outline" asChild
              className="border-border text-foreground hover:border-[#E5192A] flex-shrink-0">
              <Link href="/pricing#custom">Request custom plan</Link>
            </Button>
          </div>

          <div className="rounded-2xl border border-border bg-card p-6">
            <h4 className="text-foreground font-bold mb-3">Top-up packs</h4>
            <div className="grid grid-cols-4 gap-2">
              {TOPUP_PACKS.map((pack) => (
                <div
                  key={pack.name}
                  className="rounded-lg border border-border bg-background p-2 text-center"
                >
                  <p className="text-foreground text-xs font-semibold">
                    {pack.name}
                  </p>
                  <p className="text-muted-foreground text-[11px]">
                    {formatCredits(pack.credits)}
                  </p>
                  <p className="text-[#E5192A] text-xs font-bold">
                    ${pack.price_usd}
                  </p>
                </div>
              ))}
            </div>
            <p className="text-muted-foreground text-xs mt-3">
              Top-up credits never expire while your account is active.
            </p>
          </div>
        </div>

        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center text-muted-foreground text-sm mt-8"
        >
          Start free with 30 credits. No credit card required.
        </motion.p>
      </div>
    </section>
  )
}

function Feature({ label, on = true }: { label: string; on?: boolean }) {
  return (
    <li className="flex items-start gap-2">
      {on ? (
        <Check className="w-4 h-4 text-[#E5192A] mt-0.5 flex-shrink-0" />
      ) : (
        <Minus className="w-4 h-4 text-muted-foreground/60 mt-0.5 flex-shrink-0" />
      )}
      <span className={on ? "text-muted-foreground/80" : "text-muted-foreground/50"}>
        {label}
      </span>
    </li>
  )
}
