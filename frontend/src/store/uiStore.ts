import { create } from "zustand"

interface UIState {
  sidebarCollapsed: boolean
  generateModalOpen: boolean
  selectedChannelId: string | null
  toggleSidebar: () => void
  setSidebarCollapsed: (collapsed: boolean) => void
  openGenerateModal: (channelId?: string) => void
  closeGenerateModal: () => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  generateModalOpen: false,
  selectedChannelId: null,

  toggleSidebar: () =>
    set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  setSidebarCollapsed: (collapsed: boolean) =>
    set({ sidebarCollapsed: collapsed }),

  openGenerateModal: (channelId?: string) =>
    set({ generateModalOpen: true, selectedChannelId: channelId ?? null }),

  closeGenerateModal: () =>
    set({ generateModalOpen: false, selectedChannelId: null }),
}))
