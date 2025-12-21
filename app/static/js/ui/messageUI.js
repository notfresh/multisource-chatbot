/**
 * 消息 UI
 * 职责：处理消息的渲染和操作
 */

// 使用全局命名空间
window.MessageUI = window.MessageUI || {};

// 消息组件实例存储（用于流式输出时更新内容）
const messageComponentMap = new WeakMap();

/**
 * 渲染消息列表
 * @param {HTMLElement} container - 消息容器
 * @param {HTMLElement} welcomeElement - 欢迎消息元素
 * @param {Array} messages - 消息列表
 * @param {Function} organizeMessages - 消息组织函数
 */
MessageUI.renderMessages = function(container, welcomeElement, messages, organizeMessages) {
    container.innerHTML = '';
    welcomeElement.style.display = 'none';
    
    if (messages.length === 0) {
        welcomeElement.style.display = 'block';
        return;
    }
    
    // 将消息组织成结构化的形式
    const organizedMessages = organizeMessages(messages);
    
    organizedMessages.forEach(msg => {
        const messageDiv = MessageUI.createMessageElement(msg);
        container.appendChild(messageDiv);
    });
    
    MessageUI.scrollToBottom(container);
};

/**
 * 创建消息元素
 * @param {Object} msg - 消息数据
 * @returns {HTMLElement} - 消息 DOM 元素
 */
MessageUI.createMessageElement = function(msg) {
    // 使用组件创建消息
    const messageComponent = new MessageComponent({
        message: msg
    });
    const messageDiv = messageComponent.getElement();
    // 将组件实例存储到 DOM 元素上，方便后续访问
    messageComponentMap.set(messageDiv, messageComponent);
    
    return messageDiv;
};

/**
 * 获取消息组件实例
 * @param {HTMLElement} messageElement - 消息 DOM 元素
 * @returns {MessageComponent|null} - 消息组件实例
 */
MessageUI.getMessageComponent = function(messageElement) {
    return messageComponentMap.get(messageElement) || null;
};

/**
 * 通过消息ID查找消息组件
 * @param {number} messageId - 消息ID
 * @returns {MessageComponent|null} - 消息组件实例
 */
MessageUI.findMessageComponentById = function(messageId) {
    const messageDiv = document.querySelector(`[data-message-id="${messageId}"]`);
    if (messageDiv) {
        return messageComponentMap.get(messageDiv);
    }
    return null;
};

/**
 * 滚动到底部
 * @param {HTMLElement} container - 消息容器
 */
MessageUI.scrollToBottom = function(container) {
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
};

/**
 * 显示错误消息
 * @param {string} message - 错误消息
 */
MessageUI.showError = function(message) {
    alert(message);
};

/**
 * 清空消息区域
 * @param {HTMLElement} container - 消息容器
 */
MessageUI.clearMessages = function(container) {
    if (container) {
        container.innerHTML = '';
    }
};

/**
 * 显示欢迎消息
 * @param {HTMLElement} welcomeElement - 欢迎消息元素
 */
MessageUI.showWelcome = function(welcomeElement) {
    if (welcomeElement) {
        welcomeElement.style.display = 'block';
    }
};

/**
 * 隐藏欢迎消息
 * @param {HTMLElement} welcomeElement - 欢迎消息元素
 */
MessageUI.hideWelcome = function(welcomeElement) {
    if (welcomeElement) {
        welcomeElement.style.display = 'none';
    }
};

