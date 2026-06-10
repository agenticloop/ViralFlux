import Link from "next/link"
import { Zap, Youtube, Twitter, Linkedin } from "lucide-react"

const footerLinks = {
  Product: [
    { label: "Features", href: "/#features" },
    { label: "Pricing", href: "/pricing" },
    { label: "Blog", href: "/blog" },
    { label: "Changelog", href: "#" },
  ],
  Company: [
    { label: "About", href: "#" },
    { label: "Careers", href: "#" },
    { label: "Contact", href: "#" },
  ],
  Legal: [
    { label: "Privacy Policy", href: "#" },
    { label: "Terms of Service", href: "#" },
    { label: "Cookie Policy", href: "#" },
  ],
}

export default function Footer() {
  return (
    <footer className="bg-[#0A0A0A] border-t border-[#1A1A1A]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
          {/* Brand */}
          <div className="lg:col-span-2">
            <Link href="/" className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-[#E5192A] flex items-center justify-center">
                <Zap className="w-5 h-5 text-white fill-white" />
              </div>
              <span className="text-[#FAFAFA] font-bold text-xl">ViralFlux</span>
            </Link>
            <p className="text-[#666666] text-sm leading-relaxed max-w-xs">
              AI-powered YouTube Shorts automation. Generate, voice, and post
              viral content automatically — under $0.10 per video.
            </p>
            <div className="flex items-center gap-3 mt-6">
              <a
                href="#"
                className="w-8 h-8 rounded-md border border-[#222222] flex items-center justify-center text-[#666666] hover:text-[#FAFAFA] hover:border-[#E5192A] transition-all"
                aria-label="YouTube"
              >
                <Youtube className="w-4 h-4" />
              </a>
              <a
                href="#"
                className="w-8 h-8 rounded-md border border-[#222222] flex items-center justify-center text-[#666666] hover:text-[#FAFAFA] hover:border-[#E5192A] transition-all"
                aria-label="Twitter"
              >
                <Twitter className="w-4 h-4" />
              </a>
              <a
                href="#"
                className="w-8 h-8 rounded-md border border-[#222222] flex items-center justify-center text-[#666666] hover:text-[#FAFAFA] hover:border-[#E5192A] transition-all"
                aria-label="LinkedIn"
              >
                <Linkedin className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* Links */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h4 className="text-[#FAFAFA] font-semibold text-sm mb-4">
                {category}
              </h4>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-[#666666] hover:text-[#FAFAFA] text-sm transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 pt-8 border-t border-[#1A1A1A] flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-[#444444] text-sm">
            &copy; {new Date().getFullYear()} ViralFlux. All rights reserved.
          </p>
          <p className="text-[#444444] text-sm">
            Built with AI. Designed for creators.
          </p>
        </div>
      </div>
    </footer>
  )
}
