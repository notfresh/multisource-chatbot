// 聊天界面 JavaScript - v0 版本

const API_BASE = '/api';

let currentConversationId = null;
let currentAbortController = null; // 用于中断流式请求
let isStreaming = false; // 是否正在流式输出

// DOM 元素
const conversationList = document.getElementById('conversationList');
const chatMessages = document.getElementById('chatMessages');
const welcomeMessage = document.getElementById('welcomeMessage');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const stopButton = document.getElementById('stopButton');
const btnNewConversation = document.getElementById('btnNewConversation');

// 初始化
document.addEventListener('DOMContentLoaded', function() {
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
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
    });
});

// 加载会话列表
async function loadConversations() {
    try {
        const response = await fetch(`${API_BASE}/conversations`);
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/auth/login';
                return;
            }
            throw new Error('加载会话列表失败');
        }
        
        const conversations = await response.json();
        renderConversationList(conversations);
        
        // 如果有会话，默认加载第一个
        if (conversations.length > 0 && !currentConversationId) {
            loadConversation(conversations[0].id);
        }
    } catch (error) {
        console.error('加载会话列表失败:', error);
        showError('加载会话列表失败: ' + error.message);
    }
}

// 渲染会话列表
function renderConversationList(conversations) {
    conversationList.innerHTML = '';
    
    if (conversations.length === 0) {
        conversationList.innerHTML = '<div style="padding: 20px; text-align: center; color: #8e8ea0;">暂无会话</div>';
        return;
    }
    
    conversations.forEach(conv => {
        const item = document.createElement('div');
        item.className = 'conversation-item';
        if (conv.id === currentConversationId) {
            item.classList.add('active');
        }
        
        const title = document.createElement('div');
        title.className = 'conversation-title';
        title.textContent = conv.title || '新对话';
        
        const meta = document.createElement('div');
        meta.className = 'conversation-meta';
        meta.textContent = `${conv.message_count} 条消息`;
        
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete-btn';
        deleteBtn.textContent = '×';
        deleteBtn.onclick = (e) => {
            e.stopPropagation();
            deleteConversation(conv.id);
        };
        
        item.appendChild(title);
        item.appendChild(meta);
        item.appendChild(deleteBtn);
        
        item.onclick = () => loadConversation(conv.id);
        
        conversationList.appendChild(item);
    });
}

// 加载会话详情
async function loadConversation(conversationId) {
    try {
        currentConversationId = conversationId;
        
        const response = await fetch(`${API_BASE}/conversations/${conversationId}`);
        if (!response.ok) {
            throw new Error('加载会话失败');
        }
        
        const conversation = await response.json();
        renderMessages(conversation.messages);
        
        // 更新会话列表的激活状态
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
        });
        const activeItem = Array.from(document.querySelectorAll('.conversation-item'))
            .find(item => item.onclick && item.onclick.toString().includes(conversationId));
        if (activeItem) {
            activeItem.classList.add('active');
        }
        
        // 滚动到底部
        scrollToBottom();
        
        // 重新加载会话列表以更新消息数量
        loadConversations();
    } catch (error) {
        console.error('加载会话失败:', error);
        showError('加载会话失败: ' + error.message);
    }
}

// 渲染消息列表
function renderMessages(messages) {
    chatMessages.innerHTML = '';
    welcomeMessage.style.display = 'none';
    
    if (messages.length === 0) {
        welcomeMessage.style.display = 'block';
        return;
    }
    
    // 将消息组织成结构化的形式：将同一用户消息对应的多个assistant消息组织在一起
    const organizedMessages = organizeMessages(messages);
    
    organizedMessages.forEach(msg => {
        const messageDiv = createMessageElement(msg);
        chatMessages.appendChild(messageDiv);
    });
    
    scrollToBottom();
}

// 组织消息：将同一用户消息对应的多个assistant消息组织在一起
function organizeMessages(messages) {
    const organized = [];
    let currentUserMessage = null;
    let currentAssistantMessages = [];
    
    for (const msg of messages) {
        if (msg.role === 'user') {
            // 如果之前有用户消息，先保存它和对应的assistant消息
            if (currentUserMessage) {
                organized.push(currentUserMessage);
                // 将assistant消息组织成主消息和替代回答
                if (currentAssistantMessages.length > 0) {
                    // 优先选择deepseek-chat作为主消息，如果没有则选择第一个
                    let mainAssistant = currentAssistantMessages.find(
                        m => m.model === 'deepseek-chat' || !m.model
                    );
                    if (!mainAssistant) {
                        mainAssistant = currentAssistantMessages[0];
                    }
                    
                    // 其他assistant消息作为alternative_responses
                    const alternativeResponses = currentAssistantMessages.filter(
                        m => m.id !== mainAssistant.id
                    );
                    
                    if (alternativeResponses.length > 0) {
                        mainAssistant.alternative_responses = alternativeResponses;
                    }
                    
                    organized.push(mainAssistant);
                }
            }
            // 开始新的用户消息
            currentUserMessage = msg;
            currentAssistantMessages = [];
        } else if (msg.role === 'assistant') {
            // 将assistant消息添加到当前组
            currentAssistantMessages.push(msg);
        }
    }
    
    // 处理最后一条用户消息
    if (currentUserMessage) {
        organized.push(currentUserMessage);
        if (currentAssistantMessages.length > 0) {
            // 优先选择deepseek-chat作为主消息
            let mainAssistant = currentAssistantMessages.find(
                m => m.model === 'deepseek-chat' || !m.model
            );
            if (!mainAssistant) {
                mainAssistant = currentAssistantMessages[0];
            }
            
            const alternativeResponses = currentAssistantMessages.filter(
                m => m.id !== mainAssistant.id
            );
            
            if (alternativeResponses.length > 0) {
                mainAssistant.alternative_responses = alternativeResponses;
            }
            
            organized.push(mainAssistant);
        }
    }
    
    return organized;
}

// 消息组件实例存储（用于流式输出时更新内容）
const messageComponentMap = new WeakMap();

// 创建消息元素
// 内部使用 MessageComponent，但保持接口不变（返回 DOM 元素）
function createMessageElement(msg) {
    // 使用组件创建消息
    const messageComponent = new MessageComponent({
        message: msg
    });
    
    const messageDiv = messageComponent.getElement();
    
    // 将组件实例存储到 DOM 元素上，方便后续访问
    messageComponentMap.set(messageDiv, messageComponent);
    
    return messageDiv;
}

// 发送消息
async function sendMessage() {
    const content = messageInput.value.trim();
    if (!content) {
        return;
    }
    
    if (!currentConversationId) {
        // 如果没有当前会话，先创建一个
        try {
            const response = await fetch(`${API_BASE}/conversations`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ title: '新对话' })
            });
            
            if (!response.ok) {
                if (response.status === 401 || response.status === 403) {
                    window.location.href = '/auth/login';
                    return;
                }
                const contentType = response.headers.get('content-type');
                let errorMessage = '创建会话失败';
                if (contentType && contentType.includes('application/json')) {
                    try {
                        const error = await response.json();
                        errorMessage = error.error || error.message || errorMessage;
                    } catch (e) {
                        // JSON 解析失败
                    }
                }
                throw new Error(errorMessage);
            }
            
            const conversation = await response.json();
            currentConversationId = conversation.id;
            
            // 清空消息区域并隐藏欢迎消息
            chatMessages.innerHTML = '';
            welcomeMessage.style.display = 'none';
            
            // 重新加载会话列表
            loadConversations();
        } catch (error) {
            console.error('创建会话失败:', error);
            showError('创建会话失败: ' + error.message);
            return;
        }
    }
    
    // 禁用输入和按钮
    messageInput.disabled = true;
    sendButton.disabled = true;
    
    // 显示用户消息
    const userMessage = {
        role: 'user',
        content: content,
        created_at: new Date().toISOString()
    };
    const userMessageDiv = createMessageElement(userMessage);
    chatMessages.appendChild(userMessageDiv);
    messageInput.value = '';
    messageInput.style.height = 'auto';
    scrollToBottom();
    
    // 创建AI消息容器（用于流式显示）
    const aiMessage = {
        role: 'assistant',
        content: '',
        created_at: new Date().toISOString()
    };
    const aiMessageDiv = createMessageElement(aiMessage);
    // 获取组件实例，用于流式更新
    const aiMessageComponent = messageComponentMap.get(aiMessageDiv);
    chatMessages.appendChild(aiMessageDiv);
    scrollToBottom();
    
    // 显示停止按钮
    stopButton.style.display = 'block';
    stopButton.textContent = '⏹ 停止';
    stopButton.disabled = false;
    
    // 创建 AbortController 用于中断请求
    currentAbortController = new AbortController();
    isStreaming = true;
    
    try {
        const response = await fetch(`${API_BASE}/conversations/${currentConversationId}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content: content }),
            signal: currentAbortController.signal // 添加中断信号
        });
        
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/auth/login';
                return;
            }
            // 检查响应是否为 JSON
            const contentType = response.headers.get('content-type');
            let errorMessage = '发送消息失败';
            if (contentType && contentType.includes('application/json')) {
                try {
                    const error = await response.json();
                    errorMessage = error.error || error.message || errorMessage;
                } catch (e) {
                    // JSON 解析失败，使用默认错误消息
                }
            } else {
                // 非 JSON 响应（可能是 HTML 错误页面）
                errorMessage = `服务器错误 (${response.status}): 请检查会话是否存在`;
            }
            throw new Error(errorMessage);
        }
        
        // 处理流式响应
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullContent = ''; // 保存完整内容，用于停止时保存
        
        try {
            while (true) {
                const { done, value } = await reader.read();
                
                // 检查是否已停止
                if (!isStreaming) {
                    reader.cancel();
                    break;
                }
                
                if (done) {
                    // 流式输出结束，即使没有收到 done 事件也要重置状态
                    console.log('流式输出结束（连接已关闭）');
                    isStreaming = false;
                    stopButton.style.display = 'none';
                    
                    // 确保最终内容已更新
                    if (aiMessageComponent && fullContent) {
                        aiMessageComponent.updateContent(fullContent);
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
                                // 追加内容到AI消息
                                fullContent += data.chunk;
                                
                                // 使用组件更新内容
                                if (aiMessageComponent) {
                                    aiMessageComponent.updateContent(fullContent);
                                }
                                
                                scrollToBottom();
                            } else if (data.type === 'done') {
                                // 流式输出完成
                                console.log('流式输出完成，消息ID:', data.message_id);
                                isStreaming = false;
                                // 隐藏停止按钮
                                stopButton.style.display = 'none';
                                
                                // 确保最终内容已更新（组件内部已处理）
                                if (aiMessageComponent && fullContent) {
                                    aiMessageComponent.updateContent(fullContent);
                                }
                            } else if (data.type === 'error') {
                                throw new Error(data.error);
                            }
                        } catch (e) {
                            console.error('解析流式数据失败:', e);
                        }
                    }
                }
            }
        } catch (readError) {
            // 如果是用户主动中断，不显示错误
            if (readError.name === 'AbortError' || !isStreaming) {
                console.log('流式输出已中断');
                // 保存当前内容到数据库
                if (fullContent) {
                    await savePartialMessage(fullContent);
                }
            } else {
                throw readError;
            }
        }
        
        // 如果流式输出被中断，保存部分内容
        if (!isStreaming && fullContent) {
            await savePartialMessage(fullContent);
        }
        
        // 如果流式输出完成，重新加载会话列表
        if (!isStreaming) {
            loadConversations();
        }
        
    } catch (error) {
        // 如果是用户主动中断，不显示错误
        if (error.name === 'AbortError' || !isStreaming) {
            console.log('请求已中断');
        } else {
            console.error('发送消息失败:', error);
            showError('发送消息失败: ' + error.message);
            
            // 确保重置状态
            isStreaming = false;
            stopButton.style.display = 'none';
            
            // 移除用户消息和AI消息（因为发送失败）
            userMessageDiv.remove();
            aiMessageDiv.remove();
        }
    } finally {
        // 确保状态被重置（防止卡在"正在生成..."状态）
        isStreaming = false;
        stopButton.style.display = 'none';
        currentAbortController = null;
        
        // 恢复输入和按钮
        messageInput.disabled = false;
        sendButton.disabled = false;
        stopButton.style.display = 'none';
        messageInput.focus();
        currentAbortController = null;
    }
}

// 创建新会话
async function createNewConversation() {
    try {
        const response = await fetch(`${API_BASE}/conversations`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ title: '新对话' })
        });
        
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/auth/login';
                return;
            }
            throw new Error('创建会话失败');
        }
        
        const conversation = await response.json();
        currentConversationId = conversation.id;
        
        // 清空消息区域
        chatMessages.innerHTML = '';
        welcomeMessage.style.display = 'block';
        
        // 重新加载会话列表
        loadConversations();
        
        // 聚焦输入框
        messageInput.focus();
    } catch (error) {
        console.error('创建会话失败:', error);
        showError('创建会话失败: ' + error.message);
    }
}

// 删除会话
async function deleteConversation(conversationId) {
    if (!confirm('确定要删除这个会话吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/conversations/${conversationId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('删除会话失败');
        }
        
        // 如果删除的是当前会话，清空消息区域
        if (conversationId === currentConversationId) {
            currentConversationId = null;
            chatMessages.innerHTML = '';
            welcomeMessage.style.display = 'block';
        }
        
        // 重新加载会话列表
        loadConversations();
    } catch (error) {
        console.error('删除会话失败:', error);
        showError('删除会话失败: ' + error.message);
    }
}

// 滚动到底部
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 停止流式输出（打断吐字）
function stopStreaming() {
    if (isStreaming && currentAbortController) {
        isStreaming = false;
        currentAbortController.abort();
        
        // 更新停止按钮
        stopButton.textContent = '已停止';
        stopButton.disabled = true;
    }
}

// 保存部分消息到数据库
async function savePartialMessage(content) {
    if (!content || !currentConversationId) {
        return;
    }
    
    try {
        // 调用API保存部分消息
        const response = await fetch(`${API_BASE}/conversations/${currentConversationId}/messages/partial`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content: content })
        });
        
        if (response.ok) {
            console.log('部分消息已保存');
            loadConversations();
        }
    } catch (error) {
        console.error('保存部分消息失败:', error);
    }
}

// 显示错误消息
function showError(message) {
    alert(message);
}

// 按需查询另一个模型的回答
async function requestAlternativeModel(messageId, modelName, messageComponent) {
    if (!currentConversationId || !messageId) {
        console.error('缺少必要参数');
        return;
    }
    
    // 如果没有传入messageComponent，尝试通过messageId找到它
    if (!messageComponent) {
        const messageDiv = document.querySelector(`[data-message-id="${messageId}"]`);
        if (messageDiv) {
            messageComponent = messageComponentMap.get(messageDiv);
        }
    }
    
    if (!messageComponent) {
        console.error('找不到对应的消息组件');
        showError('找不到对应的消息，请刷新页面后重试');
        return;
    }
    
    // 创建替代回答的容器（如果还没有）
    const altResponse = {
        model: modelName,
        content: '',
        id: null
    };
    
    // 在消息组件中添加替代回答区域（初始为空）
    messageComponent.addAlternativeResponse(altResponse);
    
    // 显示停止按钮
    stopButton.style.display = 'block';
    stopButton.textContent = '⏹ 停止';
    stopButton.disabled = false;
    
    // 创建 AbortController 用于中断请求
    currentAbortController = new AbortController();
    isStreaming = true;
    
    try {
        const response = await fetch(
            `${API_BASE}/conversations/${currentConversationId}/messages/${messageId}/alternative`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ model: modelName }),
                signal: currentAbortController.signal
            }
        );
        
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/auth/login';
                return;
            }
            const contentType = response.headers.get('content-type');
            let errorMessage = '按需查询失败';
            if (contentType && contentType.includes('application/json')) {
                try {
                    const error = await response.json();
                    errorMessage = error.error || error.message || errorMessage;
                } catch (e) {
                    // JSON 解析失败
                }
            }
            throw new Error(errorMessage);
        }
        
        // 处理流式响应
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullContent = '';
        
        try {
            while (true) {
                const { done, value } = await reader.read();
                
                // 检查是否已停止
                if (!isStreaming) {
                    reader.cancel();
                    break;
                }
                
                if (done) {
                    // 流式输出结束，即使没有收到 done 事件也要重置状态
                    console.log('按需查询结束（连接已关闭）');
                    isStreaming = false;
                    stopButton.style.display = 'none';
                    
                    // 确保最终内容已更新
                    if (messageComponent && fullContent) {
                        altResponse.content = fullContent;
                        messageComponent.updateAlternativeResponse(modelName, fullContent);
                        messageComponent.addAlternativeResponse(altResponse);
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
                                // 追加内容到替代回答
                                fullContent += data.chunk;
                                
                                // 更新消息组件的替代回答内容
                                if (messageComponent) {
                                    messageComponent.updateAlternativeResponse(modelName, fullContent);
                                }
                                
                                scrollToBottom();
                            } else if (data.type === 'done') {
                                // 流式输出完成
                                console.log('按需查询完成，消息ID:', data.message_id);
                                isStreaming = false;
                                stopButton.style.display = 'none';
                                
                                // 更新替代回答的ID
                                altResponse.id = data.message_id;
                                altResponse.content = fullContent;
                                
                                // 确保最终内容已更新
                                if (messageComponent && fullContent) {
                                    messageComponent.updateAlternativeResponse(modelName, fullContent);
                                    // 更新消息对象中的alternative_responses
                                    messageComponent.addAlternativeResponse(altResponse);
                                }
                                
                                // 重新加载会话列表
                                loadConversations();
                            } else if (data.type === 'error') {
                                throw new Error(data.error);
                            }
                        } catch (e) {
                            console.error('解析流式数据失败:', e);
                        }
                    }
                }
            }
        } catch (readError) {
            // 如果是用户主动中断，不显示错误
            if (readError.name === 'AbortError' || !isStreaming) {
                console.log('按需查询已中断');
                // 保存当前内容
                if (fullContent) {
                    altResponse.content = fullContent;
                    if (messageComponent) {
                        messageComponent.addAlternativeResponse(altResponse);
                    }
                }
            } else {
                throw readError;
            }
        }
        
    } catch (error) {
        // 如果是用户主动中断，不显示错误
        if (error.name === 'AbortError' || !isStreaming) {
            console.log('按需查询已中断');
        } else {
            console.error('按需查询失败:', error);
            showError('按需查询失败: ' + error.message);
            
            // 移除替代回答区域（如果创建失败）
            // 这里可以添加错误提示
        }
    } finally {
        // 恢复按钮状态
        stopButton.style.display = 'none';
        currentAbortController = null;
        isStreaming = false;
    }
}

