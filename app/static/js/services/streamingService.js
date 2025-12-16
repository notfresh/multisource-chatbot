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

/*
 * 创建流式处理回调（用于发送消息）
 * @param {Object} context - 上下文对象
 * @param {MessageComponent} context.aiMessageComponent - AI消息组件
 * @param {HTMLElement} context.aiMessageHandle - AI消息DOM元素
 * @param {HTMLElement} context.chatMessages - 消息容器
 * @param {HTMLElement} context.stopButton - 停止按钮
 * @param {Function} context.onComplete - 完成后的回调
 * @returns {Object} - 流式处理回调对象
 */
StreamingService.createSendMessageCallbacks = function(context) {
    const { aiMessageComponent, aiMessageHandle, userMessageHandle, chatMessages, stopButton, onComplete, modelName } = context;
    
    // 兜底的模型名称（主要用于调试防御）
    const effectiveModelName = modelName || (typeof ModelConfig !== 'undefined' ? ModelConfig.default : 'default');
    
    return {
        onChunk: (fullContent) => {
            console.log('收到数据块:,调用 Onchunk方法');
            // 流式生成中
            if (aiMessageComponent) {
                // 解码Unicode字符
                const decodedContent = fullContent.replace(/\\u([0-9a-fA-F]{4})/g, (match, p1) => {
                    return String.fromCharCode(parseInt(p1, 16));
                });
                console.log('更新AI消息内容', effectiveModelName, decodedContent);
                
                aiMessageComponent.updateModelResponse(effectiveModelName, decodedContent, false);
            }
            MessageUI.scrollToBottom(chatMessages);
        },
        onDone: ({ messageId, userMessageId, fullContent }) => {
            // 生成完成
            chatState.endStreaming();
            InputUI.setStopButtonState(stopButton, { visible: false });
            
            if (aiMessageComponent) {
                // 即使 fullContent 为空，也要更新状态
                const content = fullContent || '';
                // 解码Unicode字符
                const decodedContent = content.replace(/\\u([0-9a-fA-F]{4})/g, (match, p1) => {
                    return String.fromCharCode(parseInt(p1, 16));
                });
                
                // 更新状态为完成（isComplete = true）
                aiMessageComponent.updateModelResponse(effectiveModelName, decodedContent, true);

                // 更新 AI 消息上的 assistant messageId
                if (messageId && aiMessageHandle) {
                    aiMessageHandle.dataset.messageId = messageId;
                }
                if (messageId && aiMessageComponent.message) {
                    aiMessageComponent.message.id = messageId;
                }

                // 如果后端返回了 user_message_id，把它补到对应的用户消息上，供按需查询使用
                if (userMessageId) {
                    try {
                        const userHandle = userMessageHandle || (aiMessageHandle ? aiMessageHandle.previousElementSibling : null);
                        if (userHandle) {
                            userHandle.dataset.messageId = userMessageId;

                            const userMessageComponent = MessageUI.getMessageComponent(userHandle);
                            if (userMessageComponent && userMessageComponent.message) {
                                userMessageComponent.message.id = userMessageId;
                            }

                            // 关键：把 userMessageId 记录到当前 AI 消息组件上，后续按需查询时直接使用
                            if (aiMessageComponent) {
                                aiMessageComponent.userMessageId = userMessageId;
                            }
                        }
                    } catch (e) {
                        console.warn('更新用户消息ID失败:', e);
                    }
                }
            }
            
            if (onComplete) {
                onComplete();
            }
        },
        onError: (error) => {
            console.error('流式处理错误:', error);
            // 确保状态被重置
            chatState.endStreaming();
            InputUI.setStopButtonState(stopButton, { visible: false });
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
            
            if (messageComponent) {
                // 即使 fullContent 为空，也要更新状态
                const content = fullContent || '';
                modelResponse.id = responseMessageId;
                modelResponse.content = content;
                // 更新状态为完成（isComplete = true）
                messageComponent.updateModelResponse(modelName, content, true);
                // 如果内容不为空，添加到模型管理器
                if (content) {
                    messageComponent.addModelResponse(modelResponse);
                }
            }
            
            if (onComplete) {
                onComplete();
            }
        },
        onError: (error) => {
            console.error('流式处理错误:', error);
            // 确保状态被重置
            chatState.endStreaming();
            InputUI.setStopButtonState(stopButton, { visible: false });
            throw error;
        },
        shouldStop: () => !chatState.isStreamingNow()
    };
};

