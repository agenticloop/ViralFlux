"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import Sidebar from "@/components/dashboard/Sidebar"
import Topbar from "@/components/dashboard/Topbar"
import GenerateModal from "@/components/dashboard/GenerateModal"
import { useAuthStore } from "@/store/authStore"
import { LoadingSpinner } from "@/components/shared/LoadingSpinner"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user, fetchMe, isLoading } = useAuthStore()
  const router = useRouter()

  useEffect(() => {
    if (!user) {
      fetchMe().catch(() => {
        router.push("/login")
      })
    }
  }, [user, fetchMe, router])

  if (isLoading && !user) {
    return <LoadingSpinner fullScreen />
  }

  if (!user && !isLoading) {
    return null
  }

  return (
    <div className="flex h-screen bg-[#0A0A0A] overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
      <GenerateModal />
    </div>
  )
}
