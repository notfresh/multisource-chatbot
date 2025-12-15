/**
 * 消息领域模型
 * 组件层：表达消息是什么
 */

class Message {
    /**
     * 构造函数
     * @param {Object} data - 消息数据
     */
    constructor(data = {}) {
        this.id = data.id || null;
        this.role = data.role || 'user'; // 'user' | 'assistant'
        this.content = data.content || '';
        this.model = data.model || null;
        this.createdAt = data.created_at || data.createdAt || null;
        this.alternativeResponses = data.alternative_responses || [];
    }
    
    /**
     * 是否是用户消息
     * @returns {boolean}
     */
    isUser() {
        return this.role === 'user';
    }
    
    /**
     * 是否是助手消息
     * @returns {boolean}
     */
    isAssistant() {
        return this.role === 'assistant';
    }
    
    /**
     * 是否有模型信息
     * @returns {boolean}
     */
    hasModel() {
        return !!this.model;
    }
    
    /**
     * 是否有替代回答
     * @returns {boolean}
     */
    hasAlternativeResponses() {
        return this.alternativeResponses && this.alternativeResponses.length > 0;
    }
}

