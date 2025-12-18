# -*- coding:utf-8 -*-
"""
测试聊天 API
"""
import requests
import json
import sys

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# 测试用的会话ID（需要先创建一个会话）
def test_send_message():
    """测试发送消息"""
    # 首先需要登录获取 session
    print("=" * 50)
    print("测试发送消息 API")
    print("=" * 50)
    
    # 创建会话
    print("\n1. 创建新会话...")
    session = requests.Session()
    
    # 这里需要先登录，但为了测试，我们假设已经登录
    # 实际使用时，需要先调用登录接口获取 session
    
    # 创建会话
    create_response = session.post(
        f"{API_BASE}/conversations",
        json={"title": "测试会话"},
        headers={"Content-Type": "application/json"}
    )
    
    if create_response.status_code != 201:
        print(f"创建会话失败: {create_response.status_code}")
        print(f"响应: {create_response.text}")
        return
    
    conversation = create_response.json()
    conversation_id = conversation['id']
    print(f"会话创建成功，ID: {conversation_id}")
    
    # 发送消息
    print(f"\n2. 发送消息到会话 {conversation_id}...")
    send_response = session.post(
        f"{API_BASE}/conversations/{conversation_id}/messages",
        json={"content": "你好，这是一条测试消息"},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"状态码: {send_response.status_code}")
    print(f"响应头: {dict(send_response.headers)}")
    
    if send_response.status_code == 200:
        result = send_response.json()
        print(f"发送成功!")
        print(f"用户消息: {result.get('user_message', {}).get('content', 'N/A')}")
        print(f"AI回答: {result.get('assistant_message', {}).get('content', 'N/A')}")
    else:
        print(f"发送失败!")
        print(f"响应内容: {send_response.text[:500]}")  # 只显示前500个字符
        
        # 尝试解析 JSON 错误
        try:
            error_data = send_response.json()
            print(f"错误信息: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
        except:
            print("无法解析为 JSON，可能是 HTML 错误页面")

if __name__ == "__main__":
    try:
        test_send_message()
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

