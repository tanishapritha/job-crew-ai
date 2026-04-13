import random
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

from config import settings
from sheets_client import get_sheet
from utils.auth_utils import hash_password

def request_otp(payload: dict) -> dict:
    email = payload.get("email")
    if not email:
        raise ValueError("Email is required")
        
    users_sheet = get_sheet("Users")
    all_users = users_sheet.get_all_values()
    
    user_found = False
    for row in all_users[1:]:
        if len(row) > 2 and row[2].strip().lower() == email.strip().lower():
            status = row[8] if len(row) > 8 else "active"
            if status.lower() == "blocked":
                raise ValueError("Account is blocked")
            user_found = True
            break
            
    if not user_found:
        raise ValueError("Email not found")
        
    otp = str(random.randint(100000, 999999))
    expiry = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
    
    otp_sheet = get_sheet("Password_OTP")
    # Headers: email | otp | expiry | used | created_at
    otp_sheet.append_row([
        email.strip().lower(),
        otp,
        expiry,
        "FALSE",
        datetime.utcnow().isoformat()
    ], value_input_option="USER_ENTERED")
    
    # Send email
    msg = EmailMessage()
    msg["Subject"] = "Password Reset OTP"
    msg["From"] = settings.MAIL_FROM
    msg["To"] = email
    msg.set_content(f"Your OTP for password reset is: {otp}\nIt will expire in 15 minutes.")
    
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        raise ValueError(f"Failed to send email: {str(e)}")
        
    return {"message": "OTP sent to your email"}

def verify_otp(payload: dict) -> dict:
    email = payload.get("email")
    otp = payload.get("otp")
    new_password = payload.get("newPassword")
    
    if not all([email, otp, new_password]):
        raise ValueError("Email, OTP, and new password are required")
        
    otp_sheet = get_sheet("Password_OTP")
    all_otps = otp_sheet.get_all_values()
    
    matching_row_idx = -1
    for i, row in enumerate(all_otps):
        if i == 0: continue
        # email | otp | expiry | used | created_at
        if len(row) >= 4 and row[0] == email.strip().lower() and row[1] == otp and row[3].upper() == "FALSE":
            # check expiry
            expiry = datetime.fromisoformat(row[2])
            if datetime.utcnow() <= expiry:
                matching_row_idx = i + 1
                break
                
    if matching_row_idx == -1:
        raise ValueError("Invalid or expired OTP")
        
    users_sheet = get_sheet("Users")
    all_users = users_sheet.get_all_values()
    
    user_row_idx = -1
    for i, row in enumerate(all_users):
        if i == 0: continue
        if len(row) > 2 and row[2].strip().lower() == email.strip().lower():
            user_row_idx = i + 1
            break
            
    if user_row_idx == -1:
        raise ValueError("User not found")
        
    # update password_hash in Users sheet (column 4, 1-indexed)
    pw_hash = hash_password(new_password)
    users_sheet.update_cell(user_row_idx, 4, pw_hash)
    
    # mark OTP used in Password_OTP sheet (column 4)
    otp_sheet.update_cell(matching_row_idx, 4, "TRUE")
    
    return {"message": "Password reset successful"}
