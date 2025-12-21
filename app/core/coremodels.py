# -*- coding:utf-8 -*-
"""
核心领域模型（Core Domain Models）
纯 Python 实现，不依赖任何第三方库（Flask、SQLAlchemy 等）

设计理念：
- 纯数据类，只包含核心属性和业务逻辑
- 不依赖任何 Web 框架或 ORM
- 可用于领域驱动设计（DDD）的核心层
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Generator, Union, Callable
from enum import Enum


class MessageRole(Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

# 
@dataclass
class Message:
    """
    消息领域模型
    纯数据类，不依赖任何框架
    
    属性：
        id: 消息ID（可选，由持久化层分配）
        conversation_id: 所属会话ID
        role: 消息角色（'user' 或 'assistant'）
        content: 消息内容
        created_at: 创建时间
        order_index: 消息在会话中的顺序索引
        model: 模型标识（如 'deepseek-chat', 'qwen-max' 等）
        generation_time: 生成答案耗时（秒），仅助手消息有此属性
    """
    conversation_id: Optional[int] = None
    role: str = MessageRole.USER.value
    content: str = ""
    order_index: Optional[int] = None
    model: str = "deepseek-chat"
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    generation_time: Optional[float] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.created_at is None:
            self.created_at = datetime.now()
        
        # 验证 role 是否有效
        valid_roles = [r.value for r in MessageRole]
        if self.role not in valid_roles:
            raise ValueError(f"Invalid role: {self.role}. Must be one of {valid_roles}")
    
    def is_user_message(self) -> bool:
        """判断是否为用户消息"""
        return self.role == MessageRole.USER.value
    
    def is_assistant_message(self) -> bool:
        """判断是否为助手消息"""
        return self.role == MessageRole.ASSISTANT.value
    
    def is_system_message(self) -> bool:
        """判断是否为系统消息"""
        return self.role == MessageRole.SYSTEM.value
    
    # ==================== 数据库操作包装方法 ====================
    # 这些方法内部使用 MessageOp，提供便捷的数据库操作接口
    
    @classmethod
    def _get_op(cls):
        """获取 MessageOp 实例（延迟导入避免循环依赖）"""
        from app.core.db_model_op import MessageOp
        return MessageOp()
    
    @classmethod
    def list(
        cls, 
        conversation_id: Optional[int] = None, 
        limit: Optional[int] = None,
        order_by: str = "order_index"
    ) -> List['Message']:
        """
        列出消息（包装 MessageOp.list()）
        
        Args:
            conversation_id: 可选，如果指定则只列出该会话的消息
            limit: 可选，限制返回数量
            order_by: 排序字段，可选值：'order_index', 'created_at'
        
        Returns:
            List[Message]: 消息列表
        
        Examples:
            >>> # 列出所有消息
            >>> messages = Message.list()
            >>> # 列出特定会话的消息
            >>> messages = Message.list(conversation_id=1)
            >>> # 限制数量
            >>> messages = Message.list(limit=10)
        """
        with cls._get_op() as op:
            return op.list(conversation_id=conversation_id, limit=limit, order_by=order_by)
    
    @classmethod
    def get_by_id(cls, message_id: int) -> Optional['Message']:
        """
        根据 ID 获取消息（包装 MessageOp.get_by_id()）
        
        Args:
            message_id: 消息ID
        
        Returns:
            Optional[Message]: 消息对象，如果不存在则返回 None
        
        Examples:
            >>> msg = Message.get_by_id(1)
            >>> if msg:
            ...     print(msg.content)
        """
        with cls._get_op() as op:
            return op.get_by_id(message_id)
    
    @classmethod
    def get_by_conversation_id(
        cls, 
        conversation_id: int, 
        order_by: str = "order_index"
    ) -> List['Message']:
        """
        获取会话的所有消息（包装 MessageOp.get_by_conversation_id()）
        
        Args:
            conversation_id: 会话ID
            order_by: 排序字段，可选值：'order_index', 'created_at'
        
        Returns:
            List[Message]: 消息列表
        
        Examples:
            >>> messages = Message.get_by_conversation_id(1)
            >>> for msg in messages:
            ...     print(msg.content)
        """
        with cls._get_op() as op:
            return op.get_by_conversation_id(conversation_id, order_by=order_by)
    
    @classmethod
    def create(
        cls,
        conversation_id: int,
        role: str = MessageRole.USER.value,
        content: str = "",
        order_index: Optional[int] = None,
        model: str = "deepseek-chat"
    ) -> 'Message':
        """
        创建新消息（包装 MessageOp.create()）
        
        Args:
            conversation_id: 会话ID
            role: 消息角色（'user' 或 'assistant'）
            content: 消息内容
            order_index: 消息顺序索引
            model: 模型标识
        
        Returns:
            Message: 创建后的消息对象（包含生成的 ID）
        
        Examples:
            >>> msg = Message.create(
            ...     conversation_id=1,
            ...     role="user",
            ...     content="你好"
            ... )
            >>> print(f"创建的消息ID: {msg.id}")
        """
        msg = cls(
            conversation_id=conversation_id,
            role=role,
            content=content,
            order_index=order_index,
            model=model
        )
        with cls._get_op() as op:
            return op.create(msg)
    
    def save(self) -> 'Message':
        """
        保存消息到数据库（如果已存在则更新，否则创建）
        
        Returns:
            Message: 保存后的消息对象
        
        Examples:
            >>> msg = Message(conversation_id=1, content="测试")
            >>> saved = msg.save()  # 创建新消息
            >>> saved.content = "更新后的内容"
            >>> saved.save()  # 更新消息
        """
        with self._get_op() as op:
            if self.id is None:
                # 创建新消息
                return op.create(self)
            else:
                # 更新现有消息
                result = op.update(self)
                if result is None:
                    # 如果更新失败（不存在），则创建
                    self.id = None
                    return op.create(self)
                return result
    
    def delete(self) -> bool:
        """
        删除消息（包装 MessageOp.delete()）
        
        Returns:
            bool: 是否成功删除
        
        Examples:
            >>> msg = Message.get_by_id(1)
            >>> if msg:
            ...     msg.delete()
        """
        if self.id is None:
            return False
        with self._get_op() as op:
            return op.delete(self.id)
    
    def __repr__(self):
        """字符串表示"""
        role_str = self.role
        content_preview = self.content[:30] + "..." if len(self.content) > 30 else self.content
        return f'<Message id={self.id} role={role_str} content="{content_preview}">'


@dataclass
class Conversation:
    """
    会话领域模型
    纯数据类，不依赖任何框架
    
    属性：
        id: 会话ID（可选，由持久化层分配）
        title: 会话标题
        user_id: 所属用户ID
        created_at: 创建时间
        updated_at: 更新时间
        messages: 消息列表（关联关系）
    """
    title: str = "新对话"
    user_id: Optional[int] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    messages: List[Message] = field(default_factory=list)
    
    def __post_init__(self):
        """初始化后处理"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at
    
    def add_message(self, message: Message):
        """
        添加消息到会话
        
        Args:
            message: 要添加的消息对象
        """
        message.conversation_id = self.id
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def remove_message(self, message_id: int) -> bool:
        """
        从会话中移除消息
        
        Args:
            message_id: 要移除的消息ID
        
        Returns:
            bool: 是否成功移除
        """
        for i, msg in enumerate(self.messages):
            if msg.id == message_id:
                self.messages.pop(i)
                self.updated_at = datetime.now()
                return True
        return False
    
    def get_user_messages(self) -> List[Message]:
        """获取所有用户消息"""
        return [msg for msg in self.messages if msg.is_user_message()]
    
    def get_assistant_messages(self) -> List[Message]:
        """获取所有助手消息"""
        return [msg for msg in self.messages if msg.is_assistant_message()]
    
    def get_messages_by_model(self, model: str) -> List[Message]:
        """
        获取指定模型的所有消息
        
        Args:
            model: 模型标识（如 'deepseek-chat', 'qwen-max'）
        
        Returns:
            List[Message]: 匹配的消息列表
        """
        return [msg for msg in self.messages 
                if msg.is_assistant_message() and msg.model == model]
    
    def get_last_message(self) -> Optional[Message]:
        """
        获取最后一条消息（按 order_index 排序）
        
        Returns:
            Optional[Message]: 最后一条消息，如果没有则返回 None
        """
        if not self.messages:
            return None
        return max(self.messages, key=lambda m: m.order_index or 0)
    
    def get_messages_sorted(self) -> List[Message]:
        """
        获取按 order_index 排序的消息列表
        
        Returns:
            List[Message]: 排序后的消息列表
        """
        return sorted(self.messages, key=lambda m: m.order_index or 0)
    
    def get_message_count(self) -> int:
        """获取消息总数"""
        return len(self.messages)
    
    def update_title(self, new_title: str):
        """
        更新会话标题
        
        Args:
            new_title: 新标题
        """
        self.title = new_title
        self.updated_at = datetime.now()
    
    # ==================== 数据库操作包装方法 ====================
    # 这些方法内部使用 ConversationOp，提供便捷的数据库操作接口
    
    @classmethod
    def _get_op(cls):
        """获取 ConversationOp 实例（延迟导入避免循环依赖）"""
        from app.core.db_model_op import ConversationOp
        return ConversationOp()
    
    @classmethod
    def list(cls, user_id: Optional[int] = None, limit: Optional[int] = None) -> List['Conversation']:
        """
        列出所有会话（包装 ConversationOp.list()）
        
        Args:
            user_id: 可选，如果指定则只列出该用户的对话
            limit: 可选，限制返回数量
        
        Returns:
            List[Conversation]: 会话列表
        
        Examples:
            >>> # 列出所有会话
            >>> conversations = Conversation.list()
            >>> # 列出特定用户的会话
            >>> conversations = Conversation.list(user_id=1)
            >>> # 限制数量
            >>> conversations = Conversation.list(limit=10)
        """
        with cls._get_op() as op:
            return op.list(user_id=user_id, limit=limit)
    
    @classmethod
    def get_by_id(cls, conversation_id: int) -> Optional['Conversation']:
        """
        根据 ID 获取会话（包装 ConversationOp.get_by_id()）
        
        Args:
            conversation_id: 会话ID
        
        Returns:
            Optional[Conversation]: 会话对象，如果不存在则返回 None
        
        Examples:
            >>> conv = Conversation.get_by_id(1)
            >>> if conv:
            ...     print(conv.title)
        """
        with cls._get_op() as op:
            return op.get_by_id(conversation_id)
    
    @classmethod
    def create(cls, title: str = "新对话", user_id: Optional[int] = None) -> 'Conversation':
        """
        创建新会话（包装 ConversationOp.create()）
        
        Args:
            title: 会话标题
            user_id: 用户ID
        
        Returns:
            Conversation: 创建后的会话对象（包含生成的 ID）
        
        Examples:
            >>> conv = Conversation.create(title="测试对话", user_id=1)
            >>> print(f"创建的会话ID: {conv.id}")
        """
        conv = cls(title=title, user_id=user_id)
        with cls._get_op() as op:
            return op.create(conv)
    
    def save(self) -> 'Conversation':
        """
        保存会话到数据库（如果已存在则更新，否则创建）
        
        Returns:
            Conversation: 保存后的会话对象
        
        Examples:
            >>> conv = Conversation(title="测试", user_id=1)
            >>> saved = conv.save()  # 创建新会话
            >>> saved.title = "新标题"
            >>> saved.save()  # 更新会话
        """
        with self._get_op() as op:
            if self.id is None:
                # 创建新会话
                return op.create(self)
            else:
                # 更新现有会话
                result = op.update(self)
                if result is None:
                    # 如果更新失败（不存在），则创建
                    self.id = None
                    return op.create(self)
                return result
    
    def delete(self) -> bool:
        """
        删除会话（包装 ConversationOp.delete()）
        
        Returns:
            bool: 是否成功删除
        
        Examples:
            >>> conv = Conversation.get_by_id(1)
            >>> if conv:
            ...     conv.delete()
        """
        if self.id is None:
            return False
        with self._get_op() as op:
            return op.delete(self.id)
    
    def refresh_messages(self) -> 'Conversation':
        """
        从数据库刷新当前会话的消息列表到 self.messages
        
        注意：这是一个读操作，不会修改数据库，只是让内存中的会话对象与数据库保持同步。
        
        Returns:
            Conversation: 刷新后的当前会话实例（便于链式调用）
        
        Examples:
            >>> conv = Conversation.get_by_id(1)
            >>> # 其他地方插入了新消息，此时内存中的 conv.messages 可能过期
            >>> conv.refresh_messages()
            >>> print(len(conv.messages))
        """
        if self.id is None:
            raise ValueError("当前会话尚未保存到数据库，无法刷新消息（id 为 None）")
        
        with self._get_op() as op:
            # 使用 ConversationOp 的 refresh_messages 从数据库取最新的消息列表
            messages = op.refresh_messages(self.id)
        
        self.messages = messages
        return self
    
    def send_message(
        self,
        user_content: Optional[str]='',
        model_name: str = 'deepseek-chat',
        auto_title: bool = True,
        user_message_id: Optional[int] = None,
        save_response: bool = False,
        return_iterator: bool = False,
        should_stop: Optional[Callable[[], bool]] = None
    ) -> Union[Generator[dict, None, None], Optional[dict]]:
        """
        发送消息并获取AI回答
        
        这是一个便捷方法，使用当前会话实例的 ID，封装了两类场景：
        1. 正常对话模式（user_message_id 为空）：
           - 创建用户消息
           - 生成并保存 AI 回答
           - 默认打印流式输出到屏幕，或通过迭代器返回
        2. 对比模型回答模式（user_message_id 有值）：
           - 不再新增用户消息，而是选定一条已存在的用户消息
           - 使用指定模型生成回答，用于"查看这个模型回答得怎么样"
           - 可通过 save_response 参数控制是否将回答持久化到数据库
        
        Args:
            user_content: 用户消息内容（正常对话模式使用；对比模式下会自动读取 user_message_id 对应消息内容）
            model_name: 模型名称（默认：'deepseek-chat'）
            auto_title: 是否自动生成会话标题（默认：True，仅正常对话模式生效）
            user_message_id: 可选，已存在的用户消息 ID，用于"查看其他模型如何回答这条消息"
            save_response: 是否保存 AI 回答到数据库（默认：False，仅对比模式生效；正常对话模式始终保存）
            return_iterator: 是否返回迭代器（默认：False，打印到控制台；True 时返回生成器供 API 使用）
            should_stop: 可选，停止检查函数，返回 True 时停止生成。如果不提供，在 CLI 环境下会自动创建基于 Ctrl+C 的检查器
        
        Returns:
            如果 return_iterator=False（默认）：
                Optional[dict]: 完成时的结果字典，包含 'message_id' 和 'user_message_id'，如果出错则返回 None
            如果 return_iterator=True：
                Generator[dict, None, None]: 生成器，yield 包含 'type' 和数据的字典
                    - type='chunk': {'type': 'chunk', 'chunk': str}
                    - type='done': {'type': 'done', 'message_id': int, 'user_message_id': int}
                    - type='interrupted': {'type': 'interrupted', 'message': str}  # 用户中断
                    - type='error': {'type': 'error', 'error': str}
        
        Examples:
            >>> conv = Conversation.get_by_id(1)
            >>> # 正常对话（默认打印到控制台，自动支持 Ctrl+C）
            >>> result = conv.send_message("你好", model_name='deepseek-chat')
            >>> # 正常对话（返回迭代器，用于 API）
            >>> for result in conv.send_message("你好", model_name='deepseek-chat', return_iterator=True):
            ...     if result['type'] == 'chunk':
            ...         # 处理流式数据块
            ...         pass
            >>> # 对比模式（默认打印到控制台）
            >>> conv.send_message(user_message_id=5, model_name='qwen-max')
            >>> # 对比模式（返回迭代器，用于 API）
            >>> for result in conv.send_message(user_message_id=5, model_name='qwen-max', save_response=True, return_iterator=True):
            ...     if result['type'] == 'chunk':
            ...         # 处理流式数据块
            ...         pass
        """
        # 如果没有提供 should_stop，在 CLI 环境下自动创建基于信号的检查器
        if should_stop is None:
            try:
                from app.core.stop_checker import create_cli_stop_checker
                cli_checker = create_cli_stop_checker()
                cli_checker.reset()  # 重置状态
                should_stop = cli_checker.should_stop
            except Exception:
                # 如果无法创建检查器（如在某些环境中），使用 None
                should_stop = None
        
        # 内部生成器函数
        def _generate():
            if self.id is None:
                yield {'type': 'error', 'error': '会话尚未保存到数据库，请先调用 save() 方法'}
                return
            
            # 参数校验：user_content 与 user_message_id 二选一
            if user_message_id is not None and user_content:
                yield {'type': 'error', 'error': 'user_content 和 user_message_id 不能同时提供，请二选一。正常对话：只传 user_content；对比模型回答：只传 user_message_id'}
                return
            if user_message_id is None and not user_content:
                yield {'type': 'error', 'error': '需要提供 user_content（正常对话）或 user_message_id（二选一）'}
                return
            
            # ========== 模式2：对比模型回答（基于已有 user_message_id） ==========
            if user_message_id is not None:
                from app.core.db_model_op import ConversationOp, MessageOp  # 延迟导入，避免循环依赖
                
                # 验证用户消息是否存在
                with MessageOp() as msg_op:
                    user_msg = msg_op.get_by_id(user_message_id)
                
                if not user_msg:
                    yield {'type': 'error', 'error': f'指定的用户消息不存在，user_message_id={user_message_id}'}
                    return
                
                if user_msg.conversation_id != self.id:
                    yield {'type': 'error', 'error': f'用户消息 {user_message_id} 不属于当前会话（当前会话ID={self.id}）'}
                    return
                
                # 使用 ConversationOp 的包装方法生成回答
                with ConversationOp() as op:
                    try:
                        for result in op.generate_response_for_existing_message(
                            conversation_id=self.id,
                            user_message_id=user_message_id,
                            model_name=model_name,
                            save_response=save_response,
                            should_stop=should_stop
                        ):
                            # 检查是否应该停止
                            if should_stop and should_stop():
                                yield {'type': 'interrupted', 'message': '用户中断生成'}
                                return
                            
                            yield result
                            
                            # 如果保存成功，刷新当前会话的消息列表
                            if result['type'] == 'done' and save_response and result.get('message_id'):
                                self.refresh_messages()
                    except KeyboardInterrupt:
                        # 捕获 Ctrl+C（双重保险）
                        yield {'type': 'interrupted', 'message': '检测到 Ctrl+C，已中断生成'}
                        return
                    except Exception as e:
                        import traceback
                        error_detail = traceback.format_exc()
                        print(f"生成模型回答异常: {str(e)}")
                        print(f"详细错误: {error_detail}")
                        yield {'type': 'error', 'error': f'生成模型回答失败: {str(e)}'}
                return
            
            # ========== 模式1：正常对话（创建新用户消息并落库） ==========
            from app.core.db_model_op import ConversationOp  # 延迟导入，避免循环依赖
            with ConversationOp() as op:
                try:
                    for result in op.send_message(
                        conversation_id=self.id,
                        user_content=user_content,
                        model_name=model_name,
                        auto_title=auto_title,
                        should_stop=should_stop
                    ):
                        # 检查是否应该停止
                        if should_stop and should_stop():
                            yield {'type': 'interrupted', 'message': '用户中断生成'}
                            return
                        
                        yield result
                except KeyboardInterrupt:
                    # 捕获 Ctrl+C（双重保险）
                    yield {'type': 'interrupted', 'message': '检测到 Ctrl+C，已中断生成'}
                    return
                except Exception as e:
                    import traceback
                    error_detail = traceback.format_exc()
                    print(f"发送消息异常: {str(e)}")
                    print(f"详细错误: {error_detail}")
                    yield {'type': 'error', 'error': f'发送消息失败: {str(e)}'}
        
        # 如果返回迭代器，直接返回生成器
        if return_iterator:
            return _generate()
        
        # 否则，消费生成器并打印到控制台
        assistant_message_id = None
        created_user_message_id = None
        
        try:
            for result in _generate():
                if result['type'] == 'chunk':
                    print(result['chunk'], end='', flush=True)
                elif result['type'] == 'done':
                    assistant_message_id = result.get('message_id')
                    created_user_message_id = result.get('user_message_id')
                    print()  # 换行
                    if save_response and assistant_message_id:
                        print(f"✅ AI 回答已保存，消息ID: {assistant_message_id}")
                elif result['type'] == 'error':
                    print(f"\n❌ 错误: {result['error']}")
                    return None
            
            # 返回完成信息
            if assistant_message_id:
                return {
                    'message_id': assistant_message_id,
                    'user_message_id': created_user_message_id or user_message_id
                }
            return None
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"处理消息异常: {str(e)}")
            print(f"详细错误: {error_detail}")
            return None
    
    def __repr__(self):
        """字符串表示"""
        message_count = len(self.messages)
        return f'<Conversation id={self.id} title="{self.title}" messages={message_count}>'

