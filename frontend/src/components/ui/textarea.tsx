import * as React from "react"
import { cn } from "@/lib/utils"

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "flex min-h-[80px] w-full rounded-md border border-[#222222] bg-[#111111] px-3 py-2 text-sm text-[#FAFAFA] placeholder:text-[#555555] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#E5192A] focus-visible:ring-offset-2 focus-visible:border-[#E5192A] disabled:cursor-not-allowed disabled:opacity-50 resize-none transition-colors",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Textarea.displayName = "Textarea"

export { Textarea }
