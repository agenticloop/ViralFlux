import { create } from "zustand"
import { persist } from "zustand/middleware"

interface UIState {
  sidebarCollapsed: boolean
  generateModalOpen: boolean
  selectedChannelId: string | null
  toggleSidebar: () => void
  setSidebarCollapsed: (collapsed: boolean) => void
  setSelectedChannelId: (channelId: string | null) => void
  openGenerateModal: (channelId?: string) => void
  closeGenerateModal: () => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      generateModalOpen: false,
      selectedChannelId: null,

      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

      setSidebarCollapsed: (collapsed: boolean) =>
        set({ sidebarCollapsed: collapsed }),

      setSelectedChannelId: (channelId: string | null) =>
        set({ selectedChannelId: channelId }),

      openGenerateModal: (channelId?: string) =>
        set((state) => ({
          generateModalOpen: true,
          selectedChannelId: channelId ?? state.selectedChannelId,
        })),

      closeGenerateModal: () => set({ generateModalOpen: false }),
    }),
    {
      name: "viralflux-ui",
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        selectedChannelId: state.selectedChannelId,
      }),
    }
  )
)
