import uuid
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

from config import settings
from sheets_client import get_sheet
from services.user_service import _find_user_row
from services.admin_service import _log_audit


def submit_proof(payload: dict) -> dict:
    user_id = payload.get("user_id")
    user_email = payload.get("user_email")
    plan_id = payload.get("plan_id")
    plan_name = payload.get("plan_name")
    amount = float(payload.get("amount", 0))
    emails = int(payload.get("emails", 0))
    txn_id = payload.get("transaction_id", "").strip()
    proof = payload.get("payment_proof", "")

    if not (6 <= len(txn_id) <= 50):
        raise ValueError("Transaction ID must be between 6 and 50 characters")
    if not (50 <= amount <= 10000):
        raise ValueError("Amount must be between 50 and 10000")

    sheet, row_idx, headers = _find_user_row(user_id)
    if row_idx == -1:
        raise ValueError("User not found")

    # check user status
    user_row = sheet.row_values(row_idx)
    status_col = headers.index("status")
    if len(user_row) > status_col and user_row[status_col].lower() == "blocked":
        raise ValueError("User account is blocked")

    pymt_sheet = get_sheet("Payments")
    all_pymts = pymt_sheet.get_all_values()

    recent_submissions = 0
    now = datetime.utcnow()

    if len(all_pymts) > 1:
        for row in all_pymts[1:]:
            if len(row) > 7 and row[7].strip() == txn_id:
                raise ValueError("Transaction ID already exists")
            if len(row) > 1 and row[1] == user_id and len(row) > 10:
                try:
                    sub_time = datetime.fromisoformat(row[10])
                    if now - sub_time < timedelta(days=1):
                        recent_submissions += 1
                except Exception:
                    pass

    if recent_submissions >= 3:
        raise ValueError("Too many submissions in the last 24 hours")

    pay_id = f"pay_{int(now.timestamp())}_{uuid.uuid4().hex[:9]}"

    pymt_sheet.append_row([
        pay_id, user_id, user_email, plan_id, plan_name, str(amount), str(emails),
        txn_id, proof, "pending", now.isoformat(), "", "", ""
    ], value_input_option="USER_ENTERED")

    # Notify admin
    try:
        msg = EmailMessage()
        msg["Subject"] = "New Payment Proof Submitted"
        msg["From"] = settings.MAIL_FROM
        msg["To"] = settings.ADMIN_EMAIL
        msg.set_content(f"User {user_email} submitted payment proof for {plan_name} ({amount} Rs). Txn ID: {txn_id}")

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
    except Exception:
        pass  # dont fail submission if notify fails

    return {"payment_id": pay_id, "message": "Payment proof submitted successfully"}


def get_pending(payload: dict = {}) -> list:
    sheet = get_sheet("Payments")
    all_pymts = sheet.get_all_values()
    if len(all_pymts) < 2:
        return []
    headers = all_pymts[0]
    return [dict(zip(headers, row)) for row in all_pymts[1:] if len(row) > 9 and row[9] == "pending"]


def _find_payment(payment_id: str):
    """Returns (sheet, row_idx, headers, row_data) — always 4 values."""
    sheet = get_sheet("Payments")
    all_rows = sheet.get_all_values()
    if not all_rows:
        return sheet, -1, [], None
    headers = all_rows[0]
    for i, row in enumerate(all_rows):
        if i > 0 and len(row) > 0 and row[0] == payment_id:
            return sheet, i + 1, headers, row
    return sheet, -1, headers, None


def approve(payload: dict) -> dict:
    payment_id = payload.get("payment_id")
    admin_email = payload.get("admin_email", settings.ADMIN_EMAIL)

    if not payment_id:
        raise ValueError("payment_id is required")

    sheet, row_idx, headers, row = _find_payment(payment_id)
    if row_idx == -1:
        raise ValueError("Payment not found")
    if len(row) > 9 and row[9] != "pending":
        raise ValueError("Payment is not pending")

    sheet.update_cell(row_idx, headers.index("status") + 1, "approved")
    sheet.update_cell(row_idx, headers.index("reviewed_at") + 1, datetime.utcnow().isoformat())
    sheet.update_cell(row_idx, headers.index("reviewed_by") + 1, admin_email)

    user_id = row[1]
    emails_to_add = int(row[6])

    u_sheet, u_row_idx, u_headers = _find_user_row(user_id)
    if u_row_idx != -1:
        tot_limit_col = u_headers.index("total_limit") + 1
        current_limit = int(u_sheet.cell(u_row_idx, tot_limit_col).value or 0)
        u_sheet.update_cell(u_row_idx, tot_limit_col, str(current_limit + emails_to_add))

    _log_audit("APPROVE_PAYMENT", admin_email, user_id, f"Approved {emails_to_add} emails", "pending", "approved")

    try:
        msg = EmailMessage()
        msg["Subject"] = "Payment Approved"
        msg["From"] = settings.MAIL_FROM
        msg["To"] = row[2]
        msg.set_content(f"Your payment of {row[5]} has been approved. {emails_to_add} emails added to your limit.")
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
    except Exception:
        pass

    return {"message": "Payment approved"}


def reject(payload: dict) -> dict:
    payment_id = payload.get("payment_id")
    reason = payload.get("reason", "Invalid proof")
    admin_email = payload.get("admin_email", settings.ADMIN_EMAIL)

    if not payment_id:
        raise ValueError("payment_id is required")

    sheet, row_idx, headers, row = _find_payment(payment_id)
    if row_idx == -1:
        raise ValueError("Payment not found")
    if len(row) > 9 and row[9] != "pending":
        raise ValueError("Payment is not pending")

    sheet.update_cell(row_idx, headers.index("status") + 1, "rejected")
    sheet.update_cell(row_idx, headers.index("reviewed_at") + 1, datetime.utcnow().isoformat())
    sheet.update_cell(row_idx, headers.index("reviewed_by") + 1, admin_email)
    sheet.update_cell(row_idx, headers.index("rejection_reason") + 1, reason)

    _log_audit("REJECT_PAYMENT", admin_email, row[1], reason, "pending", "rejected")

    try:
        msg = EmailMessage()
        msg["Subject"] = "Payment Rejected"
        msg["From"] = settings.MAIL_FROM
        msg["To"] = row[2]
        msg.set_content(f"Your payment proof was rejected. Reason: {reason}.")
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
    except Exception:
        pass

    return {"message": "Payment rejected"}


def get_analytics(payload: dict = {}) -> dict:
    sheet = get_sheet("Payments")
    all_rows = sheet.get_all_values()

    if len(all_rows) < 2:
        return {"total_revenue": 0, "approved": 0, "pending": 0, "rejected": 0, "recent_payments": []}

    headers = all_rows[0]
    revenue = 0.0
    status_counts = {"approved": 0, "pending": 0, "rejected": 0}

    recent = []

    for row in all_rows[1:]:
        st = row[headers.index("status")] if len(row) > headers.index("status") else ""
        if st in status_counts:
            status_counts[st] += 1

        if st == "approved":
            amount = float(row[headers.index("amount")]) if len(row) > headers.index("amount") else 0
            revenue += amount

        recent.append(dict(zip(headers, row)))

    recent.reverse()

    return {
        "total_revenue": revenue,
        **status_counts,
        "recent_payments": recent[:10],
    }
