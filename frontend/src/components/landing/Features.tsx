"use client"

import { motion } from "framer-motion"
import {
  LayoutDashboard,
  Brain,
  Youtube,
  TrendingUp,
  DollarSign,
  BarChart3,
} from "lucide-react"

const features = [
  {
    icon: LayoutDashboard,
    title: "Multi-Channel Management",
    description:
      "Run multiple YouTube channels from one dashboard. Set unique formats, voices, and schedules per channel.",
    color: "text-purple-400",
    bg: "bg-purple-900/10 border-purple-900/20",
  },
  {
    icon: Brain,
    title: "AI Story Engine",
    description:
      "Powered by Google Gemini. Generates hooks, story arcs, and endings optimized for Shorts retention.",
    color: "text-blue-400",
    bg: "bg-blue-900/10 border-blue-900/20",
  },
  {
    icon: Youtube,
    title: "Auto YouTube Posting",
    description:
      "Direct OAuth integration. Videos upload with full SEO metadata — title, description, tags, thumbnail.",
    color: "text-red-400",
    bg: "bg-red-900/10 border-red-900/20",
  },
  {
    icon: TrendingUp,
    title: "Trend Detection",
    description:
      "Scans Reddit, Twitter, and viral content daily to surface the highest-potential topics for your niche.",
    color: "text-orange-400",
    bg: "bg-orange-900/10 border-orange-900/20",
  },
  {
    icon: DollarSign,
    title: "Cost Tracking",
    description:
      "See exactly what each Short costs — down to the cent. Average cost under $0.10. Budget alerts built in.",
    color: "text-green-400",
    bg: "bg-green-900/10 border-green-900/20",
  },
  {
    icon: BarChart3,
    title: "Full Analytics",
    description:
      "Views, CTR, retention, and cost-per-view across all channels. Know what's working and double down.",
    color: "text-yellow-400",
    bg: "bg-yellow-900/10 border-yellow-900/20",
  },
]

export default function Features() {
  return (
    <section id="features" className="py-20 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <span className="text-[#E5192A] text-sm font-semibold uppercase tracking-wider mb-3 block">
            Features
          </span>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-foreground mb-4">
            Everything You Need to{" "}
            <span className="text-gradient-red">Scale</span>
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            A complete automation stack for serious YouTube Shorts creators.
          </p>
        </motion.div>

        {/* Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, i) => {
            const Icon = feature.icon
            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className={`p-6 rounded-xl border ${feature.bg} hover:border-opacity-60 transition-all duration-300 group cursor-default`}
              >
                <div className="mb-4">
                  <div
                    className={`w-10 h-10 rounded-lg bg-background flex items-center justify-center mb-4`}
                  >
                    <Icon className={`w-5 h-5 ${feature.color}`} />
                  </div>
                  <h3 className="text-foreground font-bold text-lg mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-muted-foreground text-sm leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
