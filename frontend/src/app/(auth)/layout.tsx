import Link from "next/link"
import { Zap } from "lucide-react"

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      {/* Background glow */}
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-[#E5192A]/5 rounded-full blur-[100px] pointer-events-none" />

      {/* Logo */}
      <Link href="/" className="flex items-center gap-2 mb-8 group">
        <div className="w-9 h-9 rounded-xl bg-[#E5192A] flex items-center justify-center group-hover:bg-[#C01020] transition-colors">
          <Zap className="w-5 h-5 text-white fill-white" />
        </div>
        <span className="text-foreground font-bold text-2xl tracking-tight">
          ViralFlux
        </span>
      </Link>

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
