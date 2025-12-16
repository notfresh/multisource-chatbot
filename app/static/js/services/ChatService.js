/**
 * 聊天服务类
 * 封装可复用的聊天功能，供多个页面使用
 */
class ChatService {
    

    /**
     * 加载会话列表
     */
    async loadConversations() {
        try {
            const conversations = await ConversationAPI.getConversations();
            if (!conversations) return;
            
            ConversationUI.renderConversationList(
                conversationList,
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
     */
    async loadConversation(conversationId) {
        try {
            chatState.setConversationId(conversationId);
            
            const conversation = await ConversationAPI.getConversation(conversationId);
            MessageUI.renderMessages(
                chatMessages,
                welcomeMessage,
                conversation.messages,
                MessageOrganizer.organizeMessages
            );
            
            // 更新会话列表的激活状态
            ConversationUI.updateActiveConversation(conversationList, conversationId);
            
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
            const conversation = await ConversationAPI.createConversation('新对话');
            if (!conversation) return;
            
            chatState.setConversationId(conversation.id);
            
            // 清空消息区域
            chatMessages.innerHTML = '';
            welcomeMessage.style.display = 'block';
            
            // 重新加载会话列表
            this.loadConversations();
            
            // 聚焦输入框
            messageInput.focus();
        } catch (error) {
            console.error('创建会话失败:', error);
            MessageUI.showError('创建会话失败: ' + error.message);
        }
    }
    
    /**
     * 处理会话选择
     */
    handleConversationSelect(conversationId) {
        this.loadConversation(conversationId);
    }

    /**
     * 处理会话删除
     */
    async handleConversationDelete(conversationId) {
        if (!confirm('确定要删除这个会话吗？')) {
            return;
        }
        
        try {
            await ConversationAPI.deleteConversation(conversationId);
            
            // 如果删除的是当前会话，清空消息区域
            if (conversationId === chatState.getConversationId()) {
                chatState.setConversationId(null);
                chatMessages.innerHTML = '';
                welcomeMessage.style.display = 'block';
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
     */
    async ensureConversationId() {
        let conversationId = chatState.getConversationId();
        
        if (!conversationId) {
            const conversation = await ConversationAPI.createConversation('新对话');
            if (!conversation) return null;
            
            conversationId = conversation.id;
            chatState.setConversationId(conversationId);
            
            // 清空消息区域并隐藏欢迎消息
            chatMessages.innerHTML = '';
            welcomeMessage.style.display = 'none';
            
            // 重新加载会话列表
            this.loadConversations();
        }
        
        return conversationId;
    }

    //////////////////////////////////////////////////////////////////
    ////////
    //////////////////////////////////////////////////////////////////

    /**
     * 按需请求模型回答
     * @param {number} messageId - 消息ID
     * @param {string} modelName - 模型名称
     * @param {MessageComponent} messageComponent - 消息组件实例
     */
    async requestModelResponse(messageId, modelName, messageComponent) {
        const conversationId = chatState.getConversationId();
        if (!conversationId || !messageId) {
            console.error('缺少必要参数');
            return;
        }
        
        // 如果没有传入messageComponent，尝试通过messageId找到它
        if (!messageComponent) {
            messageComponent = MessageUI.findMessageComponentById(messageId);
        }
        
        if (!messageComponent) {
            console.error('找不到对应的消息组件');
            MessageUI.showError('找不到对应的消息，请刷新页面后重试');
            return;
        }
        
        // 创建模型回答的容器（如果还没有）
        const modelResponse = {
            model: modelName,
            content: '',
            id: null
        };
        
        // 在消息组件中添加模型回答区域（初始为空）
        messageComponent.addModelResponse(modelResponse);
        
        // 显示停止按钮
        InputUI.setStopButtonState(stopButton, { visible: true, disabled: false });
        
        // 开始流式输出
        const abortController = chatState.startStreaming();
        
        try {
            // 请求模型回答
            const response = await MessageAPI.requestModelResponse(
                conversationId,
                messageId,
                modelName,
                abortController.signal
            );
            
            if (!response) return;
            
            // 处理流式响应
            await StreamingService.handleStreaming(response.body,
                StreamingService.createRequestModelCallbacks({
                    messageComponent,
                    modelResponse,
                    modelName,
                    chatMessages,
                    stopButton,
                    onComplete: () => this.loadConversations()
                })
            );
            
        } catch (error) {
            // 处理错误
            this.handleRequestModelError(error, messageComponent, modelResponse);
        } finally {
            // 恢复按钮状态
            chatState.endStreaming();
            InputUI.setStopButtonState(stopButton, { visible: false });
        }
    }

    /**
     * 处理按需请求模型回答的错误
     * @private
     */
    handleRequestModelError(error, messageComponent, modelResponse) {
        // 如果是用户主动中断，不显示错误
        if (error.name === 'AbortError' || !chatState.isStreamingNow()) {
            console.log('按需查询已中断');
            // 保存当前内容
            if (messageComponent && modelResponse.content) {
                messageComponent.addModelResponse(modelResponse);
            }
        } else {
            console.error('按需查询失败:', error);
            MessageUI.showError('按需查询失败: ' + error.message);
        }
    }

    /**
     * 处理发送消息的错误
     * @private
     */
    async handleSendMessageError(error, response, conversationId, userMessageDiv, aiMessageHandle) {
        // 如果是用户主动中断，不显示错误
        if (error.name === 'AbortError' || !chatState.isStreamingNow()) {
            console.log('请求已中断');
                // 保存部分内容
                try {
                    const fullContent = await StreamingService.handleStreaming(
                        response?.body || new ReadableStream(),
                        {
                            onChunk: () => {},
                            shouldStop: () => true
                        }
                    );
                    if (fullContent) {
                        await MessageAPI.savePartialMessage(conversationId, fullContent);
                        this.loadConversations();
                    }
                } catch (e) {
                    console.error('保存部分消息失败:', e);
                }
        } else {
            console.error('发送消息失败:', error);
            MessageUI.showError('发送消息失败: ' + error.message);
            
            // 移除用户消息和AI消息（因为发送失败）
            if (userMessageDiv) userMessageDiv.remove();
            if (aiMessageHandle) aiMessageHandle.remove();
        }
    }

    /**
     * 发送消息
     */
    async sendMessage() {
        const content = messageInput.value.trim();
        if (!content) {
            return;
        }
        
        // 确保有会话ID
        const conversationId = await this.ensureConversationId();
        if (!conversationId) {
            return;
        }
        
        // 禁用输入和按钮
        InputUI.setInputEnabled(messageInput, sendButton, stopButton, false);
        
        // 显示用户消息
        const userMessage = {
            role: 'user',
            content: content,
            created_at: new Date().toISOString()
        };
        const userMessageDiv = MessageUI.createMessageElement(userMessage);
        chatMessages.appendChild(userMessageDiv);
        InputUI.clearInput(messageInput);
        MessageUI.scrollToBottom(chatMessages);
        
        // 创建AI消息容器（用于流式显示）
        const aiMessage = {
            role: 'assistant',
            content: '',
            model: ModelConfig.default,
            created_at: new Date().toISOString()
        };
        const aiMessageHandle = MessageUI.createMessageElement(aiMessage);
        const aiMessageComponent = MessageUI.getMessageComponent(aiMessageHandle);
        chatMessages.appendChild(aiMessageHandle);
        MessageUI.scrollToBottom(chatMessages);

        // 为默认模型提前创建一个可见的回答区域，方便后续流式更新内容
        if (aiMessageComponent && aiMessage.model) {
            const initialModelResponse = {
                model: aiMessage.model,
                content: '',
                id: null
            };
            aiMessageComponent.addModelResponse(initialModelResponse);
            // 默认模型展开，用户能立即看到流式吐字
            if (aiMessageComponent.modelManager) {
                aiMessageComponent.modelManager.toggle(aiMessage.model);
            }
        }
        
        // 显示停止按钮
        InputUI.setStopButtonState(stopButton, { visible: true, disabled: false });
        
        // 开始流式输出
        const abortController = chatState.startStreaming();
        
        try {
            // 发送消息并获取流式响应
            const response = await MessageAPI.sendMessage(
                conversationId,
                content,
                abortController.signal,
                aiMessage.model  // 传递默认模型名称
            );
            
            if (!response) {
                // 如果 response 为 null（可能是重定向），清理状态
                console.warn('发送消息失败：response 为 null');
                chatState.endStreaming();
                InputUI.setStopButtonState(stopButton, { visible: false });
                InputUI.setInputEnabled(messageInput, sendButton, stopButton, true);
                // 移除空的 AI 消息
                if (aiMessageHandle) aiMessageHandle.remove();
                return;
            }
            
            // 检查响应体是否存在
            if (!response.body) {
                console.error('响应体不存在');
                throw new Error('服务器响应异常：响应体为空');
            }
            
            // 处理流式响应
            await StreamingService.handleStreaming(response.body, 
                StreamingService.createSendMessageCallbacks({
                    aiMessageComponent,
                    modelName: aiMessage.model,
                    aiMessageHandle,
                    chatMessages,
                    stopButton,
                    // 把用户消息 DOM 也传进去，方便在 onDone 里补充 userMessageId
                    userMessageHandle: userMessageDiv,
                    onComplete: () => this.loadConversations()
                })
            );
            
        } catch (error) {
            // 处理错误
            await this.handleSendMessageError(error, response, conversationId, userMessageDiv, aiMessageHandle);
        } finally {
            // 确保状态被重置
            chatState.endStreaming();
            InputUI.setStopButtonState(stopButton, { visible: false });
            InputUI.setInputEnabled(messageInput, sendButton, stopButton, true);
        }
    }

    /**
     * 停止流式输出
     */
    stopStreaming() {
        if (chatState.isStreamingNow()) {
            chatState.stopStreaming();
            InputUI.setStopButtonState(stopButton, { visible: true, disabled: true, text: '已停止' });
        }
    }
}

// 导出 ChatService 类
window.ChatService = ChatService;

// 创建全局实例
window.chatService = new ChatService();
