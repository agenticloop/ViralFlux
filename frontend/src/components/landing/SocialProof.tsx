"use client"

import { useEffect, useRef, useState } from "react"
import { motion, useInView } from "framer-motion"

interface CounterProps {
  end: number
  suffix: string
  prefix?: string
  duration?: number
}

function AnimatedCounter({ end, suffix, prefix = "", duration = 2000 }: CounterProps) {
  const [count, setCount] = useState(0)
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true })

  useEffect(() => {
    if (!inView) return
    const startTime = performance.now()
    const animate = (currentTime: number) => {
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setCount(Math.floor(eased * end))
      if (progress < 1) requestAnimationFrame(animate)
    }
    requestAnimationFrame(animate)
  }, [inView, end, duration])

  return (
    <span ref={ref}>
      {prefix}
      {count.toLocaleString()}
      {suffix}
    </span>
  )
}

const stats = [
  {
    value: 12450,
    suffix: "+",
    label: "Shorts Generated",
    description: "AI-crafted stories published and growing",
  },
  {
    value: 847,
    suffix: "",
    label: "Channels Managed",
    description: "Creators automating their content strategy",
  },
  {
    value: 2.1,
    suffix: "M+",
    label: "Views Driven",
    description: "Organic views from automated content",
    isDecimal: true,
  },
]

export default function SocialProof() {
  return (
    <section className="py-16 bg-[#0A0A0A] border-y border-[#1A1A1A]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-12">
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className="text-center"
            >
              <div className="text-4xl md:text-5xl font-black text-[#FAFAFA] mb-2">
                {stat.isDecimal ? (
                  <motion.span
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    viewport={{ once: true }}
                    className="text-gradient-red"
                  >
                    {stat.value}M+
                  </motion.span>
                ) : (
                  <span className="text-gradient-red">
                    <AnimatedCounter
                      end={stat.value as number}
                      suffix={stat.suffix}
                      duration={2000}
                    />
                  </span>
                )}
              </div>
              <div className="text-[#FAFAFA] font-semibold text-lg mb-1">
                {stat.label}
              </div>
              <div className="text-[#666666] text-sm">{stat.description}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
