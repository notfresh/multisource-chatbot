/**
 * 消息相关 API
 * 职责：处理所有与消息相关的后端 API 调用
 */

// 使用全局命名空间
window.MessageAPI = window.MessageAPI || {};

// 调试信息：确认文件已加载
console.log('MessageAPI 模块已加载');

// 使用 var 避免重复声明错误（如果其他文件也定义了 API_BASE）
var API_BASE = window.API_BASE || '/api';

/**
 * 发送用户消息并获取流式响应
 * @param {number} conversationId - 会话ID
 * @param {string} content - 消息内容
 * @param {AbortSignal} signal - 中断信号
 * @param {string} [model] - 模型名称（可选，默认由后端决定）
 * @returns {Promise<Response>} - 流式响应对象
 */
MessageAPI.sendMessage = async function(conversationId, content, signal, model) {
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
            window.location.href = '/auth/login';
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
MessageAPI.requestModelResponse = async function(conversationId, messageId, modelName, signal) {
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
            window.location.href = '/auth/login';
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
 * 停止当前会话的消息生成（软中断）
 * @param {number} conversationId - 会话ID
 * @returns {Promise<boolean>} - 是否成功发送停止信号
 */
MessageAPI.stopMessageGeneration = async function(conversationId) {
    if (!conversationId) {
        return false;
    }
    
    try {
        const response = await fetch(`${API_BASE}/conversations/${conversationId}/messages/stop`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            return data.success || false;
        }
    } catch (error) {
        console.error('停止消息生成失败:', error);
    }
    
    return false;
};
