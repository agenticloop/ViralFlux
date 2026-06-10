from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_RESEND_URL = "https://api.resend.com/emails"
_BRAND_COLOR = "#E5192A"


class EmailServiceError(Exception):
    pass


class EmailService:
    """Resend-backed transactional email service for ViralFlux."""

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    async def send_otp(self, to_email: str, otp: str, purpose: str = "verification") -> None:
        if purpose == "password_reset":
            subject = "ViralFlux — Password Reset Code"
        else:
            subject = "ViralFlux — Verify Your Email"

        await self._send(to_email, subject, self._otp_template(otp, purpose))
        logger.info("OTP email sent to %s (purpose=%s)", to_email, purpose)

    async def send_approval_request(
        self, to_email: str, job_id: str, approve_token: str, preview_url: str
    ) -> None:
        subject = "ViralFlux — Your Short Is Ready to Review"
        await self._send(to_email, subject, self._approval_template(job_id, approve_token, preview_url))
        logger.info("Approval email sent to %s for job %s", to_email, job_id)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _send(self, to: str, subject: str, html: str) -> None:
        if not settings.RESEND_API_KEY:
            logger.warning("RESEND_API_KEY not set — skipping email to %s", to)
            return

        payload = {
            "from": settings.EMAIL_FROM,
            "to": [to],
            "subject": subject,
            "html": html,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                _RESEND_URL,
                json=payload,
                headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
            )
        if resp.status_code not in (200, 201):
            logger.error("Resend error %s: %s", resp.status_code, resp.text)
            raise EmailServiceError(f"Email delivery failed ({resp.status_code}): {resp.text}")

    def _otp_template(self, otp: str, purpose: str) -> str:
        if purpose == "password_reset":
            heading = "Reset Your Password"
            body_text = (
                "We received a request to reset your ViralFlux password. "
                "Use the code below — it expires in 15 minutes."
            )
            footer_note = "If you didn't request this, you can safely ignore this email."
        else:
            heading = "Verify Your Email"
            body_text = (
                "Welcome to ViralFlux! Use the code below to verify your email address. "
                "It expires in 15 minutes."
            )
            footer_note = "If you didn't create a ViralFlux account, you can safely ignore this email."

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
</head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 0;">
    <tr><td align="center">
      <table width="520" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:12px;overflow:hidden;max-width:520px;
                    box-shadow:0 2px 12px rgba(0,0,0,0.08);">
        <tr>
          <td align="center" style="background:{_BRAND_COLOR};padding:28px 40px;">
            <span style="color:#fff;font-size:24px;font-weight:800;letter-spacing:1px;">ViralFlux</span>
          </td>
        </tr>
        <tr>
          <td style="padding:40px;">
            <h2 style="color:#111;font-size:20px;margin:0 0 12px;">{heading}</h2>
            <p style="color:#555;font-size:15px;line-height:1.6;margin:0 0 28px;">{body_text}</p>
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr><td align="center">
                <div style="display:inline-block;background:#fff8f8;
                            border:2px solid {_BRAND_COLOR};border-radius:10px;
                            padding:16px 36px;letter-spacing:14px;
                            font-size:38px;font-weight:800;color:#111;">
                  {otp}
                </div>
              </td></tr>
            </table>
            <p style="color:#999;font-size:13px;margin:28px 0 0;text-align:center;">
              {footer_note}
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#fafafa;border-top:1px solid #eee;
                     padding:18px 40px;text-align:center;">
            <p style="color:#bbb;font-size:12px;margin:0;">
              &copy; 2026 ViralFlux &bull; Powered by SkyPulseForge
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    def _approval_template(self, job_id: str, approve_token: str, preview_url: str) -> str:
        base_url = settings.APP_URL.rstrip("/")
        approve_url = f"{base_url}/api/v1/jobs/{job_id}/approve?token={approve_token}&action=approve"
        reject_url  = f"{base_url}/api/v1/jobs/{job_id}/approve?token={approve_token}&action=reject"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
</head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 0;">
    <tr><td align="center">
      <table width="520" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:12px;overflow:hidden;max-width:520px;
                    box-shadow:0 2px 12px rgba(0,0,0,0.08);">
        <tr>
          <td align="center" style="background:{_BRAND_COLOR};padding:28px 40px;">
            <span style="color:#fff;font-size:24px;font-weight:800;letter-spacing:1px;">ViralFlux</span>
          </td>
        </tr>
        <tr>
          <td style="padding:40px;">
            <h2 style="color:#111;font-size:20px;margin:0 0 12px;">Your Short Is Ready</h2>
            <p style="color:#555;font-size:15px;line-height:1.6;margin:0 0 24px;">
              A new Short has been generated and is waiting for your approval before upload.
            </p>
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;">
              <tr><td align="center">
                <a href="{preview_url}"
                   style="display:inline-block;background:#f5f5f5;color:#333;
                          text-decoration:none;padding:11px 24px;border-radius:6px;
                          font-size:14px;font-weight:600;border:1px solid #ddd;">
                  ▶ Watch Preview
                </a>
              </td></tr>
            </table>
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td width="50%" style="padding-right:8px;">
                  <a href="{approve_url}"
                     style="display:block;background:#22c55e;color:#fff;text-decoration:none;
                            padding:13px 0;border-radius:6px;font-size:15px;font-weight:700;
                            text-align:center;">
                    Approve &amp; Post
                  </a>
                </td>
                <td width="50%" style="padding-left:8px;">
                  <a href="{reject_url}"
                     style="display:block;background:#ef4444;color:#fff;text-decoration:none;
                            padding:13px 0;border-radius:6px;font-size:15px;font-weight:700;
                            text-align:center;">
                    Reject
                  </a>
                </td>
              </tr>
            </table>
            <p style="color:#ccc;font-size:11px;margin:20px 0 0;text-align:center;">
              Job ID: {job_id}
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#fafafa;border-top:1px solid #eee;
                     padding:18px 40px;text-align:center;">
            <p style="color:#bbb;font-size:12px;margin:0;">
              &copy; 2026 ViralFlux &bull; Powered by SkyPulseForge
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
