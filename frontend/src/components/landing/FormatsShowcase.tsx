"use client"

import { motion } from "framer-motion"
import { Ghost, Flame, List, Quote, Film } from "lucide-react"

const formats = [
  {
    icon: Ghost,
    slug: "horror_story",
    name: "Horror Story",
    description:
      "60-second terrifying narratives with building tension and shocking endings. The highest-performing format.",
    isActive: true,
    badge: "ACTIVE",
    badgeColor: "bg-green-100 text-green-700 border-green-200 dark:bg-green-900/40 dark:text-green-400 dark:border-green-800/40",
    iconBg: "bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-900/30",
    iconColor: "text-red-600 dark:text-red-400",
    glow: "hover:shadow-red-900/20",
    tags: ["Horror", "Suspense", "Ghost Stories"],
  },
  {
    icon: Flame,
    slug: "brainrot_dialogue",
    name: "Brainrot Dialogue",
    description:
      "Chaotic Gen Z style conversations and absurd humor designed to go viral on the explore page.",
    isActive: false,
    badge: "COMING SOON",
    badgeColor: "bg-zinc-100 text-zinc-600 border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700",
    iconBg: "bg-orange-50 border-orange-200 dark:bg-orange-900/10 dark:border-orange-900/20",
    iconColor: "text-orange-600 dark:text-orange-400",
    tags: ["Humor", "Gen Z", "Trending"],
  },
  {
    icon: List,
    slug: "ranking_listicle",
    name: "Ranking / Listicle",
    description:
      "Top 5, Top 10 countdowns across any niche. Highly shareable, great for comments and engagement.",
    isActive: false,
    badge: "COMING SOON",
    badgeColor: "bg-zinc-100 text-zinc-600 border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700",
    iconBg: "bg-blue-50 border-blue-200 dark:bg-blue-900/10 dark:border-blue-900/20",
    iconColor: "text-blue-600 dark:text-blue-400",
    tags: ["Lists", "Rankings", "Facts"],
  },
  {
    icon: Quote,
    slug: "motivational_quotes",
    name: "Motivational Quotes",
    description:
      "Powerful quote compilations with cinematic visuals. Perfect for lifestyle and self-improvement channels.",
    isActive: false,
    badge: "COMING SOON",
    badgeColor: "bg-zinc-100 text-zinc-600 border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700",
    iconBg: "bg-yellow-50 border-yellow-200 dark:bg-yellow-900/10 dark:border-yellow-900/20",
    iconColor: "text-amber-600 dark:text-yellow-400",
    tags: ["Motivation", "Quotes", "Lifestyle"],
  },
  {
    icon: Film,
    slug: "clip_stitch",
    name: "Clip Stitch",
    description:
      "AI-curated clip compilations stitched together with commentary. Perfect for reaction and commentary channels.",
    isActive: false,
    badge: "COMING SOON",
    badgeColor: "bg-zinc-100 text-zinc-600 border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700",
    iconBg: "bg-purple-50 border-purple-200 dark:bg-purple-900/10 dark:border-purple-900/20",
    iconColor: "text-purple-600 dark:text-purple-400",
    tags: ["Clips", "Compilation", "Reactions"],
  },
]

export default function FormatsShowcase() {
  return (
    <section className="py-20 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <span className="text-[#E5192A] text-sm font-semibold uppercase tracking-wider mb-3 block">
            Content Formats
          </span>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-foreground mb-4">
            Start with Horror.{" "}
            <span className="text-gradient-red">More Coming.</span>
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            We&apos;re launching with the highest-converting format first and
            expanding fast.
          </p>
        </motion.div>

        {/* Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {formats.map((format, i) => {
            const Icon = format.icon
            return (
              <motion.div
                key={format.slug}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className={`p-6 rounded-xl border border-border bg-background transition-all duration-300 ${
                  format.isActive
                    ? "border-[#E5192A]/30 hover:border-[#E5192A]/60 hover:shadow-xl hover:shadow-red-900/10"
                    : "opacity-60 hover:opacity-75"
                }`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div
                    className={`w-10 h-10 rounded-lg border flex items-center justify-center ${format.iconBg}`}
                  >
                    <Icon className={`w-5 h-5 ${format.iconColor}`} />
                  </div>
                  <span
                    className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${format.badgeColor}`}
                  >
                    {format.badge}
                  </span>
                </div>

                <h3 className="text-foreground font-bold text-lg mb-2">
                  {format.name}
                </h3>
                <p className="text-muted-foreground text-sm leading-relaxed mb-4">
                  {format.description}
                </p>

                <div className="flex flex-wrap gap-2">
                  {format.tags.map((tag) => (
                    <span
                      key={tag}
                      className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded-md"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
