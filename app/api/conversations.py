# -*- coding:utf-8 -*-
"""
会话管理 API 路由
"""
from flask import request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app.models import Conversation, Message, db
from .blueprint import api

@api.route('/conversations', methods=['GET'])
@login_required
def get_conversations():
    """获取会话列表"""
    try:
        if not current_user or not current_user.is_authenticated:
            return jsonify({'error': '未登录'}), 401
        
        conversations = Conversation.query.filter_by(
            user_id=current_user.id
        ).order_by(Conversation.updated_at.desc()).all()
        
        result = []
        for conv in conversations:
            # 统计消息数量
            message_count = Message.query.filter_by(conversation_id=conv.id).count()
            
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
    conversation = Conversation.query.get(conversation_id)
    if not conversation:
        return jsonify({'error': '会话不存在'}), 404
    
    # 权限检查：只能访问自己的会话
    if conversation.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # 获取所有消息（按顺序）
    messages = Message.query.filter_by(
        conversation_id=conversation_id
    ).order_by(Message.order_index.asc()).all()
    
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
                'model': msg.model if hasattr(msg, 'model') else 'deepseek-chat'
            }
            for msg in messages
        ]
    })



@api.route('/conversations', methods=['POST'])
@login_required
def create_conversation():
    """创建新会话"""
    data = request.get_json() or {}
    title = data.get('title', '新对话')
    
    # 如果标题为空，使用默认标题
    if not title or title.strip() == '':
        title = '新对话'
    
    conversation = Conversation(
        title=title,
        user_id=current_user.id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    db.session.add(conversation)
    db.session.commit()
    
    return jsonify({
        'id': conversation.id,
        'title': conversation.title,
        'created_at': conversation.created_at.isoformat(),
        'updated_at': conversation.updated_at.isoformat()
    }), 201


@api.route('/conversations/<int:conversation_id>', methods=['PUT'])
@login_required
def update_conversation(conversation_id):
    """更新会话标题"""
    conversation = Conversation.query.get(conversation_id)
    if not conversation:
        return jsonify({'error': '会话不存在'}), 404
    
    # 权限检查
    if conversation.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400
    
    conversation.title = data['title']
    conversation.updated_at = datetime.now()
    db.session.commit()
    
    return jsonify({
        'id': conversation.id,
        'title': conversation.title
    })


@api.route('/conversations/<int:conversation_id>', methods=['DELETE'])
@login_required
def delete_conversation(conversation_id):
    """删除会话"""
    conversation = Conversation.query.get(conversation_id)
    if not conversation:
        return jsonify({'error': '会话不存在'}), 404
    
    # 权限检查
    if conversation.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(conversation)
    db.session.commit()
    
    return jsonify({'success': True})

