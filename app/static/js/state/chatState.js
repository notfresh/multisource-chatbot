/**
 * 聊天状态管理
 * 职责：管理全局状态，提供状态访问和更新接口
 */

class ChatState {
    constructor() {
        this.currentConversationId = null;
        this.currentAbortController = null;
        this.isStreaming = false;
    }
    
    /**
     * 获取当前会话ID
     */
    getConversationId() {
        return this.currentConversationId;
    }
    
    /**
     * 设置当前会话ID
     */
    setConversationId(conversationId) {
        this.currentConversationId = conversationId;
    }
    
    /**
     * 开始流式输出
     */
    startStreaming() {
        this.isStreaming = true;
        this.currentAbortController = new AbortController();
        return this.currentAbortController;
    }
    
    /**
     * 停止流式输出
     */
    stopStreaming() {
        this.isStreaming = false;
        if (this.currentAbortController) {
            this.currentAbortController.abort();
            this.currentAbortController = null;
        }
    }
    
    /**
     * 结束流式输出
     */
    endStreaming() {
        this.isStreaming = false;
        this.currentAbortController = null;
    }
    
    /**
     * 是否正在流式输出
     */
    isStreamingNow() {
        return this.isStreaming;
    }
    
    /**
     * 获取中断信号
     */
    getAbortSignal() {
        return this.currentAbortController ? this.currentAbortController.signal : null;
    }
}

// 导出单例到全局命名空间
window.chatState = new ChatState();

