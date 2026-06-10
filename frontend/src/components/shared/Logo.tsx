import Link from "next/link"
import { cn } from "@/lib/utils"

interface LogoProps {
  href?: string
  size?: "sm" | "md" | "lg"
  showWordmark?: boolean
  className?: string
}

export function LogoIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      {/* Red rounded rectangle — YouTube-like badge */}
      <rect width="32" height="32" rx="7" fill="#E5192A" />
      {/* White play triangle — offset slightly right for optical centering */}
      <path
        d="M13 10.5L22 16L13 21.5V10.5Z"
        fill="white"
      />
      {/* Small "V" slash accent — top-left corner, subtle brand mark */}
      <path
        d="M7 8L10.5 14L14 8"
        stroke="white"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.45"
      />
    </svg>
  )
}

const sizes = {
  sm: { icon: "w-7 h-7", text: "text-base" },
  md: { icon: "w-8 h-8", text: "text-xl" },
  lg: { icon: "w-10 h-10", text: "text-2xl" },
}

export function Logo({
  href = "/",
  size = "md",
  showWordmark = true,
  className,
}: LogoProps) {
  const s = sizes[size]

  return (
    <Link
      href={href}
      className={cn("flex items-center gap-2.5 group select-none", className)}
    >
      <LogoIcon
        className={cn(
          s.icon,
          "transition-transform duration-150 group-hover:scale-105"
        )}
      />
      {showWordmark && (
        <span
          className={cn(
            "font-bold tracking-tight text-foreground",
            s.text
          )}
        >
          Viral<span className="text-[#E5192A]">Flux</span>
        </span>
      )}
    </Link>
  )
}
