"use client"

import { motion } from "framer-motion"
import { Bot, PenLine, Video, Upload } from "lucide-react"

const steps = [
  {
    icon: Bot,
    emoji: "🤖",
    step: "01",
    title: "AI Picks Topic",
    description:
      "Our AI analyzes viral patterns, niche signals, and trending topics to pick a winning concept automatically — or you can specify one.",
    color: "text-purple-600 dark:text-purple-400",
    bg: "bg-purple-50 border-purple-200 dark:bg-purple-900/20 dark:border-purple-800/30",
  },
  {
    icon: PenLine,
    emoji: "✍️",
    step: "02",
    title: "Script Written",
    description:
      "Gemini AI crafts a suspense-filled 60-second story with a powerful hook designed for maximum viewer retention.",
    color: "text-blue-600 dark:text-blue-400",
    bg: "bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800/30",
  },
  {
    icon: Video,
    emoji: "🎬",
    step: "03",
    title: "Video Built",
    description:
      "ElevenLabs voice narration + matching visuals + auto-generated captions + background music — fully assembled in minutes.",
    color: "text-amber-600 dark:text-yellow-400",
    bg: "bg-amber-50 border-amber-200 dark:bg-yellow-900/20 dark:border-yellow-800/30",
  },
  {
    icon: Upload,
    emoji: "📤",
    step: "04",
    title: "Posted to YouTube",
    description:
      "Your Short goes live with optimized title, description, and tags. Scheduled for peak engagement times automatically.",
    color: "text-green-600 dark:text-green-400",
    bg: "bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800/30",
  },
]

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-20 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <span className="text-[#E5192A] text-sm font-semibold uppercase tracking-wider mb-3 block">
            How It Works
          </span>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-foreground mb-4">
            From Zero to Posted in{" "}
            <span className="text-gradient-red">Minutes</span>
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Four automated steps. Zero effort on your end.
          </p>
        </motion.div>

        {/* Steps */}
        <div className="relative">
          {/* Connecting Line */}
          <div className="hidden lg:block absolute top-16 left-[12.5%] right-[12.5%] h-0.5 bg-gradient-to-r from-transparent via-[#E5192A]/30 to-transparent" />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {steps.map((step, i) => {
              const Icon = step.icon
              return (
                <motion.div
                  key={step.step}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: i * 0.15 }}
                  className="relative text-center group"
                >
                  {/* Step Number */}
                  <div className="relative mx-auto mb-6 w-16 h-16">
                    <div
                      className={`w-16 h-16 rounded-2xl border flex items-center justify-center ${step.bg} group-hover:scale-110 transition-transform duration-300`}
                    >
                      <Icon className={`w-7 h-7 ${step.color}`} />
                    </div>
                    <div className="absolute -top-2 -right-2 w-6 h-6 bg-[#E5192A] rounded-full flex items-center justify-center text-white text-xs font-bold">
                      {i + 1}
                    </div>
                  </div>

                  <h3 className="text-foreground font-bold text-lg mb-3">
                    {step.emoji} {step.title}
                  </h3>
                  <p className="text-muted-foreground text-sm leading-relaxed">
                    {step.description}
                  </p>
                </motion.div>
              )
            })}
          </div>
        </div>
      </div>
    </section>
  )
}
