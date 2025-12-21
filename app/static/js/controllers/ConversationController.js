/**
 * 会话控制器
 * 控制层：协调会话相关的业务逻辑、UI 渲染和 API 调用
 */

class ConversationController {
    /**
     * @param {Object} config - 配置对象
     * @param {HTMLElement} config.conversationList - 会话列表容器
     * @param {HTMLElement} config.chatMessages - 消息容器
     * @param {HTMLElement} config.welcomeMessage - 欢迎消息元素
     * @param {HTMLElement} config.messageInput - 消息输入框
     */
    constructor(config = {}) {
        this.conversationList = config.conversationList;
        this.chatMessages = config.chatMessages;
        this.welcomeMessage = config.welcomeMessage;
        this.messageInput = config.messageInput;
    }

    /**
     * 加载会话列表
     */
    async loadConversations() {
        try {
            const conversationsData = await ConversationAPI.getConversations();
            if (!conversationsData) return;
            
            // 将 JSON 数据转换为 Conversation 模型实例
            const conversations = conversationsData.map(data => new Conversation(data));
            
            ConversationUI.renderConversationList(
                this.conversationList,
                conversations,
                chatState.getConversationId(),
                this.handleConversationSelect.bind(this),
                this.handleConversationDelete.bind(this)
            );
            
            // 如果有会话，默认加载第一个
            if (conversations.length > 0 && !chatState.getConversationId()) {
                await this.loadConversation(conversations[0].id);
            }
        } catch (error) {
            console.error('加载会话列表失败:', error);
            MessageUI.showError('加载会话列表失败: ' + error.message);
        }
    }

    /**
     * 加载会话详情
     * @param {number} conversationId - 会话ID
     */
    async loadConversation(conversationId) {
        try {
            chatState.setConversationId(conversationId);
            
            const conversationData = await ConversationAPI.getConversation(conversationId);
            // 将 JSON 数据转换为 Conversation 模型实例
            const conversation = new Conversation(conversationData);
            
            MessageUI.renderMessages(
                this.chatMessages,
                this.welcomeMessage,
                conversation.messages,
                MessageService.organizeMessages
            );
            
            // 更新会话列表的激活状态
            ConversationUI.updateActiveConversation(this.conversationList, conversationId);
            
            // 重新加载会话列表以更新消息数量
            this.loadConversations();
        } catch (error) {
            console.error('加载会话失败:', error);
            MessageUI.showError('加载会话失败: ' + error.message);
        }
    }

    /**
     * 创建新会话
     */
    async createNewConversation() {
        try {
            const conversationData = await ConversationAPI.createConversation('新对话');
            if (!conversationData) return;
            
            // 将 JSON 数据转换为 Conversation 模型实例
            const conversation = new Conversation(conversationData);
            
            chatState.setConversationId(conversation.id);
            
            // 清空消息区域并显示欢迎消息（通过UI层）
            MessageUI.clearMessages(this.chatMessages);
            MessageUI.showWelcome(this.welcomeMessage);
            
            // 重新加载会话列表
            this.loadConversations();
            
            // 聚焦输入框（通过UI层）
            InputUI.focusInput(this.messageInput);
        } catch (error) {
            console.error('创建会话失败:', error);
            MessageUI.showError('创建会话失败: ' + error.message);
        }
    }

    /**
     * 处理会话选择
     * @param {number} conversationId - 会话ID
     */
    handleConversationSelect(conversationId) {
        this.loadConversation(conversationId);
    }

    /**
     * 处理会话删除
     * @param {number} conversationId - 会话ID
     */
    async handleConversationDelete(conversationId) {
        if (!confirm('确定要删除这个会话吗？')) {
            return;
        }
        
        try {
            await ConversationAPI.deleteConversation(conversationId);
            
            // 如果删除的是当前会话，清空消息区域（通过UI层）
            if (conversationId === chatState.getConversationId()) {
                chatState.setConversationId(null);
                MessageUI.clearMessages(this.chatMessages);
                MessageUI.showWelcome(this.welcomeMessage);
            }
            
            // 重新加载会话列表
            this.loadConversations();
        } catch (error) {
            console.error('删除会话失败:', error);
            MessageUI.showError('删除会话失败: ' + error.message);
        }
    }

    /**
     * 确保有会话ID（如果没有则创建）
     * @returns {Promise<number|null>} 会话ID
     */
    async ensureConversationId() {
        let conversationId = chatState.getConversationId();
        
        if (!conversationId) {
            const conversationData = await ConversationAPI.createConversation('新对话');
            if (!conversationData) return null;
            
            // 将 JSON 数据转换为 Conversation 模型实例
            const conversation = new Conversation(conversationData);
            
            conversationId = conversation.id;
            chatState.setConversationId(conversationId);
            
            // 清空消息区域并隐藏欢迎消息（通过UI层）
            MessageUI.clearMessages(this.chatMessages);
            MessageUI.hideWelcome(this.welcomeMessage);
            
            // 重新加载会话列表
            this.loadConversations();
        }
        
        return conversationId;
    }
}

// 导出 ConversationController 类
window.ConversationController = ConversationController;

