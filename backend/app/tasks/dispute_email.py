import logging
import os

from celery import Task
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.dispute_email.send_dispute_raised_email"
)
def send_dispute_raised_email(payload):
    try:
        sg_api_key = os.getenv("SENDGRID_API_KEY")
        from_email = os.getenv("SENDGRID_FROM_EMAIL")

        if not sg_api_key or not from_email:
            logger.error("SendGrid API key or from email not configured")
            return

        merchant_email = payload.get("merchant_email")
        dispute_id = payload.get("dispute_id")
        reason = payload.get("reason")
        status = payload.get("status")
        raised_at = payload.get("raised_at")
        sla_deadline = payload.get("sla_deadline")

        if not merchant_email:
            raise ValueError("merchant_email is required")

        subject = f"Dispute Raised - Dispute ID {dispute_id}"

        body = f"""
        <html>
        <body>
            <p>Dear Merchant,</p>
            <p>A new dispute has been raised with the following details:</p>
            <ul>
                <li>Dispute ID: {dispute_id}</li>
                <li>Reason: {reason}</li>
                <li>Status: {status}</li>
                <li>Raised At: {raised_at}</li>
                <li>SLA Deadline: {sla_deadline}</li>
            </ul>
            <p>Please review the dispute at your earliest convenience.</p>
            <p>Regards,<br/>PayOS Team</p>
        </body>
        </html>
        """

        message = Mail(
            from_email=from_email,
            to_emails=merchant_email,
            subject=subject,
            html_content=body,
        )

        sg = SendGridAPIClient(sg_api_key)
        response = sg.send(message)

        logger.info(
            "Dispute raised email sent to %s for dispute %s, status code: %s",
            merchant_email,
            dispute_id,
            response.status_code,
        )

    except Exception:
        logger.exception("Failed to send dispute raised email")
        raise


@celery_app.task(
    name="app.tasks.dispute_email.send_dispute_resolution_email"
)
def send_dispute_resolution_email(payload):
    try:
        sg_api_key = os.getenv("SENDGRID_API_KEY")
        from_email = os.getenv("SENDGRID_FROM_EMAIL")

        if not sg_api_key or not from_email:
            logger.error("SendGrid API key or from email not configured")
            return

        merchant_email = payload.get("merchant_email")
        customer_email = payload.get("customer_email")
        dispute_id = payload.get("dispute_id")
        status = payload.get("status")
        resolution_notes = payload.get("resolution_notes")
        resolved_at = payload.get("resolved_at")

        if not merchant_email or not customer_email:
            raise ValueError("merchant_email and customer_email are required")

        subject = f"Dispute {status.capitalize()} - Dispute ID {dispute_id}"

        body = f"""
        <html>
        <body>
            <p>Dear Merchant and Customer,</p>
            <p>The dispute with the following details has been {status}:</p>
            <ul>
                <li>Dispute ID: {dispute_id}</li>
                <li>Status: {status}</li>
                <li>Resolution Notes: {resolution_notes}</li>
                <li>Resolved At: {resolved_at}</li>
            </ul>
            <p>Thank you for your attention.</p>
            <p>Regards,<br/>PayOS Team</p>
        </body>
        </html>
        """

        to_emails = [merchant_email, customer_email]

        message = Mail(
            from_email=from_email,
            to_emails=to_emails,
            subject=subject,
            html_content=body,
        )

        sg = SendGridAPIClient(sg_api_key)
        response = sg.send(message)

        logger.info(
            "Dispute resolution email sent to %s and %s for dispute %s, status code: %s",
            merchant_email,
            customer_email,
            dispute_id,
            response.status_code,
        )

    except Exception:
        logger.exception("Failed to send dispute resolution email")
        raise