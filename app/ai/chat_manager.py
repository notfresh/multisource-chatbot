# -*- coding:utf-8 -*-
"""
聊天管理器 - 使用 LangChain 管理对话和生成AI回答（v0 简化版）
"""
from typing import Optional, Generator, Union
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from app.models import Message
from app.ai.llm_config import get_default_llm


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
        # 获取所有消息（按顺序）
        messages = Message.query.filter_by(
            conversation_id=conversation_id
        ).order_by(Message.order_index.asc()).all()
        
        # 创建内存对象
        # 注意：ConversationChain 默认使用 'history' 作为 memory_key
        # return_messages=False 表示返回字符串格式的历史记录，而不是消息对象列表
        memory = ConversationBufferMemory(
            return_messages=False,  # 返回字符串格式，以匹配 ConversationChain 的默认 prompt
            memory_key="history"  # 使用 'history' 以匹配 ConversationChain 的默认 prompt
        )
        
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
        
        return memory
    
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
            stream: 是否流式返回（v0 暂不支持）
        
        Returns:
            str: AI回答内容（stream=False 时）
            Generator: 生成器对象（stream=True 时）
        """
        # 构建对话历史（排除最后一条用户消息，因为 predict 方法会自动添加）
        memory = self.build_memory_from_conversation(conversation_id, exclude_last_user=True)
        
        # 创建对话链
        conversation = ConversationChain(
            llm=self.llm,
            memory=memory,
            verbose=True
        )
        
        # 生成回答
        if stream:
            # 流式输出（v0 暂不支持，后续版本实现）
            return self._generate_stream(conversation, user_message)
        else:
            # 普通输出
            return self._generate_normal(conversation, user_message)
    
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
    
    def _generate_stream(self, conversation, user_message: str) -> Generator:
        """生成流式回答"""
        try:
            # 尝试使用 LLM 的流式方法（ChatOpenAI 等支持流式）
            if hasattr(self.llm, 'stream'):
                # 直接使用 LLM 的 stream 方法
                # 需要构建完整的消息列表
                messages = []
                # 添加历史消息
                if hasattr(conversation.memory, 'chat_memory') and hasattr(conversation.memory.chat_memory, 'messages'):
                    for msg in conversation.memory.chat_memory.messages:
                        messages.append(msg)
                # 添加当前用户消息
                try:
                    from langchain_core.messages import HumanMessage
                except ImportError:
                    from langchain.schema import HumanMessage
                messages.append(HumanMessage(content=user_message))
                
                # 流式调用 LLM
                for chunk in self.llm.stream(messages):
                    if hasattr(chunk, 'content'):
                        content = chunk.content
                    else:
                        content = str(chunk)
                    if content:
                        yield content
            elif hasattr(conversation, 'predict_stream'):
                # 使用 ConversationChain 的流式方法
                yield from conversation.predict_stream(input=user_message)
            else:
                # 如果不支持流式，模拟流式输出（逐字符）
                response = conversation.predict(input=user_message)
                # 逐字符输出，模拟流式效果
                for char in response:
                    yield char
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

