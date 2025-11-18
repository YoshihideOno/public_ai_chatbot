"""
ストレージサービス

このファイルはファイルストレージへの抽象化レイヤーを提供します。
開発環境ではローカルファイルシステム、本番環境ではVercel Blob Storageを使用します。
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService(ABC):
    """ストレージサービスの抽象基底クラス"""
    
    @abstractmethod
    async def upload_file(
        self, 
        file_content: bytes, 
        file_name: str, 
        tenant_id: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        ファイルをアップロード
        
        引数:
            file_content: ファイルのバイト内容
            file_name: ファイル名
            tenant_id: テナントID
            content_type: MIMEタイプ（オプション）
        
        戻り値:
            str: ストレージ内のファイルパス/URL（s3_keyに保存される値）
        """
        pass
    
    @abstractmethod
    async def get_file(self, storage_key: str) -> bytes:
        """
        ファイルを取得
        
        引数:
            storage_key: ストレージ内のファイルパス/URL
        
        戻り値:
            bytes: ファイルのバイト内容
        """
        pass
    
    @abstractmethod
    async def delete_file(self, storage_key: str) -> bool:
        """
        ファイルを削除
        
        引数:
            storage_key: ストレージ内のファイルパス/URL
        
        戻り値:
            bool: 削除成功時True、失敗時False
        """
        pass


class LocalFileStorage(StorageService):
    """
    ローカルファイルシステムストレージサービス（開発環境用）
    
    開発環境でローカルファイルシステムにファイルを保存します。
    """
    
    DEFAULT_FALLBACK_PATH = Path("/tmp/rag_storage")

    def __init__(self, base_path: str = None):
        """
        ローカルファイルストレージの初期化
        
        引数:
            base_path: ベースパス（デフォルト: settings.STORAGE_LOCAL_PATH）
        """
        requested_path_str = base_path or settings.STORAGE_LOCAL_PATH or str(self.DEFAULT_FALLBACK_PATH)
        requested_path = Path(requested_path_str)
        self.base_path = self._prepare_base_path(requested_path)
        logger.info(f"LocalFileStorage initialized: {self.base_path}")

    def _prepare_base_path(self, requested_path: Path) -> Path:
        """
        ベースパスの作成と書き込み確認を行い、失敗時はフォールバックパスを使用する
        """
        candidates = [requested_path]
        if requested_path != self.DEFAULT_FALLBACK_PATH:
            candidates.append(self.DEFAULT_FALLBACK_PATH)

        last_error: Optional[Exception] = None

        for candidate in candidates:
            try:
                candidate.mkdir(parents=True, exist_ok=True)
                test_file = candidate / ".write_test"
                test_file.write_text("")  # 書き込みテスト
                test_file.unlink(missing_ok=True)
                if candidate != requested_path:
                    logger.warning(
                        "LocalFileStorage: 指定パス %s は書き込み不可のため %s にフォールバックしました",
                        requested_path,
                        candidate,
                    )
                return candidate
            except (OSError, PermissionError) as err:
                last_error = err
                logger.error(f"LocalFileStorage: パス {candidate} の初期化に失敗しました: {err}")

        # すべての候補で失敗した場合は例外を送出
        raise RuntimeError(
            f"LocalFileStorage: 書き込み可能なストレージパスを確保できませんでした (last_error={last_error})"
        )
    
    def _get_file_path(self, tenant_id: str, file_name: str) -> Path:
        """
        ファイルパスを生成
        
        引数:
            tenant_id: テナントID
            file_name: ファイル名
        
        戻り値:
            Path: ファイルパス
        """
        # テナントごとにディレクトリを分割
        tenant_dir = self.base_path / tenant_id
        tenant_dir.mkdir(parents=True, exist_ok=True)
        return tenant_dir / file_name
    
    async def upload_file(
        self, 
        file_content: bytes, 
        file_name: str, 
        tenant_id: str,
        content_type: Optional[str] = None
    ) -> str:
        """ファイルをアップロード"""
        try:
            file_path = self._get_file_path(tenant_id, file_name)
            
            # ファイルを書き込み
            file_path.write_bytes(file_content)
            
            # 相対パスを返す（tenant_id/file_name形式）
            storage_key = f"{tenant_id}/{file_name}"
            logger.info(f"File uploaded to local storage: {storage_key}")
            return storage_key
            
        except Exception as e:
            logger.error(f"Local file upload error: {str(e)}")
            raise
    
    async def get_file(self, storage_key: str) -> bytes:
        """ファイルを取得"""
        try:
            # storage_keyは tenant_id/file_name 形式
            file_path = self.base_path / storage_key
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {storage_key}")
            
            return file_path.read_bytes()
            
        except Exception as e:
            logger.error(f"Local file get error: {str(e)}")
            raise
    
    async def delete_file(self, storage_key: str) -> bool:
        """ファイルを削除"""
        try:
            file_path = self.base_path / storage_key
            
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted from local storage: {storage_key}")
                return True
            else:
                logger.warning(f"File not found for deletion: {storage_key}")
                return False
                
        except Exception as e:
            logger.error(f"Local file delete error: {str(e)}")
            return False


class VercelBlobStorage(StorageService):
    """
    Vercel Blob Storageサービス（本番環境用）
    
    本番環境でVercel Blob Storageにファイルを保存します。
    """
    
    def __init__(self, token: str = None):
        """
        Vercel Blob Storageの初期化
        
        引数:
            token: Vercel Blob Storageの読み取り/書き込みトークン
        """
        self.token = token or settings.BLOB_READ_WRITE_TOKEN
        if not self.token:
            raise ValueError("BLOB_READ_WRITE_TOKENが設定されていません")
        
        self.base_url = "https://blob.vercel-storage.com"
        logger.info("VercelBlobStorage initialized")
    
    async def upload_file(
        self, 
        file_content: bytes, 
        file_name: str, 
        tenant_id: str,
        content_type: Optional[str] = None
    ) -> str:
        """ファイルをアップロード"""
        try:
            # パスを生成（tenant_id/file_name形式）
            path = f"{tenant_id}/{file_name}"
            
            # Vercel Blob Storage APIにアップロード
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/{path}",
                    content=file_content,
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": content_type or "application/octet-stream",
                    },
                    timeout=30.0
                )
                response.raise_for_status()
            
            # URLを返す（またはpathを返す）
            storage_key = path
            logger.info(f"File uploaded to Vercel Blob Storage: {storage_key}")
            return storage_key
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Vercel Blob upload HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Vercel Blob upload error: {str(e)}")
            raise
    
    async def get_file(self, storage_key: str) -> bytes:
        """ファイルを取得"""
        try:
            # Vercel Blob Storage APIから取得
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/{storage_key}",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                return response.content
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Vercel Blob get HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Vercel Blob get error: {str(e)}")
            raise
    
    async def delete_file(self, storage_key: str) -> bool:
        """ファイルを削除"""
        try:
            # Vercel Blob Storage APIから削除
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/{storage_key}",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(f"File deleted from Vercel Blob Storage: {storage_key}")
                    return True
                elif response.status_code == 404:
                    logger.warning(f"File not found for deletion: {storage_key}")
                    return False
                else:
                    logger.error(f"Vercel Blob delete error: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Vercel Blob delete error: {str(e)}")
            return False


class StorageServiceFactory:
    """ストレージサービスのファクトリクラス"""
    
    @staticmethod
    def create() -> StorageService:
        """
        環境に応じたストレージサービスインスタンスを生成
        
        戻り値:
            StorageService: ストレージサービスインスタンス
        """
        if settings.ENVIRONMENT == "production":
            return VercelBlobStorage()
        else:
            return LocalFileStorage()
