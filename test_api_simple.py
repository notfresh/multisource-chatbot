# -*- coding:utf-8 -*-
"""
简单的 API 测试脚本
使用示例: python test_api_simple.py testuser testpass
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def main():
    if len(sys.argv) < 3:
        print("使用方法: python test_api_simple.py <username> <password>")
        print("示例: python test_api_simple.py testuser testpass")
        return
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    session = requests.Session()
    
    # 1. 登录
    print("\n[1] 登录...")
    login_url = f"{BASE_URL}/auth/login"
    login_data = {'username': username, 'password': password}
    resp = session.post(login_url, data=login_data, allow_redirects=False)
    
    if resp.status_code not in [200, 302]:
        print(f"登录失败: {resp.status_code}")
        print(f"响应: {resp.text[:200]}")
        return
    
    print("登录成功!")
    
    # 2. 创建会话
    print("\n[2] 创建会话...")
    conv_url = f"{BASE_URL}/api/conversations"
    conv_data = {'title': 'API测试对话'}
    resp = session.post(conv_url, json=conv_data)
    
    if resp.status_code != 201:
        print(f"创建会话失败: {resp.status_code}")
        print(f"响应: {resp.text[:200]}")
        return
    
    conv = resp.json()
    conv_id = conv['id']
    print(f"会话创建成功! ID: {conv_id}")
    
    # 3. 发送消息
    print("\n[3] 发送消息...")
    msg_url = f"{BASE_URL}/api/conversations/{conv_id}/messages"
    msg_data = {'content': '你好，请简单介绍一下你自己'}
    resp = session.post(msg_url, json=msg_data)
    
    if resp.status_code != 200:
        print(f"发送消息失败: {resp.status_code}")
        print(f"响应: {resp.text[:500]}")
        return
    
    result = resp.json()
    print("消息发送成功!")
    print(f"\n用户: {result['user_message']['content']}")
    print(f"\nAI: {result['assistant_message']['content'][:200]}...")
    
    # 4. 获取会话详情
    print("\n[4] 获取会话详情...")
    detail_url = f"{BASE_URL}/api/conversations/{conv_id}"
    resp = session.get(detail_url)
    
    if resp.status_code == 200:
        detail = resp.json()
        print(f"会话标题: {detail['title']}")
        print(f"消息数量: {len(detail['messages'])}")
    
    print("\n测试完成!")

if __name__ == '__main__':
    main()

