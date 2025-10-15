"""
チャット・メッセージモデル

このファイルはチャット機能に関するSQLAlchemyモデルを定義します。
チャットセッションとメッセージの管理、ユーザーとの関連付けなどの機能を提供します。

主な機能:
- チャットセッションの管理
- メッセージの保存・管理
- ユーザーとの関連付け
- メッセージの役割管理（ユーザー・アシスタント）
- 時系列でのメッセージ管理
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Chat(Base):
    """
    チャットモデル
    
    ユーザーとAIアシスタント間のチャットセッションを管理します。
    Baseクラスを継承し、SQLAlchemyのORM機能を利用します。
    
    属性:
        id: チャットの一意識別子（整数）
        user_id: チャットを開始したユーザーID（外部キー）
        title: チャットのタイトル（オプション）
        created_at: 作成日時
        updated_at: 更新日時
    """
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")


class Message(Base):
    """
    メッセージモデル
    
    チャット内の個別メッセージを管理します。
    ユーザーメッセージとAIアシスタントの応答の両方を保存します。
    
    属性:
        id: メッセージの一意識別子（整数）
        chat_id: 所属チャットID（外部キー）
        role: メッセージの役割（'user' または 'assistant'）
        content: メッセージの内容
        created_at: 作成日時
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    chat = relationship("Chat", back_populates="messages")
