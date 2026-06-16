"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Loader2, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { channelsAPI } from "@/lib/api"
import { TIMEZONES } from "@/types"
import type { ChannelSchedule } from "@/types"
import { formatDate } from "@/lib/utils"

const schema = z.object({
  is_enabled: z.boolean(),
  frequency_days: z.number().min(1).max(30),
  post_time: z.string().regex(/^\d{2}:\d{2}$/, "Enter time as HH:MM"),
  timezone: z.string().min(1),
  require_approval: z.boolean(),
  approval_email: z.string().email().optional().or(z.literal("")),
})

type FormData = z.infer<typeof schema>

interface ScheduleConfigProps {
  channelId: string
  initialSchedule?: ChannelSchedule | null
  onSaved?: () => void
}

export default function ScheduleConfig({
  channelId,
  initialSchedule,
  onSaved,
}: ScheduleConfigProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      is_enabled: initialSchedule?.is_enabled ?? false,
      frequency_days: initialSchedule?.frequency_days ?? 1,
      post_time: initialSchedule?.post_time ?? "09:00",
      timezone: initialSchedule?.timezone ?? "America/New_York",
      require_approval: initialSchedule?.require_approval ?? true,
      approval_email: initialSchedule?.approval_email ?? "",
    },
  })

  const isEnabled = watch("is_enabled")
  const requireApproval = watch("require_approval")

  const onSubmit = async (data: FormData) => {
    setError(null)
    setIsLoading(true)
    try {
      await channelsAPI.setSchedule(channelId, {
        is_enabled: data.is_enabled,
        frequency_days: Number(data.frequency_days),
        post_time: data.post_time,
        timezone: data.timezone,
        require_approval: data.require_approval,
        approval_email: data.approval_email || undefined,
      })
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
      onSaved?.()
    } catch {
      setError("Failed to save schedule. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Enable Schedule */}
      <div className="flex items-center justify-between p-4 bg-muted rounded-xl border border-border">
        <div>
          <p className="text-foreground font-semibold">Enable Auto-Schedule</p>
          <p className="text-muted-foreground text-sm">
            Automatically generate and post Shorts on a schedule
          </p>
        </div>
        <Switch
          checked={isEnabled}
          onCheckedChange={(v) => setValue("is_enabled", v)}
        />
      </div>

      {isEnabled && (
        <div className="space-y-5">
          {/* Frequency + Time */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Post Every N Days</Label>
              <Input
                type="number"
                min={1}
                max={30}
                {...register("frequency_days", { valueAsNumber: true })}
              />
              {errors.frequency_days && (
                <p className="text-[#E5192A] text-xs">
                  {errors.frequency_days.message}
                </p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Post Time
              </Label>
              <Input type="time" {...register("post_time")} />
              {errors.post_time && (
                <p className="text-[#E5192A] text-xs">
                  {errors.post_time.message}
                </p>
              )}
            </div>
          </div>

          {/* Timezone */}
          <div className="space-y-1.5">
            <Label>Timezone</Label>
            <Select
              value={watch("timezone")}
              onValueChange={(v) => setValue("timezone", v)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TIMEZONES.map((tz) => (
                  <SelectItem key={tz} value={tz}>
                    {tz}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Require Approval */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-foreground text-sm font-medium">
                  Require Approval
                </p>
                <p className="text-muted-foreground text-xs">
                  Review videos before they go live
                </p>
              </div>
              <Switch
                checked={requireApproval}
                onCheckedChange={(v) => setValue("require_approval", v)}
              />
            </div>

            {requireApproval && (
              <div className="space-y-1.5 pl-2 border-l-2 border-[#E5192A]/30">
                <Label className="text-xs">Approval Email (optional)</Label>
                <Input
                  type="email"
                  placeholder="approver@example.com"
                  {...register("approval_email")}
                />
                {errors.approval_email && (
                  <p className="text-[#E5192A] text-xs">
                    {errors.approval_email.message}
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Next run */}
          {initialSchedule?.next_run_at && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground bg-background border border-border rounded-lg px-4 py-3">
              <Clock className="w-4 h-4 text-[#E5192A]" />
              Next run scheduled for{" "}
              <span className="text-foreground font-medium">
                {formatDate(initialSchedule.next_run_at)}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Error / Success */}
      {error && (
        <div className="bg-red-50 border border-red-200 dark:bg-red-900/20 dark:border-red-800/40 rounded-lg px-4 py-3">
          <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
        </div>
      )}
      {success && (
        <div className="bg-green-50 border border-green-200 dark:bg-green-900/20 dark:border-green-800/40 rounded-lg px-4 py-3">
          <p className="text-green-600 dark:text-green-400 text-sm">
            Schedule saved successfully!
          </p>
        </div>
      )}

      {/* Save */}
      <Button type="submit" variant="red" disabled={isLoading}>
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Saving...
          </>
        ) : (
          "Save Schedule"
        )}
      </Button>
    </form>
  )
}
