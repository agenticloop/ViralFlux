"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { ArrowRight, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"

const staticPosts = [
  {
    slug: "how-to-grow-youtube-shorts",
    title: "How to Grow to 100K Subscribers Using YouTube Shorts",
    excerpt:
      "Discover the exact automation strategy that helped creators grow from 0 to 100K subscribers posting nothing but AI-generated Shorts.",
    tags: ["Growth", "Strategy"],
    readingTime: 8,
    date: "Jun 5, 2026",
  },
  {
    slug: "best-horror-story-hooks-for-shorts",
    title: "The 7 Horror Story Hook Templates That Get 80%+ Retention",
    excerpt:
      "After analyzing 10,000+ horror Shorts, we identified the exact hook patterns that keep viewers watching until the end.",
    tags: ["Content", "Horror"],
    readingTime: 6,
    date: "Jun 1, 2026",
  },
  {
    slug: "youtube-shorts-cost-analysis",
    title: "Real Cost Analysis: How Much Does It Cost to Post 100 Shorts?",
    excerpt:
      "A transparent breakdown of AI generation costs, voice costs, and platform fees when running a high-volume Shorts channel.",
    tags: ["Finance", "Analytics"],
    readingTime: 5,
    date: "May 28, 2026",
  },
]

export default function BlogPreview() {
  return (
    <section className="py-20 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="flex items-end justify-between mb-12"
        >
          <div>
            <span className="text-[#E5192A] text-sm font-semibold uppercase tracking-wider mb-3 block">
              Blog
            </span>
            <h2 className="text-3xl sm:text-4xl font-black text-foreground">
              Creator Resources
            </h2>
          </div>
          <Button variant="ghost" asChild className="text-muted-foreground hover:text-foreground hidden sm:flex">
            <Link href="/blog" className="flex items-center gap-1">
              View All <ArrowRight className="w-4 h-4" />
            </Link>
          </Button>
        </motion.div>

        {/* Posts */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {staticPosts.map((post, i) => (
            <motion.article
              key={post.slug}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.1 }}
              className="group"
            >
              <Link href={`/blog/${post.slug}`}>
                <div className="bg-card border border-border rounded-xl p-6 hover:border-[#E5192A]/40 transition-all duration-300 h-full flex flex-col">
                  {/* Tags */}
                  <div className="flex gap-2 mb-4">
                    {post.tags.map((tag) => (
                      <span
                        key={tag}
                        className="text-xs text-[#E5192A] bg-[#E5192A]/10 px-2 py-0.5 rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>

                  {/* Title */}
                  <h3 className="text-foreground font-bold text-lg leading-tight mb-3 group-hover:text-[#E5192A] transition-colors flex-1">
                    {post.title}
                  </h3>

                  {/* Excerpt */}
                  <p className="text-muted-foreground text-sm leading-relaxed mb-4">
                    {post.excerpt}
                  </p>

                  {/* Meta */}
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <Clock className="w-3 h-3" />
                    <span>{post.readingTime} min read</span>
                    <span>&bull;</span>
                    <span>{post.date}</span>
                  </div>
                </div>
              </Link>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  )
}
