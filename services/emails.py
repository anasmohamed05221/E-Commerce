import resend
from core.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

resend.api_key = settings.RESEND_API_KEY

class EmailService:
    @staticmethod
    def send_email(to_email: str, subject: str, body: str):
        """Send an HTML email via Resend API. Skipped in test environment."""
        if settings.ENV == "testing":
            logger.info(
                "[TEST MODE] Email skipped",
                extra={"recipient": to_email, "subject": subject}
            )
            return
        
        logger.debug(
            "Attempting to send email",
            extra={"recipient": to_email, "subject": subject}
        )

        try:
            resend.Emails.send({
                "from": settings.MAIL_FROM,
                "to": to_email,
                "subject": subject,
                "html": body
            })
            logger.info(
                "Email sent successfully",
                extra={"recipient": to_email, "subject": subject}
            )
        except Exception as e:
            logger.error(
                "Failed to send email",
                extra={"recipient": to_email, "subject": subject, "error": str(e)}
            )
            raise