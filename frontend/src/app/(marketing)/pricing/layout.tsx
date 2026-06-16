import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Pricing",
  description:
    "Credit-based pricing for YouTube Shorts automation. Start free with 30 credits. Free, Starter, Pro, Agency + custom plans.",
}

export default function PricingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <>{children}</>
}
