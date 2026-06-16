import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

/** Tailwind-aware className combiner (shadcn/ui convention). */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Compact integer formatting with thousands separators, e.g. 12345 → "12,345". */
export function formatNumber(value: number | null | undefined): string {
  const n = typeof value === "number" && Number.isFinite(value) ? value : 0
  return new Intl.NumberFormat("en-US").format(n)
}

/**
 * Credit-balance formatting, e.g. 2600 → "2,600", -40 → "-40".
 * Credits are always whole numbers; sign is preserved so ledger debits read
 * correctly. Null/invalid → "0".
 */
export function formatCredits(value: number | null | undefined): string {
  const n = typeof value === "number" && Number.isFinite(value) ? Math.round(value) : 0
  return new Intl.NumberFormat("en-US").format(n)
}

/** USD cost formatting, e.g. 1.5 → "$1.50". Null/invalid → "$0.00". */
export function formatCost(value: number | null | undefined): string {
  const n = typeof value === "number" && Number.isFinite(value) ? value : 0
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(n)
}

/** Absolute date, e.g. "Jan 5, 2026". Null/invalid → "—". */
export function formatDate(value: string | null | undefined): string {
  if (!value) return "—"
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return "—"
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

/** Relative time, e.g. "3h ago". Falls back to an absolute date past a week. */
export function timeAgo(value: string | null | undefined): string {
  if (!value) return "—"
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return "—"

  const seconds = Math.floor((Date.now() - d.getTime()) / 1000)
  if (seconds < 0) return formatDate(value)
  if (seconds < 60) return "just now"

  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`

  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`

  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`

  return formatDate(value)
}

/** Up-to-two-letter initials from a name, e.g. "Jane Doe" → "JD". */
export function getInitials(name: string | null | undefined): string {
  if (!name) return "?"
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return "?"
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}
