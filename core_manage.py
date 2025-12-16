# -*- coding:utf-8 -*-
"""
核心层管理工具（Core Layer Management Tool）
不依赖 Flask，直接使用核心层的类进行交互和测试

使用方法：
    python core_manage.py shell           # 打开交互式 Python shell
    python core_manage.py test            # 运行测试示例
    python core_manage.py create-demo     # 创建演示数据
"""

import os
import sys
import code
from datetime import datetime
from typing import Optional

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 导入核心层的类
from app.core.coremodels import (
    Conversation,
    Message,
    MessageRole
)
from app.core.db import (
    ConversationOp,
    MessageModel,
    ConversationModel,
    get_conversation_by_id,
    get_conversations_by_user_id,
    create_conversation,
    update_conversation,
    delete_conversation
)
from app.core.llm_config import (
    get_llm,
    get_default_llm
)


def make_shell_context():
    """
    为交互式 shell 提供上下文
    返回一个字典，包含所有关键类和函数
    """
    return {
        # 领域模型
        'Conversation': Conversation,
        'Message': Message,
        'MessageRole': MessageRole,
        
        # 数据库操作
        'ConversationOp': ConversationOp,
        'ConversationModel': ConversationModel,
        'MessageModel': MessageModel,
        
        # 便捷函数
        'get_conversation_by_id': get_conversation_by_id,
        'get_conversations_by_user_id': get_conversations_by_user_id,
        'create_conversation': create_conversation,
        'update_conversation': update_conversation,
        'delete_conversation': delete_conversation,
        
        # LLM 配置
        'get_llm': get_llm,
        'get_default_llm': get_default_llm,
        
        # 标准库
        'datetime': datetime,
        'os': os,
    }


def shell():
    """启动交互式 Python shell"""
    print("=" * 60)
    print("核心层交互式 Shell")
    print("=" * 60)
    print("\n已注入的关键类：")
    print("  - Conversation, Message, MessageRole (领域模型)")
    print("  - ConversationOp (数据库操作)")
    print("  - get_conversation_by_id, create_conversation 等 (便捷函数)")
    print("  - get_llm, get_default_llm (LLM 配置)")
    print("\n示例用法：")
    print("  # 列出所有对话（推荐方式）")
    print("  conversations = Conversation.list()")
    print("  for c in conversations:")
    print("      print(f'ID: {c.id}, 标题: {c.title}')")
    print("\n  # 列出特定用户的对话")
    print("  conversations = Conversation.list(user_id=1)")
    print("  print(f'用户1有 {len(conversations)} 个对话')")
    print("\n  # 创建会话")
    print("  conv = Conversation.create(title='测试对话', user_id=1)")
    print("  print(f'创建的会话ID: {conv.id}')")
    print("\n  # 查询会话")
    print("  conv = Conversation.get_by_id(1)")
    print("  if conv:")
    print("      print(conv.title)")
    print("\n  # 保存会话（创建或更新）")
    print("  conv = Conversation(title='新对话', user_id=1)")
    print("  saved = conv.save()  # 创建")
    print("  saved.title = '更新后的标题'")
    print("  saved.save()  # 更新")
    print("\n  # 删除会话")
    print("  conv = Conversation.get_by_id(1)")
    print("  if conv:")
    print("      conv.delete()")
    print("\n  # 使用 ConversationOp（高级用法）")
    print("  with ConversationOp() as op:")
    print("      conversations = op.list()")
    print("      conv = op.get_by_id(1)")
    print("\n" + "=" * 60)
    print("输入 exit() 或 Ctrl+D 退出")
    print("=" * 60 + "\n")
    
    # 创建 shell 上下文
    context = make_shell_context()
    
    # 启动交互式 shell
    code.interact(
        local=context,
        banner='',
        exitmsg='再见！'
    )


def test_example():
    """运行测试示例"""
    print("=" * 60)
    print("核心层测试示例")
    print("=" * 60)
    
    try:
        # 示例1：创建会话
        print("\n[示例1] 创建会话")
        conv = Conversation(title="测试对话", user_id=1)
        print(f"创建会话对象: {conv}")
        
        created = create_conversation(conv)
        print(f"已保存到数据库: {created}")
        
        # 示例2：查询会话
        print("\n[示例2] 查询会话")
        found = get_conversation_by_id(created.id)
        if found:
            print(f"查询结果: {found}")
            print(f"消息数量: {found.get_message_count()}")
        else:
            print("未找到会话")
        
        # 示例3：使用 ConversationOp
        print("\n[示例3] 使用 ConversationOp")
        with ConversationOp() as op:
            convs = op.get_by_user_id(user_id=1)
            print(f"用户1的所有会话: {len(convs)} 个")
            for c in convs[:3]:  # 只显示前3个
                print(f"  - {c}")
        
        # 示例4：创建消息
        print("\n[示例4] 创建消息")
        if found:
            msg = Message(
                conversation_id=found.id,
                role=MessageRole.USER.value,
                content="这是一条测试消息",
                order_index=0
            )
            found.add_message(msg)
            print(f"添加消息: {msg}")
            print(f"会话消息数量: {found.get_message_count()}")
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

def create_demo():
    """创建演示数据"""
    print("=" * 60)
    print("创建演示数据")
    print("=" * 60)
    
    try:
        # 创建几个演示会话
        demo_conversations = [
            Conversation(title="Python 学习", user_id=1),
            Conversation(title="算法讨论", user_id=1),
            Conversation(title="项目规划", user_id=1),
        ]
        
        created_convs = []
        for conv in demo_conversations:
            created = create_conversation(conv)
            created_convs.append(created)
            print(f"✓ 创建会话: {created.title} (ID: {created.id})")
        
        # 为第一个会话添加一些消息
        if created_convs:
            first_conv = created_convs[0]
            messages = [
                Message(
                    conversation_id=first_conv.id,
                    role=MessageRole.USER.value,
                    content="什么是 Python？",
                    order_index=0
                ),
                Message(
                    conversation_id=first_conv.id,
                    role=MessageRole.ASSISTANT.value,
                    content="Python 是一种高级编程语言...",
                    order_index=1,
                    model="deepseek-chat"
                ),
            ]
            
            # 注意：这里只是演示，实际需要保存到数据库
            for msg in messages:
                first_conv.add_message(msg)
            
            print(f"\n✓ 为会话 '{first_conv.title}' 添加了 {len(messages)} 条消息")
        
        print("\n" + "=" * 60)
        print("演示数据创建完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='核心层管理工具')
    parser.add_argument(
        'command',
        nargs='?',
        default='shell',
        choices=['shell', 'test', 'create-demo'],
        help='要执行的命令 (默认: shell)'
    )
    parser.add_argument(
        '--user-id',
        type=int,
        help='用户ID（用于 list 命令，筛选特定用户的对话）'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='限制返回数量（用于 list 命令）'
    )
    
    args = parser.parse_args()
    
    if args.command == 'shell':
        shell()
    elif args.command == 'test':
        test_example()
    elif args.command == 'create-demo':
        create_demo()


if __name__ == '__main__':
    main()

