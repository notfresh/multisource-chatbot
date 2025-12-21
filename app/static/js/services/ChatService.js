/**
 * 聊天服务类
 * 封装可复用的聊天功能，供多个页面使用
 * 专注于消息发送和流式处理，会话管理由 ConversationController 负责
 */
class ChatService {
    /**
     * @param {ConversationController} conversationController - 会话控制器实例
     */
    constructor(conversationController) {
        this.conversationController = conversationController;
        this.currentOnComplete = null;  // 存储当前的 onComplete 回调
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
        const stopButton = window.stopButton;
        if (stopButton) {
            InputUI.setStopButtonState(stopButton, { visible: true, disabled: false });
        }
        
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
            const chatMessages = window.chatMessages;
            const stopButton = window.stopButton;
            await StreamingService.handleStreaming(response.body,
                StreamingService.createRequestModelCallbacks({
                    messageComponent,
                    modelResponse,
                    modelName,
                    chatMessages: chatMessages || null,
                    stopButton: stopButton || null,
                    onComplete: () => this.conversationController.loadConversations()
                })
            );
            
        } catch (error) {
            // 处理错误
            this.handleRequestModelError(error, messageComponent, modelResponse);
        } finally {
            // 恢复按钮状态
            chatState.endStreaming();
            const stopButton = window.stopButton;
            if (stopButton) {
                InputUI.setStopButtonState(stopButton, { visible: false });
            }
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
        // 注意：后端已经在 GeneratorExit 时自动保存了部分内容，不需要前端再保存
        if (error.name === 'AbortError' || !chatState.isStreamingNow()) {
            console.log('请求已中断（后端已自动保存部分内容）');
            // 刷新会话列表，以显示后端保存的消息
            this.conversationController.loadConversations();
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
        const messageInput = window.messageInput;
        const sendButton = window.sendButton;
        const stopButton = window.stopButton;
        const chatMessages = window.chatMessages;
        
        if (!messageInput || !sendButton || !stopButton || !chatMessages) {
            console.error('必要的 DOM 元素未找到');
            return;
        }
        
        const content = messageInput.value.trim();
        if (!content) {
            return;
        }
        
        // 确保有会话ID（通过 ConversationController）
        const conversationId = await this.conversationController.ensureConversationId();
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
            
            // 创建 onComplete 回调
            const onCompleteCallback = () => {
                this.conversationController.loadConversations();
                this.currentOnComplete = null;  // 清理
            };
            
            // 存储当前的 onComplete 回调，以便在 stopStreaming 中使用
            this.currentOnComplete = onCompleteCallback;
            
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
                    onComplete: onCompleteCallback
                })
            );
            
        } catch (error) {
            // 处理错误
            await this.handleSendMessageError(error, response, conversationId, userMessageDiv, aiMessageHandle);
        } finally {
            // 清理 onComplete 回调
            this.currentOnComplete = null;
            // 确保状态被重置
            chatState.endStreaming();
            InputUI.setStopButtonState(stopButton, { visible: false });
            InputUI.setInputEnabled(messageInput, sendButton, stopButton, true);
        }
    }

    /**
     * 停止流式输出（软中断）
     * 先调用后端中断 API，如果失败则使用硬中断（abort）
     */
    async stopStreaming() {
        if (!chatState.isStreamingNow()) {
            return;
        }
        
        const conversationId = chatState.getConversationId();
        const stopButton = window.stopButton;
        
        // 先尝试软中断（调用后端 API）
        if (conversationId) {
            try {
                const success = await MessageAPI.stopMessageGeneration(conversationId);
                if (success) {
                    console.log('已发送停止信号到服务器');
                    // 等待服务器返回 interrupted 消息，不立即 abort
                    // interrupted 消息会触发 onDone，进而调用 onComplete
                    // 如果服务器响应慢，设置超时后使用硬中断，并手动调用 onComplete
                    setTimeout(() => {
                        if (chatState.isStreamingNow()) {
                            console.warn('软中断超时，使用硬中断');
                            // 如果超时，手动调用 onComplete（如果存在）
                            if (this.currentOnComplete) {
                                try {
                                    this.currentOnComplete();
                                } catch (e) {
                                    console.error('调用 onComplete 失败:', e);
                                }
                            }
                            chatState.stopStreaming(); // 硬中断作为兜底
                        }
                    }, 2000); // 2秒超时
                } else {
                    // 软中断失败，使用硬中断
                    console.warn('软中断失败，使用硬中断');
                    // 手动调用 onComplete（如果存在）
                    if (this.currentOnComplete) {
                        try {
                            this.currentOnComplete();
                        } catch (e) {
                            console.error('调用 onComplete 失败:', e);
                        }
                    }
                    chatState.stopStreaming();
                }
            } catch (error) {
                console.error('调用停止 API 失败:', error);
                // 出错时使用硬中断，并手动调用 onComplete（如果存在）
                if (this.currentOnComplete) {
                    try {
                        this.currentOnComplete();
                    } catch (e) {
                        console.error('调用 onComplete 失败:', e);
                    }
                }
                chatState.stopStreaming();
            }
        } else {
            // 没有会话ID，直接使用硬中断
            // 手动调用 onComplete（如果存在）
            if (this.currentOnComplete) {
                try {
                    this.currentOnComplete();
                } catch (e) {
                    console.error('调用 onComplete 失败:', e);
                }
            }
            chatState.stopStreaming();
        }
        
        // 更新按钮状态
        if (stopButton) {
            InputUI.setStopButtonState(stopButton, { visible: true, disabled: true, text: '已停止' });
        }
    }
}

// 导出 ChatService 类
window.ChatService = ChatService;

// 注意：全局实例在 chat.js 中创建，因为需要 ConversationController 参数
