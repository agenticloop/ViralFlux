"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/store/authStore"

export function useRequireAuth() {
  const { user, fetchMe } = useAuthStore()
  const router = useRouter()

  useEffect(() => {
    if (!user) {
      fetchMe().catch(() => {
        router.push("/login")
      })
    }
  }, [user, fetchMe, router])

  return { user }
}

export function useRedirectIfAuth() {
  const { user } = useAuthStore()
  const router = useRouter()

  useEffect(() => {
    if (user) {
      router.push("/dashboard")
    }
  }, [user, router])
}
