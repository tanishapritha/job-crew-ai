import uuid
from datetime import datetime
from sheets_client import get_sheet
from utils.auth_utils import hash_password


def register(payload: dict) -> dict:
    name = payload.get("name")
    email = payload.get("email")
    password = payload.get("password")

    if not all([name, email, password]):
        raise ValueError("Name, email, and password are required")

    sheet = get_sheet("Users")
    all_rows = sheet.get_all_values()

    # all_rows[0] is always headers (auto-bootstrapped by sheets_client)
    if len(all_rows) >= 86:
        raise ValueError("Registration closed: User limit reached")

    for row in all_rows[1:]:
        if len(row) > 2 and row[2].strip().lower() == email.strip().lower():
            raise ValueError("Email already registered")
        if payload.get("username") and len(row) > 17 and row[17].strip().lower() == payload["username"].strip().lower():
            raise ValueError("Username already taken")

    user_id = str(uuid.uuid4())
    pw_hash = hash_password(password)
    created_at = datetime.utcnow().isoformat()

    # 0 user_id | 1 name | 2 email | 3 password_hash | 4 domains
    # 5 daily_limit | 6 total_limit | 7 emails_sent | 8 status
    # 9 created_at | 10 location_1 | 11 location_2 | 12 location_3
    # 13 remote_jobs | 14 experience_level | 15 min_salary
    # 16 phone | 17 username

    new_row = [
        user_id,                        # 0
        name,                           # 1
        email.strip(),                  # 2
        pw_hash,                        # 3
        "",                             # 4 domains
        "25",                           # 5 daily_limit
        "1000",                         # 6 total_limit
        "0",                            # 7 emails_sent
        "active",                       # 8 status
        created_at,                     # 9
        "",                             # 10 loc 1
        "",                             # 11 loc 2
        "",                             # 12 loc 3
        "false",                        # 13 remote
        "beginner",                     # 14 exp
        "0",                            # 15 min_salary
        "",                             # 16 phone
        payload.get("username", ""),    # 17 username
    ]

    sheet.append_row(new_row, value_input_option="USER_ENTERED")
    return {"message": "Registration successful"}


def login(payload: dict) -> dict:
    email = payload.get("email")
    password = payload.get("password")

    if not all([email, password]):
        raise ValueError("Email and password are required")

    sheet = get_sheet("Users")
    all_rows = sheet.get_all_values()

    # all_rows[0] is always headers; need at least 1 data row
    if len(all_rows) < 2:
        raise ValueError("Invalid email or password")

    headers = all_rows[0]
    pw_hash = hash_password(password)

    for row in all_rows[1:]:
        if len(row) > 3 and row[2].strip().lower() == email.strip().lower():
            if row[3] == pw_hash:
                status = row[8] if len(row) > 8 else "active"
                if status.lower() == "blocked":
                    raise ValueError("Account is blocked")

                # build profile dict — never include password_hash
                profile = {}
                for i, header in enumerate(headers):
                    if header == "password_hash" or i == 3:
                        continue
                    val = row[i] if i < len(row) else ""
                    profile[header] = val
                return profile

    raise ValueError("Invalid email or password")
