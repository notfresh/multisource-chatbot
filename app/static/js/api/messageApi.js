/**
 * 消息相关 API
 * 职责：处理所有与消息相关的后端 API 调用
 */

// 使用全局命名空间
(function(global) {
    'use strict';
    if (typeof global === 'undefined') {
        console.error('MessageAPI: 全局对象未定义');
        return;
    }
    
    const API_BASE = '/api';
    global.MessageAPI = global.MessageAPI || {};
    console.log('MessageAPI 模块已加载，版本:', new Date().toISOString());
    
    /**
     * 发送用户消息并获取流式响应
     * @param {number} conversationId - 会话ID
     * @param {string} content - 消息内容
     * @param {AbortSignal} signal - 中断信号
     * @param {string} [model] - 模型名称（可选，默认由后端决定）
     * @returns {Promise<Response>} - 流式响应对象
     */
    global.MessageAPI.sendMessage = async function(conversationId, content, signal, model) {
        const body = { content };
        if (model) {
            body.model = model;
        }
        const response = await fetch(`${API_BASE}/conversations/${conversationId}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
            signal
        });
        
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                global.location.href = '/auth/login';
                return null;
            }
            
            const contentType = response.headers.get('content-type');
            let errorMessage = '发送消息失败';
            if (contentType && contentType.includes('application/json')) {
                try {
                    const error = await response.json();
                    errorMessage = error.error || error.message || errorMessage;
                } catch (e) {
                    // JSON 解析失败
                }
            } else {
                errorMessage = `服务器错误 (${response.status}): 请检查会话是否存在`;
            }
            throw new Error(errorMessage);
        }
        
        return response;
    };
    
    /**
     * 按需请求模型回答（流式响应）
     * @param {number} conversationId - 会话ID
     * @param {number} messageId - 用户消息ID
     * @param {string} modelName - 模型名称
     * @param {AbortSignal} signal - 中断信号
     * @returns {Promise<Response>} - 流式响应对象
     */
    global.MessageAPI.requestModelResponse = async function(conversationId, messageId, modelName, signal) {
        const response = await fetch(
            `${API_BASE}/conversations/${conversationId}/messages/${messageId}/responses`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ model: modelName }),
                signal
            }
        );
        
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                global.location.href = '/auth/login';
                return null;
            }
            
            const contentType = response.headers.get('content-type');
            let errorMessage = '按需查询失败';
            if (contentType && contentType.includes('application/json')) {
                try {
                    const error = await response.json();
                    errorMessage = error.error || error.message || errorMessage;
                } catch (e) {
                    // JSON 解析失败
                }
            }
            throw new Error(errorMessage);
        }
        
        return response;
    };
    
    /**
     * 保存部分消息（中断时保存）
     * @param {number} conversationId - 会话ID
     * @param {string} content - 消息内容
     */
    global.MessageAPI.savePartialMessage = async function(conversationId, content) {
        if (!content || !conversationId) {
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE}/conversations/${conversationId}/messages/partial`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content })
            });
            
            if (response.ok) {
                console.log('部分消息已保存');
                return true;
            }
        } catch (error) {
            console.error('保存部分消息失败:', error);
        }
        
        return false;
    };
    
})(typeof window !== 'undefined' ? window : this);
