/**
 * 模型回答领域模型
 * 组件层：表达模型回答是什么
 */

class ModelResponse {
    /**
     * 构造函数
     * @param {string} model - 模型名称
     * @param {string} content - 回答内容
     * @param {number|null} messageId - 消息ID
     */
    constructor(model, content = '', messageId = null) {
        this.model = model;
        this.content = content;
        this.messageId = messageId;
        this.isExpanded = false;
    }
    
    /**
     * 展开
     */
    expand() {
        this.isExpanded = true;
    }
    
    /**
     * 折叠
     */
    collapse() {
        this.isExpanded = false;
    }
    
    /**
     * 切换展开/折叠状态
     */
    toggle() {
        this.isExpanded = !this.isExpanded;
    }
    
    /**
     * 更新内容
     * @param {string} content - 新内容
     */
    updateContent(content) {
        this.content = content;
    }
    
    /**
     * 是否有内容
     * @returns {boolean}
     */
    hasContent() {
        return !!this.content;
    }
}

