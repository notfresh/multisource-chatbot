# -*- coding:utf-8 -*-
"""
模型操作类（Model Operations）
封装 Conversation 和 Message 的数据库操作

设计理念：
- 提供 ConversationOp 和 MessageOp 类，封装 CRUD 操作
- 提供便捷函数，简化常用操作
- 依赖 db.py 中的数据库配置和模型定义
"""

from datetime import datetime
from typing import List, Optional, Generator, Callable
import time
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound

# 从 db.py 导入数据库配置和模型
from app.core.db import (
    SessionLocal,
    ConversationDBModel,
    MessageDBModel,
    conversation_model_to_core,
    conversation_core_to_model,
    message_model_to_core,
    message_core_to_model
)
from app.core.coremodels import Conversation as CoreConversation, Message as CoreMessage


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
    
    def refresh_messages(self, conversation_id: int) -> List[CoreMessage]:
        """
        刷新指定会话的消息列表（仅查询，不修改会话元信息）
        
        Args:
            conversation_id: 会话ID
        
        Returns:
            List[CoreMessage]: 该会话最新的消息列表（按 order_index 排序）
        """
        from app.core.db_model_op import MessageOp  # 延迟导入，避免循环依赖
        
        with MessageOp(self.session) as msg_op:
            return msg_op.get_by_conversation_id(conversation_id, order_by="order_index")
    
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
        auto_title: bool = True,
        should_stop: Optional[Callable[[], bool]] = None
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
            auto_title=auto_title,
            should_stop=should_stop
        )
    
    def generate_response_for_existing_message(
        self,
        conversation_id: int,
        user_message_id: int,
        model_name: str = 'deepseek-chat',
        save_response: bool = False,
        should_stop: Optional[Callable[[], bool]] = None
    ) -> Generator[dict, None, None]:
        """
        为已存在的用户消息生成AI回答（对比模式）
        
        这是一个便捷方法，用于"查看其他模型如何回答这条消息"的场景：
        1. 验证用户消息是否存在且属于该会话
        2. 使用指定模型生成回答
        3. 可选择是否将回答保存到数据库
        
        Args:
            conversation_id: 会话ID
            user_message_id: 已存在的用户消息ID
            model_name: 模型名称（默认：'deepseek-chat'）
            save_response: 是否保存 AI 回答到数据库（默认：False）
        
        Yields:
            dict: 包含 'type' 和数据的字典
                - type='chunk': {'type': 'chunk', 'chunk': str}
                - type='done': {'type': 'done', 'message_id': int, 'user_message_id': int} (仅当 save_response=True)
                - type='error': {'type': 'error', 'error': str}
        
        Examples:
            >>> with ConversationOp() as op:
            ...     for result in op.generate_response_for_existing_message(
            ...         1, user_message_id=5, model_name='qwen-max', save_response=True
            ...     ):
            ...         if result['type'] == 'chunk':
            ...             print(result['chunk'], end='')
            ...         elif result['type'] == 'done':
            ...             print(f"\n完成！消息ID: {result['message_id']}")
        """
        from app.core.coremodels import Message, MessageRole
        
        # 1. 验证会话是否存在
        conversation = self.get_by_id(conversation_id)
        if not conversation:
            yield {'type': 'error', 'error': f'会话 {conversation_id} 不存在'}
            return
        
        # 2. 验证用户消息是否存在且属于该会话
        with MessageOp(self.session) as msg_op:
            user_msg = msg_op.get_by_id(user_message_id)
        
        if not user_msg:
            yield {'type': 'error', 'error': f'指定的用户消息不存在，user_message_id={user_message_id}'}
            return
        
        if user_msg.conversation_id != conversation_id:
            yield {'type': 'error', 'error': f'用户消息 {user_message_id} 不属于当前会话（当前会话ID={conversation_id}）'}
            return
        
        # 3. 使用 ChatManager 生成回答
        full_response = ""
        generation_start_time = time.time()  # 记录生成开始时间
        
        try:
            for chunk in self.chat_manager.generate_response_for_user_message(
                conversation_id=conversation_id,
                user_message=user_msg.content,
                user_message_id=user_message_id,
                model_name=model_name,
                stream=True,
                should_stop=should_stop
            ):
                # 检查是否应该停止
                if should_stop and should_stop():
                    yield {'type': 'interrupted', 'message': '用户中断生成'}
                    return
                
                yield {'type': 'chunk', 'chunk': chunk}
                if save_response:
                    full_response += chunk
            
            # 计算生成时长
            generation_time = time.time() - generation_start_time
            
            # 4. 如果 save_response=True，保存 AI 回答到数据库
            if save_response and full_response:
                with MessageOp(self.session) as msg_op:
                    # 获取该会话中最后一条消息的 order_index，用于确定新消息的顺序
                    existing_messages = msg_op.get_by_conversation_id(
                        conversation_id, 
                        order_by="order_index"
                    )
                    max_order = max([msg.order_index for msg in existing_messages], default=-1) if existing_messages else -1
                    new_order_index = max_order + 1
                    
                    # 创建 AI 消息对象
                    assistant_message = Message(
                        conversation_id=conversation_id,
                        role=MessageRole.ASSISTANT.value,
                        content=full_response,
                        model=model_name,
                        order_index=new_order_index,
                        generation_time=generation_time
                    )
                    
                    # 保存到数据库
                    saved_message = msg_op.create(assistant_message)
                    
                    yield {
                        'type': 'done',
                        'message_id': saved_message.id,
                        'user_message_id': user_message_id
                    }
            else:
                # 如果未保存，只 yield 一个 done 信号（不包含 message_id）
                yield {
                    'type': 'done',
                    'message_id': None,
                    'user_message_id': user_message_id
                }
        except Exception as e:
            yield {'type': 'error', 'error': f'生成模型回答失败: {str(e)}'}


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

