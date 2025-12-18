# -*- coding:utf-8 -*-
"""
测试后端 API - 实际请求测试
需要先确保有用户账号，或者先注册一个
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

class APITester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.conversation_id = None
    
    def login(self, username, password):
        """登录"""
        print(f"\n[1] 登录: {username}")
        url = f"{self.base_url}/auth/login"
        data = {
            'username': username,
            'password': password
        }
        response = self.session.post(url, data=data, allow_redirects=False)
        
        if response.status_code in [200, 302]:
            print("✅ 登录成功")
            return True
        else:
            print(f"❌ 登录失败: {response.status_code}")
            print(f"响应: {response.text[:200]}")
            return False
    
    def create_conversation(self, title="测试对话"):
        """创建会话"""
        print(f"\n[2] 创建会话: {title}")
        url = f"{self.base_url}/api/conversations"
        data = {'title': title}
        response = self.session.post(url, json=data)
        
        if response.status_code == 201:
            result = response.json()
            self.conversation_id = result['id']
            print(f"✅ 会话创建成功: ID={self.conversation_id}")
            print(f"   标题: {result['title']}")
            return result
        else:
            print(f"❌ 创建会话失败: {response.status_code}")
            print(f"响应: {response.text[:200]}")
            return None
    
    def get_conversations(self):
        """获取会话列表"""
        print(f"\n[3] 获取会话列表")
        url = f"{self.base_url}/api/conversations"
        response = self.session.get(url)
        
        if response.status_code == 200:
            conversations = response.json()
            print(f"✅ 获取成功: 共 {len(conversations)} 个会话")
            for conv in conversations[:3]:  # 只显示前3个
                print(f"   - [{conv['id']}] {conv['title']} (消息数: {conv['message_count']})")
            return conversations
        else:
            print(f"❌ 获取失败: {response.status_code}")
            print(f"响应: {response.text[:200]}")
            return None
    
    def send_message(self, content):
        """发送消息"""
        if not self.conversation_id:
            print("❌ 请先创建会话")
            return None
        
        print(f"\n[4] 发送消息: {content[:30]}...")
        url = f"{self.base_url}/api/conversations/{self.conversation_id}/messages"
        data = {'content': content}
        response = self.session.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 消息发送成功")
            print(f"   用户消息: {result['user_message']['content'][:50]}...")
            print(f"   AI回答: {result['assistant_message']['content'][:100]}...")
            return result
        else:
            print(f"❌ 发送消息失败: {response.status_code}")
            print(f"响应: {response.text[:500]}")
            return None
    
    def get_conversation_detail(self):
        """获取会话详情"""
        if not self.conversation_id:
            print("❌ 请先创建会话")
            return None
        
        print(f"\n[5] 获取会话详情 (ID: {self.conversation_id})")
        url = f"{self.base_url}/api/conversations/{self.conversation_id}"
        response = self.session.get(url)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 获取成功")
            print(f"   标题: {result['title']}")
            print(f"   消息数: {len(result['messages'])}")
            for msg in result['messages'][-2:]:  # 显示最后2条
                role = "用户" if msg['role'] == 'user' else "AI"
                print(f"   [{role}]: {msg['content'][:60]}...")
            return result
        else:
            print(f"❌ 获取失败: {response.status_code}")
            print(f"响应: {response.text[:200]}")
            return None

def main():
    print("=" * 60)
    print("API 测试工具")
    print("=" * 60)
    print("\n注意: 需要先有用户账号")
    print("如果没有账号，请先访问 http://localhost:8000/auth/register 注册")
    print("\n" + "=" * 60)
    
    # 从命令行参数获取用户名和密码，或使用默认值
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]
    else:
        username = input("\n请输入用户名: ").strip()
        password = input("请输入密码: ").strip()
    
    if not username or not password:
        print("❌ 用户名和密码不能为空")
        return
    
    tester = APITester()
    
    # 1. 登录
    if not tester.login(username, password):
        print("\n❌ 登录失败，请检查用户名和密码")
        return
    
    # 2. 创建会话
    tester.create_conversation("API测试对话")
    
    # 3. 获取会话列表
    tester.get_conversations()
    
    # 4. 发送消息
    tester.send_message("你好，请简单介绍一下你自己")
    
    # 5. 获取会话详情
    tester.get_conversation_detail()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == '__main__':
    main()

