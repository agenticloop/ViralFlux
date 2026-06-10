from __future__ import annotations

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

logger = logging.getLogger(__name__)

_BRAND_COLOR = "#6C3BF5"  # ViralFlux purple


class EmailServiceError(Exception):
    """Raised when an email send operation fails."""


class EmailService:
    """Async SMTP email service for ViralFlux transactional emails."""

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        from_name: str,
        from_email: str,
    ) -> None:
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.from_name = from_name
        self.from_email = from_email

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    async def send_otp(
        self,
        to_email: str,
        otp: str,
        purpose: str = "verification",
    ) -> None:
        """Send a one-time-password email.

        purpose: 'verification' (account sign-up) or 'password_reset'.
        """
        if purpose == "password_reset":
            subject = "ViralFlux Password Reset Code"
        else:
            subject = "ViralFlux Email Verification Code"

        html = self._otp_template(otp, purpose)
        await self._send(to_email, subject, html)
        logger.info("OTP email sent to %s (purpose=%s)", to_email, purpose)

    async def send_approval_request(
        self,
        to_email: str,
        job_id: str,
        approve_token: str,
        preview_url: str,
    ) -> None:
        """Send a video approval email with approve/reject action links."""
        subject = "ViralFlux: Your Video Is Ready for Review"
        html = self._approval_template(job_id, approve_token, preview_url)
        await self._send(to_email, subject, html)
        logger.info(
            "Approval request email sent to %s for job %s", to_email, job_id
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _send(self, to: str, subject: str, html: str) -> None:
        """Send an HTML email via SMTP with STARTTLS."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to

        msg.attach(MIMEText(html, "html", "utf-8"))

        try:
            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                start_tls=True,
            )
        except Exception as exc:
            logger.exception("Failed to send email to %s: %s", to, exc)
            raise EmailServiceError(
                f"Email delivery failed to {to}: {exc}"
            ) from exc

    def _otp_template(self, otp: str, purpose: str) -> str:
        """Return an HTML email body containing the OTP code."""
        if purpose == "password_reset":
            heading = "Reset Your Password"
            body_text = (
                "We received a request to reset your ViralFlux password. "
                "Use the code below to complete the process. "
                "This code expires in 10 minutes."
            )
            footer_note = "If you did not request a password reset, ignore this email."
        else:
            heading = "Verify Your Email Address"
            body_text = (
                "Welcome to ViralFlux! Use the verification code below to "
                "confirm your email address and activate your account. "
                "This code expires in 10 minutes."
            )
            footer_note = "If you did not create a ViralFlux account, ignore this email."

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{heading}</title>
</head>
<body style="margin:0;padding:0;background:#0f0f0f;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f0f0f;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0"
               style="background:#1a1a2e;border-radius:12px;overflow:hidden;max-width:560px;">
          <!-- Header -->
          <tr>
            <td align="center" style="background:{_BRAND_COLOR};padding:28px 40px;">
              <h1 style="color:#fff;margin:0;font-size:22px;letter-spacing:1px;">
                ViralFlux
              </h1>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:40px;">
              <h2 style="color:#ffffff;font-size:20px;margin:0 0 16px;">{heading}</h2>
              <p style="color:#b0b0c0;font-size:15px;line-height:1.6;margin:0 0 28px;">
                {body_text}
              </p>
              <!-- OTP Box -->
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center">
                    <div style="display:inline-block;background:#0f0f0f;
                                border:2px solid {_BRAND_COLOR};border-radius:8px;
                                padding:18px 40px;letter-spacing:12px;
                                font-size:36px;font-weight:700;color:#ffffff;">
                      {otp}
                    </div>
                  </td>
                </tr>
              </table>
              <p style="color:#808090;font-size:13px;margin:28px 0 0;text-align:center;">
                {footer_note}
              </p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background:#111120;padding:20px 40px;text-align:center;">
              <p style="color:#505060;font-size:12px;margin:0;">
                &copy; 2026 ViralFlux &bull; Automate Your YouTube Shorts
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    def _approval_template(
        self,
        job_id: str,
        approve_token: str,
        preview_url: str,
    ) -> str:
        """Return an HTML email body with approve/reject action buttons."""
        from app.core.config import settings

        base_url = settings.APP_URL.rstrip("/")
        approve_url = f"{base_url}/api/v1/jobs/{job_id}/approve?token={approve_token}&action=approve"
        reject_url = f"{base_url}/api/v1/jobs/{job_id}/approve?token={approve_token}&action=reject"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Video Ready for Review</title>
</head>
<body style="margin:0;padding:0;background:#0f0f0f;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f0f0f;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0"
               style="background:#1a1a2e;border-radius:12px;overflow:hidden;max-width:560px;">
          <!-- Header -->
          <tr>
            <td align="center" style="background:{_BRAND_COLOR};padding:28px 40px;">
              <h1 style="color:#fff;margin:0;font-size:22px;letter-spacing:1px;">
                ViralFlux
              </h1>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:40px;">
              <h2 style="color:#ffffff;font-size:20px;margin:0 0 12px;">
                Your Video Is Ready for Review
              </h2>
              <p style="color:#b0b0c0;font-size:15px;line-height:1.6;margin:0 0 24px;">
                A new Short has been generated and is awaiting your approval
                before it's scheduled for upload. Preview it below and
                approve or reject with one click.
              </p>
              <!-- Preview button -->
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
                <tr>
                  <td align="center">
                    <a href="{preview_url}"
                       style="display:inline-block;background:#2a2a4a;color:#a0a0ff;
                              text-decoration:none;padding:12px 28px;border-radius:6px;
                              font-size:14px;font-weight:600;">
                      ▶ Watch Preview
                    </a>
                  </td>
                </tr>
              </table>
              <!-- Approve / Reject buttons -->
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td width="50%" align="center" style="padding-right:8px;">
                    <a href="{approve_url}"
                       style="display:block;background:#22c55e;color:#fff;
                              text-decoration:none;padding:14px 0;border-radius:6px;
                              font-size:15px;font-weight:700;text-align:center;">
                      Approve &amp; Schedule
                    </a>
                  </td>
                  <td width="50%" align="center" style="padding-left:8px;">
                    <a href="{reject_url}"
                       style="display:block;background:#ef4444;color:#fff;
                              text-decoration:none;padding:14px 0;border-radius:6px;
                              font-size:15px;font-weight:700;text-align:center;">
                      Reject
                    </a>
                  </td>
                </tr>
              </table>
              <p style="color:#606070;font-size:12px;margin:24px 0 0;text-align:center;">
                Job ID: {job_id}
              </p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background:#111120;padding:20px 40px;text-align:center;">
              <p style="color:#505060;font-size:12px;margin:0;">
                &copy; 2026 ViralFlux &bull; Automate Your YouTube Shorts
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
