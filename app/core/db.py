# -*- coding:utf-8 -*-
"""
核心数据库操作层（Core Database Layer）
使用 SQLAlchemy 直接操作数据库，不依赖 Flask

设计理念：
- 纯 SQLAlchemy 实现，不依赖 Flask-SQLAlchemy
- 写死 SQLite 数据库文件位置
- 提供领域模型（coremodels）和数据库模型之间的转换
- 定义 SQLAlchemy 模型和转换函数

注意：CRUD 操作类（ConversationOp、MessageOp）已移至 model_op.py
"""

import os
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

from app.core.coremodels import Conversation as CoreConversation, Message as CoreMessage

# 写死 SQLite 数据库文件位置（项目根目录）
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
DATABASE_PATH = os.path.join(BASE_DIR, 'app.sqlite')
DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

# 创建 SQLAlchemy 引擎和会话
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# ==================== SQLAlchemy 模型定义 ====================
# 复用 coremodels.py 中的字段定义，通过引用其默认值避免重复定义

class ConversationDBModel(Base):
    """
    会话数据库模型
    复用 coremodels.Conversation 的字段定义（通过引用默认值）
    """
    __tablename__ = 'conversations'
    
    # 字段定义复用 coremodels.Conversation
    # 参考: coremodels.Conversation.title = "新对话"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), default="新对话")  # 复用 CoreConversation 的默认值
    # TODO: 暂时注释外键约束，等 User 表引入后再启用
    # user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user_id = Column(Integer, nullable=False)  # 暂时去掉外键约束
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系（数据库层特有）
    messages = relationship('MessageDBModel', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ConversationDBModel {self.id}: {self.title}>'
    
    def to_core(self) -> CoreConversation:
        """转换为领域模型（复用 coremodels.Conversation）"""
        message_models = self.messages.order_by(MessageDBModel.order_index.asc()).all()
        messages = [msg.to_core() for msg in message_models]
        
        return CoreConversation(
            id=self.id,
            title=self.title,
            user_id=self.user_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            messages=messages
        )
    
    @classmethod
    def from_core(cls, core_model: CoreConversation) -> 'ConversationDBModel':
        """从领域模型创建数据库模型（复用 coremodels.Conversation）"""
        return cls(
            id=core_model.id,
            title=core_model.title,
            user_id=core_model.user_id,
            created_at=core_model.created_at,
            updated_at=core_model.updated_at
        )


class MessageDBModel(Base):
    """
    消息数据库模型
    复用 coremodels.Message 的字段定义（通过引用默认值）
    """
    __tablename__ = 'messages'
    
    # 字段定义复用 coremodels.Message
    # 参考: coremodels.Message.role = MessageRole.USER.value, model = "deepseek-chat"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # 复用 CoreMessage 的默认值
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    order_index = Column(Integer)
    model = Column(String(50), nullable=False, default="deepseek-chat")  # 复用 CoreMessage 的默认值
    generation_time = Column(Float, nullable=True)  # 生成答案耗时（秒），仅助手消息有此属性
    
    def __repr__(self):
        return f'<MessageDBModel {self.id}: {self.role}>'
    
    def to_core(self) -> CoreMessage:
        """转换为领域模型（复用 coremodels.Message）"""
        return CoreMessage(
            id=self.id,
            conversation_id=self.conversation_id,
            role=self.role,
            content=self.content,
            created_at=self.created_at,
            order_index=self.order_index,
            model=self.model,
            generation_time=self.generation_time
        )
    
    @classmethod
    def from_core(cls, core_model: CoreMessage) -> 'MessageDBModel':
        """从领域模型创建数据库模型（复用 coremodels.Message）"""
        return cls(
            id=core_model.id,
            conversation_id=core_model.conversation_id,
            role=core_model.role,
            content=core_model.content,
            created_at=core_model.created_at,
            order_index=core_model.order_index,
            model=core_model.model,
            generation_time=core_model.generation_time
        )


# ==================== 模型转换函数 ====================
# 这些函数内部调用模型类的 to_core() 和 from_core() 方法，复用 coremodels 定义

def conversation_model_to_core(db_model: ConversationDBModel) -> CoreConversation:
    """
    将数据库模型转换为领域模型（复用 coremodels.Conversation）
    
    Args:
        db_model: SQLAlchemy 模型实例
    
    Returns:
        CoreConversation: 领域模型实例
    """
    return db_model.to_core()


def conversation_core_to_model(core_model: CoreConversation) -> ConversationDBModel:
    """
    将领域模型转换为数据库模型（复用 coremodels.Conversation）
    
    Args:
        core_model: 领域模型实例
    
    Returns:
        ConversationDBModel: SQLAlchemy 模型实例
    """
    return ConversationDBModel.from_core(core_model)


def message_model_to_core(db_model: MessageDBModel) -> CoreMessage:
    """
    将消息数据库模型转换为领域模型（复用 coremodels.Message）
    
    Args:
        db_model: SQLAlchemy 模型实例
    
    Returns:
        CoreMessage: 领域模型实例
    """
    return db_model.to_core()


def message_core_to_model(core_model: CoreMessage) -> MessageDBModel:
    """
    将消息领域模型转换为数据库模型（复用 coremodels.Message）
    
    Args:
        core_model: 领域模型实例
    
    Returns:
        MessageDBModel: SQLAlchemy 模型实例
    """
    return MessageDBModel.from_core(core_model)
