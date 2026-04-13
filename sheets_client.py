import gspread
import os
from config import settings

_client = None
_spreadsheet = None

# Header definitions for auto-bootstrap on first run
SHEET_HEADERS = {
    "Users": [
        "user_id", "name", "email", "password_hash", "domains",
        "daily_limit", "total_limit", "emails_sent", "status",
        "created_at", "location_1", "location_2", "location_3",
        "remote_jobs", "experience_level", "min_salary",
        "phone", "username"
    ],
    "Payments": [
        "payment_id", "user_id", "user_email", "plan_id", "plan_name",
        "amount", "emails", "transaction_id", "payment_proof",
        "status", "submitted_at", "reviewed_at",
        "reviewed_by", "rejection_reason"
    ],
    "Password_OTP": [
        "email", "otp", "expiry", "used", "created_at"
    ],
    "Audit_Log": [
        "timestamp", "action", "admin_email", "target_user",
        "reason", "old_value", "new_value"
    ],
    "System_Settings": [
        "key", "value"
    ],
    "Fetched_Jobs": [
        "timestamp", "user_id", "job_id", "title", "company",
        "location", "description", "salary_min", "salary_max",
        "contract_type", "created", "redirect_url", "matched_domain", "source"
    ],
}


def get_client() -> gspread.client.Client:
    global _client
    if _client is None:
        if not os.path.exists(settings.GOOGLE_SERVICE_ACCOUNT_FILE):
            raise ValueError(f"Service account file {settings.GOOGLE_SERVICE_ACCOUNT_FILE} not found")
        _client = gspread.service_account(filename=settings.GOOGLE_SERVICE_ACCOUNT_FILE)
    return _client


def get_spreadsheet() -> gspread.Spreadsheet:
    global _spreadsheet
    if _spreadsheet is None:
        client = get_client()
        _spreadsheet = client.open_by_key(settings.SPREADSHEET_ID)
    return _spreadsheet


def get_sheet(name: str) -> gspread.worksheet.Worksheet:
    spreadsheet = get_spreadsheet()
    try:
        ws = spreadsheet.worksheet(name)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=name, rows="1000", cols="20")

    # Auto-bootstrap headers if missing and we have a definition
    if name in SHEET_HEADERS:
        existing = ws.get_all_values()
        expected_headers = SHEET_HEADERS[name]
        if not existing:
            # Sheet is completely empty — add headers
            ws.append_row(expected_headers, value_input_option="USER_ENTERED")
            if name == "System_Settings":
                ws.append_row(["system_enabled", "TRUE"], value_input_option="USER_ENTERED")
        elif not existing[0] or existing[0][0] != expected_headers[0]:
            # Row 1 is data or empty, not headers — insert headers above existing data
            ws.insert_row(expected_headers, 1, value_input_option="USER_ENTERED")

    return ws
