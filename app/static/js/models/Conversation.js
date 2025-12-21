/**
 * 会话领域模型
 * 组件层：表达会话是什么
 */

class Conversation {
    /**
     * 构造函数
     * @param {Object} data - 会话数据
     */
    constructor(data = {}) {
        this.id = data.id || null;
        this.title = data.title || '新对话';
        this.userId = data.user_id || data.userId || null;
        this.createdAt = data.created_at || data.createdAt || null;
        this.updatedAt = data.updated_at || data.updatedAt || null;
        this.messageCount = data.message_count || data.messageCount || 0;
        this.messages = data.messages || []; // 消息列表（仅在获取详情时包含）
    }
    
    /**
     * 是否有消息
     * @returns {boolean}
     */
    hasMessages() {
        return this.messageCount > 0 || (this.messages && this.messages.length > 0);
    }
    
    /**
     * 是否为空会话
     * @returns {boolean}
     */
    isEmpty() {
        return !this.hasMessages();
    }
    
    /**
     * 获取显示标题（如果没有标题则使用默认值）
     * @returns {string}
     */
    getDisplayTitle() {
        return this.title || '新对话';
    }
    
    /**
     * 获取消息数量（优先使用 messageCount，如果没有则使用 messages.length）
     * @returns {number}
     */
    getMessageCount() {
        if (this.messageCount !== undefined) {
            return this.messageCount;
        }
        return this.messages ? this.messages.length : 0;
    }
    
    /**
     * 是否已保存（有ID）
     * @returns {boolean}
     */
    isSaved() {
        return this.id !== null && this.id !== undefined;
    }
}

