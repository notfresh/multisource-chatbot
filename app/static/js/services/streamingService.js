/**
 * 流式处理服务
 * 职责：封装流式处理的通用逻辑，减少重复代码
 */

// 使用全局命名空间
window.StreamingService = window.StreamingService || {};

/**
 * 处理流式响应的通用逻辑
 * @param {ReadableStream} stream - 响应流
 * @param {Object} options - 配置选项
 * @param {Function} [options.onChunk] - 收到数据块时的回调 (fullContent: string) => void
 * @param {Function} [options.onDone] - 流式完成时的回调 (data: { messageId, fullContent }) => void
 * @param {Function} [options.onError] - 错误回调 (error: Error) => void
 * @param {Function} [options.shouldStop] - 是否应该停止 (() => boolean)
 * @returns {Promise<string>} - 完整内容
 */
StreamingService.handleStreaming = async function(stream, options = {}) {
    const { onChunk, onDone, onError, shouldStop } = options;
    
    return await StreamHandler.handleStream(stream, {
        onChunk: onChunk || (() => {}),
        onDone: onDone || (() => {}),
        onError: onError || ((error) => { throw error; }),
        shouldStop: shouldStop || (() => false)
    });
};

/**
 * 创建流式处理回调（用于发送消息）
 * @param {Object} context - 上下文对象
 * @param {MessageComponent} context.aiMessageComponent - AI消息组件
 * @param {HTMLElement} context.aiMessageDiv - AI消息DOM元素
 * @param {HTMLElement} context.chatMessages - 消息容器
 * @param {HTMLElement} context.stopButton - 停止按钮
 * @param {Function} context.onComplete - 完成后的回调
 * @returns {Object} - 流式处理回调对象
 */
StreamingService.createSendMessageCallbacks = function(context) {
    const { aiMessageComponent, aiMessageDiv, chatMessages, stopButton, onComplete } = context;
    
    return {
        onChunk: (fullContent) => {
            // 流式生成中
            if (aiMessageComponent) {
                aiMessageComponent.updateModelResponse('deepseek-chat', fullContent, false);
            }
            MessageUI.scrollToBottom(chatMessages);
        },
        onDone: ({ messageId, fullContent }) => {
            // 生成完成
            chatState.endStreaming();
            InputUI.setStopButtonState(stopButton, { visible: false });
            
            if (aiMessageComponent && fullContent) {
                aiMessageComponent.updateModelResponse('deepseek-chat', fullContent, true);
                if (messageId && aiMessageDiv) {
                    aiMessageDiv.dataset.messageId = messageId;
                    const responseData = aiMessageComponent.modelManager?.get('deepseek-chat');
                    if (responseData) {
                        responseData.messageId = messageId;
                    }
                }
            }
            
            if (onComplete) {
                onComplete();
            }
        },
        onError: (error) => {
            throw error;
        },
        shouldStop: () => !chatState.isStreamingNow()
    };
};

/**
 * 创建流式处理回调（用于按需请求模型回答）
 * @param {Object} context - 上下文对象
 * @param {MessageComponent} context.messageComponent - 消息组件
 * @param {Object} context.modelResponse - 模型回答对象
 * @param {string} context.modelName - 模型名称
 * @param {HTMLElement} context.chatMessages - 消息容器
 * @param {HTMLElement} context.stopButton - 停止按钮
 * @param {Function} context.onComplete - 完成后的回调
 * @returns {Object} - 流式处理回调对象
 */
StreamingService.createRequestModelCallbacks = function(context) {
    const { messageComponent, modelResponse, modelName, chatMessages, stopButton, onComplete } = context;
    
    return {
        onChunk: (fullContent) => {
            // 流式生成中
            if (messageComponent) {
                messageComponent.updateModelResponse(modelName, fullContent, false);
            }
            MessageUI.scrollToBottom(chatMessages);
        },
        onDone: ({ messageId: responseMessageId, fullContent }) => {
            // 生成完成
            chatState.endStreaming();
            InputUI.setStopButtonState(stopButton, { visible: false });
            
            if (messageComponent && fullContent) {
                modelResponse.id = responseMessageId;
                modelResponse.content = fullContent;
                messageComponent.updateModelResponse(modelName, fullContent, true);
                messageComponent.addModelResponse(modelResponse);
            }
            
            if (onComplete) {
                onComplete();
            }
        },
        onError: (error) => {
            throw error;
        },
        shouldStop: () => !chatState.isStreamingNow()
    };
};

