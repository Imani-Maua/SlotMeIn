from fastapi import HTTPException, status
import resend
from app.database.auth import User
from app.config.config import Settings


settings = Settings()
resend.api_key = settings.RESEND_API_KEY
SECRET_KEY = settings.KEY
algorithm = "HS256"


def send_email(to_email:str, subject: str, html: str):

    resend.Emails.send({
         "from": "onboarding@resend.dev",
         "to": to_email,
         "subject": subject,
         "html": html
    })



def invite_message(invite_token: str, user: User):
    
    INVITE_EXPIRY_HOURS = 24
    invite_link = f"https://slotmein.vercel.app/accept-invite?token={invite_token}"
    name = user.username.split(".")[0].capitalize()

    subject = "You've been invited to SlotMeIn!"
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <body style="margin:0;padding:40px 20px;background-color:#F5F4EF;font-family:Inter,system-ui,sans-serif;">
      <div style="max-width:480px;margin:0 auto;background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 16px rgba(27,42,94,0.12);">
        
        <!-- Header -->
        <div style="background-color:#1B2A5E;padding:28px 32px;display:flex;align-items:center;gap:12px;">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="40" height="40" style="flex-shrink:0;">
            <rect width="100" height="100" rx="16" fill="#1B2A5E"/>
            <path d="M20,20 H40 C40,14 38,4 50,4 C62,4 60,14 60,20 H80 V40 C74,40 64,38 64,50 C64,62 74,60 80,60 V80 H60 C60,74 62,64 50,64 C38,64 40,74 40,80 H20 V60 C14,60 4,62 4,50 C4,38 14,40 20,40 V20Z" fill="#D4A843"/>
          </svg>
          <span style="color:#FFFFFF;font-size:20px;font-weight:700;letter-spacing:0.3px;">SlotMeIn</span>
        </div>
        <!-- Body -->
        <div style="padding:36px 32px;">
          <p style="margin:0 0 8px;font-size:22px;font-weight:700;color:#111827;">Hello, {name} 👋</p>
          <p style="margin:0 0 24px;font-size:15px;color:#4B5563;line-height:1.6;">
            You've been invited to join <strong>SlotMeIn</strong> as a <strong>{user.user_role}</strong>.<br/>
            Click the button below to set your password and activate your account.
          </p>
          <!-- CTA Button -->
          <div style="text-align:center;margin:32px 0;">
            <a href="{invite_link}"
               style="background-color:#D4A843;color:#1B2A5E;font-size:15px;font-weight:700;
                      padding:14px 36px;border-radius:9999px;text-decoration:none;display:inline-block;
                      letter-spacing:0.3px;">
              Accept Invitation
            </a>
          </div>
          <p style="margin:0;font-size:13px;color:#9CA3AF;text-align:center;">
            This link expires in {INVITE_EXPIRY_HOURS} hours.
          </p>
        </div>
        <!-- Footer -->
        <div style="border-top:1px solid #EDECEA;padding:20px 32px;text-align:center;">
          <p style="margin:0;font-size:12px;color:#9CA3AF;">
            If you didn't expect this invitation, you can safely ignore this email.
          </p>
        </div>
      </div>
    </body>
    </html>
    """

    try:
        send_email(to_email=user.email, subject=subject, html=html)
    except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send email: {e}")
    
    return {"message": f"Invite sent to {user.email}"}






