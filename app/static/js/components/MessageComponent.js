/**
 * 消息组件
 * 封装消息的渲染、状态管理和操作按钮
 */

class MessageComponent {
    constructor(config) {
        // 配置参数
        this.message = config.message || {};
        this.actions = config.actions || [];
        this.onAction = config.onAction || null;
        
        // 内部状态
        this.originalContent = this.message.content || '';
        this.isRendered = true; // 当前是否显示渲染后的内容
        this.buttons = new Map(); // 存储所有按钮 { id: { element, config } }
        
        // DOM 元素引用
        this.rootElement = null;
        this.contentDiv = null;
        this.actionBar = null;
        
        // 初始化
        this._init();
    }
    
    /**
     * 初始化组件
     */
    _init() {
        this.rootElement = this._createRootElement();
        this._renderContent();
        this._initActionBar();
        this._initDefaultActions();
    }
    
    /**
     * 创建根元素结构
     */
    _createRootElement() {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${this.message.role}`;
        
        // 存储原始内容到数据属性
        messageDiv.dataset.originalContent = this.originalContent;
        
        // 头像
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = this.message.role === 'user' ? 'U' : 'AI';
        messageDiv.appendChild(avatar);
        
        // 内容包装器
        const contentWrapper = document.createElement('div');
        contentWrapper.className = 'message-content-wrapper';
        
        // 内容区域
        this.contentDiv = document.createElement('div');
        this.contentDiv.className = 'message-content';
        contentWrapper.appendChild(this.contentDiv);
        
        // 操作按钮栏（初始为空）
        this.actionBar = document.createElement('div');
        this.actionBar.className = 'message-actions';
        contentWrapper.appendChild(this.actionBar);
        
        messageDiv.appendChild(contentWrapper);
        
        // 时间戳
        const time = document.createElement('div');
        time.className = 'message-time';
        if (this.message.created_at) {
            const date = new Date(this.message.created_at);
            time.textContent = date.toLocaleString('zh-CN');
        }
        messageDiv.appendChild(time);
        
        return messageDiv;
    }
    
    /**
     * 渲染消息内容
     */
    _renderContent() {
        if (typeof renderMarkdown !== 'undefined') {
            this.contentDiv.innerHTML = renderMarkdown(this.originalContent);
            // 如果是 Markdown 内容，添加 markdown 类名用于样式
            if (containsMarkdown && containsMarkdown(this.originalContent)) {
                this.contentDiv.classList.add('markdown-content');
                // 为代码块添加复制按钮
                this._addCodeBlockCopyButtons();
            }
        } else {
            // 如果 Markdown 渲染器未加载，使用纯文本
            this.contentDiv.textContent = this.originalContent;
        }
    }
    
    /**
     * 为代码块添加复制按钮
     */
    _addCodeBlockCopyButtons() {
        const codeBlocks = this.contentDiv.querySelectorAll('pre');
        codeBlocks.forEach((pre, index) => {
            // 如果已经有复制按钮，跳过
            if (pre.querySelector('.code-copy-btn')) {
                return;
            }
            
            // 创建复制按钮
            const copyBtn = document.createElement('button');
            copyBtn.className = 'code-copy-btn';
            copyBtn.textContent = '📋';
            copyBtn.title = '复制代码';
            
            // 获取代码内容
            const codeElement = pre.querySelector('code');
            const codeText = codeElement ? codeElement.textContent : pre.textContent;
            
            // 绑定点击事件
            copyBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this._copyCodeBlock(codeText, copyBtn);
            });
            
            // 将 pre 设置为相对定位，以便按钮定位
            if (getComputedStyle(pre).position === 'static') {
                pre.style.position = 'relative';
            }
            
            // 添加按钮到代码块
            pre.appendChild(copyBtn);
        });
    }
    
    /**
     * 复制代码块内容
     */
    _copyCodeBlock(codeText, button) {
        if (!codeText) {
            return;
        }
        
        // 使用 Clipboard API 复制
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(codeText).then(() => {
                // 复制成功反馈
                const originalText = button.textContent;
                button.textContent = '✓';
                button.title = '已复制';
                setTimeout(() => {
                    button.textContent = originalText;
                    button.title = '复制代码';
                }, 2000);
            }).catch(err => {
                console.error('复制失败:', err);
                this._fallbackCopyCode(codeText, button);
            });
        } else {
            // 降级方案
            this._fallbackCopyCode(codeText, button);
        }
    }
    
    /**
     * 降级复制代码方案
     */
    _fallbackCopyCode(codeText, button) {
        const textArea = document.createElement('textarea');
        textArea.value = codeText;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            const successful = document.execCommand('copy');
            if (successful) {
                const originalText = button.textContent;
                button.textContent = '✓';
                button.title = '已复制';
                setTimeout(() => {
                    button.textContent = originalText;
                    button.title = '复制代码';
                }, 2000);
            } else {
                alert('复制失败，请手动复制');
            }
        } catch (err) {
            console.error('复制失败:', err);
            alert('复制失败，请手动复制');
        } finally {
            document.body.removeChild(textArea);
        }
    }
    
    /**
     * 初始化操作按钮栏
     */
    _initActionBar() {
        // actionBar 已经在 _createRootElement 中创建
        // 这里可以添加一些初始化逻辑
    }
    
    /**
     * 初始化默认操作按钮
     */
    _initDefaultActions() {
        // 如果有 Markdown 内容，添加切换按钮
        if (typeof containsMarkdown !== 'undefined' && containsMarkdown(this.originalContent)) {
            this.addActionButton({
                id: 'toggle-markdown',
                text: '📝 查看 Markdown',
                title: '切换显示 Markdown 原始文本',
                className: 'message-toggle-btn',
                onClick: () => this._toggleMarkdown()
            });
        }
        
        // 添加复制按钮（所有消息都显示）
        this.addActionButton({
            id: 'copy',
            text: '📋 复制',
            title: '复制消息内容',
            className: 'message-action-btn',
            onClick: () => this._copyContent()
        });
        
        // 添加配置的按钮
        if (this.actions && this.actions.length > 0) {
            this.actions.forEach(actionConfig => {
                this.addActionButton(actionConfig);
            });
        }
    }
    
    /**
     * 切换 Markdown 显示
     */
    _toggleMarkdown() {
        const toggleButton = this.buttons.get('toggle-markdown');
        if (!toggleButton) return;
        
        if (this.isRendered) {
            // 切换到 Markdown 原始文本
            this.contentDiv.textContent = this.originalContent;
            this.contentDiv.classList.remove('markdown-content');
            toggleButton.element.textContent = '👁 查看渲染';
            toggleButton.element.title = '切换显示渲染后的内容';
            this.isRendered = false;
        } else {
            // 切换到渲染后的内容
            this.contentDiv.innerHTML = renderMarkdown(this.originalContent);
            if (containsMarkdown && containsMarkdown(this.originalContent)) {
                this.contentDiv.classList.add('markdown-content');
                // 重新添加代码块复制按钮
                this._addCodeBlockCopyButtons();
            }
            toggleButton.element.textContent = '📝 查看 Markdown';
            toggleButton.element.title = '切换显示 Markdown 原始文本';
            this.isRendered = true;
        }
        
        // 同步 actionBar 宽度（切换后内容宽度可能变化）
        this._syncActionBarWidth();
        
        // 触发回调
        if (this.onAction) {
            this.onAction('toggle-markdown', this.isRendered);
        }
    }
    
    /**
     * 复制消息内容
     * 根据当前显示状态复制：
     * - 如果显示的是 Markdown 原始文本，复制 Markdown 原始文本
     * - 如果显示的是渲染后的内容，复制渲染后的纯文本（浏览器会自动处理 HTML 转纯文本）
     */
    _copyContent() {
        let textToCopy = '';
        
        if (this.isRendered) {
            // 当前显示的是渲染后的内容
            // 复制渲染后的纯文本（从 DOM 中提取文本内容）
            textToCopy = this.contentDiv.textContent || this.contentDiv.innerText || '';
        } else {
            // 当前显示的是 Markdown 原始文本
            // 直接复制原始内容
            textToCopy = this.originalContent;
        }
        
        // 如果没有内容，直接返回
        if (!textToCopy) {
            console.warn('没有内容可复制');
            return;
        }
        
        // 使用 Clipboard API 复制
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(textToCopy).then(() => {
                // 复制成功，给用户反馈
                const copyButton = this.buttons.get('copy');
                if (copyButton) {
                    const originalText = copyButton.element.textContent;
                    copyButton.element.textContent = '✓ 已复制';
                    setTimeout(() => {
                        copyButton.element.textContent = originalText;
                    }, 2000);
                }
            }).catch(err => {
                console.error('复制失败:', err);
                // 降级方案：使用传统方法
                this._fallbackCopy(textToCopy);
            });
        } else {
            // 降级方案：使用传统方法
            this._fallbackCopy(textToCopy);
        }
    }
    
    /**
     * 降级复制方案（兼容旧浏览器）
     */
    _fallbackCopy(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            const successful = document.execCommand('copy');
            if (successful) {
                const copyButton = this.buttons.get('copy');
                if (copyButton) {
                    const originalText = copyButton.element.textContent;
                    copyButton.element.textContent = '✓ 已复制';
                    setTimeout(() => {
                        copyButton.element.textContent = originalText;
                    }, 2000);
                }
            } else {
                console.error('复制失败');
                alert('复制失败，请手动复制');
            }
        } catch (err) {
            console.error('复制失败:', err);
            alert('复制失败，请手动复制');
        } finally {
            document.body.removeChild(textArea);
        }
    }
    
    /**
     * 添加操作按钮
     * @param {Object} config - 按钮配置
     * @param {string} config.id - 按钮唯一标识
     * @param {string} config.text - 按钮文本
     * @param {string} [config.title] - 按钮提示文本
     * @param {string} [config.className] - 按钮样式类
     * @param {Function} [config.condition] - 显示条件函数
     * @param {Function} config.onClick - 点击处理函数
     */
    addActionButton(config) {
        // 检查条件
        if (config.condition && !config.condition(this.message)) {
            return;
        }
        
        // 检查是否已存在
        if (this.buttons.has(config.id)) {
            console.warn(`按钮 ${config.id} 已存在，将被替换`);
            this.removeActionButton(config.id);
        }
        
        // 创建按钮元素
        const button = document.createElement('button');
        button.className = config.className || 'message-action-btn';
        button.textContent = config.text || '';
        button.title = config.title || '';
        button.dataset.actionId = config.id;
        
        // 绑定点击事件
        const clickHandler = (e) => {
            e.stopPropagation();
            if (config.onClick) {
                config.onClick(this.message, this, e);
            }
            // 触发全局回调
            if (this.onAction) {
                this.onAction(config.id, this.message, this);
            }
        };
        button.addEventListener('click', clickHandler);
        
        // 存储按钮引用
        this.buttons.set(config.id, {
            element: button,
            config: config,
            clickHandler: clickHandler
        });
        
        // 添加到操作栏
        this.actionBar.appendChild(button);
    }
    
    /**
     * 移除操作按钮
     * @param {string} id - 按钮 ID
     */
    removeActionButton(id) {
        const buttonData = this.buttons.get(id);
        if (buttonData) {
            // 移除事件监听
            buttonData.element.removeEventListener('click', buttonData.clickHandler);
            // 从 DOM 中移除
            buttonData.element.remove();
            // 从 Map 中移除
            this.buttons.delete(id);
        }
    }
    
    /**
     * 更新消息内容（用于流式输出）
     * @param {string} newContent - 新内容
     */
    updateContent(newContent) {
        this.originalContent = newContent;
        if (this.rootElement) {
            this.rootElement.dataset.originalContent = newContent;
        }
        
        // 根据当前显示状态更新内容
        if (this.isRendered) {
            // 渲染模式：更新 HTML
            if (typeof renderMarkdown !== 'undefined') {
                this.contentDiv.innerHTML = renderMarkdown(newContent);
                // 检查是否需要显示切换按钮
                if (containsMarkdown && containsMarkdown(newContent)) {
                    this.contentDiv.classList.add('markdown-content');
                    // 为代码块添加复制按钮
                    this._addCodeBlockCopyButtons();
                    // 如果还没有切换按钮，添加一个
                    if (!this.buttons.has('toggle-markdown')) {
                        this.addActionButton({
                            id: 'toggle-markdown',
                            text: '📝 查看 Markdown',
                            title: '切换显示 Markdown 原始文本',
                            className: 'message-toggle-btn',
                            onClick: () => this._toggleMarkdown()
                        });
                    }
                }
                
                // 如果还没有复制按钮，添加一个（流式输出时）
                if (!this.buttons.has('copy')) {
                    this.addActionButton({
                        id: 'copy',
                        text: '📋 复制',
                        title: '复制消息内容',
                        className: 'message-action-btn',
                        onClick: () => this._copyContent()
                    });
                }
            } else {
                this.contentDiv.textContent = newContent;
            }
        } else {
            // 原始模式：更新文本
            this.contentDiv.textContent = newContent;
        }
    }
    
    /**
     * 获取根 DOM 元素
     * @returns {HTMLElement}
     */
    getElement() {
        return this.rootElement;
    }
    
    /**
     * 销毁组件
     */
    destroy() {
        // 移除所有按钮的事件监听
        this.buttons.forEach((buttonData, id) => {
            buttonData.element.removeEventListener('click', buttonData.clickHandler);
        });
        
        // 清空 Map
        this.buttons.clear();
        
        // 移除 DOM 元素
        if (this.rootElement && this.rootElement.parentNode) {
            this.rootElement.parentNode.removeChild(this.rootElement);
        }
        
        // 清空引用
        this.rootElement = null;
        this.contentDiv = null;
        this.actionBar = null;
    }
}

