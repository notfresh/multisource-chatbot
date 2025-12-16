/**
 * 消息-模型回答视图组件
 * 组件层：表达模型回答视图是什么
 */

class MessageModelResponseView {
    /**
     * 构造函数
     * @param {ModelResponse} modelResponse - 模型回答对象
     */
    constructor(modelResponse) {
        this.modelResponse = modelResponse;
        this.label = new MessageModelLabel(
            modelResponse.model,
            modelResponse.isExpanded,
            () => this.toggle()
        );
        this.contentRenderer = new ContentRenderer();
        this.element = null;
        this.contentElement = null;
    }
    
    /**
     * 渲染视图
     * @returns {HTMLElement}
     */
    render() {
        // 创建根元素
        this.element = DOMUtils.createElement('div', {
            className: 'model-response peer-response',
            dataset: {
                model: this.modelResponse.model,
                messageId: this.modelResponse.messageId || '',
                expanded: this.modelResponse.isExpanded ? 'true' : 'false'
            }
        });
        
        if (!this.modelResponse.isExpanded) {
            DOMUtils.addClass(this.element, 'collapsed');
        }
        
        // 添加模型标签
        const label = this.label.render();
        DOMUtils.append(this.element, label);
        
        // 添加内容包装器
        const contentWrapper = DOMUtils.createElement('div', {
            className: 'response-content-wrapper'
        });
        
        // 渲染内容
        if (this.modelResponse.hasContent()) {
            this.contentElement = this.contentRenderer.render(this.modelResponse.content);
        } else {
            this.contentElement = DOMUtils.createElement('div', {
                className: 'message-content loading-placeholder',
                textContent: '正在生成...'
            });
        }
        
        DOMUtils.append(contentWrapper, this.contentElement);
        DOMUtils.append(this.element, contentWrapper);
        
        return this.element;
    }
    
    /**
     * 切换展开/折叠状态
     */
    toggle() {
        this.modelResponse.toggle();
        this.updateExpanded(this.modelResponse.isExpanded);
    }
    
    /**
     * 更新展开状态
     * @param {boolean} isExpanded - 是否展开
     */
    updateExpanded(isExpanded) {
        this.label.updateExpanded(isExpanded);
        
        if (this.element) {
            this.element.dataset.expanded = isExpanded ? 'true' : 'false';
            
            if (isExpanded) {
                DOMUtils.removeClass(this.element, 'collapsed');
            } else {
                DOMUtils.addClass(this.element, 'collapsed');
            }
        }
    }
    
    /**
     * 更新内容
     * @param {string} content - 新内容
     */
    updateContent(content) {
        this.modelResponse.updateContent(content);
        
        if (this.contentElement) {
            DOMUtils.removeClass(this.contentElement, 'loading-placeholder');
            
            if (content) {
                // 重新渲染内容
                const newContent = this.contentRenderer.render(content);
                if (this.contentElement.parentNode) {
                    this.contentElement.parentNode.replaceChild(newContent, this.contentElement);
                }
                this.contentElement = newContent;
            }
        }
    }
    
    /**
     * 销毁视图
     */
    destroy() {
        if (this.label) {
            this.label.destroy();
        }
        if (this.element && this.element.parentNode) {
            DOMUtils.remove(this.element);
        }
        this.element = null;
        this.contentElement = null;
    }
}

