# -*- coding:utf-8 -*-
"""
消息管理 API 路由
"""
from flask import request, jsonify, Response, stream_with_context
from flask_login import login_required, current_user
from datetime import datetime
import json
import threading
from app.core.coremodels import Conversation, Message
from app.core.stop_checker import WebStopChecker
from .blueprint import api

# 全局字典：存储每个会话的停止检查器
# key: (conversation_id, user_id), value: WebStopChecker
_stop_checkers = {}
_checkers_lock = threading.Lock()

@api.route('/conversations/<int:conversation_id>/messages', methods=['POST'])
@login_required
def send_message(conversation_id):
    """发送消息并获取AI回答"""
    try:
        if not current_user or not current_user.is_authenticated:
            return jsonify({'error': '未登录'}), 401
        
        # 使用 core 层的 Conversation.get_by_id() 方法获取会话
        conversation = Conversation.get_by_id(conversation_id)
        if not conversation:
            return jsonify({'error': '会话不存在'}), 404
        if conversation.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request'}), 400
        
        user_content = data.get('content', '')
        # 从请求中获取模型名称，如果没有则使用默认值
        model_name = data.get('model', 'deepseek-chat')
        
        if not user_content:
            return jsonify({'error': 'Content is required'}), 400
        
        # 创建停止检查器并存储
        stop_checker = WebStopChecker()
        checker_key = (conversation_id, current_user.id)
        
        with _checkers_lock:
            # 如果已存在旧的检查器，先清理
            if checker_key in _stop_checkers:
                old_checker = _stop_checkers[checker_key]
                old_checker.set_stop()  # 停止旧的生成
            _stop_checkers[checker_key] = stop_checker
        
        # 使用 Conversation.send_message() 方法（优先使用 coremodels，返回迭代器）
        def generate_stream():
            try:
                for result in conversation.send_message(
                    user_content=user_content,
                    model_name=model_name,
                    auto_title=True,
                    return_iterator=True,  # 返回迭代器，不打印到控制台
                    should_stop=stop_checker.should_stop  # 传递停止检查器
                ):
                    if result['type'] == 'chunk':
                        # 发送数据块
                        yield f"data: {json.dumps({'chunk': result['chunk'], 'type': 'chunk'})}\n\n"
                    elif result['type'] == 'done':
                        # 发送完成信号
                        yield f"data: {json.dumps({'type': 'done', 'message_id': result.get('message_id'), 'user_message_id': result.get('user_message_id')})}\n\n"
                    elif result['type'] == 'interrupted':
                        # 发送中断信号
                        yield f"data: {json.dumps({'type': 'interrupted', 'message': result.get('message'), 'message_id': result.get('message_id'), 'user_message_id': result.get('user_message_id')})}\n\n"
                        break  # 中断后停止
                    elif result['type'] == 'error':
                        # 发送错误信息
                        yield f"data: {json.dumps({'type': 'error', 'error': result.get('error')})}\n\n"
            finally:
                # 清理停止检查器
                with _checkers_lock:
                    if checker_key in _stop_checkers and _stop_checkers[checker_key] == stop_checker:
                        del _stop_checkers[checker_key]
        
        # 返回流式响应
        return Response(
            stream_with_context(generate_stream()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"发送消息失败: {str(e)}")
        print(f"详细错误: {error_detail}")
        return jsonify({'error': f'发送消息失败: {str(e)}'}), 500

@api.route('/conversations/<int:conversation_id>/messages/<int:message_id>/responses', methods=['POST'])
@login_required
def generate_model_response(conversation_id, message_id):
    """
    为指定用户消息生成模型回答（Peer 架构）
    接受用户消息 ID，为该用户消息生成指定模型的回答
    """
    try:
        if not current_user or not current_user.is_authenticated:
            return jsonify({'error': '未登录'}), 401
        
        # 使用 core 层的 Conversation.get_by_id() 方法获取会话
        conversation = Conversation.get_by_id(conversation_id)
        if not conversation:
            return jsonify({'error': '会话不存在'}), 404
        if conversation.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # 使用 core 层的 Message.get_by_id() 方法获取用户消息
        user_message = Message.get_by_id(message_id)
        if not user_message:
            return jsonify({'error': '消息不存在'}), 404
        if user_message.conversation_id != conversation_id:
            return jsonify({'error': '消息不属于当前会话'}), 400
        if user_message.role != 'user':
            return jsonify({'error': '只能为用户消息生成模型回答'}), 400
        
        # 获取请求参数
        data = request.get_json() or {}
        model_name = data.get('model', 'qwen-max')  # 默认使用 qwen-max
        
        # 使用 Message.list() 方法检查是否已经存在该模型的回答
        messages = Message.list(conversation_id=conversation_id, order_by="order_index")
        
        # 查找在该用户消息之后、该模型的回答
        existing_response = None
        for msg in messages:
            if (msg.order_index > user_message.order_index and 
                msg.role == 'assistant' and 
                msg.model == model_name):
                existing_response = msg
                break
        
        # 如果已存在该模型的回答，检查是否是在该用户消息之后、下一个用户消息之前生成的
        if existing_response:
            # 查找下一个用户消息
            next_user_message = None
            for msg in messages:
                if msg.order_index > user_message.order_index and msg.role == 'user':
                    next_user_message = msg
                    break
            
            # 如果回答在下一个用户消息之前，说明是为该用户消息生成的
            if not next_user_message or existing_response.order_index < next_user_message.order_index:
                return jsonify({'error': f'该用户消息已有 {model_name} 模型的回答'}), 400
        
        # 创建停止检查器并存储
        stop_checker = WebStopChecker()
        checker_key = (conversation_id, current_user.id)
        
        with _checkers_lock:
            # 如果已存在旧的检查器，先清理
            if checker_key in _stop_checkers:
                old_checker = _stop_checkers[checker_key]
                old_checker.set_stop()  # 停止旧的生成
            _stop_checkers[checker_key] = stop_checker
        
        # 使用 Conversation.send_message() 方法的对比模式（优先使用 coremodels，返回迭代器）
        def generate_stream():
            try:
                for result in conversation.send_message(
                    user_message_id=message_id,
                    model_name=model_name,
                    save_response=True,  # 保存回答到数据库
                    return_iterator=True,  # 返回迭代器，不打印到控制台
                    should_stop=stop_checker.should_stop  # 传递停止检查器
                ):
                    if result['type'] == 'chunk':
                        # 发送数据块
                        yield f"data: {json.dumps({'chunk': result['chunk'], 'type': 'chunk'})}\n\n"
                    elif result['type'] == 'done':
                        # 发送完成信号
                        yield f"data: {json.dumps({'type': 'done', 'message_id': result.get('message_id'), 'user_message_id': result.get('user_message_id')})}\n\n"
                    elif result['type'] == 'interrupted':
                        # 发送中断信号
                        yield f"data: {json.dumps({'type': 'interrupted', 'message': result.get('message'), 'message_id': result.get('message_id'), 'user_message_id': result.get('user_message_id')})}\n\n"
                        break  # 中断后停止
                    elif result['type'] == 'error':
                        # 发送错误信息
                        yield f"data: {json.dumps({'type': 'error', 'error': result.get('error')})}\n\n"
            finally:
                # 清理停止检查器
                with _checkers_lock:
                    if checker_key in _stop_checkers and _stop_checkers[checker_key] == stop_checker:
                        del _stop_checkers[checker_key]
        
        # 返回流式响应
        return Response(
            stream_with_context(generate_stream()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"生成模型回答失败: {str(e)}")
        print(f"详细错误: {error_detail}")
        return jsonify({'error': f'生成模型回答失败: {str(e)}'}), 500


@api.route('/conversations/<int:conversation_id>/messages/stop', methods=['POST'])
@login_required
def stop_message_generation(conversation_id):
    """
    停止当前会话的消息生成（软中断）
    
    通过设置停止标志来中断正在进行的流式生成，而不是直接断开连接
    这样可以确保：
    1. 已生成的内容能正常保存
    2. 前端能收到 interrupted 消息
    3. 流程更可控
    """
    try:
        if not current_user or not current_user.is_authenticated:
            return jsonify({'error': '未登录'}), 401
        
        # 验证会话是否存在且属于当前用户
        conversation = Conversation.get_by_id(conversation_id)
        if not conversation:
            return jsonify({'error': '会话不存在'}), 404
        if conversation.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # 获取并设置停止标志
        checker_key = (conversation_id, current_user.id)
        with _checkers_lock:
            if checker_key in _stop_checkers:
                stop_checker = _stop_checkers[checker_key]
                stop_checker.set_stop()
                return jsonify({
                    'success': True,
                    'message': '已发送停止信号'
                })
            else:
                # 没有正在进行的生成
                return jsonify({
                    'success': False,
                    'message': '当前没有正在进行的生成'
                })
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"停止消息生成失败: {str(e)}")
        print(f"详细错误: {error_detail}")
        return jsonify({'error': f'停止消息生成失败: {str(e)}'}), 500
