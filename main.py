from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Any, Dict, Optional
from fastapi.responses import HTMLResponse

from scheduler import start_scheduler, stop_scheduler
from services import auth_service, otp_service, user_service, admin_service, payment_service
from services.admin_service import get_system_stats

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(lifespan=lifespan, title="Job Automation Backend")

# CORS — allow frontend to call the API
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ActionRequest(BaseModel):
    action: str
    payload: dict = {}

@app.post("/")
async def handle_action(request: ActionRequest):
    action = request.action
    payload = request.payload

    routes = {
        "register": auth_service.register,
        "login": auth_service.login,
        "requestPasswordOTP": otp_service.request_otp,
        "verifyOTPAndResetPassword": otp_service.verify_otp,
        "updateUserProfile": user_service.update_profile,
        "updateDomains": user_service.update_domains,
        "toggleUserStatus": user_service.toggle_status,
        "unsubscribeUser": user_service.unsubscribe,
        "getActiveUsersForEmail": user_service.get_active_users,
        "adminLogin": admin_service.admin_login,
        "getAllUsers": admin_service.get_all_users,
        "updateUserStatus": admin_service.update_user_status,
        "bulkUpdateStatus": admin_service.bulk_update_status,
        "getSystemSettings": admin_service.get_system_settings,
        "updateSystemSettings": admin_service.update_system_settings,
        "getSystemStats": admin_service.get_system_stats,
        "getAuditLogs": admin_service.get_audit_logs,
        "submitPaymentProof": payment_service.submit_proof,
        "getPendingPayments": payment_service.get_pending,
        "approvePayment": payment_service.approve,
        "rejectPayment": payment_service.reject,
        "getPaymentAnalytics": payment_service.get_analytics,
    }

    if action not in routes:
        raise HTTPException(status_code=400, detail="Invalid action")

    try:
        if action in ["getActiveUsersForEmail", "getAllUsers", "getSystemSettings", "getSystemStats"]:
            data = routes[action]()
        else:
            data = routes[action](payload)
        return {"success": True, "data": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe(user_id: str):
    try:
        user_service.unsubscribe({"user_id": user_id})
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f7fafc; color: #2d3748; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
                .card {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-align: center; max-width: 400px; width: 100%; }}
                h1 {{ font-size: 24px; color: #e53e3e; margin-bottom: 20px; }}
                p {{ font-size: 16px; color: #718096; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Unsubscribed Successfully</h1>
                <p>You have been removed from our active mailing list and will no longer receive job emails.</p>
            </div>
        </body>
        </html>
        """
    except ValueError as e:
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f7fafc; color: #2d3748; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
                .card {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-align: center; max-width: 400px; width: 100%; }}
                h1 {{ font-size: 24px; color: #e53e3e; margin-bottom: 20px; }}
                p {{ font-size: 16px; color: #718096; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Error</h1>
                <p>{str(e)}</p>
            </div>
        </body>
        </html>
        """

@app.get("/health")
async def health():
    try:
        stats = get_system_stats()
        return {"status": "ok", "stats": stats}
    except Exception:
        return {"status": "ok", "stats": {}}
