"""SMTP delivery for background task assignment notifications."""

import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import Settings, get_settings

logger = logging.getLogger("taskhub.notifications")


def send_task_assignment_email(
    recipient_email: str,
    task_title: str,
    project_name: str,
    task_id: int,
) -> None:
    """Send a plain-text assignment notice without exposing SMTP details."""

    settings = get_settings()
    if not settings.EMAIL_NOTIFICATIONS_ENABLED:
        return

    if not settings.SMTP_HOST:
        logger.warning(
            "Task assignment email skipped because SMTP is not configured "
            "for task_id=%s",
            task_id,
        )
        return

    try:
        message = EmailMessage()
        message["Subject"] = f"TaskHub: you were assigned to {task_title}"
        message["From"] = settings.SMTP_SENDER_EMAIL
        message["To"] = recipient_email
        message.set_content(
            "You have been assigned a task in TaskHub.\n\n"
            f"Task: {task_title}\n"
            f"Project: {project_name}\n"
            f"Task ID: {task_id}\n"
        )

        if settings.SMTP_USE_SSL:
            with smtplib.SMTP_SSL(
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                timeout=10,
                context=ssl.create_default_context(),
            ) as smtp:
                _authenticate_and_send(smtp, settings, message)
        else:
            with smtplib.SMTP(
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                timeout=10,
            ) as smtp:
                if settings.SMTP_USE_STARTTLS:
                    smtp.starttls(context=ssl.create_default_context())
                _authenticate_and_send(smtp, settings, message)
    except Exception:
        # SMTP exceptions can contain server diagnostics. Log only the task ID.
        logger.error("Task assignment email delivery failed for task_id=%s", task_id)


def _authenticate_and_send(
    smtp: smtplib.SMTP,
    settings: Settings,
    message: EmailMessage,
) -> None:
    """Authenticate when configured, then deliver the prepared message."""

    username = settings.SMTP_USERNAME
    password = settings.SMTP_PASSWORD
    if username is not None and password is not None:
        smtp.login(username, password.get_secret_value())
    smtp.send_message(message)
