import { cn } from "@/lib/utils"
import type { VideoStatus } from "@/types"

interface StatusBadgeProps {
  status: VideoStatus
  className?: string
}

const statusConfig: Record<
  VideoStatus,
  { label: string; color: string; dot: string; pulse: boolean }
> = {
  queued: {
    label: "Queued",
    color: "bg-zinc-100 text-zinc-600 border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700",
    dot: "bg-zinc-400 dark:bg-zinc-400",
    pulse: false,
  },
  generating: {
    label: "Generating",
    color: "bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-900/40 dark:text-yellow-400 dark:border-yellow-800/50",
    dot: "bg-yellow-500 dark:bg-yellow-400",
    pulse: true,
  },
  pending_approval: {
    label: "Pending Approval",
    color: "bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-900/40 dark:text-orange-400 dark:border-orange-800/50",
    dot: "bg-orange-500 dark:bg-orange-400",
    pulse: false,
  },
  approved: {
    label: "Approved",
    color: "bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/40 dark:text-blue-400 dark:border-blue-800/50",
    dot: "bg-blue-500 dark:bg-blue-400",
    pulse: false,
  },
  uploading: {
    label: "Uploading",
    color: "bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/40 dark:text-blue-400 dark:border-blue-800/50",
    dot: "bg-blue-500 dark:bg-blue-400",
    pulse: true,
  },
  posted: {
    label: "Posted",
    color: "bg-green-100 text-green-700 border-green-200 dark:bg-green-900/40 dark:text-green-400 dark:border-green-800/50",
    dot: "bg-green-500 dark:bg-green-400",
    pulse: false,
  },
  failed: {
    label: "Failed",
    color: "bg-red-100 text-red-700 border-red-200 dark:bg-red-900/40 dark:text-red-400 dark:border-red-800/50",
    dot: "bg-red-500 dark:bg-red-400",
    pulse: false,
  },
  rejected: {
    label: "Rejected",
    color: "bg-zinc-100 text-zinc-600 border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700",
    dot: "bg-zinc-400 dark:bg-zinc-400",
    pulse: false,
  },
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status]

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold",
        config.color,
        className
      )}
    >
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          config.dot,
          config.pulse && "animate-pulse"
        )}
      />
      {config.label}
    </span>
  )
}
