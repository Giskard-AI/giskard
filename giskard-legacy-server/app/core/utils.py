import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from django.core.mail import send_mail
from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings as django_settings
from smtplib import SMTPException

from jinja2 import Template
from jose import jwt

from bs4 import BeautifulSoup

from app.core.config import settings

django_settings.configure()

email_backend = EmailBackend(
    host=settings.SMTP_HOST,
    port=settings.SMTP_PORT,
    username=settings.SMTP_USER,
    password=settings.SMTP_PASSWORD,
    use_tls=settings.SMTP_TLS,
    use_ssl=not settings.SMTP_TLS,
    timeout=5,
    fail_silently=False,
)


def send_email(
    email_to: str,
    subject: str = "",
    html_template: str = "",
    template_environment: Dict[str, Any] = {},
    from_email: str = settings.WELCOME_FROM_EMAIL,
) -> None:
    if not settings.EMAILS_ENABLED:
        logging.warning("Trying to send and email, while EMAILS_ENABLED is not set")
        return
    html = Template(html_template).render(**template_environment)
    text = BeautifulSoup(html, "html.parser").get_text().strip()
    try:
        logging.info(f"Sending email '{subject}'...")
        result = send_mail(
            from_email=from_email,
            recipient_list=[email_to],
            subject=subject,
            message=text,
            html_message=html,
            connection=email_backend,
        )
        logging.info("Email sent!")
        logging.debug(f"Result: {result}")
    except SMTPException as e:
        logging.error(f"Failed to send email: {e}")


def send_test_email(email_to: str) -> None:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    with open(Path(settings.EMAIL_TEMPLATES_DIR) / "test_email.html") as f:
        html_template = f.read()
    template_environment = {"project_name": settings.PROJECT_NAME, "email": email_to}
    send_email(email_to, subject, html_template, template_environment)


def send_reset_password_email(email_to: str) -> None:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password recovery"
    with open(Path(settings.EMAIL_TEMPLATES_DIR) / "reset_password.html") as f:
        html_template = f.read()
    server_host = settings.SERVER_HOST
    password_reset_token = generate_password_reset_token(email_to)
    link = f"{server_host}/reset-password?token={password_reset_token}"
    template_environment = {
        "project_name": settings.PROJECT_NAME,
        "email": email_to,
        "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
        "link": link,
    }
    send_email(email_to, subject, html_template, template_environment)


def send_new_account_email(email_to: str, new_user_id: str) -> None:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - New account for user {new_user_id}"
    with open(Path(settings.EMAIL_TEMPLATES_DIR) / "new_account.html") as f:
        html_template = f.read()
    host = settings.SERVER_HOST
    password_reset_token = generate_password_reset_token(email_to)
    link_reset = f"{host}/reset-password?token={password_reset_token}"
    template_environment = {
        "project_name": settings.PROJECT_NAME,
        "user_id": new_user_id,
        "email": email_to,
        "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
        "link_host": host,
        "link_reset": link_reset,
    }
    send_email(email_to, subject, html_template, template_environment)


def send_invite_email(email_to: str, sender_email: str, sender_id: str) -> None:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - You have been invited to sign up"
    with open(Path(settings.EMAIL_TEMPLATES_DIR) / "invite_signup.html") as f:
        html_template = f.read()
    token = generate_signup_token(sender_email, email_to)
    link = f"{settings.SERVER_HOST}/auth/signup?to={email_to}&token={token}"
    template_environment = {
        "project_name": settings.PROJECT_NAME,
        "sender": sender_id,
        "valid_hours": settings.EMAIL_SIGNUP_TOKEN_EXPIRE_HOURS,
        "signup_link": link,
    }
    send_email(email_to, subject, html_template, template_environment)


def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        expiryDate = datetime.fromtimestamp(decoded_token["exp"])
        if expiryDate < datetime.utcnow():
            return None
        return decoded_token["sub"]
    except jwt.JWTError:
        return None


def generate_signup_token(issuer: str, recipient: str = "") -> str:
    # Recipient is made optional for the case of generating signup link from UI
    delta = timedelta(hours=settings.EMAIL_SIGNUP_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "iss": issuer, "sub": recipient},
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    return encoded_jwt


def decode_signup_token(token: str) -> Optional[str]:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        expiryDate = datetime.fromtimestamp(decoded_token["exp"])
        if expiryDate < datetime.utcnow():
            return None
        return (decoded_token["iss"], decoded_token["sub"])
    except jwt.JWTError as e:
        logging.error(f"Exception while decoding JWT token: {e}")
        return None


def verify_api_access_token(token: str) -> Optional[str]:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return decoded_token["sub"]
    except jwt.JWTError as e:
        logging.error(f"Exception while decoding JWT token: {e}")
        return None


def transmogrify(text: str) -> str:
    """
    Generate a cleaner string, without non-ascii or special characters,
    that can be used as a key and displayed in URL
    """
    # filter non ascii
    ascii_text_ = text.encode("ascii", "ignore").decode()
    # filter special characters
    without_special = "".join(e for e in ascii_text_ if e.isalnum() or e.isspace() or e == "-")
    return without_special.strip().replace(" ", "-").lower()


def send_new_feedback_notification(
    recipient: str,
    originator_name: str,
    project_id: int,
    project_name: str,
    feedback_id: int,
    content: str,
) -> None:
    send_feedback_notification(
        recipient,
        "You received a feedback!",
        "new_feedback.html",
        originator_name,
        project_id,
        project_name,
        feedback_id,
        content,
    )


def send_feedback_comment_notification(
    recipient: str,
    originator_name: str,
    project_id: int,
    project_name: str,
    feedback_id: int,
    content: str,
) -> None:
    send_feedback_notification(
        recipient,
        "New comment on feedback",
        "new_feedback_comment.html",
        originator_name,
        project_id,
        project_name,
        feedback_id,
        content,
    )


def send_feedback_reply_notification(
    recipient: str,
    originator_name: str,
    project_id: int,
    project_name: str,
    feedback_id: int,
    content: str,
) -> None:
    send_feedback_notification(
        recipient,
        "You received a reply",
        "new_feedback_reply.html",
        originator_name,
        project_id,
        project_name,
        feedback_id,
        content,
    )


def send_feedback_notification(
    email_to,
    subject,
    template_name,
    originator_name,
    project_id,
    project_name,
    feedback_id,
    content,
):
    with open(Path(settings.EMAIL_TEMPLATES_DIR) / template_name) as f:
        html_template = f.read()
    template_environment = {
        "platform": settings.PROJECT_NAME,
        "project": project_name,
        "commenter": originator_name,
        "feedback_link": f"{settings.SERVER_HOST}/main/projects/{project_id}/feedbacks/{feedback_id}",
        "message": content.replace("\n", "<br>"),
    }
    if settings.NOTIFICATION_FROM_EMAIL:
        send_email(
            email_to=email_to,
            subject=f"{settings.PROJECT_NAME} - {subject}",
            html_template=html_template,
            template_environment=template_environment,
            from_email=settings.NOTIFICATION_FROM_EMAIL,
        )
