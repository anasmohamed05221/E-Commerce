import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from core.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class EmailService:
    @staticmethod
    def _get_gmail_service():
        """Build an authenticated Gmail API service client."""
        creds = Credentials(
            token=None,
            refresh_token=settings.GMAIL_REFRESH_TOKEN,
            client_id=settings.GMAIL_CLIENT_ID,
            client_secret=settings.GMAIL_CLIENT_SECRET,
            token_uri="https://oauth2.googleapis.com/token"
        )
        return build("gmail", "v1", credentials=creds)

    @staticmethod
    def send_email(to_email: str, subject: str, body: str):
        """Send an HTML email via Gmail API. Skipped in test environment."""
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
            service = EmailService._get_gmail_service()

            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = settings.MAIL_FROM
            message["To"] = to_email
            message.attach(MIMEText(body, "html"))

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            service.users().messages().send(userId="me", body={"raw": raw}).execute()

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