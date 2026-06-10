"use client"

import { usePathname } from "next/navigation"
import { Bell, Zap } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/shared/ThemeToggle"
import { useUIStore } from "@/store/uiStore"
import { useAuthStore } from "@/store/authStore"
import { getInitials } from "@/lib/utils"

const pageTitles: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/dashboard/channels": "Channels",
  "/dashboard/videos": "Videos",
  "/dashboard/videos/new": "New Video",
  "/dashboard/analytics": "Analytics",
  "/dashboard/settings": "Settings",
}

function getPageTitle(pathname: string): string {
  if (pageTitles[pathname]) return pageTitles[pathname]
  if (pathname.startsWith("/dashboard/channels/"))
    return "Channel Details"
  if (pathname.startsWith("/dashboard/videos/"))
    return "Video Details"
  return "Dashboard"
}

export default function Topbar() {
  const pathname = usePathname()
  const { openGenerateModal } = useUIStore()
  const { user } = useAuthStore()

  return (
    <header className="h-16 bg-background border-b border-border flex items-center justify-between px-6 flex-shrink-0">
      {/* Page Title */}
      <div>
        <h1 className="text-foreground font-bold text-lg">
          {getPageTitle(pathname)}
        </h1>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3">
        {/* Quick Generate */}
        <Button
          variant="red"
          size="sm"
          onClick={() => openGenerateModal()}
          className="hidden sm:flex items-center gap-2"
        >
          <Zap className="w-4 h-4 fill-white" />
          Generate
        </Button>

        {/* Notifications */}
        <button className="relative w-9 h-9 rounded-md border border-border flex items-center justify-center text-muted-foreground hover:text-foreground hover:border-border transition-all">
          <Bell className="w-4 h-4" />
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-[#E5192A] rounded-full text-white text-[10px] flex items-center justify-center font-bold">
            3
          </span>
        </button>

        {/* Theme Toggle */}
        <ThemeToggle />

        {/* User Avatar */}
        <div className="w-9 h-9 rounded-full bg-[#E5192A]/20 border border-[#E5192A]/30 flex items-center justify-center cursor-pointer hover:border-[#E5192A] transition-all">
          <span className="text-[#E5192A] text-xs font-bold">
            {user ? getInitials(user.full_name) : "?"}
          </span>
        </div>
      </div>
    </header>
  )
}
