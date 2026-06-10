import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Providers } from "./providers"

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
})

export const metadata: Metadata = {
  title: {
    default: "ViralFlux — Automate Your YouTube Shorts Empire",
    template: "%s | ViralFlux",
  },
  description:
    "AI-powered YouTube Shorts automation. Generate, voice, and post viral shorts automatically. Under $0.10 per video.",
  keywords: [
    "YouTube Shorts automation",
    "AI video generation",
    "YouTube automation",
    "viral shorts",
    "content automation",
  ],
  authors: [{ name: "ViralFlux" }],
  creator: "ViralFlux",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://viralflux.io",
    title: "ViralFlux — Automate Your YouTube Shorts Empire",
    description:
      "AI-powered YouTube Shorts automation. Generate, voice, and post viral shorts automatically.",
    siteName: "ViralFlux",
  },
  twitter: {
    card: "summary_large_image",
    title: "ViralFlux — Automate Your YouTube Shorts Empire",
    description: "AI-powered YouTube Shorts automation. Under $0.10 per video.",
    creator: "@viralflux",
  },
  robots: {
    index: true,
    follow: true,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning className={inter.variable}>
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
