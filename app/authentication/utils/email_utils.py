from fastapi import HTTPException, status
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.database.auth import User
from app.config.config import Settings


settings = Settings()
SECRET_KEY = settings.KEY
algorithm = "HS256"
SMTP_HOST = settings.SMTP_HOST
SMTP_PORT = int(settings.SMTP_PORT)
SMTP_USER = settings.SMTP_USER
SMTP_PASS = settings.SMTP_PASS

def send_email(to_email:str, subject: str, body: str):

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
            print(f"Email successfully sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise



def invite_message(invite_token: str, user: User):
    
    INVITE_EXPIRY_HOURS = 24
    invite_link = f"https://shiftly.app/register?token={invite_token}"
    name = user.username.split(".")[0].capitalize()

    subject = "You've been invited to Shiftly!"
    body = f""" 
Hello {name},
You’ve been invited to join Shiftly as a {user.user_role}.

    Registration link (valid {INVITE_EXPIRY_HOURS} h): {invite_link}

    Please login and change your password immediately after first access.
    """

    try:
        send_email(to_email=user.email, subject=subject, body=body)
    except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send email: {e}")
    
    return {"message": f"Invite sent to {user.email}"}






