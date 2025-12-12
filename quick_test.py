# -*- coding:utf-8 -*-
"""
快速测试 API - 非交互式
需要先确保有用户账号
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def quick_test():
    """快速测试"""
    print("=" * 60)
    print("快速 API 测试")
    print("=" * 60)
    
    # 检查服务器是否运行
    try:
        response = requests.get(BASE_URL, timeout=2)
        print("[OK] 服务器运行正常")
    except:
        print("[ERROR] 服务器未运行，请先运行: python run_server.py")
        return
    
    print("\n提示: 要测试 API，需要:")
    print("1. 确保有用户账号（如果没有，访问 http://localhost:8000/auth/register 注册）")
    print("2. 使用以下命令测试:")
    print("\n   python test_api_requests.py <username> <password>")
    print("\n或者使用 curl:")
    print("\n   # 登录")
    print("   curl -X POST http://localhost:8000/auth/login \\")
    print("     -H 'Content-Type: application/x-www-form-urlencoded' \\")
    print("     -d 'username=YOUR_USERNAME&password=YOUR_PASSWORD' \\")
    print("     -c cookies.txt -v")
    print("\n   # 创建会话")
    print("   curl -X POST http://localhost:8000/api/conversations \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -b cookies.txt \\")
    print("     -d '{\"title\":\"测试对话\"}'")
    print("\n   # 发送消息（假设会话ID为1）")
    print("   curl -X POST http://localhost:8000/api/conversations/1/messages \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -b cookies.txt \\")
    print("     -d '{\"content\":\"你好\"}'")
    
    print("\n" + "=" * 60)
    print("API 端点列表:")
    print("=" * 60)
    print("GET  /api/conversations              - 获取会话列表")
    print("POST /api/conversations              - 创建新会话")
    print("GET  /api/conversations/<id>         - 获取会话详情")
    print("PUT  /api/conversations/<id>         - 更新会话标题")
    print("DELETE /api/conversations/<id>       - 删除会话")
    print("POST /api/conversations/<id>/messages - 发送消息")
    print("=" * 60)

if __name__ == '__main__':
    quick_test()

