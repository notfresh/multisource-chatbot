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
        order_index=message_count * 2,
        model='deepseek-chat'  # 用户消息也设置 model 字段
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
            # 即使内容为空也要保存（可能是API返回了空内容）
            assistant_message = Message(
                conversation_id=conversation_id,
                role='assistant',
                content=assistant_content,
                order_index=message_count * 2 + 1,
                model='deepseek-chat'  # 默认使用 deepseek-chat
            )
            db.session.add(assistant_message)
            
            # 更新会话的 updated_at
            conversation.updated_at = datetime.now()
            
            # 如果这是第一条消息，自动生成会话标题
            if message_count == 0 and (not conversation.title or conversation.title == '新对话'):
                title = user_content[:20] if len(user_content) > 20 else user_content
                conversation.title = title
            
            db.session.commit()
            
            # 发送完成信号（确保总是发送）
            yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_message.id})}\n\n"
            
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
    
    # 返回流式响应
    return Response(
        stream_with_context(generate_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@api.route('/conversations/<int:conversation_id>/messages/<int:message_id>/alternative', methods=['POST'])
@login_required
def get_alternative_model_response(conversation_id, message_id):
    """按需查询另一个模型的回答"""
    # 验证会话是否存在和所有权
    conversation = Conversation.query.get(conversation_id)
    if not conversation:
        return jsonify({'error': '会话不存在'}), 404
    if conversation.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # 验证目标消息是否存在且属于当前会话
    target_message = Message.query.get(message_id)
    if not target_message:
        return jsonify({'error': '消息不存在'}), 404
    if target_message.conversation_id != conversation_id:
        return jsonify({'error': '消息不属于当前会话'}), 400
    if target_message.role != 'assistant':
        return jsonify({'error': '只能为 assistant 消息查询替代回答'}), 400
    
    # 获取请求参数
    data = request.get_json() or {}
    model_name = data.get('model', 'qwen-max')  # 默认使用 qwen-max
    
    # 获取该消息对应的用户消息
    # 找到该 assistant 消息之前的最近一条用户消息
    user_message = Message.query.filter_by(
        conversation_id=conversation_id
    ).filter(
        Message.order_index < target_message.order_index,
        Message.role == 'user'
    ).order_by(Message.order_index.desc()).first()
    
    if not user_message:
        return jsonify({'error': '找不到对应的用户消息'}), 400
    
    # 使用流式输出
    def generate_stream():
        assistant_content = ""
        try:
            # 生成流式回答
            for chunk in chat_manager.generate_alternative_model_response(
                conversation_id,
                message_id,  # target_message_id
                user_message.content,
                model_name,
                stream=True
            ):
                assistant_content += chunk
                # 发送数据块
                yield f"data: {json.dumps({'chunk': chunk, 'type': 'chunk'})}\n\n"
            
            # 流式输出完成，保存AI回答到数据库
            # 获取当前消息数量，用于设置 order_index
            message_count = Message.query.filter_by(
                conversation_id=conversation_id
            ).count()
            
            # 即使内容为空也要保存（可能是API返回了空内容）
            assistant_message = Message(
                conversation_id=conversation_id,
                role='assistant',
                content=assistant_content,
                order_index=message_count * 2 + 1,  # 放在最后
                model=model_name
            )
            db.session.add(assistant_message)
            
            # 更新会话的 updated_at
            conversation.updated_at = datetime.now()
            db.session.commit()
            
            # 发送完成信号（确保总是发送）
            yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_message.id})}\n\n"
            
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
    
    # 返回流式响应
    return Response(
        stream_with_context(generate_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

