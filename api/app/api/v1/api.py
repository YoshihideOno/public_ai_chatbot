from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, chats, tenants, contents, stats, billing, api_keys, reminders, audit_logs, query_analytics

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(chats.router, prefix="/chats", tags=["chats"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(contents.router, prefix="/contents", tags=["contents"])
api_router.include_router(stats.router, prefix="/stats", tags=["statistics"])
api_router.include_router(query_analytics.router, prefix="/query-analytics", tags=["query-analytics"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
api_router.include_router(reminders.router, prefix="/reminders", tags=["reminders"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["audit-logs"])
