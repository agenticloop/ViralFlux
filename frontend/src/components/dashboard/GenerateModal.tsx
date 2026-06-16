"use client"

import { Zap } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import { useUIStore } from "@/store/uiStore"
import { useQueryClient } from "@tanstack/react-query"
import GenerateForm from "@/components/dashboard/GenerateForm"

export default function GenerateModal() {
  const { generateModalOpen, closeGenerateModal, selectedChannelId } =
    useUIStore()
  const queryClient = useQueryClient()

  return (
    <Dialog open={generateModalOpen} onOpenChange={closeGenerateModal}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-[#E5192A] fill-[#E5192A]" />
            Generate New Short
          </DialogTitle>
          <DialogDescription>
            Pick a channel, genre, model tier and script source. You&apos;re
            billed in credits.
          </DialogDescription>
        </DialogHeader>

        {generateModalOpen && (
          <div className="mt-2">
            <GenerateForm
              initialChannelId={selectedChannelId}
              onSuccess={() => {
                queryClient.invalidateQueries({ queryKey: ["videos"] })
                queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] })
                queryClient.invalidateQueries({ queryKey: ["plan-current"] })
                closeGenerateModal()
              }}
            />
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
