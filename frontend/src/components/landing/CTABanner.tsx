"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { ArrowRight, Zap } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function CTABanner() {
  return (
    <section className="py-20 bg-[#0F0F0F]">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="relative rounded-2xl overflow-hidden"
        >
          {/* Red gradient background */}
          <div className="absolute inset-0 bg-gradient-to-br from-[#E5192A] via-[#C01020] to-[#8B0010]" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />

          {/* Noise texture */}
          <div className="absolute inset-0 opacity-10 noise-bg" />

          {/* Glow effects */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/5 rounded-full blur-2xl" />

          {/* Content */}
          <div className="relative px-8 py-14 sm:px-14 text-center">
            <div className="flex items-center justify-center mb-4">
              <Zap className="w-8 h-8 text-white fill-white animate-pulse" />
            </div>

            <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-white mb-4 leading-tight">
              Start Automating Today
            </h2>
            <p className="text-white/80 text-lg mb-8 max-w-xl mx-auto">
              Your first 3 Shorts are completely free. No credit card. No setup
              fees. Just results.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                size="lg"
                asChild
                className="bg-white text-[#E5192A] hover:bg-white/90 font-bold text-base px-8 shadow-xl"
              >
                <Link href="/register" className="flex items-center gap-2">
                  Get Started Free
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </Button>
              <Button
                size="lg"
                variant="outline"
                asChild
                className="border-white/40 text-white hover:bg-white/10 text-base px-8"
              >
                <Link href="/pricing">View Pricing</Link>
              </Button>
            </div>

            <p className="text-white/50 text-sm mt-6">
              Join 847+ channels already automating with ViralFlux
            </p>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
