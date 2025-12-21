/**
 * 会话相关 API
 * 职责：处理所有与会话相关的后端 API 调用
 */

// 使用全局命名空间
window.ConversationAPI = window.ConversationAPI || {};

// 使用 var 避免重复声明错误（如果其他文件也定义了 API_BASE）
var API_BASE = window.API_BASE || '/api';

/**
 * 获取会话列表
 */
ConversationAPI.getConversations = async function() {
    const response = await fetch(`${API_BASE}/conversations`);
    
    if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
            window.location.href = '/auth/login';
            return null;
        }
        throw new Error('加载会话列表失败');
    }
    
    return await response.json();
}

/**
 * 获取会话详情（包含消息列表）
 */
ConversationAPI.getConversation = async function(conversationId) {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}`);
    
    if (!response.ok) {
        throw new Error('加载会话失败');
    }
    
    return await response.json();
}

/**
 * 创建新会话
 */
ConversationAPI.createConversation = async function(title = '新对话') {
    const response = await fetch(`${API_BASE}/conversations`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title })
    });
    
    if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
            window.location.href = '/auth/login';
            return null;
        }
        
        const contentType = response.headers.get('content-type');
        let errorMessage = '创建会话失败';
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
    
    return await response.json();
}

/**
 * 删除会话
 */
ConversationAPI.deleteConversation = async function(conversationId) {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}`, {
        method: 'DELETE'
    });
    
    if (!response.ok) {
        throw new Error('删除会话失败');
    }
    
    return true;
}

