import type { Metadata } from "next"
import Link from "next/link"
import { ArrowLeft, Clock, Tag } from "lucide-react"
import { Button } from "@/components/ui/button"

// Static post content map for the placeholder posts
const postsContent: Record<
  string,
  {
    title: string
    excerpt: string
    tags: string[]
    readingTime: number
    date: string
    author: string
    content: string
  }
> = {
  "how-to-grow-youtube-shorts-2024": {
    title: "How to Grow to 100K Subscribers Using YouTube Shorts in 2024",
    excerpt:
      "Discover the exact automation strategy that helped creators grow from 0 to 100K subscribers posting nothing but AI-generated Shorts.",
    tags: ["Growth", "Strategy"],
    readingTime: 8,
    date: "Jun 5, 2026",
    author: "ViralFlux Team",
    content: `
## The YouTube Shorts Gold Rush Is Still Happening

In 2024, YouTube Shorts are getting billions of daily views. The platform is actively pushing Short content to new audiences — and creators who post consistently are getting massive organic reach.

The problem? Most creators don't have time to produce a Short every day.

That's where automation changes everything.

## The 3-Video-Per-Day Strategy

The most successful channels we work with post 3 Shorts per day across 1-3 channels. That's 90+ Shorts per month — and with AI automation, it costs less than $10/month in AI API fees.

Here's what those creators do differently:

1. **They pick a tight niche.** Horror stories. True crime. Motivational quotes. Whatever the niche, they stick to it.
2. **They automate end-to-end.** Topic → script → voice → video → post. Zero manual work per Short.
3. **They optimize the hook.** The first 2 seconds are everything. ViralFlux's AI has been trained on thousands of viral hooks.

## The Math

- 90 Shorts/month × $0.08 average cost = **$7.20/month in AI costs**
- Average views per Short: **8,000–15,000** on a new channel
- At 15K views × 90 Shorts = **1.35M views/month**

That's growth that would take a manual creator years to achieve.

## Getting Started

1. Create a ViralFlux account (3 free Shorts to start)
2. Connect your YouTube channel via OAuth
3. Enable the Horror Story format
4. Set your schedule to 3 posts/day
5. Watch the views roll in

The channels that grow fastest are the ones that stay consistent for 60+ days.
    `,
  },
  "best-horror-story-hooks-for-shorts": {
    title: "The 7 Horror Story Hook Templates That Get 80%+ Retention",
    excerpt:
      "After analyzing 10,000+ horror Shorts, we identified the exact hook patterns that keep viewers watching until the end.",
    tags: ["Content", "Horror"],
    readingTime: 6,
    date: "Jun 1, 2026",
    author: "ViralFlux Team",
    content: `
## Why the First 2 Seconds Are Everything

YouTube's algorithm ranks Shorts heavily on average view duration. If your first 2 seconds don't hook viewers, the algorithm buries your video.

After analyzing 10,000+ horror Shorts, we've identified the 7 hooks that consistently achieve 80%+ retention.

## Hook #1: The Impossible Witness

*"I watched my own funeral last night. Here's what I saw."*

Impossible scenarios force the viewer to ask "How is that possible?" — creating immediate cognitive engagement.

## Hook #2: The Direct Address Escalation

*"If you're reading this in bed at 2am, turn on a light. What I'm about to tell you is real."*

Breaking the fourth wall creates personal tension. The viewer feels addressed directly.

## Hook #3: The Rule That Must Not Be Broken

*"There's a rule in our town: never look out the window after midnight. My brother forgot last Wednesday."*

Rules with consequences create automatic dread. The viewer waits for the rule to be broken.

## Hook #4: The Unreliable Narrator Warning

*"I know how this sounds. I know you won't believe me. But I have proof."*

Pre-empting disbelief paradoxically increases belief. The admission of implausibility builds credibility.

## Hook #5: The Countdown

*"In three days, something is going to happen to me. I want this documented."*

Deadlines create urgency. The viewer stays to see if the deadline is met.

## Hook #6: The Familiar Made Wrong

*"My neighbor has lived alone for 20 years. Yesterday I heard children laughing inside her house."*

The uncanny — something normal made slightly wrong — is the most powerful horror trigger.

## Hook #7: The Found Evidence

*"I found a journal in my grandmother's attic. The last entry was written 40 years after she died."*

Physical evidence (journals, recordings, photos) implies verifiability, making the story feel real.

## How ViralFlux Uses These Hooks

Our AI story engine has been trained on all 7 hook archetypes and automatically selects the optimal one based on topic category and trending patterns.
    `,
  },
}

type Params = { slug: string }

export async function generateMetadata({
  params,
}: {
  params: Params
}): Promise<Metadata> {
  const post = postsContent[params.slug]
  if (!post) {
    return { title: "Post Not Found" }
  }
  return {
    title: post.title,
    description: post.excerpt,
  }
}

export default function BlogPostPage({ params }: { params: Params }) {
  const post = postsContent[params.slug]

  if (!post) {
    return (
      <div className="bg-background min-h-screen pt-24 pb-16 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-foreground mb-4">
            Post Not Found
          </h1>
          <p className="text-muted-foreground mb-6">
            This post doesn&apos;t exist or hasn&apos;t been published yet.
          </p>
          <Button variant="red" asChild>
            <Link href="/blog">Back to Blog</Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-background min-h-screen pt-24 pb-16">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Back */}
        <Link
          href="/blog"
          className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground text-sm mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Blog
        </Link>

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
        <h1 className="text-3xl sm:text-4xl font-black text-foreground leading-tight mb-4">
          {post.title}
        </h1>

        {/* Meta */}
        <div className="flex items-center gap-4 text-sm text-muted-foreground mb-8 pb-8 border-b border-border">
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" />
            <span>{post.readingTime} min read</span>
          </div>
          <span>&bull;</span>
          <span>{post.date}</span>
          <span>&bull;</span>
          <span>By {post.author}</span>
        </div>

        {/* Content */}
        <div className="prose prose-invert prose-sm max-w-none">
          {post.content.split("\n\n").map((block, i) => {
            if (block.startsWith("## ")) {
              return (
                <h2
                  key={i}
                  className="text-xl font-bold text-foreground mt-8 mb-4"
                >
                  {block.slice(3)}
                </h2>
              )
            }
            if (block.startsWith("*")) {
              return (
                <blockquote
                  key={i}
                  className="border-l-4 border-[#E5192A] pl-4 italic text-muted-foreground/70 my-4"
                >
                  {block.replace(/\*/g, "")}
                </blockquote>
              )
            }
            return (
              <p key={i} className="text-muted-foreground/70 leading-relaxed mb-4">
                {block.split(/(\*\*[^*]+\*\*)/).map((part, j) => {
                  if (part.startsWith("**") && part.endsWith("**")) {
                    return (
                      <strong key={j} className="text-foreground font-semibold">
                        {part.slice(2, -2)}
                      </strong>
                    )
                  }
                  return part
                })}
              </p>
            )
          })}
        </div>

        {/* CTA */}
        <div className="mt-12 pt-8 border-t border-border bg-card rounded-xl p-8 text-center">
          <h3 className="text-foreground font-bold text-xl mb-2">
            Ready to automate your Shorts?
          </h3>
          <p className="text-muted-foreground text-sm mb-4">
            Start with 3 free Shorts — no credit card required.
          </p>
          <Button variant="red" asChild>
            <Link href="/register">Get Started Free</Link>
          </Button>
        </div>
      </div>
    </div>
  )
}
