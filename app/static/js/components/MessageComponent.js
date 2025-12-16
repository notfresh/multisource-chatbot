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
        // 多模型回答相关组件
        this.modelManager = null;
        this.modelSelector = null;
        // 对应的用户消息 ID（用于按需请求其他模型回答）
        this.userMessageId = null;
        
        // 如果是助手消息，初始化消息-模型相关组件
        if (this.message.isAssistant()) {
            this.modelManager = new MessageModelResponseManager();
            this.modelSelector = new MessageModelSelector(
                ModelConfig.available,
                (model, action) => this.controller.handleModelSelect(model, action)
            );
        }

        // 控制器：协调模型、视图和服务
        this.controller = new MessageController(this);
        
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
            const content = this.contentRenderer.render(this.message.content);
            DOMUtils.append(wrapper, content);
        } else {
            // 助手消息：多模型回答
            // 1. 添加模型选择器
            const selector = this.modelSelector.render();
            DOMUtils.append(wrapper, selector);

            // 2. 添加已有模型回答
            const existingResponses = this.message.alternative_responses || [];
            existingResponses.forEach(response => {
                const view = this.modelManager.add(
                    response.model,
                    response.content,
                    response.id
                );
                if (view) {
                    const viewElement = view.render();
                    if (viewElement) {
                        DOMUtils.append(wrapper, viewElement);
                    }
                }
            });

            // 3. 如果有默认模型回答，添加它
            if (this.message.content) {
                const defaultModel = this.message.model || ModelConfig.default;
                const view = this.modelManager.add(
                    defaultModel,
                    this.message.content,
                    this.message.id
                );
                if (view) {
                    const viewElement = view.render();
                    if (viewElement) {
                        DOMUtils.append(wrapper, viewElement);
                    }
                }
                // 默认展开
                this.modelManager.toggle(defaultModel);
            }
        }

        // 4. 添加操作栏
        const actionBar = this.actionBar.render();
        DOMUtils.append(wrapper, actionBar);

        return wrapper;
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
        // 保留兼容旧调用入口，实际逻辑交由控制器处理
        this.controller.handleModelSelect(model, action);
    }
    
    /**
     * 请求模型回答
     * @param {string} modelName - 模型名称
     */
    requestModelResponse(modelName) {
        this.controller.requestModelResponse(modelName);
    }
    
    /**
     * 更新模型回答内容（用于流式输出）
     * @param {string} modelName - 模型名称
     * @param {string} content - 内容
     * @param {boolean} isComplete - 是否已完成生成（默认 false，表示流式生成中）
     */
    updateModelResponse(modelName, content, isComplete = false) {
        this.controller.updateModelResponse(modelName, content, isComplete);
    }
    
    /**
     * 添加模型回答（兼容旧接口）
     * @param {Object} response - 回答对象 { model, content, id }
     */
    addModelResponse(response) {
        this.controller.addModelResponse(response);
    }
    
    /**
     * 更新消息内容（用于流式输出，仅用户消息）
     * @param {string} newContent - 新内容
     */
    updateContent(newContent) {
        this.controller.updateContent(newContent);
    }
    
    /**
     * 复制内容
     */
    copyContent() {
        this.controller.copyContent();
    }
    
    /**
     * 查找用户消息ID
     * @returns {number|null}
     */
    findUserMessageId() {
        return this.controller.findUserMessageId();
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
