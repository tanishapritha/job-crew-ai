from datetime import datetime
from config import settings
from sheets_client import get_sheet

def admin_login(payload: dict) -> dict:
    email = payload.get("email")
    password = payload.get("password")
    
    if email == settings.ADMIN_EMAIL and password == settings.ADMIN_PASSWORD:
        return {"isAdmin": True, "email": email, "name": "Admin"}
    
    raise ValueError("Invalid admin credentials")

def get_all_users() -> list:
    sheet = get_sheet("Users")
    all_rows = sheet.get_all_values()
    if len(all_rows) < 2: return []
    
    headers = all_rows[0]
    users = []
    
    for row in all_rows[1:]:
        user_dict = {}
        for i, header in enumerate(headers):
            if header == "password_hash": continue
            user_dict[header] = row[i] if i < len(row) else ""
        users.append(user_dict)
        
    return users

def _log_audit(action, admin_email, target_user, reason, old_val, new_val):
    sheet = get_sheet("Audit_Log")
    headers = sheet.get_all_values()
    if not headers:
        sheet.append_row(["timestamp", "action", "admin_email", "target_user", "reason", "old_value", "new_value"])
    
    sheet.append_row([
        datetime.utcnow().isoformat(), action, admin_email, target_user, reason, old_val, new_val
    ], value_input_option="USER_ENTERED")

def update_user_status(payload: dict) -> dict:
    user_id = payload.get("user_id")
    status = payload.get("status")
    reason = payload.get("reason", "Admin status update")
    admin_email = payload.get("admin_email", settings.ADMIN_EMAIL)
    
    if not user_id or not status:
        raise ValueError("user_id and status are required")
        
    sheet = get_sheet("Users")
    all_rows = sheet.get_all_values()
    
    if len(all_rows) < 2:
        raise ValueError("User not found")
        
    headers = all_rows[0]
    for i, row in enumerate(all_rows):
        if i > 0 and len(row) > 0 and row[0] == user_id:
            col_idx = headers.index("status") + 1
            old_status = row[col_idx-1] if len(row) >= col_idx else ""
            sheet.update_cell(i + 1, col_idx, status)
            
            # Log to audit
            _log_audit("UPDATE_STATUS", admin_email, user_id, reason, old_status, status)
            return {"message": "Status updated successfully"}
            
    raise ValueError("User not found")

def bulk_update_status(payload: dict) -> dict:
    user_ids = payload.get("user_ids", [])
    status = payload.get("status")
    
    if not user_ids or not status:
        raise ValueError("user_ids and status are required")
        
    for uid in user_ids:
        update_user_status({"user_id": uid, "status": status})
        
    return {"message": f"Successfully updated {len(user_ids)} users"}

def get_system_settings() -> dict:
    sheet = get_sheet("System_Settings")
    all_rows = sheet.get_all_values()
    
    if not all_rows:
        sheet.append_row(["key", "value"])
        sheet.append_row(["system_enabled", "TRUE"])
        return {"system_enabled": True}
        
    settings_dict = {}
    for row in all_rows[1:]:
        if len(row) >= 2:
            val = row[1].upper() == "TRUE" if row[1].upper() in ["TRUE", "FALSE"] else row[1]
            settings_dict[row[0]] = val
            
    if "system_enabled" not in settings_dict:
        settings_dict["system_enabled"] = True
        
    return settings_dict

def update_system_settings(payload: dict) -> dict:
    key = payload.get("key")
    value = str(payload.get("value")).upper() if isinstance(payload.get("value"), bool) else str(payload.get("value"))
    
    if not key or value is None:
        raise ValueError("key and value are required")
        
    sheet = get_sheet("System_Settings")
    all_rows = sheet.get_all_values()
    
    row_updated = False
    for i, row in enumerate(all_rows):
        if i > 0 and len(row) > 0 and row[0] == key:
            sheet.update_cell(i + 1, 2, value)
            row_updated = True
            break
            
    if not row_updated:
        sheet.append_row([key, value])
        
    return {"message": "Settings updated"}

def get_system_stats() -> dict:
    users = get_all_users()
    active = sum(1 for u in users if u.get('status') == 'active')
    paused = sum(1 for u in users if u.get('status') == 'paused')
    blocked = sum(1 for u in users if u.get('status') == 'blocked')
    
    total_emails = sum(int(u.get('emails_sent') or 0) for u in users)
    
    return {
        "total_users": len(users),
        "active_users": active,
        "paused_users": paused,
        "blocked_users": blocked,
        "total_emails_sent": total_emails
    }

def get_audit_logs(payload: dict = {}) -> list:
    limit = int(payload.get("limit", 100))
    sheet = get_sheet("Audit_Log")
    all_rows = sheet.get_all_values()
    
    if len(all_rows) < 2: return []
    
    headers = all_rows[0]
    logs = [dict(zip(headers, row)) for row in all_rows[1:]]
    logs.reverse()
    
    return logs[:limit]
