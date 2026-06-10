"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Loader2, ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { authAPI } from "@/lib/api"

const schema = z.object({
  email: z.string().email("Please enter a valid email"),
})

type FormData = z.infer<typeof schema>

export default function ForgotPasswordPage() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const [submittedEmail, setSubmittedEmail] = useState("")

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    setIsLoading(true)
    try {
      await authAPI.forgotPassword(data.email)
      setSubmittedEmail(data.email)
      setSent(true)
    } catch {
      // Still show success to avoid email enumeration
      setSubmittedEmail(data.email)
      setSent(true)
    } finally {
      setIsLoading(false)
    }
  }

  if (sent) {
    return (
      <>
        <div className="text-center">
          <div className="w-12 h-12 bg-green-900/30 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">✉️</span>
          </div>
          <h1 className="text-2xl font-bold text-[#FAFAFA] mb-2">
            Check your inbox
          </h1>
          <p className="text-[#888888] text-sm mb-6">
            If <span className="text-[#FAFAFA]">{submittedEmail}</span> is
            registered, you&apos;ll receive a reset code shortly.
          </p>
          <Button
            variant="red"
            className="w-full mb-4"
            onClick={() =>
              router.push(
                `/reset-password?email=${encodeURIComponent(submittedEmail)}`
              )
            }
          >
            Enter Reset Code
          </Button>
          <Link
            href="/login"
            className="text-sm text-[#888888] hover:text-[#FAFAFA] transition-colors flex items-center justify-center gap-1"
          >
            <ArrowLeft className="w-3 h-3" />
            Back to login
          </Link>
        </div>
      </>
    )
  }

  return (
    <>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[#FAFAFA] mb-1">
          Reset your password
        </h1>
        <p className="text-[#888888] text-sm">
          Enter your email and we&apos;ll send you a reset code.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="email">Email Address</Label>
          <Input
            id="email"
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
            {...register("email")}
          />
          {errors.email && (
            <p className="text-[#E5192A] text-xs">{errors.email.message}</p>
          )}
        </div>

        <Button
          type="submit"
          variant="red"
          className="w-full"
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Sending...
            </>
          ) : (
            "Send Reset Code"
          )}
        </Button>
      </form>

      <div className="mt-6 text-center">
        <Link
          href="/login"
          className="text-sm text-[#888888] hover:text-[#FAFAFA] transition-colors flex items-center justify-center gap-1"
        >
          <ArrowLeft className="w-3 h-3" />
          Back to login
        </Link>
      </div>
    </>
  )
}
