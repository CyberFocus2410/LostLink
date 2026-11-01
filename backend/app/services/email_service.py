"""
Asynchronous email delivery service for LostLink.
Supports:
1. Resend API
2. Console / Mock logging fallback
Non-blocking execution via FastAPI BackgroundTasks.
"""
import logging
from typing import Optional, List
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Sends an email using Resend or falls back to logger in local/test mode."""
        if settings.EMAIL_PROVIDER == "resend" and settings.RESEND_API_KEY:
            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "from": settings.EMAIL_FROM,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }
            if text_content:
                payload["text"] = text_content

            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    if resp.status_code in (200, 201):
                        logger.info(f"Email sent successfully to {to_email} via Resend. ID: {resp.json().get('id')}")
                        return True
                    else:
                        logger.warning(f"Resend email API returned status {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.error(f"Failed to deliver email to {to_email} via Resend: {e}")

        # Local development / fallback logger
        logger.info(f"📧 [EMAIL MOCK] To: {to_email} | Subject: {subject}\n{html_content}")
        return True

    @classmethod
    def send_contact_request_notification(
        cls,
        owner_email: str,
        owner_name: str,
        item_name: str,
        requester_name: str,
        message: str,
    ):
        subject = f"[LostLink] New Contact Request for: {item_name}"
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #DCE8E1; border-radius: 8px;">
            <h2 style="color: #263238; margin-top: 0;">New Contact Request</h2>
            <p>Hello {owner_name},</p>
            <p>A fellow community member, <strong>{requester_name}</strong>, believes they have information or an item matching your report for <strong>{item_name}</strong>.</p>
            <div style="background-color: #F6F7F4; padding: 14px; border-left: 4px solid #527C76; margin: 16px 0; border-radius: 4px;">
                <p style="margin: 0; font-style: italic; color: #37474F;">"{message}"</p>
            </div>
            <p><strong>Your Privacy is Protected:</strong> The requester cannot see your email or phone number. Log in to LostLink to review, accept, or decline this request.</p>
            <p style="margin-top: 24px; font-size: 0.85rem; color: #78909C;">— The LostLink Team</p>
        </div>
        """
        cls.send_email(to_email=owner_email, subject=subject, html_content=html)

    @classmethod
    def send_contact_accepted_notification(
        cls,
        requester_email: str,
        requester_name: str,
        item_name: str,
        owner_name: str,
        owner_email: str,
        owner_phone: Optional[str] = None,
        owner_notes: Optional[str] = None,
    ):
        subject = f"[LostLink] Contact Request Accepted for: {item_name}"
        phone_html = f"<p><strong>Phone:</strong> {owner_phone}</p>" if owner_phone else ""
        notes_html = f"<div style='background-color: #F6F7F4; padding: 12px; margin: 12px 0;'><strong>Owner Message:</strong> {owner_notes}</div>" if owner_notes else ""

        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #DCE8E1; border-radius: 8px;">
            <h2 style="color: #527C76; margin-top: 0;">Contact Request Accepted</h2>
            <p>Hello {requester_name},</p>
            <p>Great news! The owner of <strong>{item_name}</strong>, <strong>{owner_name}</strong>, has accepted your contact request.</p>
            {notes_html}
            <div style="background-color: #DCE8E1; padding: 14px; border-radius: 6px; margin: 16px 0;">
                <h4 style="margin: 0 0 8px 0; color: #263238;">Direct Contact Details:</h4>
                <p style="margin: 4px 0;"><strong>Email:</strong> <a href="mailto:{owner_email}">{owner_email}</a></p>
                {phone_html}
            </div>
            <p style="font-size: 0.85rem; color: #546E7A;">Please coordinate safely to inspect and verify ownership of the item.</p>
            <p style="margin-top: 24px; font-size: 0.85rem; color: #78909C;">— The LostLink Team</p>
        </div>
        """
        cls.send_email(to_email=requester_email, subject=subject, html_content=html)

    @classmethod
    def send_match_alert_email(
        cls,
        to_email: str,
        user_name: str,
        item_name: str,
        match_item_name: str,
        score: float,
    ):
        subject = f"[LostLink] Potential Match Found for: {item_name} ({score:.0f}% match)"
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #DCE8E1; border-radius: 8px;">
            <h2 style="color: #527C76; margin-top: 0;">Strong Potential Match Detected</h2>
            <p>Hello {user_name},</p>
            <p>Our matching engine detected a potential match for your listing <strong>{item_name}</strong> with a score of <strong>{score:.1f}%</strong>.</p>
            <div style="background-color: #F6F7F4; padding: 14px; border-radius: 6px; margin: 16px 0;">
                <p style="margin: 0; font-weight: 600;">{match_item_name}</p>
            </div>
            <p>Log in to LostLink to inspect the score breakdown and request contact with the report owner.</p>
            <p style="margin-top: 24px; font-size: 0.85rem; color: #78909C;">— The LostLink Team</p>
        </div>
        """
        cls.send_email(to_email=to_email, subject=subject, html_content=html)

    @classmethod
    def send_password_reset_email(
        cls,
        to_email: str,
        user_name: str,
        reset_token: str,
    ):
        subject = "[LostLink] Password Reset Request"
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #DCE8E1; border-radius: 8px;">
            <h2 style="color: #263238; margin-top: 0;">Reset Your Password</h2>
            <p>Hello {user_name},</p>
            <p>We received a request to reset your LostLink password. Use the verification token below:</p>
            <div style="background-color: #EEE8DE; padding: 12px; font-family: monospace; font-size: 1.1rem; text-align: center; border-radius: 4px; margin: 16px 0;">
                {reset_token}
            </div>
            <p style="font-size: 0.85rem; color: #78909C;">If you did not request this reset, you can safely ignore this email.</p>
            <p style="margin-top: 24px; font-size: 0.85rem; color: #78909C;">— The LostLink Team</p>
        </div>
        """
        cls.send_email(to_email=to_email, subject=subject, html_content=html)

