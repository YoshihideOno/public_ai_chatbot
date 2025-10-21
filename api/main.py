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
    await init_db()
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
