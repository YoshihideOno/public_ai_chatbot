from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
from contextlib import asynccontextmanager
import json

from app.core.config import settings
from app.core.database import init_db
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # テスト環境ではinit_db()をスキップ（pytest実行時）
    import sys
    if "pytest" not in sys.modules:
        try:
            await init_db()
        except Exception as e:
            # テスト環境やデータベース未起動時はエラーを無視
            if "pytest" in sys.modules or settings.ENVIRONMENT == "test":
                pass
            else:
                raise
    yield
    # Shutdown
    pass


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="AI Chatbot API",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    # リクエストボディをログに記録するミドルウェア
    @app.middleware("http")
    async def log_request_body(request: Request, call_next):
        if request.url.path == "/api/v1/auth/register":
            body = await request.body()
            print(f"Register request body: {body.decode('utf-8')}")
            print(f"Content-Type: {request.headers.get('content-type')}")
        
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            print(f"Error in request: {e}")
            print(f"Error type: {type(e)}")
            raise

    # CORS middleware
    # 開発環境では広く許可し、運用環境では設定値に基づく厳格な許可を適用
    if settings.DEBUG:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3001",
                "http://localhost:8080",
                "http://127.0.0.1:8080",
                "null",  # file://プロトコル用
            ],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=[
                "Authorization",
                "Content-Type",
                "Accept",
                "X-Requested-With",
                "Origin",
                "X-Tenant-ID",  # Widget認証用
                "X-API-Key",    # Widget認証用
            ],
            expose_headers=[
                "Content-Length",
                "Content-Type",
                "X-Request-Id",
            ],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Trusted host middleware
    if settings.BACKEND_CORS_ORIGINS:
        # Extract hostnames from URLs for trusted hosts
        trusted_hosts = []
        for origin in settings.BACKEND_CORS_ORIGINS:
            if origin.startswith("http://") or origin.startswith("https://"):
                host = origin.split("://")[1].split(":")[0]
                trusted_hosts.append(host)
        
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=trusted_hosts + ["localhost", "127.0.0.1", "*"],
        )

    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
