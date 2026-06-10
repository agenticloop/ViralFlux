"use client"

import { Suspense } from "react"
import { useState, useRef, useEffect, KeyboardEvent, ClipboardEvent } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Loader2, Mail } from "lucide-react"
import { Button } from "@/components/ui/button"
import { authAPI } from "@/lib/api"

function VerifyContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const email = searchParams.get("email") || ""

  const [otp, setOtp] = useState(["", "", "", "", "", ""])
  const [isLoading, setIsLoading] = useState(false)
  const [isResending, setIsResending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [resendCooldown, setResendCooldown] = useState(0)
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])

  useEffect(() => {
    inputRefs.current[0]?.focus()
  }, [])

  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => setResendCooldown((c) => c - 1), 1000)
      return () => clearTimeout(timer)
    }
  }, [resendCooldown])

  const handleChange = (index: number, value: string) => {
    const digit = value.replace(/\D/g, "").slice(-1)
    const newOtp = [...otp]
    newOtp[index] = digit
    setOtp(newOtp)
    if (digit && index < 5) inputRefs.current[index + 1]?.focus()
    if (digit && index === 5 && newOtp.every((d) => d !== "")) handleVerify(newOtp.join(""))
  }

  const handleKeyDown = (index: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace") {
      if (!otp[index] && index > 0) inputRefs.current[index - 1]?.focus()
      const newOtp = [...otp]
      newOtp[index] = ""
      setOtp(newOtp)
    }
    if (e.key === "ArrowLeft" && index > 0) inputRefs.current[index - 1]?.focus()
    if (e.key === "ArrowRight" && index < 5) inputRefs.current[index + 1]?.focus()
  }

  const handlePaste = (e: ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault()
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6)
    if (pasted.length === 6) {
      setOtp(pasted.split(""))
      inputRefs.current[5]?.focus()
      handleVerify(pasted)
    }
  }

  const handleVerify = async (code: string) => {
    if (code.length !== 6) return
    setError(null)
    setIsLoading(true)
    try {
      await authAPI.verifyOtp({ email, otp: code })
      router.push("/dashboard")
    } catch {
      setError("Invalid or expired OTP. Please try again.")
      setOtp(["", "", "", "", "", ""])
      inputRefs.current[0]?.focus()
    } finally {
      setIsLoading(false)
    }
  }

  const handleResend = async () => {
    setIsResending(true)
    try {
      await authAPI.forgotPassword(email)
      setResendCooldown(60)
    } catch {
      // ignore
    } finally {
      setIsResending(false)
    }
  }

  return (
    <>
      <div className="mb-6 text-center">
        <div className="w-12 h-12 bg-[#E5192A]/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <Mail className="w-6 h-6 text-[#E5192A]" />
        </div>
        <h1 className="text-2xl font-bold text-foreground mb-1">Check your email</h1>
        <p className="text-muted-foreground text-sm">
          We sent a 6-digit code to{" "}
          <span className="text-foreground font-medium">{email}</span>
        </p>
      </div>

      <div className="space-y-6">
        <div className="flex gap-3 justify-center">
          {otp.map((digit, i) => (
            <input
              key={i}
              ref={(el) => { inputRefs.current[i] = el }}
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength={1}
              value={digit}
              onChange={(e) => handleChange(i, e.target.value)}
              onKeyDown={(e) => handleKeyDown(i, e)}
              onPaste={handlePaste}
              className={`w-12 h-14 text-center text-xl font-bold rounded-xl border bg-card text-foreground focus:outline-none transition-all ${
                digit
                  ? "border-[#E5192A] ring-1 ring-[#E5192A]"
                  : "border-border focus:border-[#E5192A] focus:ring-1 focus:ring-[#E5192A]"
              }`}
            />
          ))}
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-800/40 rounded-lg px-4 py-3">
            <p className="text-red-400 text-sm text-center">{error}</p>
          </div>
        )}

        <Button
          onClick={() => handleVerify(otp.join(""))}
          variant="red"
          className="w-full"
          disabled={isLoading || otp.some((d) => !d)}
        >
          {isLoading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Verifying...</> : "Verify Email"}
        </Button>

        <div className="text-center">
          <p className="text-muted-foreground text-sm">
            Didn&apos;t receive the code?{" "}
            {resendCooldown > 0 ? (
              <span className="text-muted-foreground">Resend in {resendCooldown}s</span>
            ) : (
              <button
                type="button"
                onClick={handleResend}
                disabled={isResending}
                className="text-[#E5192A] hover:text-[#FF3040] font-medium transition-colors disabled:opacity-50"
              >
                {isResending ? "Sending..." : "Resend code"}
              </button>
            )}
          </p>
        </div>
      </div>
    </>
  )
}

export default function VerifyPage() {
  return (
    <Suspense fallback={<div className="h-48 flex items-center justify-center"><Loader2 className="w-6 h-6 animate-spin text-[#E5192A]" /></div>}>
      <VerifyContent />
    </Suspense>
  )
}
