/**
 * 消息组件
 * 业务层：协调所有子组件和服务，表达完整的消息组件
 */

class MessageComponent {
    /**
     * 构造函数
     * @param {Object} config - 配置对象
     * @param {Object} config.message - 消息数据
     * @param {Array} config.actions - 自定义操作按钮配置
     * @param {Function} config.onAction - 操作回调函数
     */
    constructor(config = {}) {
        // 创建领域模型
        this.message = new Message(config.message || {});
        
        // 初始化组件和服务
        this.contentRenderer = new ContentRenderer();
        this.actionBar = new ActionBar();
        this.modelManager = null;
        this.modelSelector = null;
        
        // 如果是助手消息，初始化模型管理器
        if (this.message.isAssistant()) {
            this.modelManager = new ModelResponseManager();
            this.modelSelector = new ModelSelector(
                ModelConfig.available,
                (model, action) => this.handleModelSelect(model, action)
            );
        }
        
        // 自定义操作和回调
        this.customActions = config.actions || [];
        this.onAction = config.onAction || null;
        
        // DOM 元素引用
        this.rootElement = null;
    }
    
    /**
     * 渲染主入口
     * @returns {HTMLElement}
     */
    render() {
        if (this.rootElement) {
            return this.rootElement;
        }
        
        // 创建根元素
        this.rootElement = DOMUtils.createElement('div', {
            className: `message ${this.message.role}`,
            dataset: {
                messageId: this.message.id || '',
                originalContent: this.message.content || ''
            }
        });
        
        // 添加头像
        const avatar = this.createAvatar();
        DOMUtils.append(this.rootElement, avatar);
        
        // 添加内容区域
        const contentWrapper = this.createContentWrapper();
        DOMUtils.append(this.rootElement, contentWrapper);
        
        // 添加时间戳
        const time = this.createTime();
        if (time) {
            DOMUtils.append(this.rootElement, time);
        }
        
        return this.rootElement;
    }
    
    /**
     * 创建内容区域
     * @returns {HTMLElement}
     */
    createContentWrapper() {
        const wrapper = DOMUtils.createElement('div', {
            className: 'message-content-wrapper'
        });
        
        if (this.message.isUser()) {
            // 用户消息：简单渲染
            this.renderUserMessage(wrapper);
        } else {
            // 助手消息：多模型回答
            this.renderAssistantMessage(wrapper);
        }
        
        // 添加操作栏
        const actionBar = this.actionBar.render();
        DOMUtils.append(wrapper, actionBar);
        
        // 初始化默认操作按钮
        this.initDefaultActions();
        
        return wrapper;
    }
    
    /**
     * 渲染用户消息
     * @param {HTMLElement} wrapper - 内容包装器
     */
    renderUserMessage(wrapper) {
        const content = this.contentRenderer.render(this.message.content);
        DOMUtils.append(wrapper, content);
    }
    
    /**
     * 渲染助手消息
     * @param {HTMLElement} wrapper - 内容包装器
     */
    renderAssistantMessage(wrapper) {
        // 1. 先收集所有模型回答
        const allResponses = [];
        
        // 当前消息本身就是一个模型回答
        if (this.message.hasModel() || this.message.content) {
            allResponses.push({
                model: this.message.model || ModelConfig.default,
                content: this.message.content || '',
                id: this.message.id
            });
        }
        
        // 添加替代回答
        if (this.message.hasAlternativeResponses()) {
            allResponses.push(...this.message.alternativeResponses);
        }
        
        // 2. 先将所有模型回答添加到 modelManager（这样 getModelNames 才能获取到）
        // 只添加有内容的回答（空内容不算已有回答）
        const validResponses = [];
        allResponses.forEach(response => {
            // 只有当内容不为空时才认为是有效的回答
            if (response.content && response.content.trim()) {
                this.modelManager.add(
                    response.model,
                    response.content,
                    response.id,
                    false
                );
                validResponses.push(response.model);
            }
        });
        
        // 3. 添加模型选择器（只包含有有效回答的模型）
        const existingModels = validResponses;
        const selector = this.modelSelector.render(existingModels);
        DOMUtils.append(wrapper, selector);
        
        // 4. 渲染所有模型回答视图（只渲染有内容的）
        allResponses.forEach(response => {
            // 只渲染有内容的回答
            if (response.content && response.content.trim()) {
                const view = this.modelManager.getView(response.model);
                if (view) {
                    const viewElement = view.render();
                    DOMUtils.append(wrapper, viewElement);
                }
            }
        });
        
        // 5. 如果没有回答，创建默认模型的占位符
        if (allResponses.length === 0) {
            const view = this.modelManager.add(
                ModelConfig.default,
                '',
                null,
                false
            );
            const viewElement = view.render();
            DOMUtils.append(wrapper, viewElement);
        }
        
        // 5. 默认展开第一个回答（优先 deepseek）
        const defaultResponse = allResponses.find(r => r.model === ModelConfig.default) || allResponses[0];
        if (defaultResponse && this.modelManager.has(defaultResponse.model)) {
            this.modelManager.toggle(defaultResponse.model);
        }
    }
    
    /**
     * 创建头像
     * @returns {HTMLElement}
     */
    createAvatar() {
        return DOMUtils.createElement('div', {
            className: 'message-avatar',
            textContent: this.message.isUser() ? 'U' : 'AI'
        });
    }
    
    /**
     * 创建时间戳
     * @returns {HTMLElement|null}
     */
    createTime() {
        if (!this.message.createdAt) {
            return null;
        }
        
        return DOMUtils.createElement('div', {
            className: 'message-time',
            textContent: Utils.formatDate(this.message.createdAt)
        });
    }
    
    /**
     * 初始化默认操作按钮
     */
    initDefaultActions() {
        // 添加复制按钮
        this.actionBar.addAction({
            id: 'copy',
            text: '📋 复制',
            title: '复制消息内容',
            className: 'message-action-btn',
            onClick: () => this.copyContent()
        });
        
        // 添加自定义操作按钮
        this.customActions.forEach(action => {
            this.actionBar.addAction(action);
        });
    }
    
    /**
     * 处理模型选择
     * @param {string} model - 模型名称
     * @param {string} action - 操作类型 ('toggle' | 'request')
     */
    handleModelSelect(model, action) {
        if (action === 'toggle') {
            // 切换展开/折叠
            this.modelManager.toggle(model);
        } else if (action === 'request') {
            // 请求生成模型回答
            this.requestModelResponse(model);
        }
    }
    
    /**
     * 请求模型回答
     * @param {string} modelName - 模型名称
     */
    requestModelResponse(modelName) {
        // 检查是否已有该模型的回答
        if (this.modelManager && this.modelManager.has(modelName)) {
            const response = this.modelManager.get(modelName);
            // 如果已有回答且有内容，直接展开/折叠，不发送请求
            if (response && response.content && response.content.trim()) {
                console.log(`模型 ${modelName} 已有回答，直接展开/折叠`);
                this.modelManager.toggle(modelName);
                return;
            }
        }
        
        // 检查是否正在加载
        const status = this.modelSelector.modelStatus?.get(modelName);
        if (status && status.isLoading) {
            console.log(`模型 ${modelName} 正在生成中，忽略重复请求`);
            return;
        }
        
        // 更新模型选择器状态
        this.modelSelector.updateModelStatus(modelName, false, true);
        
        // 创建占位符视图
        const view = this.modelManager.add(modelName, '', null, false);
        const viewElement = view.render();
        
        // 插入到模型选择器之后
        const wrapper = DOMUtils.find(this.rootElement, '.message-content-wrapper');
        if (wrapper) {
            const selector = DOMUtils.find(wrapper, '.model-selector');
            if (selector && selector.nextSibling) {
                DOMUtils.insertBefore(wrapper, viewElement, selector.nextSibling);
            } else {
                DOMUtils.append(wrapper, viewElement);
            }
        }
        
        // 调用外部 API
        const userMessageId = this.findUserMessageId();
        if (userMessageId) {
            if (typeof requestModelResponse === 'function') {
                requestModelResponse(userMessageId, modelName, this);
            } else if (typeof requestAlternativeModel === 'function') {
                // 兼容旧接口
                requestAlternativeModel(userMessageId, modelName, this);
            } else {
                console.error('requestModelResponse 函数未定义');
                this.modelSelector.updateModelStatus(modelName, false, false);
            }
        } else {
            console.error('无法找到用户消息ID');
            if (typeof showError === 'function') {
                showError('无法找到对应的用户消息，请刷新页面后重试');
            } else {
                alert('无法找到对应的用户消息，请刷新页面后重试');
            }
            this.modelSelector.updateModelStatus(modelName, false, false);
        }
    }
    
    /**
     * 更新模型回答内容（用于流式输出）
     * @param {string} modelName - 模型名称
     * @param {string} content - 内容
     * @param {boolean} isComplete - 是否已完成生成（默认 false，表示流式生成中）
     */
    updateModelResponse(modelName, content, isComplete = false) {
        if (!this.modelManager) return;
        
        this.modelManager.update(modelName, content);
        
        // 如果还在生成中，保持 isLoading 状态；只有完成时才设置为已完成
        if (isComplete) {
            this.modelSelector.updateModelStatus(modelName, true, false);
        } else {
            // 流式生成中，保持加载状态
            this.modelSelector.updateModelStatus(modelName, false, true);
        }
    }
    
    /**
     * 添加模型回答（兼容旧接口）
     * @param {Object} response - 回答对象 { model, content, id }
     */
    addModelResponse(response) {
        if (!this.modelManager) return;
        
        const view = this.modelManager.add(
            response.model,
            response.content || '',
            response.id || null,
            false
        );
        
        // 如果视图还没有添加到 DOM，添加它
        const existingView = DOMUtils.find(
            this.rootElement,
            `.model-response[data-model="${response.model}"]`
        );
        
        if (!existingView) {
            const viewElement = view.render();
            const wrapper = DOMUtils.find(this.rootElement, '.message-content-wrapper');
            if (wrapper) {
                const actionBar = DOMUtils.find(wrapper, '.message-actions');
                if (actionBar) {
                    DOMUtils.insertBefore(wrapper, viewElement, actionBar);
                } else {
                    DOMUtils.append(wrapper, viewElement);
                }
            }
        }
        
        this.modelSelector.updateModelStatus(response.model, true, false);
    }
    
    /**
     * 更新消息内容（用于流式输出，仅用户消息）
     * @param {string} newContent - 新内容
     */
    updateContent(newContent) {
        this.message.content = newContent;
        
        if (this.rootElement) {
            this.rootElement.dataset.originalContent = newContent;
        }
        
        // 如果是用户消息，更新内容
        if (this.message.isUser()) {
            const contentElement = DOMUtils.find(this.rootElement, '.message-content');
            if (contentElement) {
                const newElement = this.contentRenderer.render(newContent);
                if (contentElement.parentNode) {
                    contentElement.parentNode.replaceChild(newElement, contentElement);
                }
            }
        }
    }
    
    /**
     * 复制内容
     */
    copyContent() {
        let textToCopy = '';
        
        if (this.message.isUser()) {
            // 用户消息：复制原始内容
            textToCopy = this.message.content;
        } else {
            // 助手消息：复制当前展开的回答
            const expanded = this.modelManager ? this.modelManager.getExpanded() : null;
            if (expanded) {
                textToCopy = expanded.content;
            }
        }
        
        if (textToCopy) {
            const copyButton = this.actionBar.getButton('copy');
            ClipboardService.copy(textToCopy, copyButton);
        }
    }
    
    /**
     * 查找用户消息ID
     * @returns {number|null}
     */
    findUserMessageId() {
        // 尝试从当前消息的父级找到用户消息
        if (this.rootElement) {
            const prevElement = this.rootElement.previousElementSibling;
            if (prevElement && prevElement.dataset.messageId) {
                return parseInt(prevElement.dataset.messageId);
            }
        }
        
        // 如果找不到，使用当前消息ID（后端应该能处理）
        return this.message.id;
    }
    
    /**
     * 获取根 DOM 元素
     * @returns {HTMLElement}
     */
    getElement() {
        if (!this.rootElement) {
            this.render();
        }
        return this.rootElement;
    }
    
    /**
     * 销毁组件
     */
    destroy() {
        // 销毁子组件
        if (this.actionBar) {
            this.actionBar.destroy();
        }
        if (this.modelManager) {
            this.modelManager.destroy();
        }
        if (this.modelSelector) {
            this.modelSelector.destroy();
        }
        
        // 移除 DOM 元素
        if (this.rootElement && this.rootElement.parentNode) {
            DOMUtils.remove(this.rootElement);
        }
        
        // 清空引用
        this.rootElement = null;
        this.modelManager = null;
        this.modelSelector = null;
    }
    
    // ==================== 兼容旧接口 ====================
    
    /**
     * 添加替代回答（兼容旧接口）
     * @deprecated 使用 addModelResponse 代替
     */
    addAlternativeResponse(altResponse) {
        this.addModelResponse(altResponse);
    }
    
    /**
     * 更新替代回答（兼容旧接口）
     * @deprecated 使用 updateModelResponse 代替
     */
    updateAlternativeResponse(modelName, content) {
        this.updateModelResponse(modelName, content);
    }
}
