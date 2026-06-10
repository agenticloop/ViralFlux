"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { Check } from "lucide-react"
import { Button } from "@/components/ui/button"

const plans = [
  {
    name: "Starter",
    price: 29,
    tagline: "Perfect to get started",
    shorts: 20,
    channels: 1,
    features: [
      "20 Shorts per month",
      "1 YouTube channel",
      "Horror Story format",
      "ElevenLabs voice",
      "Auto YouTube posting",
      "Basic analytics",
      "Email support",
    ],
    cta: "Start Free Trial",
    popular: false,
  },
  {
    name: "Creator",
    price: 79,
    tagline: "Most popular for creators",
    shorts: 100,
    channels: 5,
    features: [
      "100 Shorts per month",
      "5 YouTube channels",
      "All active formats",
      "Priority ElevenLabs voice",
      "Auto YouTube posting",
      "Advanced analytics",
      "Approval workflow",
      "Trend detection AI",
      "Priority support",
    ],
    cta: "Start Free Trial",
    popular: true,
  },
  {
    name: "Agency",
    price: 199,
    tagline: "For agencies & power users",
    shorts: null,
    channels: null,
    features: [
      "Unlimited Shorts",
      "Unlimited channels",
      "All formats (incl. upcoming)",
      "Custom voice cloning",
      "White-label option",
      "API access",
      "Custom approval workflows",
      "Dedicated account manager",
      "SLA support",
    ],
    cta: "Contact Sales",
    popular: false,
  },
]

export default function PricingSection() {
  return (
    <section id="pricing" className="py-20 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <span className="text-[#E5192A] text-sm font-semibold uppercase tracking-wider mb-3 block">
            Pricing
          </span>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-foreground mb-4">
            Simple,{" "}
            <span className="text-gradient-red">Transparent</span> Pricing
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Start free. Scale when you&apos;re ready. Cancel anytime.
          </p>
        </motion.div>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {plans.map((plan, i) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.1 }}
              className={`relative rounded-2xl p-8 border transition-all duration-300 ${
                plan.popular
                  ? "border-[#E5192A] bg-gradient-to-b from-[#E5192A]/5 to-[#111111] shadow-xl shadow-red-900/20"
                  : "border-border bg-card hover:border-border"
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                  <span className="bg-[#E5192A] text-white text-xs font-bold px-3 py-1 rounded-full">
                    MOST POPULAR
                  </span>
                </div>
              )}

              <div className="mb-6">
                <h3 className="text-foreground font-bold text-xl mb-1">
                  {plan.name}
                </h3>
                <p className="text-muted-foreground text-sm mb-4">{plan.tagline}</p>
                <div className="flex items-end gap-1">
                  <span className="text-4xl font-black text-foreground">
                    ${plan.price}
                  </span>
                  <span className="text-muted-foreground text-sm mb-1">/month</span>
                </div>
                {plan.shorts && (
                  <p className="text-muted-foreground text-sm mt-1">
                    {plan.shorts} Shorts &bull; {plan.channels} channel
                    {(plan.channels ?? 0) > 1 ? "s" : ""}
                  </p>
                )}
                {!plan.shorts && (
                  <p className="text-muted-foreground text-sm mt-1">
                    Unlimited Shorts & channels
                  </p>
                )}
              </div>

              <Button
                variant={plan.popular ? "red" : "outline"}
                className={`w-full mb-6 ${
                  !plan.popular &&
                  "border-border text-foreground hover:border-[#E5192A]"
                }`}
                asChild
              >
                <Link href={plan.name === "Agency" ? "#" : "/register"}>
                  {plan.cta}
                </Link>
              </Button>

              <ul className="space-y-3">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm">
                    <Check className="w-4 h-4 text-[#E5192A] mt-0.5 flex-shrink-0" />
                    <span className="text-muted-foreground/70">{feature}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>

        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center text-muted-foreground text-sm mt-8"
        >
          All plans include a free trial with 3 Shorts. No credit card required.
        </motion.p>
      </div>
    </section>
  )
}
