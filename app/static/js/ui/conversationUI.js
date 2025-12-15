/**
 * 会话列表 UI
 * 职责：处理会话列表的渲染和交互
 */

// 使用全局命名空间
window.ConversationUI = window.ConversationUI || {};

/**
 * 渲染会话列表
 * @param {HTMLElement} container - 容器元素
 * @param {Array} conversations - 会话列表
 * @param {number} currentConversationId - 当前会话ID
 * @param {Function} onSelect - 选择会话回调 (conversationId) => void
 * @param {Function} onDelete - 删除会话回调 (conversationId) => void
 */
ConversationUI.renderConversationList = function(container, conversations, currentConversationId, onSelect, onDelete) {
    container.innerHTML = '';
    
    if (conversations.length === 0) {
        container.innerHTML = '<div style="padding: 20px; text-align: center; color: #8e8ea0;">暂无会话</div>';
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
            onDelete(conv.id);
        };
        
        item.appendChild(title);
        item.appendChild(meta);
        item.appendChild(deleteBtn);
        
        item.onclick = () => onSelect(conv.id);
        
        container.appendChild(item);
    });
}

/**
 * 更新会话列表的激活状态
 * @param {HTMLElement} container - 容器元素
 * @param {number} conversationId - 要激活的会话ID
 */
ConversationUI.updateActiveConversation = function(container, conversationId) {
    container.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 找到对应的会话项并激活
    const items = Array.from(container.querySelectorAll('.conversation-item'));
    const activeItem = items.find(item => {
        const title = item.querySelector('.conversation-title');
        return title && item.onclick && item.onclick.toString().includes(conversationId);
    });
    
    if (activeItem) {
        activeItem.classList.add('active');
    }
}

