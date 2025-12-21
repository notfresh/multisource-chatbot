# -*- coding:utf-8 -*-
"""
核心 LLM 配置模块
纯 Python 实现，仅支持 302.ai 和兼容的 OpenAI 框架

设计理念：
- 核心层只保留必要的 LLM 提供商
- 使用 LangChain 作为统一的 LLM 接口
- 不依赖 Web 框架
"""
import os
from typing import Optional


def get_llm(provider: str = '302ai', model_name: Optional[str] = None):
    """
    获取配置好的 LLM 实例
    
    Args:
        provider: LLM提供商，可选值：
            - '302ai': 302.ai 服务（兼容 OpenAI 格式）
            - 'openai': OpenAI GPT 模型
        model_name: 模型名称
            - OpenAI: 'gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo-preview' 等
            - 302.ai: 'deepseek-chat', 'qwen-max' 等
    
    Returns:
        LangChain LLM 实例（ChatOpenAI）
    
    Raises:
        ValueError: 当 API Key 未设置时
        ImportError: 当 langchain-openai 未安装时
    """
    if provider == '302ai':
        try:
            import os
            from langchain_openai import ChatOpenAI
            api_key = os.environ['API_302_AI_KEY']
            if not api_key:
                raise ValueError("API_302_AI_KEY 环境变量未设置")
            
            # 使用 base_url 指定 302.ai 的 API 端点
            return ChatOpenAI(
                model_name=model_name or 'deepseek-chat',
                temperature=0.7,
                openai_api_key=api_key,
                base_url="https://api.302.ai/v1"  # 关键：指定 302.ai 的 API 端点
            )
        except ImportError:
            raise ImportError("请安装 langchain-openai: pip install langchain-openai")
    
    elif provider == 'openai':
        try:
            from langchain_openai import ChatOpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY 环境变量未设置")
            
            return ChatOpenAI(
                model_name=model_name or 'gpt-3.5-turbo',
                temperature=0.7,
                openai_api_key=api_key
            )
        except ImportError:
            raise ImportError("请安装 langchain-openai: pip install langchain-openai")
    
    else:
        raise ValueError(f"不支持的 provider: {provider}。仅支持 '302ai' 或 'openai'")


def get_default_llm():
    """
    获取默认的 LLM 实例
    
    优先级：
    1. 如果设置了 API_302_AI_KEY，使用 302.ai
    2. 如果设置了 OPENAI_API_KEY，使用 OpenAI
    3. 否则抛出异常
    
    Returns:
        LangChain LLM 实例
    
    Raises:
        ValueError: 当没有配置任何 API Key 时
    """
    
    return get_llm('302ai')
    
