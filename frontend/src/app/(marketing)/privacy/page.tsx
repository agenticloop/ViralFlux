import type { Metadata } from "next"
import Link from "next/link"
import { ArrowLeft } from "lucide-react"

export const metadata: Metadata = {
  title: "Privacy Policy — ViralFlux",
  description: "How ViralFlux collects, uses, and protects your information.",
}

const sections = [
  {
    title: "Information We Collect",
    content: `We collect information you provide directly to us, including your name, email address, and payment information when you register for an account. We also collect information about how you use our service, including the channels you connect, videos generated, and feature usage patterns.

When you connect a YouTube channel, we request OAuth access limited to uploading videos and reading channel analytics. We never access your YouTube password.`,
  },
  {
    title: "How We Use Your Information",
    content: `We use the information we collect to:
• Provide, maintain, and improve our services
• Process transactions and send related information
• Generate AI content on your behalf based on your settings
• Upload videos to your connected YouTube channels
• Send you technical notices, security alerts, and support messages
• Analyze usage patterns to improve the product`,
  },
  {
    title: "AI-Generated Content",
    content: `ViralFlux uses third-party AI services (Google Gemini for scripts, ElevenLabs for voice synthesis) to generate scripts and content. Prompts sent to these services include your channel settings and niche preferences but do not include personal identifying information beyond what is necessary for generation. We do not use your content to train our own models.`,
  },
  {
    title: "Data Sharing",
    content: `We do not sell, trade, or rent your personal information to third parties. We share information only with:
• Service providers that help us deliver our service (cloud infrastructure, payment processors)
• Third-party AI providers for content generation (subject to their own privacy policies)
• Law enforcement when required by law

All service providers are contractually bound to protect your data.`,
  },
  {
    title: "Data Retention",
    content: `We retain your account information for as long as your account is active or as needed to provide services. Video generation logs are retained for 90 days. You may delete your account at any time from account settings, which removes all personally identifiable information within 30 days.`,
  },
  {
    title: "Security",
    content: `We implement industry-standard security measures including encrypted data transmission (TLS), encrypted credential storage, and regular security audits. Passwords are hashed and salted — we never store them in plain text. API keys for connected services are encrypted at rest.`,
  },
  {
    title: "Your Rights",
    content: `You have the right to:
• Access the personal data we hold about you
• Correct inaccurate data
• Request deletion of your data
• Export your data in a portable format
• Opt out of marketing communications at any time

To exercise these rights, contact us at privacy@skypulseforge.com`,
  },
  {
    title: "Cookies",
    content: `We use essential cookies to keep you logged in and maintain session state. We do not use tracking cookies for advertising. You can disable cookies in your browser settings, but this may affect service functionality.`,
  },
  {
    title: "Changes to This Policy",
    content: `We may update this Privacy Policy periodically. We will notify you of significant changes via email or a prominent notice in the application. Continued use after changes constitutes acceptance of the updated policy.`,
  },
]

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Back */}
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground text-sm mb-10 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to home
        </Link>

        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-black text-foreground mb-3">Privacy Policy</h1>
          <p className="text-muted-foreground">
            Last updated: June 2026 &bull; Effective: June 2026
          </p>
          <p className="text-muted-foreground mt-4 leading-relaxed">
            ViralFlux (&ldquo;we,&rdquo; &ldquo;our,&rdquo; or &ldquo;us&rdquo;) is committed to protecting your
            privacy. This policy explains what information we collect, how we use it, and
            your choices.
          </p>
        </div>

        {/* Sections */}
        <div className="space-y-10">
          {sections.map((section, i) => (
            <section key={section.title}>
              <h2 className="text-xl font-bold text-foreground mb-3 flex items-center gap-3">
                <span className="text-[#E5192A] text-sm font-mono">
                  {String(i + 1).padStart(2, "0")}
                </span>
                {section.title}
              </h2>
              <div className="text-muted-foreground leading-relaxed whitespace-pre-line border-l-2 border-border pl-5">
                {section.content}
              </div>
            </section>
          ))}
        </div>

        {/* Footer */}
        <div className="mt-16 pt-8 border-t border-border">
          <p className="text-muted-foreground text-sm">
            Questions about this policy?{" "}
            <a
              href="mailto:privacy@skypulseforge.com"
              className="text-[#E5192A] hover:underline"
            >
              privacy@skypulseforge.com
            </a>
          </p>
          <p className="text-muted-foreground text-sm mt-2">
            <Link href="/terms" className="hover:text-foreground transition-colors">
              Terms of Service
            </Link>{" "}
            &bull;{" "}
            <Link href="/" className="hover:text-foreground transition-colors">
              ViralFlux Home
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
