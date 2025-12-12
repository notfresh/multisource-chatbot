# -*- coding:utf-8 -*-
"""
LLM 配置模块
支持多种 LLM 提供商：OpenAI、Anthropic、本地模型等
"""
import os
from typing import Optional


def get_llm(provider: str = 'mock', model_name: Optional[str] = None):
    """
    获取配置好的 LLM 实例
    
    Args:
        provider: LLM提供商，可选值：
            - 'openai': OpenAI GPT 模型
            - 'anthropic': Anthropic Claude 模型
            - '302ai': 302.ai 服务（兼容 OpenAI 格式）
            - 'mock': 模拟 LLM（用于开发测试）
        model_name: 模型名称
            - OpenAI: 'gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo-preview' 等
            - Anthropic: 'claude-3-opus-20240229', 'claude-3-sonnet-20240229' 等
            - 302.ai: 'deepseek-chat'
    
    Returns:
        LangChain LLM 实例
    """
    if provider == '302ai':
        try:
            from langchain_openai import ChatOpenAI
            api_key = os.getenv('API_302_AI_KEY')
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
    
    elif provider == 'anthropic':
        try:
            from langchain_anthropic import ChatAnthropic
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY 环境变量未设置")
            
            return ChatAnthropic(
                model=model_name or 'claude-3-sonnet-20240229',
                temperature=0.7,
                anthropic_api_key=api_key
            )
        except ImportError:
            raise ImportError("请安装 langchain-anthropic: pip install langchain-anthropic")
    
    else:
        # 使用模拟 LLM（开发测试用）
        try:
            from langchain.llms.fake import FakeListLLM
            responses = [
                "这是一个很好的问题。让我来帮你分析一下...\n\n根据你提供的信息，我认为可以从以下几个角度来考虑：\n1. 首先...\n2. 其次...\n3. 最后...",
                "根据你的问题，我认为...\n\n让我详细解释一下：",
                "关于这个问题，我有以下建议：\n\n1. 建议一\n2. 建议二\n3. 建议三",
                "我理解你的问题。让我来帮你解答：\n\n这个问题涉及到多个方面，我们需要综合考虑。",
                "好的，让我来分析一下这个问题。\n\n从我的角度来看，主要有以下几个要点需要注意。"
            ]
            return FakeListLLM(responses=responses)
        except ImportError:
            # 如果 FakeListLLM 不可用，创建一个简单的模拟类
            class MockLLM:
                def predict(self, input_text):
                    return f"这是模拟回答。你刚才问的是：{input_text}\n\n（这是开发阶段的模拟回答，请配置真实的 LLM API）"
                
                def predict_stream(self, input_text):
                    response = f"这是模拟回答。你刚才问的是：{input_text}\n\n（这是开发阶段的模拟回答，请配置真实的 LLM API）"
                    for word in response.split():
                        yield word + " "
            
            return MockLLM()


def get_default_llm():
    """
    获取默认的 LLM 实例
    
    优先级：
    1. 如果设置了 API_302_AI_KEY，使用 302.ai
    2. 如果设置了 OPENAI_API_KEY，使用 OpenAI
    3. 如果设置了 ANTHROPIC_API_KEY，使用 Anthropic
    4. 否则使用模拟 LLM
    """
    if os.getenv('API_302_AI_KEY'):
        return get_llm('302ai')
    elif os.getenv('OPENAI_API_KEY'):
        return get_llm('openai')
    elif os.getenv('ANTHROPIC_API_KEY'):
        return get_llm('anthropic')
    else:
        return get_llm('mock')

