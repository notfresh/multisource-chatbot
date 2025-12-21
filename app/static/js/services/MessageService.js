/**
 * 消息服务
 * 职责：处理消息相关的业务逻辑
 */

// 使用全局命名空间
window.MessageService = window.MessageService || {};

/**
 * 组织消息：将同一用户消息对应的多个assistant消息组织在一起（对等 Peer 架构）
 * @param {Array} messages - 原始消息列表（按 order_index 排序）
 * @param {string} defaultModel - 默认模型名称（用于选择默认展开的回答），如果不提供则使用 ModelConfig.default
 * @returns {Array} - 组织后的消息列表
 * 
 * 转换示例：
 * 输入：[user1, assistant1(deepseek), assistant2(qwen), user2, assistant3(deepseek)]
 * 输出：[user1, assistant1(deepseek, alternative_responses: [assistant2]), user2, assistant3]
 */
MessageService.organizeMessages = function(messages, defaultModel = null) {
    // 如果没有提供默认模型，使用配置中的默认模型
    if (!defaultModel && typeof ModelConfig !== 'undefined') {
        defaultModel = ModelConfig.default || 'deepseek-chat';
    } else if (!defaultModel) {
        defaultModel = 'deepseek-chat'; // 兜底值
    }
    const organized = [];
    let currentUserMessage = null;
    let currentAssistantMessages = [];
    
    /**
     * 处理当前用户消息和对应的assistant消息
     * @param {Object} userMsg - 用户消息
     * @param {Array} assistantMsgs - assistant消息列表
     */
    const processUserAndAssistants = (userMsg, assistantMsgs) => {
        if (userMsg) {
            organized.push(userMsg);
            
            if (assistantMsgs.length > 0) {
                // 优先选择默认模型作为第一个（默认展开），如果没有则选择第一个
                let defaultAssistant = assistantMsgs.find(
                    m => m.model === defaultModel || !m.model
                );
                if (!defaultAssistant) {
                    defaultAssistant = assistantMsgs[0];
                }
                
                // 将其他assistant消息作为alternative_responses
                const otherResponses = assistantMsgs.filter(
                    m => m.id !== defaultAssistant.id
                );
                
                if (otherResponses.length > 0) {
                    defaultAssistant.alternative_responses = otherResponses;
                }
                
                organized.push(defaultAssistant);
            }
        }
    };
    
    // 遍历所有消息
    for (const msg of messages) {
        if (msg.role === 'user') {
            // 如果之前有用户消息，先处理它和对应的assistant消息
            processUserAndAssistants(currentUserMessage, currentAssistantMessages);
            
            // 开始新的用户消息
            currentUserMessage = msg;
            currentAssistantMessages = [];
        } else if (msg.role === 'assistant') {
            // 将assistant消息添加到当前组（所有都是对等的）
            currentAssistantMessages.push(msg);
        }
    }
    
    // 处理最后一条用户消息
    processUserAndAssistants(currentUserMessage, currentAssistantMessages);
    
    return organized;
};

