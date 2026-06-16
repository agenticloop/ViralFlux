"use client"

import { motion } from "framer-motion"
import { Ghost, Brain, Sparkles } from "lucide-react"

const genres = [
  {
    icon: Ghost,
    value: "horror",
    name: "Horror",
    emoji: "🕯️",
    description:
      "Terrifying narrated short stories with eerie AI imagery and a slow-build dread that keeps watch-time high.",
    badge: "AVAILABLE",
    badgeColor:
      "bg-green-100 text-green-700 border-green-200 dark:bg-green-900/40 dark:text-green-400 dark:border-green-800/40",
    iconBg:
      "bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-900/30",
    iconColor: "text-red-600 dark:text-red-400",
    tags: ["Suspense", "Ghost stories", "True scary"],
    active: true,
  },
  {
    icon: Brain,
    value: "brainrot",
    name: "Brainrot",
    emoji: "🧠",
    description:
      "Chaotic Gen-Z narration layered over satisfying CC0 loops — engineered for the explore page and endless replays.",
    badge: "AVAILABLE",
    badgeColor:
      "bg-green-100 text-green-700 border-green-200 dark:bg-green-900/40 dark:text-green-400 dark:border-green-800/40",
    iconBg:
      "bg-orange-50 border-orange-200 dark:bg-orange-900/10 dark:border-orange-900/20",
    iconColor: "text-orange-600 dark:text-orange-400",
    tags: ["Gen-Z", "Satisfying", "Viral"],
    active: true,
  },
  {
    icon: Sparkles,
    value: "custom",
    name: "Custom",
    emoji: "✨",
    description:
      "Bring your own genre prompt and voice. Define a niche once and let ViralFlux churn it out on schedule.",
    badge: "PRO & AGENCY",
    badgeColor:
      "bg-[#E5192A]/10 text-[#E5192A] border-[#E5192A]/30",
    iconBg:
      "bg-purple-50 border-purple-200 dark:bg-purple-900/10 dark:border-purple-900/20",
    iconColor: "text-purple-600 dark:text-purple-400",
    tags: ["Your niche", "Your voice", "Saved presets"],
    active: true,
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
            Genres
          </span>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-foreground mb-4">
            Two battle-tested genres.{" "}
            <span className="text-gradient-red">One custom slot.</span>
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Pick a genre per channel, set a weekly seed prompt, and let the
            pipeline do the rest.
          </p>
        </motion.div>

        {/* Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {genres.map((genre, i) => {
            const Icon = genre.icon
            return (
              <motion.div
                key={genre.value}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className="p-6 rounded-xl border border-border bg-background transition-all duration-300 hover:border-[#E5192A]/40 hover:shadow-xl hover:shadow-red-900/10"
              >
                <div className="flex items-start justify-between mb-4">
                  <div
                    className={`w-11 h-11 rounded-lg border flex items-center justify-center text-xl ${genre.iconBg}`}
                  >
                    <Icon className={`w-5 h-5 ${genre.iconColor}`} />
                  </div>
                  <span
                    className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${genre.badgeColor}`}
                  >
                    {genre.badge}
                  </span>
                </div>

                <h3 className="text-foreground font-bold text-lg mb-2 flex items-center gap-2">
                  <span aria-hidden>{genre.emoji}</span>
                  {genre.name}
                </h3>
                <p className="text-muted-foreground text-sm leading-relaxed mb-4">
                  {genre.description}
                </p>

                <div className="flex flex-wrap gap-2">
                  {genre.tags.map((tag) => (
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
