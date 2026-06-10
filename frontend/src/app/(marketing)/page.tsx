import Hero from "@/components/landing/Hero"
import SocialProof from "@/components/landing/SocialProof"
import HowItWorks from "@/components/landing/HowItWorks"
import Features from "@/components/landing/Features"
import FormatsShowcase from "@/components/landing/FormatsShowcase"
import PricingSection from "@/components/landing/PricingSection"
import BlogPreview from "@/components/landing/BlogPreview"
import CTABanner from "@/components/landing/CTABanner"

export default function LandingPage() {
  return (
    <>
      <Hero />
      <SocialProof />
      <HowItWorks />
      <Features />
      <FormatsShowcase />
      <PricingSection />
      <BlogPreview />
      <CTABanner />
    </>
  )
}
