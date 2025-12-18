# -*- coding:utf-8 -*-
"""
聊天管理器 - 使用 LangChain 管理对话和生成AI回答（v0 简化版）
"""
from typing import Optional, Generator, Union, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_openai import ChatOpenAI
    from langchain_core.language_models.chat_models import BaseChatModel

from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

from app.core.coremodels import Message
from app.core.db import MessageOp, ConversationOp
from app.core.llm_config import get_default_llm, get_llm
from datetime import datetime


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
    
    def build_memory_for_conversation(
        self, 
        conversation_id: int, 
        user_message_id: Optional[int] = None,
        target_model_name: Optional[str] = None,
        exclude_last_user: bool = False
    ) -> ConversationBufferMemory:
        """
        从数据库构建 LangChain 的 ConversationBufferMemory
        
        支持两种模式：
        1. 简单模式（user_message_id=None）：包含所有消息，可选排除最后一条用户消息
        2. Peer 架构模式（user_message_id 有值）：只包含该用户消息之前的消息，按模型选择回答
        
        Args:
            conversation_id: 会话ID
            user_message_id: 可选，用户消息ID（Peer 架构模式）
            target_model_name: 可选，目标模型名称（Peer 架构模式，用于判断"同类模型"）
            exclude_last_user: 是否排除最后一条用户消息（简单模式）
        
        Returns:
            ConversationBufferMemory: LangChain 内存对象
        """
        # 创建内存对象
        memory = ConversationBufferMemory(
            return_messages=False,
            memory_key="history"
        )
        
        with MessageOp() as op:
            if user_message_id is None:
                # 简单模式：包含所有消息
                messages = op.get_by_conversation_id(conversation_id, order_by="order_index")
                
                # 如果排除最后一条用户消息，找到最后一条用户消息的索引
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
            else:
                # Peer 架构模式：只包含该用户消息之前的消息，按模型选择回答
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
                
                # 构建内存
                for user_msg, assistant_msgs in rounds:
                    # 添加用户消息
                    memory.chat_memory.add_user_message(user_msg.content)
                    
                    # 选择 assistant 消息
                    selected_assistant = None
                    if target_model_name:
                        # 优先选择同类模型的回答
                        for assistant_msg in assistant_msgs:
                            if assistant_msg.model == target_model_name:
                                selected_assistant = assistant_msg
                                break
                    # 如果没有同类模型或未指定模型，使用第一个其他模型的回答（按时间顺序，即 order_index 最小的）
                    if not selected_assistant and assistant_msgs:
                        # 按 order_index 排序，选择第一个
                        assistant_msgs_sorted = sorted(assistant_msgs, key=lambda m: m.order_index)
                        selected_assistant = assistant_msgs_sorted[0]
                    
                    # 添加选中的 assistant 消息
                    if selected_assistant:
                        memory.chat_memory.add_ai_message(selected_assistant.content)
        
        return memory
    def _generate_with_conversation(
        self,
        llm: Union['ChatOpenAI', 'BaseChatModel', Any],
        memory: ConversationBufferMemory,
        user_message: str,
        stream: bool = False
    ) -> Union[str, Generator[str, None, None]]:
        """
        通用的生成回答方法（内部方法）
        通义千问和 DeepSeek 都使用此方法，确保逻辑一致
        
        Args:
            llm: LangChain LLM 实例（通常是 ChatOpenAI，也可以是其他实现了 BaseChatModel 的 LLM）
            memory: ConversationBufferMemory 实例
            user_message: 用户消息内容
            stream: 是否流式输出
        
        Returns:
            str: AI回答内容（stream=False 时）
            Generator[str, None, None]: 生成器对象（stream=True 时）
        """
        # 创建对话链
        conversation = ConversationChain(
            llm=llm,
            memory=memory,
            verbose=True
        )
        
        # 生成回答
        if stream:
            return self.__generate_stream(conversation, user_message)
        else:
            return self.__generate_normal(conversation, user_message)
    
    def __generate_normal(self, conversation: ConversationChain, user_message: str) -> str:
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
    
    def __generate_stream(self, conversation: ConversationChain, user_message: str) -> Generator[str, None, None]:
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
            # 方法1：使用 ConversationChain 的流式方法（推荐）
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
            
            # 方法2：最后回退 - 模拟流式输出（逐字符）
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
        user_message: str,
        user_message_id: Optional[int] = None,
        model_name: Optional[str] = None,
        stream: bool = False,
        exclude_last_user: bool = False
    ) -> Union[str, Generator]:
        """
        生成模型回答（统一方法）
        
        支持两种模式：
        1. 简单模式（user_message_id=None）：包含所有消息，使用默认 LLM
        2. Peer 架构模式（user_message_id 有值）：只包含该用户消息之前的消息，按模型选择回答
        
        Args:
            conversation_id: 会话ID
            user_message: 用户消息内容
            user_message_id: 可选，用户消息ID（Peer 架构模式）
            model_name: 可选，模型名称（Peer 架构模式，如 'qwen-max'）
            stream: 是否流式输出
            exclude_last_user: 是否排除最后一条用户消息（简单模式，用于避免与 LangChain 自动添加的消息重复）
        
        Returns:
            str: AI回答内容（stream=False 时）
            Generator: 生成器对象（stream=True 时）
        """
        # 构建内存
        if user_message_id is None:
            # 简单模式：包含所有消息
            memory = self.build_memory_for_conversation(
                conversation_id,
                exclude_last_user=exclude_last_user
            )
            # 使用默认 LLM
            llm = self.llm
        else:
            # Peer 架构模式：只包含该用户消息之前的消息，按模型选择回答
            if not model_name:
                raise ValueError("Peer 架构模式需要指定 model_name")
            
            memory = self.build_memory_for_conversation(
                conversation_id,
                user_message_id=user_message_id,
                target_model_name=model_name
            )
            # 获取指定模型的 LLM 实例
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
    
    
    
    def generate_and_save_assistant_response(
        self,
        conversation_id: int,
        user_message_id: int,
        user_message: Message,
        model_name: str,
        precomputed_order_index: Optional[int] = None,
        auto_title: bool = False
    ) -> Generator[dict, None, None]:
        """
        生成助手回答并保存到数据库（流式）
        
        这是一个完整的工作流方法，包含：
        1. 生成流式回答
        2. 保存助手消息到数据库
        3. 更新会话的 updated_at
        4. 自动生成会话标题（可选）
        
        Args:
            conversation_id: 会话ID
            user_message_id: 用户消息ID
            user_message: 用户消息对象（领域模型）
            model_name: 模型名称
            precomputed_order_index: 预先计算的 order_index（如果为 None，则流式后计算）
            auto_title: 是否自动生成会话标题（仅第一条消息时）
        
        Yields:
            dict: 包含 'type' 和数据的字典
                - type='chunk': {'type': 'chunk', 'chunk': str}
                - type='done': {'type': 'done', 'message_id': int, 'user_message_id': int}
                - type='error': {'type': 'error', 'error': str}
        """
        assistant_content = ""
        try:
            # 生成流式回答（Peer 架构）
            for chunk in self.generate_response_for_user_message(
                conversation_id=conversation_id,
                user_message=user_message.content,
                user_message_id=user_message_id,
                model_name=model_name,
                stream=True
            ):
                assistant_content += chunk
                # 发送数据块
                yield {'type': 'chunk', 'chunk': chunk}
            
            # 流式输出完成，保存AI回答到数据库
            # 计算 order_index
            if precomputed_order_index is not None:
                order_index = precomputed_order_index
            else:
                # 流式后计算：助手消息应该紧跟在用户消息之后
                order_index = (user_message.order_index or 0) + 1
            
            # 创建助手消息
            assistant_message = Message(
                conversation_id=conversation_id,
                role='assistant',
                content=assistant_content,
                order_index=order_index,
                model=model_name
            )
            
            # 保存助手消息和更新会话
            with MessageOp() as msg_op, ConversationOp() as conv_op:
                # 保存助手消息
                saved_message = msg_op.create(assistant_message)
                
                # 更新会话的 updated_at
                conversation = conv_op.get_by_id(conversation_id)
                if conversation:
                    conversation.updated_at = datetime.now()
                    
                    # 如果这是第一条消息，自动生成会话标题
                    if auto_title:
                        messages = msg_op.get_by_conversation_id(conversation_id)
                        if len(messages) == 1 and (not conversation.title or conversation.title == '新对话'):
                            title = user_message.content[:20] if len(user_message.content) > 20 else user_message.content
                            conversation.title = title
                    
                    conv_op.update(conversation)
            
            # 发送完成信号
            yield {
                'type': 'done',
                'message_id': saved_message.id,
                'user_message_id': user_message_id
            }
            
        except GeneratorExit:
            # 生成器被关闭（客户端断开连接），不处理
            raise
        except Exception as e:
            # AI API 调用失败，记录详细错误并返回
            import traceback
            error_detail = traceback.format_exc()
            print(f"AI API调用失败: {str(e)}")
            print(f"详细错误: {error_detail}")
            # 发送错误信息
            yield {'type': 'error', 'error': str(e)}
    
