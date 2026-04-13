import json
from datetime import datetime
from crewai.tools import tool
from sheets_client import get_sheet

@tool("AuditLogTool")
def audit_log_tool(input: str) -> str:
    """Logs an action to Audit_Log. Input: JSON string with action, user_id, user_email, old_value, new_value, reason, admin_email"""
    try:
        data = json.loads(input)
        sheet = get_sheet("Audit_Log")
        headers = sheet.get_all_values()
        if not headers:
            sheet.append_row(["timestamp", "action", "admin_email", "target_user", "reason", "old_value", "new_value"])
            
        sheet.append_row([
            datetime.utcnow().isoformat(),
            data.get("action", ""),
            data.get("admin_email", "SYSTEM"),
            data.get("user_id", ""),
            data.get("reason", ""),
            str(data.get("old_value", "")),
            str(data.get("new_value", ""))
        ], value_input_option="USER_ENTERED")
        return "logged"
    except Exception as e:
        return f"Error: {e}"
