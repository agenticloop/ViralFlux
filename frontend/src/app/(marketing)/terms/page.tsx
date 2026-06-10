import type { Metadata } from "next"
import Link from "next/link"
import { ArrowLeft } from "lucide-react"

export const metadata: Metadata = {
  title: "Terms of Service — ViralFlux",
  description: "The terms governing your use of ViralFlux.",
}

const sections = [
  {
    title: "Acceptance of Terms",
    content: `By accessing or using ViralFlux ("Service"), you agree to be bound by these Terms of Service ("Terms"). If you do not agree, do not use the Service. These Terms apply to all users, including those who create accounts and use paid features.`,
  },
  {
    title: "Description of Service",
    content: `ViralFlux is an AI-powered content automation platform that generates YouTube Shorts scripts using AI models, converts scripts to audio using text-to-speech services, assembles video files, and uploads them to your connected YouTube channels according to your configured schedule and settings.`,
  },
  {
    title: "Account Registration",
    content: `You must create an account to use the Service. You are responsible for:
• Providing accurate and complete information
• Maintaining the security of your account credentials
• All activity that occurs under your account
• Notifying us immediately of any unauthorized access

You must be at least 13 years old (or the applicable minimum age in your jurisdiction) to use the Service.`,
  },
  {
    title: "YouTube Integration",
    content: `When you connect a YouTube channel, you grant ViralFlux OAuth access to upload videos and read analytics on your behalf. You remain solely responsible for all content uploaded to your channels through our Service. You must comply with YouTube's Terms of Service and Community Guidelines. We reserve the right to suspend integrations if we detect violations of YouTube policies.`,
  },
  {
    title: "Content and Conduct",
    content: `You agree not to use the Service to generate or distribute:
• Content that violates YouTube's Community Guidelines
• Spam, misleading, or deceptive content
• Content that infringes on third-party intellectual property rights
• Illegal content of any kind
• Content designed to harass, threaten, or harm others

You retain ownership of the content generated for your channels. By using the Service, you grant us a limited license to process and store your content solely to provide the Service.`,
  },
  {
    title: "Payment Terms",
    content: `Paid plans are billed monthly in advance. All fees are non-refundable except as required by law or at our sole discretion. We reserve the right to change pricing with 30 days' notice. Failure to pay will result in downgrade to the free tier. We use Stripe for payment processing — your payment details are never stored on our servers.`,
  },
  {
    title: "Free Tier and Trial",
    content: `New accounts receive 3 free video generations. After the free tier is exhausted, a paid subscription is required to continue generating videos. The free tier is subject to change or discontinuation at any time.`,
  },
  {
    title: "Service Availability",
    content: `We aim for high availability but do not guarantee uninterrupted service. We may perform maintenance, updates, or experience outages. We will provide advance notice of planned downtime where possible. We are not liable for losses caused by service interruptions.`,
  },
  {
    title: "Intellectual Property",
    content: `The ViralFlux platform, including its software, design, and branding, is owned by us and protected by intellectual property laws. You may not copy, modify, distribute, or reverse-engineer any part of the Service. AI-generated content created through the Service is owned by you, subject to the terms of the underlying AI providers (Google Gemini, OpenAI).`,
  },
  {
    title: "Limitation of Liability",
    content: `To the fullest extent permitted by law, ViralFlux shall not be liable for any indirect, incidental, special, consequential, or punitive damages arising from your use of the Service. Our total liability shall not exceed the amount paid by you in the 12 months preceding the claim. Some jurisdictions do not allow limitation of liability, so these limits may not apply to you.`,
  },
  {
    title: "Termination",
    content: `We may suspend or terminate your account at any time for violation of these Terms, non-payment, or if we discontinue the Service. You may cancel your account at any time from settings. Upon termination, your access ends and we will retain data according to our Privacy Policy.`,
  },
  {
    title: "Changes to Terms",
    content: `We may update these Terms periodically. Continued use of the Service after changes constitutes acceptance. We will provide at least 30 days' notice before material changes take effect via email or in-app notification.`,
  },
  {
    title: "Governing Law",
    content: `These Terms are governed by the laws of the jurisdiction in which ViralFlux is incorporated, without regard to conflict of law principles. Any disputes shall be resolved through binding arbitration, except where prohibited by law.`,
  },
]

export default function TermsPage() {
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
          <h1 className="text-4xl font-black text-foreground mb-3">Terms of Service</h1>
          <p className="text-muted-foreground">
            Last updated: June 2025 &bull; Effective: June 2025
          </p>
          <p className="text-muted-foreground mt-4 leading-relaxed">
            Please read these Terms carefully before using ViralFlux. These Terms
            constitute a binding legal agreement between you and ViralFlux.
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
            Questions about these Terms?{" "}
            <a
              href="mailto:legal@viralflux.ai"
              className="text-[#E5192A] hover:underline"
            >
              legal@viralflux.ai
            </a>
          </p>
          <p className="text-muted-foreground text-sm mt-2">
            <Link href="/privacy" className="hover:text-foreground transition-colors">
              Privacy Policy
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
