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
    # ログシステムの初期化（最優先）
    from app.utils.logging import setup_logging
    setup_logging()
    
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
    
    # CORS設定をログ出力（起動時に確実に出力されるように）
    cors_origins = settings.get_cors_origins()
    print(f"[CORS CONFIG] DEBUG mode: {settings.DEBUG}")
    print(f"[CORS CONFIG] BACKEND_CORS_ORIGINS raw: {settings.BACKEND_CORS_ORIGINS}")
    print(f"[CORS CONFIG] BACKEND_CORS_ORIGINS type: {type(settings.BACKEND_CORS_ORIGINS)}")
    print(f"[CORS CONFIG] Parsed CORS origins: {cors_origins}")
    logger.info(f"DEBUG mode: {settings.DEBUG}")
    logger.info(f"BACKEND_CORS_ORIGINS raw: {settings.BACKEND_CORS_ORIGINS}")
    logger.info(f"Parsed CORS origins: {cors_origins}")
    
    # パターンA: CORSは全オリジン許可とし、実際のOrigin制御はアプリケーション層で実施
    # allowed_originsはログ用のメタ情報として保持し、フィルタリングには使用しない
    allowed_origins = ["*"]
    print(f"[CORS CONFIG] Allowed origins (global): {allowed_origins}")

    # CORSヘッダーをすべてのリクエストに追加するミドルウェア
    # RailwayのエッジサーバーがOPTIONSリクエストを処理する可能性があるため、
    # すべてのレスポンスにCORSヘッダーを追加
    @app.middleware("http")
    async def add_cors_headers(request: Request, call_next):
        from fastapi import Response
        
        origin = request.headers.get("Origin")
        
        # OPTIONSリクエストの場合は、即座にCORSヘッダーを返す
        if request.method == "OPTIONS":
            print(f"[CORS] OPTIONS request detected. Origin: {origin}")
            print(f"[CORS] Allowed origins (global): {allowed_origins}")
            
            # パターンA: CORSレイヤではオリジンをフィルタせず、すべて許可
            response = Response(status_code=200)
            # Originが送信されている場合はその値を返し、無い場合はワイルドカードを使用
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = (
                "Accept, Accept-Language, Authorization, Content-Language, "
                "Content-Type, Origin, X-API-Key, X-Requested-With, X-Tenant-ID"
            )
            # allow_credentials=False とするため、Access-Control-Allow-Credentialsは付与しない
            response.headers["Access-Control-Max-Age"] = "600"
            return response
        
        # 通常のリクエストの場合
        response = await call_next(request)
        
        # レスポンスにCORSヘッダーを追加（全オリジン許可）
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
        else:
            response.headers["Access-Control-Allow-Origin"] = "*"
        # allow_credentials=False とするため、Access-Control-Allow-Credentialsは付与しない
        
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
    # パターンA: CORSは全オリジン許可（allow_origins=["*"], allow_credentials=False）
    # 実際のOrigin制御はアプリケーション層（allowed_widget_originsなど）で実施
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
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
