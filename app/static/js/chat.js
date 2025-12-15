/**
 * 聊天界面主入口
 * 职责：组装所有模块，处理事件绑定和业务逻辑协调
 * 
 * 注意：由于使用传统 script 标签加载，模块通过全局命名空间访问
 * 需要在模板中按顺序加载所有依赖模块
 */

// ==================== DOM 元素（在 DOMContentLoaded 中初始化）====================
let conversationList;
let chatMessages;
let welcomeMessage;
let messageInput;
let sendButton;
let stopButton;
let btnNewConversation;

// ==================== 业务逻辑函数 ====================

/**
 * 加载会话列表
 */
async function loadConversations() {
    try {
        const conversations = await ConversationAPI.getConversations();
        if (!conversations) return;
        
        ConversationUI.renderConversationList(
            conversationList,
            conversations,
            chatState.getConversationId(),
            handleConversationSelect,
            handleConversationDelete
        );
        
        // 如果有会话，默认加载第一个
        if (conversations.length > 0 && !chatState.getConversationId()) {
            await loadConversation(conversations[0].id);
        }
    } catch (error) {
        console.error('加载会话列表失败:', error);
        MessageUI.showError('加载会话列表失败: ' + error.message);
    }
}

/**
 * 加载会话详情
 */
async function loadConversation(conversationId) {
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
        loadConversations();
    } catch (error) {
        console.error('加载会话失败:', error);
        MessageUI.showError('加载会话失败: ' + error.message);
    }
}

/**
 * 处理会话选择
 */
function handleConversationSelect(conversationId) {
    loadConversation(conversationId);
}

/**
 * 处理会话删除
 */
async function handleConversationDelete(conversationId) {
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
        loadConversations();
    } catch (error) {
        console.error('删除会话失败:', error);
        MessageUI.showError('删除会话失败: ' + error.message);
    }
}

/**
 * 确保有会话ID（如果没有则创建）
 */
async function ensureConversationId() {
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
        loadConversations();
    }
    
    return conversationId;
}

/**
 * 处理发送消息的错误
 * @private
 */
async function handleSendMessageError(error, response, conversationId, userMessageDiv, aiMessageDiv) {
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
                    loadConversations();
                }
            } catch (e) {
                console.error('保存部分消息失败:', e);
            }
    } else {
        console.error('发送消息失败:', error);
        MessageUI.showError('发送消息失败: ' + error.message);
        
        // 移除用户消息和AI消息（因为发送失败）
        if (userMessageDiv) userMessageDiv.remove();
        if (aiMessageDiv) aiMessageDiv.remove();
    }
}

/**
 * 发送消息
 */
async function sendMessage() {
    const content = messageInput.value.trim();
    if (!content) {
        return;
    }
    
    // 确保有会话ID
    const conversationId = await ensureConversationId();
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
        model: 'deepseek-chat',
        created_at: new Date().toISOString()
    };
    const aiMessageDiv = MessageUI.createMessageElement(aiMessage);
    const aiMessageComponent = MessageUI.getMessageComponent(aiMessageDiv);
    chatMessages.appendChild(aiMessageDiv);
    MessageUI.scrollToBottom(chatMessages);
    
    // 显示停止按钮
    InputUI.setStopButtonState(stopButton, { visible: true, disabled: false });
    
    // 开始流式输出
    const abortController = chatState.startStreaming();
    
    try {
        // 发送消息并获取流式响应
        const response = await MessageAPI.sendMessage(
            conversationId,
            content,
            abortController.signal
        );
        
        if (!response) return;
        
        // 处理流式响应
        await StreamingService.handleStreaming(response.body, 
            StreamingService.createSendMessageCallbacks({
                aiMessageComponent,
                aiMessageDiv,
                chatMessages,
                stopButton,
                onComplete: () => loadConversations()
            })
        );
        
    } catch (error) {
        // 处理错误
        await handleSendMessageError(error, response, conversationId, userMessageDiv, aiMessageDiv);
    } finally {
        // 确保状态被重置
        chatState.endStreaming();
        InputUI.setStopButtonState(stopButton, { visible: false });
        InputUI.setInputEnabled(messageInput, sendButton, stopButton, true);
    }
}

/**
 * 创建新会话
 */
async function createNewConversation() {
    try {
        const conversation = await ConversationAPI.createConversation('新对话');
        if (!conversation) return;
        
        chatState.setConversationId(conversation.id);
        
        // 清空消息区域
        chatMessages.innerHTML = '';
        welcomeMessage.style.display = 'block';
        
        // 重新加载会话列表
        loadConversations();
        
        // 聚焦输入框
        messageInput.focus();
    } catch (error) {
        console.error('创建会话失败:', error);
        MessageUI.showError('创建会话失败: ' + error.message);
    }
}

/**
 * 停止流式输出
 */
function stopStreaming() {
    if (chatState.isStreamingNow()) {
        chatState.stopStreaming();
        InputUI.setStopButtonState(stopButton, { visible: true, disabled: true, text: '已停止' });
    }
}

/**
 * 按需请求模型回答
 */
async function requestModelResponse(messageId, modelName, messageComponent) {
    return requestAlternativeModel(messageId, modelName, messageComponent);
}

/**
 * 处理按需请求模型回答的错误
 * @private
 */
function handleRequestModelError(error, messageComponent, modelResponse) {
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
 * 按需查询另一个模型的回答
 */
async function requestAlternativeModel(messageId, modelName, messageComponent) {
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
                onComplete: () => loadConversations()
            })
        );
        
    } catch (error) {
        // 处理错误
        handleRequestModelError(error, messageComponent, modelResponse);
    } finally {
        // 恢复按钮状态
        chatState.endStreaming();
        InputUI.setStopButtonState(stopButton, { visible: false });
    }
}

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', function() {
    // 检查必要的全局对象是否已加载
    const requiredModules = {
        'ConversationAPI': typeof window.ConversationAPI !== 'undefined',
        'MessageAPI': typeof window.MessageAPI !== 'undefined',
        'ConversationUI': typeof window.ConversationUI !== 'undefined',
        'MessageUI': typeof window.MessageUI !== 'undefined',
        'InputUI': typeof window.InputUI !== 'undefined',
        'StreamingService': typeof window.StreamingService !== 'undefined',
        'StreamHandler': typeof window.StreamHandler !== 'undefined',
        'chatState': typeof window.chatState !== 'undefined',
        'MessageOrganizer': typeof window.MessageOrganizer !== 'undefined'
    };
    
    // 调试信息：显示所有模块的加载状态
    console.log('模块加载状态:', requiredModules);
    
    const missingModules = Object.entries(requiredModules)
        .filter(([name, loaded]) => !loaded)
        .map(([name]) => name);
    
    if (missingModules.length > 0) {
        console.error('缺少必要的模块:', missingModules);
        console.error('当前 window 对象上的属性:', Object.keys(window).filter(k => k.includes('API') || k.includes('UI') || k.includes('Service') || k.includes('Handler') || k === 'chatState' || k.includes('Organizer')));
        alert('页面加载失败：缺少必要的模块。请刷新页面重试。\n缺少的模块: ' + missingModules.join(', '));
        return;
    }
    
    // 初始化 DOM 元素引用
    conversationList = document.getElementById('conversationList');
    chatMessages = document.getElementById('chatMessages');
    welcomeMessage = document.getElementById('welcomeMessage');
    messageInput = document.getElementById('messageInput');
    sendButton = document.getElementById('sendButton');
    stopButton = document.getElementById('stopButton');
    btnNewConversation = document.getElementById('btnNewConversation');
    
    // 检查必要的 DOM 元素是否存在
    if (!conversationList || !chatMessages || !welcomeMessage || 
        !messageInput || !sendButton || !stopButton || !btnNewConversation) {
        console.error('无法找到必要的 DOM 元素，请检查 HTML 结构');
        return;
    }
    
    // 加载会话列表
    loadConversations();
    
    // 事件监听
    sendButton.addEventListener('click', sendMessage);
    stopButton.addEventListener('click', stopStreaming);
    btnNewConversation.addEventListener('click', createNewConversation);
    
    // Enter 发送，Shift+Enter 换行
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 自动调整输入框高度
    messageInput.addEventListener('input', function() {
        InputUI.autoResizeInput(this);
    });
});
