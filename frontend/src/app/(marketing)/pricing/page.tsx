import type { Metadata } from "next"
import Link from "next/link"
import { Check, X } from "lucide-react"
import { Button } from "@/components/ui/button"

export const metadata: Metadata = {
  title: "Pricing",
  description:
    "Simple, transparent pricing for YouTube Shorts automation. Start free with 3 Shorts.",
}

const plans = [
  {
    name: "Starter",
    price: 29,
    tagline: "Perfect for solo creators",
    shorts: 20,
    channels: 1,
    features: {
      "Shorts per month": "20",
      "YouTube channels": "1",
      "All active formats": true,
      "ElevenLabs voice": true,
      "OpenAI voice": false,
      "Auto YouTube posting": true,
      "Approval workflow": false,
      "Trend detection AI": false,
      "Advanced analytics": false,
      "API access": false,
      "Priority support": false,
    },
    cta: "Start Free Trial",
    ctaHref: "/register",
    popular: false,
  },
  {
    name: "Creator",
    price: 79,
    tagline: "For serious content creators",
    shorts: 100,
    channels: 5,
    features: {
      "Shorts per month": "100",
      "YouTube channels": "5",
      "All active formats": true,
      "ElevenLabs voice": true,
      "OpenAI voice": true,
      "Auto YouTube posting": true,
      "Approval workflow": true,
      "Trend detection AI": true,
      "Advanced analytics": true,
      "API access": false,
      "Priority support": true,
    },
    cta: "Start Free Trial",
    ctaHref: "/register",
    popular: true,
  },
  {
    name: "Agency",
    price: 199,
    tagline: "For agencies & power users",
    shorts: null,
    channels: null,
    features: {
      "Shorts per month": "Unlimited",
      "YouTube channels": "Unlimited",
      "All active formats": true,
      "ElevenLabs voice": true,
      "OpenAI voice": true,
      "Auto YouTube posting": true,
      "Approval workflow": true,
      "Trend detection AI": true,
      "Advanced analytics": true,
      "API access": true,
      "Priority support": true,
    },
    cta: "Contact Sales",
    ctaHref: "#",
    popular: false,
  },
]

const featureKeys = [
  "Shorts per month",
  "YouTube channels",
  "All active formats",
  "ElevenLabs voice",
  "OpenAI voice",
  "Auto YouTube posting",
  "Approval workflow",
  "Trend detection AI",
  "Advanced analytics",
  "API access",
  "Priority support",
]

const faqs = [
  {
    q: "What's included in the free trial?",
    a: "Every account starts with 3 free Shorts. No credit card required. Full access to the Horror Story format, auto YouTube posting, and analytics.",
  },
  {
    q: "How much does each Short actually cost?",
    a: "The AI generation cost (Gemini) is roughly $0.02–$0.04 per Short. Voice generation (ElevenLabs) adds ~$0.03–$0.05. Total per Short is typically $0.05–$0.09.",
  },
  {
    q: "Can I upgrade or downgrade my plan?",
    a: "Yes, anytime. Upgrades take effect immediately. Downgrades take effect at the end of your billing cycle.",
  },
  {
    q: "Do I need a YouTube channel already?",
    a: "Yes, you need at least one YouTube channel. We connect via OAuth and post on your behalf. We never ask for your password.",
  },
  {
    q: "What happens if I exceed my monthly Shorts limit?",
    a: "Video generation will pause. You'll get an email notification and can upgrade to continue or wait for the next billing cycle.",
  },
]

export default function PricingPage() {
  return (
    <div className="bg-[#0A0A0A] min-h-screen pt-24 pb-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-4xl sm:text-5xl font-black text-[#FAFAFA] mb-4">
            Simple, Transparent Pricing
          </h1>
          <p className="text-[#888888] text-lg max-w-xl mx-auto">
            Start with 3 free Shorts. Upgrade when you&apos;re ready.
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto mb-20">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative rounded-2xl p-8 border ${
                plan.popular
                  ? "border-[#E5192A] bg-gradient-to-b from-[#E5192A]/5 to-[#111111]"
                  : "border-[#222222] bg-[#111111]"
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                  <span className="bg-[#E5192A] text-white text-xs font-bold px-3 py-1 rounded-full">
                    MOST POPULAR
                  </span>
                </div>
              )}

              <h2 className="text-[#FAFAFA] font-bold text-xl mb-1">
                {plan.name}
              </h2>
              <p className="text-[#666666] text-sm mb-4">{plan.tagline}</p>

              <div className="flex items-end gap-1 mb-6">
                <span className="text-5xl font-black text-[#FAFAFA]">
                  ${plan.price}
                </span>
                <span className="text-[#666666] text-sm mb-1">/month</span>
              </div>

              <Button
                variant={plan.popular ? "red" : "outline"}
                className={`w-full mb-6 ${
                  !plan.popular &&
                  "border-[#333333] text-[#FAFAFA] hover:border-[#E5192A]"
                }`}
                asChild
              >
                <Link href={plan.ctaHref}>{plan.cta}</Link>
              </Button>

              <ul className="space-y-3">
                {Object.entries(plan.features)
                  .slice(0, 7)
                  .map(([key, val]) => (
                    <li key={key} className="flex items-center gap-2 text-sm">
                      {val === false ? (
                        <X className="w-4 h-4 text-[#444444] flex-shrink-0" />
                      ) : (
                        <Check className="w-4 h-4 text-[#E5192A] flex-shrink-0" />
                      )}
                      <span
                        className={
                          val === false ? "text-[#444444]" : "text-[#CCCCCC]"
                        }
                      >
                        {typeof val === "string" ? val + " " : ""}
                        {key}
                      </span>
                    </li>
                  ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Feature Comparison Table */}
        <div className="max-w-5xl mx-auto mb-20">
          <h2 className="text-2xl font-bold text-[#FAFAFA] mb-8 text-center">
            Full Feature Comparison
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className="text-left text-[#888888] text-sm font-medium py-3 px-4 w-1/2">
                    Feature
                  </th>
                  {plans.map((plan) => (
                    <th
                      key={plan.name}
                      className={`text-center text-sm font-bold py-3 px-4 ${
                        plan.popular ? "text-[#E5192A]" : "text-[#FAFAFA]"
                      }`}
                    >
                      {plan.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {featureKeys.map((key, i) => (
                  <tr
                    key={key}
                    className={`border-t border-[#1A1A1A] ${
                      i % 2 === 0 ? "bg-transparent" : "bg-[#0F0F0F]"
                    }`}
                  >
                    <td className="text-[#CCCCCC] text-sm py-3 px-4">{key}</td>
                    {plans.map((plan) => {
                      const val =
                        plan.features[key as keyof typeof plan.features]
                      return (
                        <td
                          key={plan.name}
                          className="text-center py-3 px-4"
                        >
                          {val === true ? (
                            <Check className="w-4 h-4 text-[#E5192A] mx-auto" />
                          ) : val === false ? (
                            <X className="w-4 h-4 text-[#444444] mx-auto" />
                          ) : (
                            <span className="text-[#FAFAFA] text-sm font-medium">
                              {val}
                            </span>
                          )}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* FAQ */}
        <div className="max-w-3xl mx-auto mb-20">
          <h2 className="text-2xl font-bold text-[#FAFAFA] mb-8 text-center">
            Frequently Asked Questions
          </h2>
          <div className="space-y-4">
            {faqs.map((faq) => (
              <div
                key={faq.q}
                className="bg-[#111111] border border-[#222222] rounded-xl p-6"
              >
                <h3 className="text-[#FAFAFA] font-semibold mb-2">{faq.q}</h3>
                <p className="text-[#888888] text-sm leading-relaxed">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="text-center">
          <h2 className="text-2xl font-bold text-[#FAFAFA] mb-4">
            Ready to start automating?
          </h2>
          <p className="text-[#888888] mb-6">
            3 free Shorts. No credit card. Set up in under 5 minutes.
          </p>
          <Button variant="red" size="lg" asChild className="px-10">
            <Link href="/register">Get Started Free</Link>
          </Button>
        </div>
      </div>
    </div>
  )
}
