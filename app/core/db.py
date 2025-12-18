# -*- coding:utf-8 -*-
"""
核心数据库操作层（Core Database Layer）
使用 SQLAlchemy 直接操作数据库，不依赖 Flask

设计理念：
- 纯 SQLAlchemy 实现，不依赖 Flask-SQLAlchemy
- 写死 SQLite 数据库文件位置
- 提供领域模型（coremodels）和数据库模型之间的转换
- 封装 Conversation 的 CRUD 操作
"""

import os
from datetime import datetime
from typing import List, Optional, Generator
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.orm.exc import NoResultFound

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
            model=self.model
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
            model=core_model.model
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


# ==================== ConversationOp 类 ====================

class ConversationOp:
    """
    会话操作类
    封装 Conversation 的增删查改和列表查询操作
    """
    
    def __init__(self, session: Optional[Session] = None, chat_manager=None):
        """
        初始化会话操作类
        
        Args:
            session: SQLAlchemy 会话对象，如果为 None 则创建新会话
            chat_manager: ChatManager 实例，如果为 None 则自动创建
        """
        self.session = session or SessionLocal()
        self._own_session = session is None
        
        # 延迟导入 ChatManager 避免循环依赖
        if chat_manager is None:
            from app.core.chat_manager import ChatManager
            self.chat_manager = ChatManager()
        else:
            self.chat_manager = chat_manager
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if self._own_session:
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
            self.session.close()
    
    def create(self, conversation: CoreConversation) -> CoreConversation:
        """
        创建新会话
        
        Args:
            conversation: 领域模型实例
        
        Returns:
            CoreConversation: 创建后的领域模型实例（包含生成的 ID）
        """
        db_model = conversation_core_to_model(conversation)
        self.session.add(db_model)
        self.session.flush()  # 获取生成的 ID
        self.session.commit()
        
        # 返回包含 ID 的领域模型
        return conversation_model_to_core(db_model)
    
    def get_by_id(self, conversation_id: int) -> Optional[CoreConversation]:
        """
        根据 ID 获取会话
        
        Args:
            conversation_id: 会话ID
        
        Returns:
            Optional[CoreConversation]: 领域模型实例，如果不存在则返回 None
        """
        try:
            db_model = self.session.query(ConversationDBModel).filter_by(id=conversation_id).one()
            return conversation_model_to_core(db_model)
        except NoResultFound:
            return None
    
    def get_by_user_id(self, user_id: int) -> List[CoreConversation]:
        """
        获取用户的所有会话（列表查询）
        
        Args:
            user_id: 用户ID
        
        Returns:
            List[CoreConversation]: 会话列表，按 updated_at 降序排列
        """
        db_models = self.session.query(ConversationDBModel).filter_by(
            user_id=user_id
        ).order_by(ConversationDBModel.updated_at.desc()).all()
        
        return [conversation_model_to_core(model) for model in db_models]
    
    def get_all(self, limit: Optional[int] = None) -> List[CoreConversation]:
        """
        获取所有会话（列表查询）
        
        Args:
            limit: 限制返回数量（可选）
        
        Returns:
            List[CoreConversation]: 会话列表，按 updated_at 降序排列
        """
        query = self.session.query(ConversationDBModel).order_by(
            ConversationDBModel.updated_at.desc()
        )
        
        if limit:
            query = query.limit(limit)
        
        db_models = query.all()
        return [conversation_model_to_core(model) for model in db_models]
    
    def list(self, user_id: Optional[int] = None, limit: Optional[int] = None) -> List[CoreConversation]:
        """
        列出会话（便捷方法）
        
        Args:
            user_id: 可选，如果指定则只列出该用户的对话
            limit: 可选，限制返回数量
        
        Returns:
            List[CoreConversation]: 会话列表
        
        Examples:
            >>> with ConversationOp() as op:
            ...     # 列出所有会话
            ...     conversations = op.list()
            ...     # 列出特定用户的会话
            ...     conversations = op.list(user_id=1)
            ...     # 限制数量
            ...     conversations = op.list(limit=10)
        """
        if user_id:
            return self.get_by_user_id(user_id)
        else:
            return self.get_all(limit=limit)
    
    def update(self, conversation: CoreConversation) -> Optional[CoreConversation]:
        """
        更新会话
        
        Args:
            conversation: 领域模型实例（必须包含 id）
        
        Returns:
            Optional[CoreConversation]: 更新后的领域模型实例，如果不存在则返回 None
        """
        if conversation.id is None:
            raise ValueError("conversation.id 不能为 None")
        
        db_model = self.session.query(ConversationDBModel).filter_by(id=conversation.id).first()
        if not db_model:
            return None
        
        # 更新字段
        db_model.title = conversation.title
        db_model.user_id = conversation.user_id
        db_model.updated_at = datetime.now()
        
        # 如果领域模型有 created_at，也更新它
        if conversation.created_at:
            db_model.created_at = conversation.created_at
        
        self.session.commit()
        
        return conversation_model_to_core(db_model)
    
    def delete(self, conversation_id: int) -> bool:
        """
        删除会话
        
        Args:
            conversation_id: 会话ID
        
        Returns:
            bool: 是否成功删除
        """
        db_model = self.session.query(ConversationDBModel).filter_by(id=conversation_id).first()
        if not db_model:
            return False
        
        self.session.delete(db_model)
        self.session.commit()
        return True
    
    def commit(self):
        """提交事务"""
        self.session.commit()
    
    def rollback(self):
        """回滚事务"""
        self.session.rollback()
    
    def send_message(
        self,
        conversation_id: int,
        user_content: str,
        model_name: str = 'deepseek-chat',
        auto_title: bool = True
    ) -> Generator[dict, None, None]:
        """
        发送消息并获取AI回答（完整工作流）
        
        这是一个便捷方法，封装了：
        1. 创建用户消息
        2. 生成并保存AI回答
        3. 更新会话信息
        
        Args:
            conversation_id: 会话ID
            user_content: 用户消息内容
            model_name: 模型名称（默认：'deepseek-chat'）
            auto_title: 是否自动生成会话标题（默认：True）
        
        Yields:
            dict: 包含 'type' 和数据的字典
                - type='chunk': {'type': 'chunk', 'chunk': str}
                - type='done': {'type': 'done', 'message_id': int, 'user_message_id': int}
                - type='error': {'type': 'error', 'error': str}
        
        Examples:
            >>> with ConversationOp() as op:
            ...     for result in op.send_message(1, "你好", model_name='deepseek-chat'):
            ...         if result['type'] == 'chunk':
            ...             print(result['chunk'], end='')
            ...         elif result['type'] == 'done':
            ...             print(f"\n完成！消息ID: {result['message_id']}")
        """
        from app.core.coremodels import Message
        
        # 获取会话
        conversation = self.get_by_id(conversation_id)
        if not conversation:
            yield {'type': 'error', 'error': f'会话 {conversation_id} 不存在'}
            return
        
        # 获取最后一条消息的 order_index
        with MessageOp(self.session) as msg_op:
            last_message = None
            messages = msg_op.get_by_conversation_id(conversation_id, order_by="order_index")
            if messages:
                last_message = messages[-1]
            
            # 计算新用户消息的 order_index
            if last_message is None:
                new_order_index = 0
            else:
                if last_message.order_index is None:
                    new_order_index = 0
                elif last_message.order_index % 2 == 0:  # 最后是用户消息
                    new_order_index = last_message.order_index + 2
                else:  # 最后是助手消息
                    new_order_index = last_message.order_index + 1
            
            # 创建用户消息
            user_message = Message(
                conversation_id=conversation_id,
                role='user',
                content=user_content,
                order_index=new_order_index,
                model=model_name
            )
            
            # 保存用户消息
            saved_user_message = msg_op.create(user_message)
        
        # 使用 ChatManager 生成并保存助手回答
        precomputed_order_index = saved_user_message.order_index + 1
        
        yield from self.chat_manager.generate_and_save_assistant_response(
            conversation_id=conversation_id,
            user_message_id=saved_user_message.id,
            user_message=saved_user_message,
            model_name=model_name,
            precomputed_order_index=precomputed_order_index,
            auto_title=auto_title
        )


# ==================== MessageOp 类 ====================

class MessageOp:
    """
    消息操作类
    封装 Message 的增删查改和列表查询操作
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        初始化消息操作类
        
        Args:
            session: SQLAlchemy 会话对象，如果为 None 则创建新会话
        """
        self.session = session or SessionLocal()
        self._own_session = session is None
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if self._own_session:
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
            self.session.close()
    
    def create(self, message: CoreMessage) -> CoreMessage:
        """
        创建新消息
        
        Args:
            message: 领域模型实例
        
        Returns:
            CoreMessage: 创建后的领域模型实例（包含生成的 ID）
        """
        db_model = message_core_to_model(message)
        self.session.add(db_model)
        self.session.flush()  # 获取生成的 ID
        self.session.commit()
        
        # 返回包含 ID 的领域模型
        return message_model_to_core(db_model)
    
    def get_by_id(self, message_id: int) -> Optional[CoreMessage]:
        """
        根据 ID 获取消息
        
        Args:
            message_id: 消息ID
        
        Returns:
            Optional[CoreMessage]: 领域模型实例，如果不存在则返回 None
        """
        try:
            db_model = self.session.query(MessageDBModel).filter_by(id=message_id).one()
            return message_model_to_core(db_model)
        except NoResultFound:
            return None
    
    def get_by_conversation_id(
        self, 
        conversation_id: int, 
        order_by: str = "order_index"
    ) -> List[CoreMessage]:
        """
        获取会话的所有消息（列表查询）
        
        Args:
            conversation_id: 会话ID
            order_by: 排序字段，可选值：'order_index', 'created_at'
        
        Returns:
            List[CoreMessage]: 消息列表
        """
        query = self.session.query(MessageDBModel).filter_by(
            conversation_id=conversation_id
        )
        
        if order_by == "order_index":
            query = query.order_by(MessageDBModel.order_index.asc())
        elif order_by == "created_at":
            query = query.order_by(MessageDBModel.created_at.asc())
        else:
            query = query.order_by(MessageDBModel.order_index.asc())
        
        db_models = query.all()
        return [message_model_to_core(model) for model in db_models]
    
    def get_all(self, limit: Optional[int] = None) -> List[CoreMessage]:
        """
        获取所有消息（列表查询）
        
        Args:
            limit: 限制返回数量（可选）
        
        Returns:
            List[CoreMessage]: 消息列表，按 created_at 降序排列
        """
        query = self.session.query(MessageDBModel).order_by(
            MessageDBModel.created_at.desc()
        )
        
        if limit:
            query = query.limit(limit)
        
        db_models = query.all()
        return [message_model_to_core(model) for model in db_models]
    
    def list(
        self, 
        conversation_id: Optional[int] = None, 
        limit: Optional[int] = None,
        order_by: str = "order_index"
    ) -> List[CoreMessage]:
        """
        列出消息（便捷方法）
        
        Args:
            conversation_id: 可选，如果指定则只列出该会话的消息
            limit: 可选，限制返回数量
            order_by: 排序字段，可选值：'order_index', 'created_at'
        
        Returns:
            List[CoreMessage]: 消息列表
        
        Examples:
            >>> with MessageOp() as op:
            ...     # 列出所有消息
            ...     messages = op.list()
            ...     # 列出特定会话的消息
            ...     messages = op.list(conversation_id=1)
            ...     # 限制数量
            ...     messages = op.list(limit=10)
        """
        if conversation_id:
            return self.get_by_conversation_id(conversation_id, order_by=order_by)
        else:
            return self.get_all(limit=limit)
    
    def update(self, message: CoreMessage) -> Optional[CoreMessage]:
        """
        更新消息
        
        Args:
            message: 领域模型实例（必须包含 id）
        
        Returns:
            Optional[CoreMessage]: 更新后的领域模型实例，如果不存在则返回 None
        """
        if message.id is None:
            raise ValueError("message.id 不能为 None")
        
        db_model = self.session.query(MessageDBModel).filter_by(id=message.id).first()
        if not db_model:
            return None
        
        # 更新字段
        db_model.conversation_id = message.conversation_id
        db_model.role = message.role
        db_model.content = message.content
        db_model.order_index = message.order_index
        db_model.model = message.model
        
        # 如果领域模型有 created_at，也更新它
        if message.created_at:
            db_model.created_at = message.created_at
        
        self.session.commit()
        
        return message_model_to_core(db_model)
    
    def delete(self, message_id: int) -> bool:
        """
        删除消息
        
        Args:
            message_id: 消息ID
        
        Returns:
            bool: 是否成功删除
        """
        db_model = self.session.query(MessageDBModel).filter_by(id=message_id).first()
        if not db_model:
            return False
        
        self.session.delete(db_model)
        self.session.commit()
        return True
    
    def commit(self):
        """提交事务"""
        self.session.commit()
    
    def rollback(self):
        """回滚事务"""
        self.session.rollback()


# ==================== 便捷函数 ====================

def get_conversation_by_id(conversation_id: int) -> Optional[CoreConversation]:
    """
    便捷函数：根据 ID 获取会话
    
    Args:
        conversation_id: 会话ID
    
    Returns:
        Optional[CoreConversation]: 领域模型实例
    """
    with ConversationOp() as op:
        return op.get_by_id(conversation_id)


def get_conversations_by_user_id(user_id: int) -> List[CoreConversation]:
    """
    便捷函数：获取用户的所有会话
    
    Args:
        user_id: 用户ID
    
    Returns:
        List[CoreConversation]: 会话列表
    """
    with ConversationOp() as op:
        return op.get_by_user_id(user_id)


def create_conversation(conversation: CoreConversation) -> CoreConversation:
    """
    便捷函数：创建会话
    
    Args:
        conversation: 领域模型实例
    
    Returns:
        CoreConversation: 创建后的领域模型实例
    """
    with ConversationOp() as op:
        return op.create(conversation)


def update_conversation(conversation: CoreConversation) -> Optional[CoreConversation]:
    """
    便捷函数：更新会话
    
    Args:
        conversation: 领域模型实例
    
    Returns:
        Optional[CoreConversation]: 更新后的领域模型实例
    """
    with ConversationOp() as op:
        return op.update(conversation)


def delete_conversation(conversation_id: int) -> bool:
    """
    便捷函数：删除会话
    
    Args:
        conversation_id: 会话ID
    
    Returns:
        bool: 是否成功删除
    """
    with ConversationOp() as op:
        return op.delete(conversation_id)


# ==================== Message 便捷函数 ====================

def get_message_by_id(message_id: int) -> Optional[CoreMessage]:
    """
    便捷函数：根据 ID 获取消息
    
    Args:
        message_id: 消息ID
    
    Returns:
        Optional[CoreMessage]: 领域模型实例
    """
    with MessageOp() as op:
        return op.get_by_id(message_id)


def get_messages_by_conversation_id(
    conversation_id: int, 
    order_by: str = "order_index"
) -> List[CoreMessage]:
    """
    便捷函数：获取会话的所有消息
    
    Args:
        conversation_id: 会话ID
        order_by: 排序字段，可选值：'order_index', 'created_at'
    
    Returns:
        List[CoreMessage]: 消息列表
    """
    with MessageOp() as op:
        return op.get_by_conversation_id(conversation_id, order_by=order_by)


def create_message(message: CoreMessage) -> CoreMessage:
    """
    便捷函数：创建消息
    
    Args:
        message: 领域模型实例
    
    Returns:
        CoreMessage: 创建后的领域模型实例
    """
    with MessageOp() as op:
        return op.create(message)


def update_message(message: CoreMessage) -> Optional[CoreMessage]:
    """
    便捷函数：更新消息
    
    Args:
        message: 领域模型实例
    
    Returns:
        Optional[CoreMessage]: 更新后的领域模型实例
    """
    with MessageOp() as op:
        return op.update(message)


def delete_message(message_id: int) -> bool:
    """
    便捷函数：删除消息
    
    Args:
        message_id: 消息ID
    
    Returns:
        bool: 是否成功删除
    """
    with MessageOp() as op:
        return op.delete(message_id)

