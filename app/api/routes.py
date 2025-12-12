# -*- coding:utf-8 -*-
"""
API 路由 - 会话和消息管理
"""
from flask import Blueprint, request, jsonify, current_app, Response, stream_with_context
from flask_login import login_required, current_user
from datetime import datetime
import json
from app.ai.chat_manager import ChatManager
from app.models import Conversation, Message, db

api = Blueprint('api', __name__, url_prefix='/api')
chat_manager = ChatManager()  # 全局聊天管理器


# ==================== 会话管理 API ====================

@api.route('/conversations', methods=['GET'])
@login_required
def get_conversations():
    """获取会话列表"""
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
                'created_at': msg.created_at.isoformat() if msg.created_at else None
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
            order_index=message_count * 2 + 1
        )
        db.session.add(assistant_message)
        conversation.updated_at = datetime.now()
        db.session.commit()
        return jsonify({
            'id': assistant_message.id,
            'message': 'Message saved'
        })


# ==================== 消息管理 API ====================

@api.route('/conversations/<int:conversation_id>/messages', methods=['POST'])
@login_required
def send_message(conversation_id):
    """发送消息并获取AI回答"""
    # 验证会话是否存在和所有权
    conversation = Conversation.query.get(conversation_id)
    if not conversation:
        return jsonify({'error': '会话不存在'}), 404
    if conversation.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    user_content = data.get('content', '')
    
    if not user_content:
        return jsonify({'error': 'Content is required'}), 400
    
    # 获取当前消息数量，用于设置 order_index
    message_count = Message.query.filter_by(
        conversation_id=conversation_id
    ).count()
    
    # 创建用户消息
    user_message = Message(
        conversation_id=conversation_id,
        role='user',
        content=user_content,
        order_index=message_count * 2
    )
    db.session.add(user_message)
    db.session.commit()
    
    # 使用流式输出
    def generate_stream():
        assistant_content = ""
        try:
            # 生成流式回答
            for chunk in chat_manager.generate_response(
                conversation_id,
                user_content,
                stream=True
            ):
                assistant_content += chunk
                # 发送数据块
                yield f"data: {json.dumps({'chunk': chunk, 'type': 'chunk'})}\n\n"
            
            # 流式输出完成，保存AI回答到数据库
            assistant_message = Message(
                conversation_id=conversation_id,
                role='assistant',
                content=assistant_content,
                order_index=message_count * 2 + 1
            )
            db.session.add(assistant_message)
            
            # 更新会话的 updated_at
            conversation.updated_at = datetime.now()
            
            # 如果这是第一条消息，自动生成会话标题
            if message_count == 0 and (not conversation.title or conversation.title == '新对话'):
                title = user_content[:20] if len(user_content) > 20 else user_content
                conversation.title = title
            
            db.session.commit()
            
            # 发送完成信号
            yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_message.id})}\n\n"
            
        except Exception as e:
            # AI API 调用失败，记录详细错误并返回
            import traceback
            error_detail = traceback.format_exc()
            print(f"AI API调用失败: {str(e)}")
            print(f"详细错误: {error_detail}")
            # 发送错误信息
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    # 返回流式响应
    return Response(
        stream_with_context(generate_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

