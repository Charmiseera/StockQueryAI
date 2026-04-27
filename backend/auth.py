"""
auth.py — Authentication utilities for StockQuery AI
JWT creation/verification, password hashing, SMTP email sending.
"""

import os
import secrets
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Header

log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────
JWT_SECRET    = os.getenv("JWT_SECRET", "stockquery-super-secret-key-change-in-prod")
ALGORITHM     = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FRONTEND_URL  = os.getenv("FRONTEND_URL", "http://localhost:5173")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Password ──────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# ── Tokens ────────────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

def generate_secure_token() -> str:
    return secrets.token_urlsafe(32)

# ── Current User Dependency ───────────────────────────────────
async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    try:
        return decode_token(token)
    except HTTPException:
        return None

async def require_current_user(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user

# ── SMTP Email ────────────────────────────────────────────────
def _send_email(to: str, subject: str, html_body: str) -> bool:
    smtp_is_placeholder = (
        SMTP_USER in {"", "your-email@gmail.com"}
        or SMTP_PASSWORD in {"", "your-gmail-app-password"}
    )
    if smtp_is_placeholder:
        log.warning("[AUTH] SMTP not configured — email not sent.")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"StockQuery AI <{SMTP_USER}>"
        msg["To"]      = to
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASSWORD)
            s.sendmail(SMTP_USER, to, msg.as_string())
        log.info(f"[AUTH] Email sent to {to}: {subject}")
        return True
    except Exception as e:
        log.error(f"[AUTH] Failed to send email to {to}: {e}")
        return False

def send_verification_email(to: str, token: str) -> bool:
    link = f"{FRONTEND_URL}/verify-email?token={token}"
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:520px;margin:0 auto;background:#0a0a0a;color:#e0e0e0;border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#00ff88,#00d4ff);padding:32px;text-align:center;">
        <h1 style="margin:0;color:#0a0a0a;font-size:24px;font-weight:700;">StockQuery AI</h1>
        <p style="margin:8px 0 0;color:#0a0a0a;opacity:0.8;">Verify your email address</p>
      </div>
      <div style="padding:32px;">
        <p style="font-size:16px;color:#ccc;">Click the button below to verify your email and activate your account.</p>
        <a href="{link}" style="display:inline-block;margin:24px 0;padding:14px 32px;background:linear-gradient(135deg,#00ff88,#00d4ff);color:#0a0a0a;text-decoration:none;border-radius:8px;font-weight:700;font-size:15px;">
          Verify Email
        </a>
        <p style="font-size:13px;color:#666;">Link expires in 24 hours. If you didn't sign up, ignore this email.</p>
        <hr style="border-color:#222;margin:24px 0;">
        <p style="font-size:12px;color:#444;">{link}</p>
      </div>
    </div>
    """
    return _send_email(to, "Verify your StockQuery AI account", html)

def send_reset_email(to: str, token: str) -> bool:
    link = f"{FRONTEND_URL}/reset-password?token={token}"
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:520px;margin:0 auto;background:#0a0a0a;color:#e0e0e0;border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#ff4488,#ff6644);padding:32px;text-align:center;">
        <h1 style="margin:0;color:#fff;font-size:24px;font-weight:700;">StockQuery AI</h1>
        <p style="margin:8px 0 0;color:#fff;opacity:0.85;">Password Reset Request</p>
      </div>
      <div style="padding:32px;">
        <p style="font-size:16px;color:#ccc;">We received a request to reset your password. Click below to set a new one.</p>
        <a href="{link}" style="display:inline-block;margin:24px 0;padding:14px 32px;background:linear-gradient(135deg,#ff4488,#ff6644);color:#fff;text-decoration:none;border-radius:8px;font-weight:700;font-size:15px;">
          Reset Password
        </a>
        <p style="font-size:13px;color:#666;">Link expires in 1 hour. If you didn't request this, ignore this email.</p>
        <hr style="border-color:#222;margin:24px 0;">
        <p style="font-size:12px;color:#444;">{link}</p>
      </div>
    </div>
    """
    return _send_email(to, "Reset your StockQuery AI password", html)
