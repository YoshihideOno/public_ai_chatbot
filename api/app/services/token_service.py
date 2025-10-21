"""
確認トークン管理サービス

このファイルはメール確認用のトークンの生成、検証、管理を行うサービスを定義します。
セキュアなトークン生成と有効期限管理を提供します。

主な機能:
- 確認トークンの生成
- トークンの検証
- トークンの無効化
- 有効期限チェック
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.verification_token import VerificationToken
from app.models.user import User
from app.utils.logging import logger


class TokenService:
    """確認トークン管理サービス"""
    
    @staticmethod
    def generate_token() -> str:
        """
        セキュアな確認トークンを生成
        
        戻り値:
            str: 生成されたトークン
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_token(token: str) -> str:
        """
        トークンをハッシュ化
        
        引数:
            token: ハッシュ化するトークン
            
        戻り値:
            str: ハッシュ化されたトークン
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    async def create_verification_token(
        db: AsyncSession,
        user_id: str,
        token_type: str = "email_verification",
        expires_hours: int = 24
    ) -> tuple[str, str]:
        """
        確認トークンを作成
        
        引数:
            db: データベースセッション
            user_id: ユーザーID
            token_type: トークンの種類
            expires_hours: 有効期限（時間）
            
        戻り値:
            tuple[str, str]: (プレーンテキストトークン, ハッシュ化トークン)
        """
        # プレーンテキストトークンを生成
        plain_token = TokenService.generate_token()
        hashed_token = TokenService.hash_token(plain_token)
        
        # 有効期限を設定
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        # 新しいトークンを作成
        verification_token = VerificationToken(
            user_id=user_id,
            token=hashed_token,
            token_type=token_type,
            expires_at=expires_at
        )
        
        db.add(verification_token)
        await db.commit()
        await db.refresh(verification_token)
        
        logger.info(f"確認トークン作成完了: user_id={user_id}, token_type={token_type}")
        
        return plain_token, hashed_token
    
    @staticmethod
    async def verify_token(
        db: AsyncSession,
        token: str,
        token_type: str = "email_verification"
    ) -> Optional[User]:
        """
        トークンを検証
        
        引数:
            db: データベースセッション
            token: 検証するトークン
            token_type: トークンの種類
            
        戻り値:
            Optional[User]: 検証成功時はユーザー、失敗時はNone
        """
        hashed_token = TokenService.hash_token(token)
        
        # トークンを検索
        stmt = select(VerificationToken).join(User).where(
            and_(
                VerificationToken.token == hashed_token,
                VerificationToken.token_type == token_type,
                VerificationToken.is_used == False,
                VerificationToken.expires_at > datetime.utcnow()
            )
        )
        
        result = await db.execute(stmt)
        verification_token = result.scalar_one_or_none()
        
        if not verification_token:
            logger.warning(f"無効なトークンまたは期限切れ: token_type={token_type}")
            return None
        
        # トークンを無効化
        verification_token.is_used = True
        await db.commit()
        
        # ユーザーを取得
        user_stmt = select(User).where(User.id == verification_token.user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        
        if user:
            logger.info(f"トークン検証成功: user_id={user.id}, token_type={token_type}")
        
        return user
    
    @staticmethod
    async def invalidate_user_tokens(
        db: AsyncSession,
        user_id: str,
        token_type: str
    ) -> None:
        """
        ユーザーの指定種類のトークンを無効化
        
        引数:
            db: データベースセッション
            user_id: ユーザーID
            token_type: トークンの種類
        """
        stmt = select(VerificationToken).where(
            and_(
                VerificationToken.user_id == user_id,
                VerificationToken.token_type == token_type,
                VerificationToken.is_used == False
            )
        )
        
        result = await db.execute(stmt)
        tokens = result.scalars().all()
        
        for token in tokens:
            token.is_used = True
        
        if tokens:
            await db.commit()
            logger.info(f"トークン無効化完了: user_id={user_id}, count={len(tokens)}")
    
    @staticmethod
    async def cleanup_expired_tokens(db: AsyncSession) -> int:
        """
        期限切れのトークンをクリーンアップ
        
        引数:
            db: データベースセッション
            
        戻り値:
            int: 削除されたトークン数
        """
        stmt = select(VerificationToken).where(
            VerificationToken.expires_at < datetime.utcnow()
        )
        
        result = await db.execute(stmt)
        expired_tokens = result.scalars().all()
        
        count = len(expired_tokens)
        for token in expired_tokens:
            await db.delete(token)
        
        if count > 0:
            await db.commit()
            logger.info(f"期限切れトークンクリーンアップ完了: count={count}")
        
        return count
