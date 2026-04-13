import gspread.utils
from sheets_client import get_sheet
from services.admin_service import get_system_settings


def _find_user_row(user_id: str):
    sheet = get_sheet("Users")
    all_rows = sheet.get_all_values()
    if not all_rows:
        return None, -1, None
    headers = all_rows[0]
    for i, row in enumerate(all_rows):
        if i > 0 and len(row) > 0 and row[0] == user_id:
            return sheet, i + 1, headers
    return sheet, -1, headers


def update_profile(payload: dict) -> dict:
    user_id = payload.get("user_id")
    if not user_id:
        raise ValueError("user_id is required")

    sheet, row_idx, headers = _find_user_row(user_id)
    if row_idx == -1:
        raise ValueError("User not found")

    # Check username uniqueness if provided
    new_username = payload.get("username")
    if new_username:
        all_rows = sheet.get_all_values()
        for i, row in enumerate(all_rows):
            if i > 0 and i + 1 != row_idx and len(row) > 17:
                if row[17].strip().lower() == new_username.strip().lower():
                    raise ValueError("Username already taken")

    # Update each field individually (reliable across gspread versions)
    for key, value in payload.items():
        if key == "user_id":
            continue
        if key in headers:
            col_idx = headers.index(key) + 1
            sheet.update_cell(row_idx, col_idx, str(value))

    return {"message": "Profile updated successfully"}


def update_domains(payload: dict) -> dict:
    user_id = payload.get("user_id")
    domains = payload.get("domains")
    if not user_id or domains is None:
        raise ValueError("user_id and domains are required")

    sheet, row_idx, headers = _find_user_row(user_id)
    if row_idx == -1:
        raise ValueError("User not found")

    col_idx = headers.index("domains") + 1
    sheet.update_cell(row_idx, col_idx, domains)
    return {"message": "Domains updated successfully"}


def toggle_status(payload: dict) -> dict:
    user_id = payload.get("user_id")
    status = payload.get("status")
    if not user_id or not status:
        raise ValueError("user_id and status are required")

    sheet, row_idx, headers = _find_user_row(user_id)
    if row_idx == -1:
        raise ValueError("User not found")

    col_idx = headers.index("status") + 1
    sheet.update_cell(row_idx, col_idx, status)
    return {"message": "Status updated successfully"}


def unsubscribe(payload: dict) -> dict:
    user_id = payload.get("user_id")
    if not user_id:
        raise ValueError("user_id is required")

    sheet, row_idx, headers = _find_user_row(user_id)
    if row_idx == -1:
        raise ValueError("User not found")

    col_idx = headers.index("status") + 1
    sheet.update_cell(row_idx, col_idx, "unsubscribed")
    return {"message": "Unsubscribed successfully"}


def get_active_users():
    sys_settings = get_system_settings()
    if not sys_settings.get("system_enabled", False):
        return []

    sheet = get_sheet("Users")
    all_rows = sheet.get_all_values()
    if len(all_rows) < 2:
        return []

    headers = all_rows[0]
    active_users = []

    for row in all_rows[1:]:
        if len(row) > 8 and row[8].lower() == "active":
            user_dict = {}
            for i, header in enumerate(headers):
                if header == "password_hash":
                    continue
                user_dict[header] = row[i] if i < len(row) else ""
            active_users.append(user_dict)

    return active_users
