import Link from "next/link"
import { Logo } from "@/components/shared/Logo"

const footerLinks = {
  Product: [
    { label: "Features", href: "/#features" },
    { label: "Pricing", href: "/pricing" },
    { label: "Blog", href: "/blog" },
  ],
  Support: [
    { label: "Contact", href: "mailto:support@skypulseforge.com" },
  ],
  Legal: [
    { label: "Privacy Policy", href: "/privacy" },
    { label: "Terms of Service", href: "/terms" },
  ],
}

export default function Footer() {
  return (
    <footer className="bg-background border-t border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
          {/* Brand */}
          <div className="lg:col-span-2">
            <div className="mb-4">
              <Logo href="/" size="md" />
            </div>
            <p className="text-muted-foreground text-sm leading-relaxed max-w-xs">
              AI-powered YouTube Shorts automation. Generate, voice, and post
              viral content automatically — under $0.10 per video.
            </p>
          </div>

          {/* Links */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h4 className="text-foreground font-semibold text-sm mb-4">
                {category}
              </h4>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 pt-8 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-foreground/70 text-sm">
            &copy; {new Date().getFullYear()} ViralFlux. All rights reserved.
          </p>
          <p className="text-foreground/70 text-sm">
            Built with AI. Designed for creators.
          </p>
        </div>
      </div>
    </footer>
  )
}
