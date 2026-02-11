# -*- coding:utf-8 -*-
"""
聊天管理器 - 使用 LangChain 管理对话和生成AI回答（v0 简化版）
"""
from typing import Optional, Generator, Union, Any, TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from langchain_openai import ChatOpenAI
    from langchain_core.language_models.chat_models import BaseChatModel

from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

from app.core.coremodels import Message
from app.core.db_model_op import MessageOp, ConversationOp
from app.core.llm_config import get_default_llm, get_llm
from datetime import datetime
import time
import threading


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
        print("user_message_id is ", user_message_id)
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
        stream: bool = False,
        should_stop: Optional[Callable[[], bool]] = None
    ) -> Union[str, Generator[str, None, None]]:
        """
        通用的生成回答方法（内部方法）
        通义千问和 DeepSeek 都使用此方法，确保逻辑一致
        
        Args:
            llm: LangChain LLM 实例（通常是 ChatOpenAI，也可以是其他实现了 BaseChatModel 的 LLM）
            memory: ConversationBufferMemory 实例
            user_message: 用户消息内容
            stream: 是否流式输出
            should_stop: 中断检查函数，返回 True 时停止生成（可选）
        
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
            return self.__generate_stream(conversation, user_message, should_stop=should_stop)
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
    
    def __generate_stream(
        self, 
        conversation: ConversationChain, 
        user_message: str,
        should_stop: Optional[Callable[[], bool]] = None
    ) -> Generator[str, None, None]:
        """
        生成流式回答（通用方法）
        通义千问和 DeepSeek 都使用此方法，确保逻辑一致
        
        Args:
            conversation: ConversationChain 实例
            user_message: 用户消息内容
            should_stop: 中断检查函数，返回 True 时停止生成（可选）
        
        Yields:
            str: 流式输出的内容块
        """
        # 记录开始时间
        start_time = time.time()
        
        # 获取 LLM 实例（从 conversation 中）
        llm = conversation.llm
        
        try:
            # 方法1：使用 ConversationChain 的流式方法（推荐）
            if hasattr(conversation, 'predict_stream'):
                print("With predict_stream~~~")
                for chunk in conversation.predict_stream(input=user_message):
                    # 检查是否应该停止（在每个 chunk 前检查）
                    if should_stop and should_stop():
                        print("⏹️  流式输出已中断（用户取消）")
                        return
                    
                    # predict_stream 返回的可能是字符串或字典
                    if isinstance(chunk, str):
                        yield chunk
                    elif isinstance(chunk, dict):
                        content = chunk.get("response", chunk.get("answer", ""))
                        if content:
                            yield content
                    else:
                        yield str(chunk)
                # 计算并输出生成时长
                elapsed_time = time.time() - start_time
                print(f"\n⏱️  生成答案耗时: {elapsed_time:.2f} 秒")
                return
            
            # 方法2：直接使用 LLM 的 stream 方法（真正的流式输出）
            # 我们已经在 memory 里构造好了历史，这里直接复用，不再重新解析字符串
            print("With direct LLM stream ~~~")
            try:
                from langchain_core.messages import HumanMessage
            except ImportError:
                from langchain.schema import HumanMessage
            
            # 往下10行，表示构建完整的对话历史
            messages = []
            if hasattr(conversation, "memory") and hasattr(conversation.memory, "chat_memory"):
                chat_memory = conversation.memory.chat_memory
                # ConversationBufferMemory 内部已经维护了 BaseMessage 列表
                if hasattr(chat_memory, "messages") and chat_memory.messages:
                    messages.extend(chat_memory.messages)
            
            # 无论是否有历史，最后都追加当前这条用户消息
            messages.append(HumanMessage(content=user_message))
            
            # 使用 LLM 的 stream 方法进行真正的流式输出
            if hasattr(llm, 'stream'):
                for chunk in llm.stream(messages):
                    # 检查是否应该停止（在每个 chunk 前检查）
                    if should_stop and should_stop():
                        print("⏹️  流式输出已中断（用户取消）")
                        return
                    
                    # 处理 chunk（可能是不同类型的对象）
                    if hasattr(chunk, 'content'):
                        content = chunk.content
                        if content:
                            yield content
                    elif isinstance(chunk, str):
                        if chunk:
                            yield chunk
                    elif isinstance(chunk, dict):
                        content = chunk.get('content', chunk.get('text', ''))
                        if content:
                            yield content
                    else:
                        # 尝试获取 delta 内容
                        if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'content'):
                            content = chunk.delta.content
                            if content:
                                yield content
                        else:
                            # 最后尝试转换为字符串
                            chunk_str = str(chunk) if chunk else ''
                            if chunk_str:
                                yield chunk_str
                # 计算并输出生成时长
                elapsed_time = time.time() - start_time
                print(f"\n⏱️  生成答案耗时: {elapsed_time:.2f} 秒")
                return
            else:
                # 如果 LLM 不支持 stream，回退到逐字符输出
                response = conversation.predict(input=user_message)
                for char in response:
                    # 检查是否应该停止（在每个字符前检查）
                    if should_stop and should_stop():
                        print("⏹️  流式输出已中断（用户取消）")
                        return
                    yield char
                # 计算并输出生成时长
                elapsed_time = time.time() - start_time
                print(f"\n⏱️  生成答案耗时: {elapsed_time:.2f} 秒")
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
                    # 检查是否应该停止（在回退模式中也要检查）
                    if should_stop and should_stop():
                        print("⏹️  流式输出已中断（用户取消）")
                        return
                    yield char
                # 计算并输出生成时长
                elapsed_time = time.time() - start_time
                print(f"\n⏱️  生成答案耗时: {elapsed_time:.2f} 秒")
            except Exception as e2:
                # 如果连普通输出都失败，返回错误信息
                elapsed_time = time.time() - start_time
                yield f"\n\n[错误: {str(e2)}]"
                print(f"\n⏱️  生成答案耗时: {elapsed_time:.2f} 秒（失败）")
    
    def generate_response_for_user_message(
        self,
        conversation_id: int,
        user_message: str,
        user_message_id: Optional[int] = None,
        model_name: Optional[str] = None,
        stream: bool = False,
        exclude_last_user: bool = False,
        should_stop: Optional[Callable[[], bool]] = None
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
            stream=stream,
            should_stop=should_stop
        )
    
    
    
    def generate_and_save_assistant_response(
        self,
        conversation_id: int,
        user_message_id: int,
        user_message: Message,
        model_name: str,
        precomputed_order_index: Optional[int] = None,
        auto_title: bool = False,
        should_stop: Optional[Callable[[], bool]] = None
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
        generation_start_time = time.time()  # 记录生成开始时间
        message_saved = False  # 标记消息是否已保存，避免重复保存
        
        try:
            # 生成流式回答（Peer 架构）
            for chunk in self.generate_response_for_user_message(
                conversation_id=conversation_id,
                user_message=user_message.content,
                user_message_id=user_message_id,
                model_name=model_name,
                stream=True,
                should_stop=should_stop
            ):
                # 检查是否应该停止
                if should_stop and should_stop():
                    # 中断时也要保存已生成的内容
                    generation_time = time.time() - generation_start_time
                    saved_message = self._save_assistant_message(
                        conversation_id=conversation_id,
                        user_message=user_message,
                        assistant_content=assistant_content,
                        model_name=model_name,
                        precomputed_order_index=precomputed_order_index,
                        generation_time=generation_time,
                        auto_title=auto_title
                    )
                    message_saved = True  # 标记已保存
                    if saved_message:
                        yield {
                            'type': 'interrupted',
                            'message': '用户中断生成',
                            'message_id': saved_message.id,
                            'user_message_id': user_message_id
                        }
                    else:
                        yield {
                            'type': 'interrupted', 
                            'message': '用户中断生成',
                            'message_id': None,
                            'user_message_id': user_message_id
                        }
                    return
                
                assistant_content += chunk
                # 发送数据块
                yield {'type': 'chunk', 'chunk': chunk}
            
            # 计算生成时长
            generation_time = time.time() - generation_start_time
            
            # 流式输出完成，保存AI回答到数据库
            saved_message = self._save_assistant_message(
                conversation_id=conversation_id,
                user_message=user_message,
                assistant_content=assistant_content,
                model_name=model_name,
                precomputed_order_index=precomputed_order_index,
                generation_time=generation_time,
                auto_title=auto_title
            )
            message_saved = True  # 标记已保存
            
            # 发送完成信号
            yield {
                'type': 'done',
                'message_id': saved_message.id,
                'user_message_id': user_message_id
            }
            
        except GeneratorExit:
            # 生成器被关闭（客户端断开连接），也要保存已生成的内容
            # 但如果已经在 should_stop 检查时保存过了，就不再重复保存
            # 注意：GeneratorExit 时无法 yield，因为生成器已经关闭
            if not message_saved:
                generation_time = time.time() - generation_start_time
                try:
                    saved_message = self._save_assistant_message(
                        conversation_id=conversation_id,
                        user_message=user_message,
                        assistant_content=assistant_content,
                        model_name=model_name,
                        precomputed_order_index=precomputed_order_index,
                        generation_time=generation_time,
                        auto_title=auto_title
                    )
                    if saved_message:
                        yield {
                            'type': 'interrupted',
                            'message': '用户中断生成',
                            'message_id': saved_message.id,
                            'user_message_id': user_message_id
                        }
                    else:
                        yield {
                            'type': 'interrupted', 
                            'message': '用户中断生成',
                            'message_id': None,
                            'user_message_id': user_message_id
                        }
                except Exception:
                    # 保存失败不影响 GeneratorExit 的传播
                    pass
            # 重新抛出 GeneratorExit，让 Python 正常处理生成器关闭
            raise
        except Exception as e:
            # AI API 调用失败，记录详细错误并返回
            import traceback
            error_detail = traceback.format_exc()
            print(f"AI API调用失败: {str(e)}")
            print(f"详细错误: {error_detail}")
            # 发送错误信息
            yield {'type': 'error', 'error': str(e)}
    
    def _save_assistant_message(
        self,
        conversation_id: int,
        user_message: Message,
        assistant_content: str,
        model_name: str,
        precomputed_order_index: Optional[int],
        generation_time: float,
        auto_title: bool
    ) -> Optional[Message]:
        """
        保存助手消息到数据库（内部辅助方法）
        
        Args:
            conversation_id: 会话ID
            user_message: 用户消息对象
            assistant_content: 助手消息内容（可能是不完整的）
            model_name: 模型名称
            precomputed_order_index: 预先计算的 order_index
            generation_time: 生成耗时
            auto_title: 是否自动生成会话标题
        
        Returns:
            Message: 保存后的助手消息对象，如果保存失败返回 None
        """
        # 如果没有内容，不保存
        if not assistant_content:
            return None
        
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
            model=model_name,
            generation_time=generation_time
        )
        
        # 保存助手消息和更新会话
        try:
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
            
            return saved_message
        except Exception as e:
            # 保存失败，记录错误但不抛出异常
            import traceback
            error_detail = traceback.format_exc()
            print(f"保存助手消息失败: {str(e)}")
            print(f"详细错误: {error_detail}")
            return None
    
