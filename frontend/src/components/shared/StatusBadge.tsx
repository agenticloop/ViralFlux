import { cn } from "@/lib/utils"
import type { VideoStatus } from "@/types"

interface StatusBadgeProps {
  status: VideoStatus
  className?: string
}

const statusConfig: Record<
  VideoStatus,
  { label: string; color: string; pulse: boolean }
> = {
  queued: {
    label: "Queued",
    color: "bg-zinc-800 text-zinc-400 border-zinc-700",
    pulse: false,
  },
  generating: {
    label: "Generating",
    color: "bg-yellow-900/40 text-yellow-400 border-yellow-800/50",
    pulse: true,
  },
  pending_approval: {
    label: "Pending Approval",
    color: "bg-orange-900/40 text-orange-400 border-orange-800/50",
    pulse: false,
  },
  approved: {
    label: "Approved",
    color: "bg-blue-900/40 text-blue-400 border-blue-800/50",
    pulse: false,
  },
  uploading: {
    label: "Uploading",
    color: "bg-blue-900/40 text-blue-400 border-blue-800/50",
    pulse: true,
  },
  posted: {
    label: "Posted",
    color: "bg-green-900/40 text-green-400 border-green-800/50",
    pulse: false,
  },
  failed: {
    label: "Failed",
    color: "bg-red-900/40 text-red-400 border-red-800/50",
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
          config.pulse && "animate-pulse",
          status === "queued" && "bg-zinc-400",
          status === "generating" && "bg-yellow-400",
          status === "pending_approval" && "bg-orange-400",
          status === "approved" && "bg-blue-400",
          status === "uploading" && "bg-blue-400",
          status === "posted" && "bg-green-400",
          status === "failed" && "bg-red-400"
        )}
      />
      {config.label}
    </span>
  )
}
