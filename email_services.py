import os

import resend


class EmailService:
    resend.api_key = os.environ.get("RESEND_API_KEY")

    async def send_email(address, subject, message):
        resend.Emails.send(
            {
                "from": "donotreply@glitchads.ai",
                "to": address,
                "subject": subject,
                "html": message,
            }
        )
