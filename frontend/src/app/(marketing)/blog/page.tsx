import type { Metadata } from "next"
import Link from "next/link"
import { Clock, Tag } from "lucide-react"

export const metadata: Metadata = {
  title: "Blog",
  description:
    "Creator resources, automation guides, and YouTube Shorts strategy from the ViralFlux team.",
}

const staticPosts = [
  {
    slug: "how-to-grow-youtube-shorts-2024",
    title: "How to Grow to 100K Subscribers Using YouTube Shorts in 2024",
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
  {
    slug: "elevenlabs-vs-openai-voices-for-youtube",
    title: "ElevenLabs vs OpenAI Voices for YouTube Shorts: Which Wins?",
    excerpt:
      "We tested both voice providers across 200 Shorts and tracked retention, comments, and subscriber growth. Here are the results.",
    tags: ["Tools", "Voice"],
    readingTime: 7,
    date: "May 22, 2026",
  },
  {
    slug: "youtube-shorts-algorithm-2024",
    title: "The YouTube Shorts Algorithm in 2024: What Actually Works",
    excerpt:
      "Everything we know about how the Shorts algorithm distributes content and the specific signals that trigger viral spread.",
    tags: ["Algorithm", "Strategy"],
    readingTime: 10,
    date: "May 15, 2026",
  },
  {
    slug: "automating-multiple-youtube-channels",
    title: "Managing 5+ YouTube Channels With One Tool: The Agency Playbook",
    excerpt:
      "How agencies and serious creators are managing multiple themed channels, scaling content output, and tracking ROI with ViralFlux.",
    tags: ["Agency", "Scale"],
    readingTime: 9,
    date: "May 8, 2026",
  },
]

export default function BlogPage() {
  return (
    <div className="bg-[#0A0A0A] min-h-screen pt-24 pb-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl sm:text-5xl font-black text-[#FAFAFA] mb-4">
            Creator Resources
          </h1>
          <p className="text-[#888888] text-lg max-w-xl mx-auto">
            Strategy guides, automation tips, and YouTube Shorts playbooks from
            the ViralFlux team.
          </p>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {staticPosts.map((post) => (
            <article key={post.slug} className="group">
              <Link href={`/blog/${post.slug}`}>
                <div className="bg-[#111111] border border-[#222222] rounded-xl p-6 hover:border-[#E5192A]/40 transition-all duration-300 h-full flex flex-col">
                  {/* Tags */}
                  <div className="flex gap-2 mb-4">
                    {post.tags.map((tag) => (
                      <span
                        key={tag}
                        className="text-xs text-[#E5192A] bg-[#E5192A]/10 px-2 py-0.5 rounded-full flex items-center gap-1"
                      >
                        <Tag className="w-2.5 h-2.5" />
                        {tag}
                      </span>
                    ))}
                  </div>

                  {/* Title */}
                  <h2 className="text-[#FAFAFA] font-bold text-lg leading-tight mb-3 group-hover:text-[#E5192A] transition-colors flex-1">
                    {post.title}
                  </h2>

                  {/* Excerpt */}
                  <p className="text-[#666666] text-sm leading-relaxed mb-4">
                    {post.excerpt}
                  </p>

                  {/* Meta */}
                  <div className="flex items-center gap-3 text-xs text-[#555555]">
                    <Clock className="w-3 h-3" />
                    <span>{post.readingTime} min read</span>
                    <span>&bull;</span>
                    <span>{post.date}</span>
                  </div>
                </div>
              </Link>
            </article>
          ))}
        </div>
      </div>
    </div>
  )
}
