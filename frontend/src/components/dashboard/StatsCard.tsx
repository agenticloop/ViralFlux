import { LucideIcon, TrendingUp, TrendingDown, Minus } from "lucide-react"
import { cn } from "@/lib/utils"

interface StatsCardProps {
  icon: LucideIcon
  label: string
  value: string
  change?: number
  changeLabel?: string
  iconColor?: string
  iconBg?: string
}

export default function StatsCard({
  icon: Icon,
  label,
  value,
  change,
  changeLabel,
  iconColor = "text-[#E5192A]",
  iconBg = "bg-[#E5192A]/10",
}: StatsCardProps) {
  const isPositive = change !== undefined && change > 0
  const isNegative = change !== undefined && change < 0
  const isNeutral = change === 0

  return (
    <div className="bg-card border border-border rounded-xl p-5 hover:border-border transition-all duration-200">
      <div className="flex items-start justify-between mb-4">
        <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", iconBg)}>
          <Icon className={cn("w-5 h-5", iconColor)} />
        </div>
        {change !== undefined && (
          <div
            className={cn(
              "flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full",
              isPositive &&
                "bg-green-100 text-green-700 border border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800/30",
              isNegative &&
                "bg-red-100 text-red-600 border border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800/30",
              isNeutral && "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
            )}
          >
            {isPositive && <TrendingUp className="w-3 h-3" />}
            {isNegative && <TrendingDown className="w-3 h-3" />}
            {isNeutral && <Minus className="w-3 h-3" />}
            <span>
              {isPositive ? "+" : ""}
              {change.toFixed(1)}%
            </span>
          </div>
        )}
      </div>

      <div className="space-y-1">
        <div className="text-2xl font-black text-foreground">{value}</div>
        <div className="text-muted-foreground text-sm">{label}</div>
        {changeLabel && (
          <div className="text-muted-foreground text-xs">{changeLabel}</div>
        )}
      </div>
    </div>
  )
}
