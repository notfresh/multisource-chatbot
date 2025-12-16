# -*- coding:utf-8 -*-
"""
消息管理 API 路由
"""
from flask import request, jsonify, Response, stream_with_context
from flask_login import login_required, current_user
from datetime import datetime
import json
from app.ai.chat_manager import ChatManager
from app.models import Conversation, Message, db
from .blueprint import api

chat_manager = ChatManager()  # 聊天管理器

def _generate_assistant_response_stream(
    conversation_id,
    user_message,
    model_name,
    precomputed_order_index=None,
    auto_title=False
):
    """
    通用的流式生成助手回答函数
    
    Args:
        conversation_id: 会话ID
        user_message: 用户消息对象
        model_name: 模型名称
        precomputed_order_index: 预先计算的 order_index（如果为 None，则流式后计算）
        auto_title: 是否自动生成会话标题（仅第一条消息时）
    
    Yields:
        str: SSE 格式的数据流
    """
    assistant_content = ""
    try:
        # 生成流式回答（Peer 架构）
        for chunk in chat_manager.generate_response_for_user_message(
            conversation_id=conversation_id,
            user_message_id=user_message.id,
            user_message=user_message.content,
            model_name=model_name,
            stream=True
        ):
            assistant_content += chunk
            # 发送数据块
            yield f"data: {json.dumps({'chunk': chunk, 'type': 'chunk'})}\n\n"
        
        # 流式输出完成，保存AI回答到数据库
        # 计算 order_index
        if precomputed_order_index is not None: #TODO
            order_index = precomputed_order_index
        else:
            # 流式后计算：助手消息应该紧跟在用户消息之后
            # 用户消息的 order_index 是偶数，助手消息应该是奇数（+1）
            order_index = user_message.order_index + 1
        
        # 即使内容为空也要保存（可能是API返回了空内容）
        assistant_message = Message(
            conversation_id=conversation_id,
            role='assistant',
            content=assistant_content,
            order_index=order_index,
            model=model_name
        )
        db.session.add(assistant_message)
        
        # 更新会话的 updated_at
        conversation = Conversation.query.get(conversation_id)
        conversation.updated_at = datetime.now()
        
        # 如果这是第一条消息，自动生成会话标题
        if auto_title:
            message_count = Message.query.filter_by(
                conversation_id=conversation_id
            ).count()
            if message_count == 1 and (not conversation.title or conversation.title == '新对话'):
                title = user_message.content[:20] if len(user_message.content) > 20 else user_message.content
                conversation.title = title
        
        db.session.commit()
        
        # 发送完成信号（确保总是发送）
        # 同时把用户消息ID也一并返回，方便前端建立 user_message 与 assistant_message 的关联
        yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_message.id, 'user_message_id': user_message.id})}\n\n"
        
    except GeneratorExit:
        # 生成器被关闭（客户端断开连接），不处理
        raise
    except Exception as e:
        # AI API 调用失败，记录详细错误并返回
        import traceback
        error_detail = traceback.format_exc()
        print(f"AI API调用失败: {str(e)}")
        print(f"详细错误: {error_detail}")
        # 发送错误信息（确保前端能收到错误信号）
        try:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        except:
            # 如果连错误信号都发送失败，忽略
            pass


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
    # 从请求中获取模型名称，如果没有则使用默认值
    default_model = data.get('model', 'deepseek-chat')
    
    if not user_content:
        return jsonify({'error': 'Content is required'}), 400
    
    # 获取最后一条消息的 order_index，用于设置新消息的 order_index
    last_message = Message.query.filter_by(
        conversation_id=conversation_id
    ).order_by(Message.order_index.desc()).first()
    
    # 计算新用户消息的 order_index
    if last_message is None:
        # 如果会话中没有消息，从0开始
        new_order_index = 0
    else:
        # 如果最后一条是用户消息（偶数），新用户消息 = 最后一条 + 2
        # 如果最后一条是助手消息（奇数），新用户消息 = 最后一条 + 1
        if last_message.order_index % 2 == 0:  # 最后是用户消息，把前一条达模型消息给强制终止了
            new_order_index = last_message.order_index + 2
        else:  # 最后是助手消息
            new_order_index = last_message.order_index + 1
    
    # 创建用户消息
    user_message = Message(
        conversation_id=conversation_id,
        role='user',
        content=user_content,
        order_index=new_order_index,
        model=default_model  # 使用请求中的模型或默认值
    )
    db.session.add(user_message)
    db.session.commit()
    
    # 使用流式输出
    def generate_stream():
        yield from _generate_assistant_response_stream(
            conversation_id=conversation_id,
            user_message=user_message,
            model_name=default_model,
            precomputed_order_index=user_message.order_index + 1,
            auto_title=True
        )
    
    # 返回流式响应
    return Response(
        stream_with_context(generate_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@api.route('/conversations/<int:conversation_id>/messages/<int:message_id>/responses', methods=['POST'])
@login_required
def generate_model_response(conversation_id, message_id):
    """
    为指定用户消息生成模型回答（Peer 架构）
    接受用户消息 ID，为该用户消息生成指定模型的回答
    """
    # 验证会话是否存在和所有权
    conversation = Conversation.query.get(conversation_id)
    if not conversation:
        return jsonify({'error': '会话不存在'}), 404
    if conversation.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # 验证用户消息是否存在且属于当前会话
    user_message = Message.query.get(message_id)
    if not user_message:
        return jsonify({'error': '消息不存在'}), 404
    if user_message.conversation_id != conversation_id:
        return jsonify({'error': '消息不属于当前会话'}), 400
    if user_message.role != 'user':
        return jsonify({'error': '只能为用户消息生成模型回答'}), 400
    
    # 获取请求参数
    data = request.get_json() or {}
    model_name = data.get('model', 'qwen-max')  # 默认使用 qwen-max
    
    # 检查是否已经存在该模型的回答
    existing_response = Message.query.filter_by(
        conversation_id=conversation_id,
        role='assistant',
        model=model_name
    ).filter(
        Message.order_index > user_message.order_index
    ).order_by(Message.order_index.asc()).first()
    
    # 如果已存在该模型的回答，返回错误
    if existing_response:
        # 检查是否是在该用户消息之后生成的
        next_user_message = Message.query.filter_by(
            conversation_id=conversation_id,
            role='user'
        ).filter(
            Message.order_index > user_message.order_index
        ).order_by(Message.order_index.asc()).first()
        
        if not next_user_message or existing_response.order_index < next_user_message.order_index:
            return jsonify({'error': f'该用户消息已有 {model_name} 模型的回答'}), 400
    
    # 使用流式输出
    def generate_stream():
        yield from _generate_assistant_response_stream(
            conversation_id=conversation_id,
            user_message=user_message,
            model_name=model_name,
            precomputed_order_index=None,  # 流式后计算
            auto_title=False  # 按需生成不处理标题
        )
    
    # 返回流式响应
    return Response(
        stream_with_context(generate_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


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

