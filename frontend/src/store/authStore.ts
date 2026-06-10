import { create } from "zustand"
import { persist } from "zustand/middleware"
import { authAPI } from "@/lib/api"
import type { User } from "@/types"

interface AuthState {
  user: User | null
  accessToken: string | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  fetchMe: () => Promise<void>
  setUser: (user: User) => void
  setToken: (token: string) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      isLoading: false,

      login: async (email: string, password: string) => {
        set({ isLoading: true })
        try {
          const { data } = await authAPI.login({ email, password })
          if (typeof window !== "undefined") {
            localStorage.setItem("access_token", data.access_token)
          }
          set({
            user: data.user,
            accessToken: data.access_token,
            isLoading: false,
          })
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      logout: async () => {
        try {
          await authAPI.logout()
        } catch {
          // Ignore logout errors
        } finally {
          if (typeof window !== "undefined") {
            localStorage.removeItem("access_token")
          }
          set({ user: null, accessToken: null })
        }
      },

      fetchMe: async () => {
        set({ isLoading: true })
        try {
          const { data } = await authAPI.me()
          set({ user: data, isLoading: false })
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      setUser: (user: User) => set({ user }),
      setToken: (token: string) => {
        if (typeof window !== "undefined") {
          localStorage.setItem("access_token", token)
        }
        set({ accessToken: token })
      },
      clearAuth: () => {
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token")
        }
        set({ user: null, accessToken: null })
      },
    }),
    {
      name: "viralflux-auth",
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
      }),
    }
  )
)
