"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Plus, X, Loader2, Clock } from "lucide-react"
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

const schema = z.object({
  enabled: z.boolean(),
  frequency_days: z.number().min(1).max(30),
  time_of_day: z.string().regex(/^\d{2}:\d{2}$/, "Enter time as HH:MM"),
  timezone: z.string().min(1),
  require_approval: z.boolean(),
  approval_email: z.string().email().optional().or(z.literal("")),
  auto_topic: z.boolean(),
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
  const [topicQueue, setTopicQueue] = useState<string[]>(
    initialSchedule?.topic_queue ?? []
  )
  const [newTopic, setNewTopic] = useState("")
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
      enabled: initialSchedule?.enabled ?? false,
      frequency_days: initialSchedule?.frequency_days ?? 1,
      time_of_day: initialSchedule?.time_of_day ?? "09:00",
      timezone: initialSchedule?.timezone ?? "America/New_York",
      require_approval: initialSchedule?.require_approval ?? true,
      approval_email: initialSchedule?.approval_email ?? "",
      auto_topic: initialSchedule?.auto_topic ?? true,
    },
  })

  const enabled = watch("enabled")
  const requireApproval = watch("require_approval")
  const autoTopic = watch("auto_topic")

  const addTopic = () => {
    if (newTopic.trim() && !topicQueue.includes(newTopic.trim())) {
      setTopicQueue([...topicQueue, newTopic.trim()])
      setNewTopic("")
    }
  }

  const removeTopic = (topic: string) => {
    setTopicQueue(topicQueue.filter((t) => t !== topic))
  }

  const onSubmit = async (data: FormData) => {
    setError(null)
    setIsLoading(true)
    try {
      await channelsAPI.setSchedule(channelId, {
        ...data,
        frequency_days: Number(data.frequency_days),
        topic_queue: topicQueue,
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
          checked={enabled}
          onCheckedChange={(v) => setValue("enabled", v)}
        />
      </div>

      {enabled && (
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
                Time of Day
              </Label>
              <Input type="time" {...register("time_of_day")} />
              {errors.time_of_day && (
                <p className="text-[#E5192A] text-xs">
                  {errors.time_of_day.message}
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
              </div>
            )}
          </div>

          {/* Auto Topic */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-foreground text-sm font-medium">
                  AI Auto-Topic
                </p>
                <p className="text-muted-foreground text-xs">
                  Let AI pick trending topics automatically
                </p>
              </div>
              <Switch
                checked={autoTopic}
                onCheckedChange={(v) => setValue("auto_topic", v)}
              />
            </div>

            {/* Manual Topic Queue */}
            {!autoTopic && (
              <div className="space-y-3 pl-2 border-l-2 border-[#E5192A]/30">
                <Label className="text-xs">Manual Topic Queue</Label>

                {topicQueue.length > 0 && (
                  <div className="space-y-2">
                    {topicQueue.map((topic, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-2 bg-muted rounded-lg px-3 py-2"
                      >
                        <span className="text-muted-foreground text-xs w-5">{i + 1}.</span>
                        <span className="text-foreground text-sm flex-1 truncate">
                          {topic}
                        </span>
                        <button
                          type="button"
                          onClick={() => removeTopic(topic)}
                          className="text-muted-foreground hover:text-red-600 dark:hover:text-red-400 transition-colors"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                <div className="flex gap-2">
                  <Input
                    placeholder="Add a topic..."
                    value={newTopic}
                    onChange={(e) => setNewTopic(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault()
                        addTopic()
                      }
                    }}
                    className="flex-1"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={addTopic}
                    className="border-border text-muted-foreground"
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            )}
          </div>
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
          <p className="text-green-600 dark:text-green-400 text-sm">Schedule saved successfully!</p>
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
