/**
 * 流式响应处理
 * 职责：处理所有流式响应的读取和解析逻辑
 */

// 使用全局命名空间
window.StreamHandler = window.StreamHandler || {};

/**
 * 处理流式响应
 * @param {ReadableStream} stream - 响应流
 * @param {Object} callbacks - 回调函数对象
 * @param {Function} callbacks.onChunk - 收到数据块时的回调 (content: string) => void
 * @param {Function} callbacks.onDone - 流式完成时的回调 (data: { messageId, fullContent }) => void
 * @param {Function} callbacks.onError - 错误回调 (error: Error) => void
 * @param {Function} callbacks.shouldStop - 是否应该停止 (() => boolean)
 * @returns {Promise<string>} - 完整内容
 */
StreamHandler.handleStream = async function(stream, callbacks) {
    const { onChunk, onDone, onError, shouldStop } = callbacks;
    const reader = stream.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullContent = '';
    
    try {
        while (true) {
            // 检查是否应该停止
            if (shouldStop && shouldStop()) {
                reader.cancel();
                break;
            }
            
            const { done, value } = await reader.read();
            
            if (done) {
                // 流式输出结束
                if (onDone && fullContent) {
                    onDone({ messageId: null, fullContent });
                }
                break;
            }
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // 保留最后一个不完整的行
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.type === 'chunk') {
                            // 追加内容
                            fullContent += data.chunk;
                            
                            // 调用 chunk 回调
                            if (onChunk) {
                                onChunk(fullContent);
                            }
                        } else if (data.type === 'done') {
                            // 流式输出完成
                            if (onDone) {
                                onDone({
                                    messageId: data.message_id,
                                    fullContent
                                });
                            }
                        } else if (data.type === 'error') {
                            // 服务器返回错误
                            if (onError) {
                                onError(new Error(data.error));
                            }
                        }
                    } catch (e) {
                        console.error('解析流式数据失败:', e);
                    }
                }
            }
        }
    } catch (readError) {
        if (readError.name === 'AbortError') {
            // 用户主动中断，不处理
            return fullContent;
        }
        
        if (onError) {
            onError(readError);
        } else {
            throw readError;
        }
    } finally {
        reader.releaseLock();
    }
    
    return fullContent;
}

