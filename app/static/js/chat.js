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
    
    messages.forEach(msg => {
        const messageDiv = createMessageElement(msg);
        chatMessages.appendChild(messageDiv);
    });
    
    scrollToBottom();
}

// 创建消息元素
function createMessageElement(msg) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${msg.role}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = msg.role === 'user' ? 'U' : 'AI';
    
    const contentWrapper = document.createElement('div');
    contentWrapper.className = 'message-content-wrapper';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    // 保存原始内容
    const originalContent = msg.content;
    // 将原始内容存储到数据属性中，方便切换按钮访问
    messageDiv.dataset.originalContent = originalContent;
    
    // 使用 Markdown 渲染器渲染内容
    if (typeof renderMarkdown !== 'undefined') {
        content.innerHTML = renderMarkdown(originalContent);
        // 如果是 Markdown 内容，添加 markdown 类名用于样式
        if (containsMarkdown && containsMarkdown(originalContent)) {
            content.classList.add('markdown-content');
        }
    } else {
        // 如果 Markdown 渲染器未加载，使用纯文本
        content.textContent = originalContent;
    }
    
    contentWrapper.appendChild(content);
    
    // 添加切换按钮（只在有 markdown 内容时显示）
    const hasMarkdown = typeof containsMarkdown !== 'undefined' && containsMarkdown(originalContent);
    if (hasMarkdown) {
        const toggleWrapper = document.createElement('div');
        toggleWrapper.className = 'message-toggle-wrapper';
        
        const toggleButton = document.createElement('button');
        toggleButton.className = 'message-toggle-btn';
        toggleButton.textContent = '📝 查看 Markdown';
        toggleButton.title = '切换显示 Markdown 原始文本';
        
        toggleButton.addEventListener('click', function() {
            const originalContent = messageDiv.dataset.originalContent || '';
            const contentDiv = messageDiv.querySelector('.message-content');
            const isRendered = contentDiv.classList.contains('markdown-content');
            
            if (isRendered) {
                // 切换到 Markdown 原始文本
                contentDiv.textContent = originalContent;
                contentDiv.classList.remove('markdown-content');
                toggleButton.textContent = '👁 查看渲染';
                toggleButton.title = '切换显示渲染后的内容';
            } else {
                // 切换到渲染后的内容
                contentDiv.innerHTML = renderMarkdown(originalContent);
                if (containsMarkdown && containsMarkdown(originalContent)) {
                    contentDiv.classList.add('markdown-content');
                }
                toggleButton.textContent = '📝 查看 Markdown';
                toggleButton.title = '切换显示 Markdown 原始文本';
            }
        });
        
        toggleWrapper.appendChild(toggleButton);
        contentWrapper.appendChild(toggleWrapper);
    }
    
    const time = document.createElement('div');
    time.className = 'message-time';
    if (msg.created_at) {
        const date = new Date(msg.created_at);
        time.textContent = date.toLocaleString('zh-CN');
    }
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentWrapper);
    messageDiv.appendChild(time);
    
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
    const aiContentDiv = aiMessageDiv.querySelector('.message-content');
    const aiContentWrapper = aiMessageDiv.querySelector('.message-content-wrapper');
    let aiIsRendered = true; // AI消息当前是否显示渲染后的内容
    // 将原始内容存储到数据属性中，方便切换按钮访问
    aiMessageDiv.dataset.originalContent = '';
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
                if (done) break;
                
                // 检查是否已停止
                if (!isStreaming) {
                    reader.cancel();
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
                                // 更新数据属性中的原始内容
                                aiMessageDiv.dataset.originalContent = fullContent;
                                
                                // 如果当前显示的是渲染后的内容，则更新渲染
                                if (aiIsRendered) {
                                    // 使用 Markdown 渲染器实时更新内容
                                    if (typeof renderMarkdown !== 'undefined') {
                                        aiContentDiv.innerHTML = renderMarkdown(fullContent);
                                        if (containsMarkdown && containsMarkdown(fullContent)) {
                                            aiContentDiv.classList.add('markdown-content');
                                            // 如果之前没有切换按钮，现在有了 markdown，需要添加切换按钮
                                            if (!aiMessageDiv.querySelector('.message-toggle-wrapper') && aiContentWrapper) {
                                                const toggleWrapper = document.createElement('div');
                                                toggleWrapper.className = 'message-toggle-wrapper';
                                                
                                                const toggleButton = document.createElement('button');
                                                toggleButton.className = 'message-toggle-btn';
                                                toggleButton.textContent = '📝 查看 Markdown';
                                                toggleButton.title = '切换显示 Markdown 原始文本';
                                                
                                                toggleButton.addEventListener('click', function() {
                                                    const originalContent = aiMessageDiv.dataset.originalContent || '';
                                                    const contentDiv = aiMessageDiv.querySelector('.message-content');
                                                    const isRendered = contentDiv.classList.contains('markdown-content');
                                                    
                                                    if (isRendered) {
                                                        // 切换到 Markdown 原始文本
                                                        contentDiv.textContent = originalContent;
                                                        contentDiv.classList.remove('markdown-content');
                                                        toggleButton.textContent = '👁 查看渲染';
                                                        toggleButton.title = '切换显示渲染后的内容';
                                                    } else {
                                                        // 切换到渲染后的内容
                                                        contentDiv.innerHTML = renderMarkdown(originalContent);
                                                        if (containsMarkdown && containsMarkdown(originalContent)) {
                                                            contentDiv.classList.add('markdown-content');
                                                        }
                                                        toggleButton.textContent = '📝 查看 Markdown';
                                                        toggleButton.title = '切换显示 Markdown 原始文本';
                                                    }
                                                });
                                                
                                                toggleWrapper.appendChild(toggleButton);
                                                aiContentWrapper.appendChild(toggleWrapper);
                                            }
                                        }
                                    } else {
                                        aiContentDiv.textContent = fullContent;
                                    }
                                } else {
                                    // 如果当前显示的是原始文本，直接更新文本
                                    aiContentDiv.textContent = fullContent;
                                }
                                scrollToBottom();
                            } else if (data.type === 'done') {
                                // 流式输出完成
                                console.log('流式输出完成，消息ID:', data.message_id);
                                isStreaming = false;
                                // 隐藏停止按钮
                                stopButton.style.display = 'none';
                                
                                // 确保最终内容已保存到数据属性
                                aiMessageDiv.dataset.originalContent = fullContent;
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
            
            // 移除用户消息和AI消息（因为发送失败）
            userMessageDiv.remove();
            aiMessageDiv.remove();
        }
    } finally {
        // 恢复输入和按钮
        messageInput.disabled = false;
        sendButton.disabled = false;
        // 隐藏停止按钮
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

