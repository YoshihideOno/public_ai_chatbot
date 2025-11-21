from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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

    # ロガーを先に定義
    import logging
    logger = logging.getLogger(__name__)

    # OPTIONSリクエスト（CORSプリフライト）を明示的に処理
    # CORSミドルウェアの前に実行されるため、ここでCORSヘッダーを手動で追加
    @app.middleware("http")
    async def handle_options_request(request: Request, call_next):
        from fastapi import Response
        
        # OPTIONSリクエストの場合、CORSヘッダーを手動で追加
        if request.method == "OPTIONS":
            origin = request.headers.get("Origin")
            logger.info(f"OPTIONS request detected. Origin: {origin}")
            logger.info(f"Allowed origins: {settings.BACKEND_CORS_ORIGINS if not settings.DEBUG else 'DEBUG mode'}")
            
            # オリジンチェック
            allowed_origins = settings.BACKEND_CORS_ORIGINS if not settings.DEBUG else [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3001",
                "http://localhost:8080",
                "http://127.0.0.1:8080",
            ]
            
            # オリジンが許可されているかチェック
            if origin and (origin in allowed_origins or "*" in allowed_origins):
                logger.info(f"Origin {origin} is allowed")
                response = Response(status_code=200)
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                response.headers["Access-Control-Allow-Headers"] = "Accept, Accept-Language, Authorization, Content-Language, Content-Type, Origin, X-API-Key, X-Requested-With, X-Tenant-ID"
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Max-Age"] = "600"
                return response
            else:
                logger.warning(f"Origin {origin} is not in allowed origins: {allowed_origins}")
                # オリジンが許可されていない場合でも、CORSミドルウェアに処理を委譲
                pass
        
        response = await call_next(request)
        return response
    
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
    # デバッグ用: CORS設定をログ出力
    logger.info(f"DEBUG mode: {settings.DEBUG}")
    logger.info(f"BACKEND_CORS_ORIGINS: {settings.BACKEND_CORS_ORIGINS}")
    logger.info(f"BACKEND_CORS_ORIGINS type: {type(settings.BACKEND_CORS_ORIGINS)}")
    logger.info(f"BACKEND_CORS_ORIGINS length: {len(settings.BACKEND_CORS_ORIGINS) if isinstance(settings.BACKEND_CORS_ORIGINS, list) else 'N/A'}")
    
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
        # 本番環境: 環境変数で設定されたCORSオリジンを使用
        # BACKEND_CORS_ORIGINSはカンマ区切りの文字列として環境変数から読み込まれる
        cors_origins = settings.BACKEND_CORS_ORIGINS
        if not cors_origins or len(cors_origins) == 0:
            logger.warning("BACKEND_CORS_ORIGINS is empty! CORS will block all requests.")
            # フォールバック: デフォルト値を設定（本番環境では環境変数を設定すべき）
            cors_origins = ["https://ai-chatbot-project-beta.vercel.app"]
            logger.warning(f"Using fallback CORS origins: {cors_origins}")
        else:
            logger.info(f"Using CORS origins: {cors_origins}")
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=[
                "Authorization",
                "Content-Type",
                "Accept",
                "Accept-Language",
                "Content-Language",
                "Origin",
                "X-Requested-With",
                "X-Tenant-ID",  # Widget認証用
                "X-API-Key",    # Widget認証用
            ],
            expose_headers=[
                "Content-Length",
                "Content-Type",
                "X-Request-Id",
            ],
        )

    # Trusted host middleware
    # OPTIONSリクエスト（CORSプリフライト）はスキップする必要があるため、
    # TrustedHostMiddlewareは適用しない（CORSミドルウェアで制御）
    # 本番環境では、CORSミドルウェアとリバースプロキシ（Railway/AWS）で
    # ホスト検証を行う

    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # OPTIONSリクエストを明示的に処理（CORSプリフライト用）
    @app.options("/{full_path:path}")
    async def options_handler(full_path: str, request: Request):
        """
        OPTIONSリクエスト（CORSプリフライト）を処理
        
        このエンドポイントは、CORSミドルウェアが処理できない場合の
        フォールバックとして機能します。
        """
        from fastapi import Response
        origin = request.headers.get("Origin")
        logger.info(f"OPTIONS request for path: {full_path}, Origin: {origin}")
        
        # CORSミドルウェアが処理するため、ここでは空のレスポンスを返す
        # 実際のCORSヘッダーはCORSミドルウェアが追加する
        return Response(status_code=200)

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
