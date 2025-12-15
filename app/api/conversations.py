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


@api.route('/conversations/<int:conversation_id>/messages/partial', methods=['POST'])
@login_required
def save_partial_message(conversation_id):
    """保存部分消息（用于暂停流式输出时）"""
    # 验证会话是否存在和所有权
    conversation = Conversation.query.get(conversation_id)
    if not conversation:
        return jsonify({'error': '会话不存在'}), 404
    if conversation.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    content = data.get('content', '')
    
    if not content:
        return jsonify({'error': 'Content is required'}), 400
    
    # 获取当前消息数量，用于设置 order_index
    message_count = Message.query.filter_by(
        conversation_id=conversation_id
    ).count()
    
    # 检查是否已有未完成的AI消息（最后一条消息是assistant且内容匹配）
    last_message = Message.query.filter_by(
        conversation_id=conversation_id
    ).order_by(Message.order_index.desc()).first()
    
    if last_message and last_message.role == 'assistant' and last_message.content == content:
        # 消息已存在且内容相同，无需重复保存
        return jsonify({
            'id': last_message.id,
            'message': 'Message already saved'
        })
    
    # 创建或更新AI消息
    # 检查最后一条消息是否是未完成的AI消息（内容较短，可能是部分内容）
    if (last_message and last_message.role == 'assistant' and 
        len(content) > len(last_message.content) and 
        content.startswith(last_message.content)):
        # 更新现有消息（内容更长，说明是更新）
        last_message.content = content
        db.session.commit()
        return jsonify({
            'id': last_message.id,
            'message': 'Message updated'
        })
    else:
        # 创建新消息
        assistant_message = Message(
            conversation_id=conversation_id,
            role='assistant',
            content=content,
            order_index=message_count * 2 + 1,
            model='deepseek-chat'  # 默认使用 deepseek-chat
        )
        db.session.add(assistant_message)
        conversation.updated_at = datetime.now()
        db.session.commit()
        return jsonify({
            'id': assistant_message.id,
            'message': 'Message saved'
        })

