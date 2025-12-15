/**
 * 消息组织工具
 * 职责：将消息组织成结构化的形式（Peer 架构）
 */

// 使用全局命名空间
window.MessageOrganizer = window.MessageOrganizer || {};

/**
 * 组织消息：将同一用户消息对应的多个assistant消息组织在一起（对等 Peer 架构）
 * @param {Array} messages - 原始消息列表
 * @returns {Array} - 组织后的消息列表
 */
MessageOrganizer.organizeMessages = function(messages) {
    const organized = [];
    let currentUserMessage = null;
    let currentAssistantMessages = [];
    
    for (const msg of messages) {
        if (msg.role === 'user') {
            // 如果之前有用户消息，先保存它和对应的assistant消息
            if (currentUserMessage) {
                organized.push(currentUserMessage);
                // 将所有assistant消息作为对等的peer组织在一起
                if (currentAssistantMessages.length > 0) {
                    // 优先选择deepseek-chat作为第一个（默认展开），如果没有则选择第一个
                    let defaultAssistant = currentAssistantMessages.find(
                        m => m.model === 'deepseek-chat' || !m.model
                    );
                    if (!defaultAssistant) {
                        defaultAssistant = currentAssistantMessages[0];
                    }
                    
                    // 将其他assistant消息作为alternative_responses
                    const otherResponses = currentAssistantMessages.filter(
                        m => m.id !== defaultAssistant.id
                    );
                    
                    // 设置alternative_responses（所有对等的peer）
                    if (otherResponses.length > 0) {
                        defaultAssistant.alternative_responses = otherResponses;
                    }
                    
                    organized.push(defaultAssistant);
                }
            }
            // 开始新的用户消息
            currentUserMessage = msg;
            currentAssistantMessages = [];
        } else if (msg.role === 'assistant') {
            // 将assistant消息添加到当前组（所有都是对等的）
            currentAssistantMessages.push(msg);
        }
    }
    
    // 处理最后一条用户消息
    if (currentUserMessage) {
        organized.push(currentUserMessage);
        if (currentAssistantMessages.length > 0) {
            // 优先选择deepseek-chat作为第一个（默认展开）
            let defaultAssistant = currentAssistantMessages.find(
                m => m.model === 'deepseek-chat' || !m.model
            );
            if (!defaultAssistant) {
                defaultAssistant = currentAssistantMessages[0];
            }
            
            const otherResponses = currentAssistantMessages.filter(
                m => m.id !== defaultAssistant.id
            );
            
            if (otherResponses.length > 0) {
                defaultAssistant.alternative_responses = otherResponses;
            }
            
            organized.push(defaultAssistant);
        }
    }
    
    return organized;
}

