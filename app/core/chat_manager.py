# -*- coding:utf-8 -*-
"""
聊天管理器 - 使用 LangChain 管理对话和生成AI回答（v0 简化版）
"""
from typing import Optional, Generator, Union
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

from app.core.coremodels import Message
from app.core.db import MessageOp
from app.core.llm_config import get_default_llm, get_llm


class ChatManager:
    """
    使用 LangChain 管理对话和生成AI回答（v0 简化版）
    
    核心功能：
    1. 从数据库构建对话历史
    2. 生成AI回答
    """
    
    def __init__(self, llm=None):
        """
        初始化聊天管理器
        
        Args:
            llm: LangChain LLM 实例，如果为 None 则使用默认配置
        """
        self.llm = llm or get_default_llm()
    
    def build_memory_from_conversation(self, conversation_id: int, exclude_last_user: bool = False) -> ConversationBufferMemory:
        """
        从数据库构建 LangChain 的 ConversationBufferMemory
        
        Args:
            conversation_id: 会话ID
            exclude_last_user: 是否排除最后一条用户消息（用于避免重复）
        
        Returns:
            ConversationBufferMemory: LangChain 内存对象
        """
        # 获取所有消息（按顺序）- 使用 MessageOp
        with MessageOp() as op:
            messages = op.get_by_conversation_id(conversation_id, order_by="order_index")
        
        # 创建内存对象
        # 注意：ConversationChain 默认使用 'history' 作为 memory_key
        # return_messages=False 表示返回字符串格式的历史记录，而不是消息对象列表
        memory = ConversationBufferMemory(
            return_messages=False,  # 返回字符串格式，以匹配 ConversationChain 的默认 prompt
            memory_key="history"  # 使用 'history' 以匹配 ConversationChain 的默认 prompt
        )
        
        # 如果排除最后一条用户消息，找到最后一条用户消息的索引 TODO
        last_user_index = -1
        if exclude_last_user:
            for i in range(len(messages) - 1, -1, -1):
                if messages[i].role == "user":
                    last_user_index = i
                    break
        
        # 将数据库消息转换为 LangChain 消息格式
        for i, msg in enumerate(messages):
            # 如果排除最后一条用户消息，跳过它
            if exclude_last_user and i == last_user_index:
                continue
                
            if msg.role == "user":
                memory.chat_memory.add_user_message(msg.content)
            elif msg.role == "assistant":
                memory.chat_memory.add_ai_message(msg.content)
        return memory
    
    def _generate_with_conversation(
        self,
        llm,
        memory: ConversationBufferMemory,
        user_message: str,
        stream: bool = False
    ) -> Union[str, Generator]:
        """
        通用的生成回答方法（内部方法）
        通义千问和 DeepSeek 都使用此方法，确保逻辑一致
        
        Args:
            llm: LangChain LLM 实例
            memory: ConversationBufferMemory 实例
            user_message: 用户消息内容
            stream: 是否流式输出
        
        Returns:
            str: AI回答内容（stream=False 时）
            Generator: 生成器对象（stream=True 时）
        """
        # 创建对话链
        conversation = ConversationChain(
            llm=llm,
            memory=memory,
            verbose=True
        )
        
        # 生成回答
        if stream:
            return self._generate_stream(conversation, user_message)
        else:
            return self._generate_normal(conversation, user_message)
    
    def generate_response(
        self, 
        conversation_id: int, 
        user_message: str, 
        stream: bool = False
    ) -> Union[str, Generator]:
        """
        生成AI回答
        
        Args:
            conversation_id: 会话ID
            user_message: 用户消息
            stream: 是否流式返回
        
        Returns:
            str: AI回答内容（stream=False 时）
            Generator: 生成器对象（stream=True 时）
        """
        # 构建对话历史（排除最后一条用户消息，因为 predict 方法会自动添加）
        memory = self.build_memory_from_conversation(conversation_id, exclude_last_user=True)
        
        # 使用通用方法生成回答
        return self._generate_with_conversation(
            llm=self.llm,
            memory=memory,
            user_message=user_message,
            stream=stream
        )
    
    def _generate_normal(self, conversation, user_message: str) -> str:
        """生成普通（非流式）回答"""
        try:
            # 尝试使用 predict 方法
            if hasattr(conversation, 'predict'):
                response = conversation.predict(input=user_message)
                return response if isinstance(response, str) else str(response)
            # 尝试使用 run 方法
            elif hasattr(conversation, 'run'):
                response = conversation.run(input=user_message)
                return response if isinstance(response, str) else str(response)
            # 尝试使用 invoke 方法（新版本 LangChain）
            elif hasattr(conversation, 'invoke'):
                result = conversation.invoke({"input": user_message})
                return result.get("response", str(result)) if isinstance(result, dict) else str(result)
            else:
                raise AttributeError("ConversationChain 没有可用的调用方法")
        except Exception as e:
            # 记录详细错误信息
            import traceback
            error_detail = traceback.format_exc()
            print(f"生成AI回答时出错: {str(e)}")
            print(f"详细错误: {error_detail}")
            raise
    
    def _stream_from_llm(self, llm, messages: list) -> Generator:
        """
        通用的 LLM 流式输出方法
        通义千问和 DeepSeek 都使用相同的 ChatOpenAI 类，复用此方法
        
        Args:
            llm: LangChain LLM 实例
            messages: 消息列表（LangChain 消息对象）
        
        Yields:
            str: 流式输出的内容块
        """
        try:
            # 流式调用 LLM
            for chunk in llm.stream(messages):
                # 处理 chunk 内容
                content = None
                if hasattr(chunk, 'content'):
                    content = chunk.content
                elif isinstance(chunk, str):
                    content = chunk
                else:
                    # 尝试获取 delta 内容（增量内容）
                    if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'content'):
                        content = chunk.delta.content
                    else:
                        content = str(chunk) if chunk else None
                
                # 只 yield 非空内容
                if content:
                    yield content
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"LLM 流式输出失败: {str(e)}")
            print(f"详细错误: {error_detail}")
            raise
    
    def _build_messages_from_conversation(self, conversation, user_message: str) -> list:
        """
        从 ConversationChain 构建消息列表
        
        Args:
            conversation: ConversationChain 实例
            user_message: 用户消息内容
        
        Returns:
            list: LangChain 消息对象列表
        """
        messages = []
        
        # 导入 HumanMessage
        try:
            from langchain_core.messages import HumanMessage, AIMessage
        except ImportError:
            try:
                from langchain.schema import HumanMessage, AIMessage
            except ImportError:
                from langchain_core.messages import HumanMessage, AIMessage
        
        # 尝试从 memory 获取历史消息
        if hasattr(conversation.memory, 'chat_memory'):
            chat_memory = conversation.memory.chat_memory
            # 检查是否有 messages 属性（return_messages=True 时）
            if hasattr(chat_memory, 'messages'):
                # 获取消息列表
                try:
                    memory_messages = chat_memory.messages
                    if memory_messages:
                        for msg in memory_messages:
                            messages.append(msg)
                except (AttributeError, TypeError):
                    # 如果无法获取 messages，返回 None
                    return None
            else:
                # 如果没有 messages 属性（return_messages=False 时）
                # 这种情况下，我们无法直接获取消息对象
                # 返回 None，让调用者使用 ConversationChain 的流式方法
                return None
        
        # 添加当前用户消息
        messages.append(HumanMessage(content=user_message))
        return messages
    
    def _generate_stream(self, conversation, user_message: str) -> Generator:
        """
        生成流式回答（通用方法）
        通义千问和 DeepSeek 都使用此方法，确保逻辑一致
        
        Args:
            conversation: ConversationChain 实例
            user_message: 用户消息内容
        
        Yields:
            str: 流式输出的内容块
        """
        # 获取 LLM 实例（从 conversation 中）
        llm = conversation.llm
        
        try:
            # 方法1：尝试使用 LLM 的 stream 方法（推荐，最直接）
            # 通义千问和 DeepSeek 都使用 ChatOpenAI，支持 stream 方法
            if hasattr(llm, 'stream'):
                messages = self._build_messages_from_conversation(conversation, user_message)
                if messages:
                    # 成功构建消息列表，使用 LLM 的 stream 方法
                    yield from self._stream_from_llm(llm, messages)
                    return
            
            # 方法2：使用 ConversationChain 的流式方法（回退方案）
            if hasattr(conversation, 'predict_stream'):
                for chunk in conversation.predict_stream(input=user_message):
                    # predict_stream 返回的可能是字符串或字典
                    if isinstance(chunk, str):
                        yield chunk
                    elif isinstance(chunk, dict):
                        content = chunk.get("response", chunk.get("answer", ""))
                        if content:
                            yield content
                    else:
                        yield str(chunk)
                return
            
            # 方法3：使用 astream（异步流式，需要特殊处理）
            if hasattr(conversation, 'astream'):
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                async def async_stream():
                    async for chunk in conversation.astream({"input": user_message}):
                        if isinstance(chunk, dict):
                            content = chunk.get("response", chunk.get("answer", ""))
                        else:
                            content = str(chunk)
                        if content:
                            yield content
                
                # 同步调用异步生成器
                for item in async_stream():
                    yield item
                return
            
            # 方法4：最后回退 - 模拟流式输出（逐字符）
            response = conversation.predict(input=user_message)
            for char in response:
                yield char
            return
                    
        except Exception as e:
            # 如果流式失败，回退到普通输出并模拟流式
            import traceback
            error_detail = traceback.format_exc()
            print(f"流式输出失败，回退到普通输出: {str(e)}")
            print(f"详细错误: {error_detail}")
            # 使用普通方法获取回答，然后逐字符输出
            try:
                response = conversation.predict(input=user_message)
                for char in response:
                    yield char
            except Exception as e2:
                # 如果连普通输出都失败，返回错误信息
                yield f"\n\n[错误: {str(e2)}]"
    
    def generate_response_for_user_message(
        self,
        conversation_id: int,
        user_message_id: int,
        user_message: str,
        model_name: str,
        stream: bool = False
    ) -> Union[str, Generator]:
        """
        为指定用户消息生成模型回答（Peer 架构）
        
        关键：构建上下文时，只包含该用户消息之前的所有消息（order_index < user_message.order_index）
        这样自动排除了该用户消息之后的所有 assistant 消息（因为它们是对该用户消息的回答）
        
        Args:
            conversation_id: 会话ID
            user_message_id: 用户消息ID
            user_message: 用户消息内容
            model_name: 要使用的模型名称（如 'qwen-max'）
            stream: 是否流式输出
        
        Returns:
            str: AI回答内容（stream=False 时）
            Generator: 生成器对象（stream=True 时）
        """
        # 构建内存（只包含该用户消息之前的所有消息，自动排除之后的消息）
        memory = self.build_memory_for_user_message(
            conversation_id,
            user_message_id,
            model_name
        )
        
        # 获取指定模型的 LLM 实例
        # 根据模型名称判断 provider
        if model_name in ['qwen-max', 'deepseek-chat']:
            llm = get_llm('302ai', model_name=model_name)
        else:
            # 默认使用 302ai provider
            llm = get_llm('302ai', model_name=model_name)
        
        # 使用通用方法生成回答
        return self._generate_with_conversation(
            llm=llm,
            memory=memory,
            user_message=user_message,
            stream=stream
        )
    
    def build_memory_for_user_message(
        self, 
        conversation_id: int, 
        user_message_id: int, 
        target_model_name: str
    ) -> ConversationBufferMemory:
        """
        构建为指定用户消息生成回答时的对话历史（Peer 架构）
        
        规则：
        1. 只包含该用户消息之前的所有消息（order_index < user_message.order_index）
        2. 自动排除该用户消息之后的所有 assistant 消息（因为它们是对该用户消息的回答）
        3. 对于每一轮用户消息，优先使用同类模型的回答
        4. 如果没有同类模型的回答，使用第一个其他模型的回答（按时间顺序）
        
        Args:
            conversation_id: 会话ID
            user_message_id: 用户消息ID
            target_model_name: 目标模型名称（用于判断"同类模型"）
        
        Returns:
            ConversationBufferMemory: LangChain 内存对象
        """
        # 获取用户消息 - 使用 MessageOp
        with MessageOp() as op:
            user_message = op.get_by_id(user_message_id)
            if not user_message:
                raise ValueError(f"用户消息 {user_message_id} 不存在")
            
            # 获取该用户消息之前的所有消息（自动排除该用户消息之后的所有消息）
            all_messages = op.get_by_conversation_id(conversation_id, order_by="order_index")
            messages = [msg for msg in all_messages if msg.order_index is not None and msg.order_index < user_message.order_index]
        
        # 按用户消息分组，构建轮次
        rounds = []  # [(user_msg, [assistant_msgs]), ...]
        current_user_msg = None
        current_assistant_msgs = []
        
        for msg in messages:
            if msg.role == 'user':
                # 保存上一轮
                if current_user_msg:
                    rounds.append((current_user_msg, current_assistant_msgs))
                # 开始新的一轮
                current_user_msg = msg
                current_assistant_msgs = []
            elif msg.role == 'assistant':
                current_assistant_msgs.append(msg)
        
        # 保存最后一轮
        if current_user_msg:
            rounds.append((current_user_msg, current_assistant_msgs))
        
        # 创建内存对象
        memory = ConversationBufferMemory(
            return_messages=False,
            memory_key="history"
        )
        
        # 构建内存
        for user_msg, assistant_msgs in rounds:
            # 添加用户消息
            memory.chat_memory.add_user_message(user_msg.content)
            
            # 选择 assistant 消息
            selected_assistant = None
            # 优先选择同类模型的回答
            for assistant_msg in assistant_msgs:
                if assistant_msg.model == target_model_name:
                    selected_assistant = assistant_msg
                    break
            # 如果没有同类模型，使用第一个其他模型的回答（按时间顺序，即 order_index 最小的）
            if not selected_assistant and assistant_msgs:
                # 按 order_index 排序，选择第一个
                assistant_msgs_sorted = sorted(assistant_msgs, key=lambda m: m.order_index)
                selected_assistant = assistant_msgs_sorted[0]
            
            # 添加选中的 assistant 消息
            if selected_assistant:
                memory.chat_memory.add_ai_message(selected_assistant.content)
        
        return memory
    
