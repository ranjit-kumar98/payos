import logging
import os

from celery import Task
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.bnpl_email.send_bnpl_loan_agreement_email"
)
def send_bnpl_loan_agreement_email(payload):
    try:
        sg_api_key = os.getenv("SENDGRID_API_KEY")
        from_email = os.getenv("SENDGRID_FROM_EMAIL")

        if not sg_api_key or not from_email:
            logger.error("SendGrid API key or from email not configured")
            return

        customer_email = payload.get("customer_email")
        customer_name = payload.get("customer_name", "Customer")
        loan_id = payload.get("loan_id")
        principal = payload.get("principal")
        tenure = payload.get("tenure_months")
        annual_interest_rate = payload.get("annual_interest_rate")
        monthly_emi = payload.get("monthly_emi")
        total_interest = payload.get("total_interest")
        total_repayment = payload.get("total_repayment")
        loan_status = payload.get("status")
        repayment_schedule = payload.get("repayment_schedule", [])

        if not customer_email:
            raise ValueError("customer_email is required")

        subject = f"BNPL Loan Agreement - Loan {loan_id}"

        body = f"""
        <html>
        <body>
            <p>Dear {customer_name},</p>

            <p>Your BNPL loan has been successfully created with the
            following details:</p>

            <ul>
                <li>Loan ID: {loan_id}</li>
                <li>Principal Amount: ₹{principal}</li>
                <li>Tenure: {tenure} months</li>
                <li>Annual Interest Rate:
                    {float(annual_interest_rate) * 100:.2f}%</li>
                <li>Monthly EMI: ₹{monthly_emi}</li>
                <li>Total Interest: ₹{total_interest}</li>
                <li>Total Repayment: ₹{total_repayment}</li>
                <li>Status: {loan_status}</li>
            </ul>

            <p><strong>Repayment Schedule</strong></p>

            <table border="1" cellpadding="5" cellspacing="0">
                <tr>
                    <th>Month</th>
                    <th>EMI</th>
                    <th>Interest</th>
                    <th>Principal</th>
                    <th>Remaining Balance</th>
                </tr>
        """

        for entry in repayment_schedule:
            body += f"""
                <tr>
                    <td>{entry.get("month")}</td>
                    <td>₹{entry.get("emi")}</td>
                    <td>₹{entry.get("interest")}</td>
                    <td>₹{entry.get("principal")}</td>
                    <td>₹{entry.get("remaining_balance")}</td>
                </tr>
            """

        body += """
            </table>

            <p>Thank you for choosing our BNPL service.</p>
            <p>Regards,<br/>PayOS Team</p>
        </body>
        </html>
        """

        message = Mail(
            from_email=from_email,
            to_emails=customer_email,
            subject=subject,
            html_content=body,
        )

        sg = SendGridAPIClient(sg_api_key)
        response = sg.send(message)

        logger.info(
            "BNPL loan agreement email sent to %s for loan %s, "
            "status code: %s",
            customer_email,
            loan_id,
            response.status_code,
        )

        return {
            "status": "sent",
            "loan_id": str(loan_id),
            "customer_email": customer_email,
            "sendgrid_status": response.status_code,
        }

    except Exception:
        logger.exception(
            "Failed to send BNPL loan agreement email"
        )
        raise