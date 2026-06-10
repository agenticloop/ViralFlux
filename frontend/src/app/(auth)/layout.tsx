import Link from "next/link"
import { Logo } from "@/components/shared/Logo"

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      {/* Background glow */}
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-[#E5192A]/5 rounded-full blur-[100px] pointer-events-none" />

      <Logo href="/" size="lg" className="mb-8" />

      {/* Card */}
      <div className="relative w-full max-w-md">
        <div className="absolute inset-0 bg-[#E5192A]/5 rounded-2xl blur-xl" />
        <div className="relative bg-card border border-border rounded-2xl p-8 shadow-2xl">
          {children}
        </div>
      </div>

      {/* Footer */}
      <p className="mt-6 text-muted-foreground text-xs text-center">
        &copy; {new Date().getFullYear()} ViralFlux &bull;{" "}
        <Link href="/privacy" className="hover:text-muted-foreground transition-colors">
          Privacy
        </Link>{" "}
        &bull;{" "}
        <Link href="/terms" className="hover:text-muted-foreground transition-colors">
          Terms
        </Link>
      </p>
    </div>
  )
}
