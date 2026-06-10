import { cn } from "@/lib/utils"

interface LoadingSpinnerProps {
  className?: string
  size?: "sm" | "md" | "lg"
  fullScreen?: boolean
}

export function LoadingSpinner({
  className,
  size = "md",
  fullScreen = false,
}: LoadingSpinnerProps) {
  const sizeMap = {
    sm: "h-4 w-4 border-2",
    md: "h-8 w-8 border-2",
    lg: "h-12 w-12 border-[3px]",
  }

  const spinner = (
    <div
      className={cn(
        "rounded-full border-transparent border-t-[#E5192A] animate-spin",
        sizeMap[size],
        className
      )}
      role="status"
      aria-label="Loading"
    />
  )

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0A0A0A]/80 backdrop-blur-sm">
        <div className="flex flex-col items-center gap-3">
          <div className="h-12 w-12 rounded-full border-[3px] border-[#222222] border-t-[#E5192A] animate-spin" />
          <p className="text-sm text-[#888888]">Loading...</p>
        </div>
      </div>
    )
  }

  return spinner
}

export function LoadingSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "rounded-md bg-[#1A1A1A] shimmer-bg animate-pulse",
        className
      )}
    />
  )
}
