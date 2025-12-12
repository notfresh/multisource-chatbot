# -*- coding:utf-8 -*-
"""测试后端 API"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_api():
    """测试 API 端点"""
    
    # 注意：这些测试需要先登录获取 session
    # 这里只是展示 API 的使用方式
    
    print("=" * 50)
    print("API 测试指南")
    print("=" * 50)
    print("\n1. 首先需要登录获取 session cookie")
    print("   POST /auth/login")
    print("   Body: { 'username': 'your_username', 'password': 'your_password' }")
    
    print("\n2. 创建新会话")
    print("   POST /api/conversations")
    print("   Body: { 'title': '新对话' }")
    print("   Response: { 'id': 1, 'title': '新对话', ... }")
    
    print("\n3. 获取会话列表")
    print("   GET /api/conversations")
    print("   Response: [{ 'id': 1, 'title': '...', ... }, ...]")
    
    print("\n4. 发送消息（获取AI回答）")
    print("   POST /api/conversations/<conversation_id>/messages")
    print("   Body: { 'content': '你好' }")
    print("   Response: { 'user_message': {...}, 'assistant_message': {...} }")
    
    print("\n5. 获取会话详情（包含所有消息）")
    print("   GET /api/conversations/<conversation_id>")
    print("   Response: { 'id': 1, 'title': '...', 'messages': [...] }")
    
    print("\n6. 更新会话标题")
    print("   PUT /api/conversations/<conversation_id>")
    print("   Body: { 'title': '新标题' }")
    
    print("\n7. 删除会话")
    print("   DELETE /api/conversations/<conversation_id>")
    
    print("\n" + "=" * 50)
    print("使用 curl 测试示例：")
    print("=" * 50)
    print("\n# 1. 登录（需要替换用户名和密码）")
    print("curl -X POST http://localhost:8000/auth/login \\")
    print("  -H 'Content-Type: application/x-www-form-urlencoded' \\")
    print("  -d 'username=your_username&password=your_password' \\")
    print("  -c cookies.txt")
    
    print("\n# 2. 创建会话")
    print("curl -X POST http://localhost:8000/api/conversations \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -b cookies.txt \\")
    print("  -d '{\"title\":\"测试对话\"}'")
    
    print("\n# 3. 发送消息（假设会话ID为1）")
    print("curl -X POST http://localhost:8000/api/conversations/1/messages \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -b cookies.txt \\")
    print("  -d '{\"content\":\"你好，请介绍一下你自己\"}'")
    
    print("\n" + "=" * 50)

if __name__ == '__main__':
    test_api()

