"use client"

import { useEffect, useState } from "react"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"

export function ThemeToggle() {
  const { setTheme, resolvedTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => setMounted(true), [])

  // Render placeholder until client-side hydration completes
  if (!mounted) return <div className="h-9 w-9 rounded-md border border-border" />

  const isDark = resolvedTheme === "dark"

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className="relative h-9 w-9 rounded-md border border-border hover:border-[#E5192A] hover:bg-[#E5192A]/10 transition-all"
    >
      {isDark
        ? <Sun className="h-4 w-4 text-foreground" />
        : <Moon className="h-4 w-4 text-foreground" />
      }
    </Button>
  )
}
