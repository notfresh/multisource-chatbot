# -*- coding:utf-8 -*-
"""
会话管理 API 路由
"""
from flask import request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app.core.coremodels import Conversation, Message
from .blueprint import api

@api.route('/conversations', methods=['GET'])
@login_required
def get_conversations():
    """获取会话列表"""
    try:
        if not current_user or not current_user.is_authenticated:
            return jsonify({'error': '未登录'}), 401
        
        # 使用 core 层的 Conversation.list() 方法获取会话列表
        conversations = Conversation.list(user_id=current_user.id)
        
        result = []
        for conv in conversations:
            # 使用 Message.list() 方法获取该会话的消息数量
            messages = Message.list(conversation_id=conv.id)
            message_count = len(messages)
            
            result.append({
                'id': conv.id,
                'title': conv.title,
                'updated_at': conv.updated_at.isoformat() if conv.updated_at else None,
                'created_at': conv.created_at.isoformat() if conv.created_at else None,
                'message_count': message_count
            })
        
        return jsonify(result)
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"获取会话列表失败: {str(e)}")
        print(f"详细错误: {error_detail}")
        return jsonify({'error': f'获取会话列表失败: {str(e)}'}), 500

@api.route('/conversations/<int:conversation_id>', methods=['GET'])
@login_required
def get_conversation(conversation_id):
    """获取单个会话详情（包含所有消息）"""
    try:
        # 使用 core 层的 Conversation.get_by_id() 方法获取会话
        conversation = Conversation.get_by_id(conversation_id)
        if not conversation:
            return jsonify({'error': '会话不存在'}), 404
        
        # 权限检查：只能访问自己的会话
        if conversation.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # 使用 Message.list() 方法获取所有消息（按顺序）
        messages = Message.list(conversation_id=conversation_id, order_by="order_index")
        
        return jsonify({
            'id': conversation.id,
            'title': conversation.title,
            'created_at': conversation.created_at.isoformat() if conversation.created_at else None,
            'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else None,
            'messages': [
                {
                    'id': msg.id,
                    'role': msg.role,
                    'content': msg.content,
                    'created_at': msg.created_at.isoformat() if msg.created_at else None,
                    'model': msg.model,
                    'order_index': msg.order_index,
                    'generation_time': msg.generation_time
                }
                for msg in messages
            ]
        })
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"获取会话详情失败: {str(e)}")
        print(f"详细错误: {error_detail}")
        return jsonify({'error': f'获取会话详情失败: {str(e)}'}), 500



@api.route('/conversations', methods=['POST'])
@login_required
def create_conversation():
    """创建新会话"""
    try:
        if not current_user or not current_user.is_authenticated:
            return jsonify({'error': '未登录'}), 401
        
        data = request.get_json() or {}
        title = data.get('title', '新对话')
        
        # 如果标题为空，使用默认标题
        if not title or title.strip() == '':
            title = '新对话'
        
        # 使用 core 层的 Conversation.create() 方法创建会话
        conversation = Conversation.create(title=title, user_id=current_user.id)
        
        return jsonify({
            'id': conversation.id,
            'title': conversation.title,
            'created_at': conversation.created_at.isoformat() if conversation.created_at else None,
            'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else None
        }), 201
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"创建会话失败: {str(e)}")
        print(f"详细错误: {error_detail}")
        return jsonify({'error': f'创建会话失败: {str(e)}'}), 500


@api.route('/conversations/<int:conversation_id>', methods=['PUT'])
@login_required
def update_conversation(conversation_id):
    """更新会话标题"""
    try:
        if not current_user or not current_user.is_authenticated:
            return jsonify({'error': '未登录'}), 401
        
        # 使用 core 层的 Conversation.get_by_id() 方法获取会话
        conversation = Conversation.get_by_id(conversation_id)
        if not conversation:
            return jsonify({'error': '会话不存在'}), 404
        
        # 权限检查
        if conversation.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        if not data or 'title' not in data:
            return jsonify({'error': 'Title is required'}), 400
        
        # 使用 core 层的 update_title() 方法更新标题
        conversation.update_title(data['title'])
        # 保存到数据库
        conversation.save()
        
        return jsonify({
            'id': conversation.id,
            'title': conversation.title,
            'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else None
        })
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"更新会话失败: {str(e)}")
        print(f"详细错误: {error_detail}")
        return jsonify({'error': f'更新会话失败: {str(e)}'}), 500


@api.route('/conversations/<int:conversation_id>', methods=['DELETE'])
@login_required
def delete_conversation(conversation_id):
    """删除会话"""
    try:
        if not current_user or not current_user.is_authenticated:
            return jsonify({'error': '未登录'}), 401
        
        # 使用 core 层的 Conversation.get_by_id() 方法获取会话
        conversation = Conversation.get_by_id(conversation_id)
        if not conversation:
            return jsonify({'error': '会话不存在'}), 404
        
        # 权限检查
        if conversation.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # 使用 core 层的 delete() 方法删除会话
        success = conversation.delete()
        if not success:
            return jsonify({'error': '删除失败'}), 500
        
        return jsonify({'success': True})
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"删除会话失败: {str(e)}")
        print(f"详细错误: {error_detail}")
        return jsonify({'error': f'删除会话失败: {str(e)}'}), 500

