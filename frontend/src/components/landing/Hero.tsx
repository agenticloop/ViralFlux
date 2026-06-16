"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { ArrowRight, Play, Zap, TrendingUp, DollarSign } from "lucide-react"
import { Button } from "@/components/ui/button"

const fadeUp = {
  initial: { opacity: 0, y: 30 },
  animate: { opacity: 1, y: 0 },
}

const stagger = {
  animate: { transition: { staggerChildren: 0.1 } },
}

function MockDashboard() {
  return (
    <motion.div
      initial={{ opacity: 0, x: 40, rotateY: -5 }}
      animate={{ opacity: 1, x: 0, rotateY: 0 }}
      transition={{ duration: 0.8, delay: 0.4, ease: "easeOut" }}
      className="relative w-full max-w-md mx-auto animate-float"
    >
      {/* Glow */}
      <div className="absolute inset-0 bg-[#E5192A]/10 rounded-2xl blur-3xl" />

      {/* Dashboard Card */}
      <div className="relative bg-background border border-border rounded-2xl overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
          <div className="w-3 h-3 rounded-full bg-[#E5192A]" />
          <div className="w-3 h-3 rounded-full bg-yellow-500" />
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span className="ml-2 text-foreground/70 text-xs">ViralFlux Dashboard</span>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-3 gap-3 p-4">
          {[
            { icon: TrendingUp, label: "Views", value: "2.1M" },
            { icon: Zap, label: "Videos", value: "847" },
            { icon: DollarSign, label: "Cost", value: "$68.90" },
          ].map(({ icon: Icon, label, value }) => (
            <div key={label} className="bg-card rounded-lg p-3 border border-border">
              <Icon className="w-3 h-3 text-[#E5192A] mb-1" />
              <div className="text-foreground text-sm font-bold">{value}</div>
              <div className="text-muted-foreground text-xs">{label}</div>
            </div>
          ))}
        </div>

        {/* Video Cards */}
        <div className="px-4 pb-4 space-y-2">
          {[
            { title: "The Haunted House", status: "posted", cost: "$0.08" },
            { title: "Dark Forest Secret", status: "generating", cost: "$0.09" },
            { title: "Unknown Caller", status: "queued", cost: "$0.07" },
          ].map((video) => (
            <div key={video.title} className="flex items-center gap-3 bg-card rounded-lg p-3 border border-border">
              <div className="w-10 h-10 bg-muted rounded-md flex items-center justify-center flex-shrink-0">
                <Play className="w-4 h-4 text-[#E5192A] fill-[#E5192A]" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-foreground text-xs font-medium truncate">{video.title}</div>
                <div className="text-muted-foreground text-xs">{video.cost}</div>
              </div>
              <span
                className={`text-xs px-2 py-0.5 rounded-full ${
                  video.status === "posted"
                    ? "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400"
                    : video.status === "generating"
                    ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-400"
                    : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
                }`}
              >
                {video.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  )
}

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center pt-16 bg-background overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-gradient-radial from-[#E5192A]/8 via-transparent to-transparent" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-[#E5192A]/5 rounded-full blur-[120px]" />

      {/* Floating particles — fixed positions avoid SSR/hydration mismatch */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {Array.from({ length: 20 }, (_, i) => ({
          left: `${(i * 17 + 7) % 100}%`,
          top: `${(i * 23 + 11) % 100}%`,
          delay: `${((i * 3) % 9) / 10}s`,
          duration: `${3 + (i % 4)}s`,
        })).map((p, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-[#E5192A]/20 rounded-full"
            style={{
              left: p.left,
              top: p.top,
              animationDelay: p.delay,
              animation: `float ${p.duration} ease-in-out infinite`,
            }}
          />
        ))}
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center py-16 lg:py-24">
          {/* Left: Copy */}
          <motion.div
            variants={stagger}
            initial="initial"
            animate="animate"
            className="text-center lg:text-left"
          >
            {/* Badge */}
            <motion.div variants={fadeUp} className="inline-flex items-center gap-2 mb-6">
              <span className="bg-[#E5192A]/10 border border-[#E5192A]/30 text-[#E5192A] text-xs font-semibold px-3 py-1 rounded-full">
                AI-Powered Automation
              </span>
            </motion.div>

            {/* Headline */}
            <motion.h1
              variants={fadeUp}
              className="text-4xl sm:text-5xl lg:text-6xl font-black text-foreground leading-[1.05] tracking-tight mb-6"
            >
              Automate Your{" "}
              <span className="text-gradient-red">YouTube Shorts</span>{" "}
              Empire.
            </motion.h1>

            {/* Subline */}
            <motion.p
              variants={fadeUp}
              className="text-lg sm:text-xl text-muted-foreground leading-relaxed mb-8 max-w-lg mx-auto lg:mx-0"
            >
              AI-powered story generation &rarr; auto voice &rarr; auto post.
              <br />
              <span className="text-foreground font-semibold">
                Under $0.10 per video.
              </span>{" "}
              No video skills required.
            </motion.p>

            {/* CTAs */}
            <motion.div
              variants={fadeUp}
              className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start"
            >
              <Button variant="red" size="lg" asChild className="text-base px-8">
                <Link href="/register" className="flex items-center gap-2">
                  Start Free — 30 Credits
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </Button>
              <Button
                variant="outline"
                size="lg"
                asChild
                className="text-base px-8 border-border text-foreground hover:border-[#E5192A]"
              >
                <Link href="#how-it-works" className="flex items-center gap-2">
                  <Play className="w-4 h-4" />
                  See How It Works
                </Link>
              </Button>
            </motion.div>

            {/* Social Proof Micro */}
            <motion.p variants={fadeUp} className="mt-6 text-muted-foreground text-sm">
              Trusted by{" "}
              <span className="text-foreground">847+ channels</span> &bull;{" "}
              <span className="text-foreground">12,450+ Shorts</span> generated
            </motion.p>
          </motion.div>

          {/* Right: Dashboard Mockup */}
          <div className="hidden lg:block">
            <MockDashboard />
          </div>
        </div>
      </div>
    </section>
  )
}
