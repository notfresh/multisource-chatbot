/**
 * 内容渲染器
 * 组件层：如何渲染内容
 */

class ContentRenderer {
    /**
     * 渲染内容
     * @param {string} content - 内容
     * @param {HTMLElement} container - 容器元素（可选）
     * @returns {HTMLElement}
     */
    render(content, container = null) {
        if (Utils.isMarkdown(content) && typeof renderMarkdown === 'function') {
            return this.renderMarkdown(content, container);
        } else {
            return this.renderPlainText(content, container);
        }
    }
    
    /**
     * 渲染 Markdown 内容
     * @param {string} content - Markdown 内容
     * @param {HTMLElement} container - 容器元素（可选）
     * @returns {HTMLElement}
     */
    renderMarkdown(content, container = null) {
        const element = container || DOMUtils.createElement('div', {
            className: 'message-content'
        });
        
        if (typeof renderMarkdown === 'function') {
            element.innerHTML = renderMarkdown(content);
            
            if (Utils.isMarkdown(content)) {
                DOMUtils.addClass(element, 'markdown-content');
                this._addCodeBlockCopyButtons(element);
            }
        } else {
            element.textContent = content;
        }
        
        return element;
    }
    
    /**
     * 渲染纯文本内容
     * @param {string} content - 文本内容
     * @param {HTMLElement} container - 容器元素（可选）
     * @returns {HTMLElement}
     */
    renderPlainText(content, container = null) {
        const element = container || DOMUtils.createElement('div', {
            className: 'message-content'
        });
        
        element.textContent = content;
        return element;
    }
    
    /**
     * 为代码块添加复制按钮
     * @private
     */
    _addCodeBlockCopyButtons(container) {
        const codeBlocks = DOMUtils.findAll(container, 'pre');
        codeBlocks.forEach(pre => {
            // 检查是否已有复制按钮
            if (DOMUtils.find(pre, '.code-copy-btn')) {
                return;
            }
            
            const codeElement = DOMUtils.find(pre, 'code');
            const codeText = codeElement ? codeElement.textContent : pre.textContent;
            
            const copyBtn = DOMUtils.createElement('button', {
                className: 'code-copy-btn',
                textContent: '📋',
                title: '复制代码'
            });
            
            EventUtils.on(copyBtn, 'click', (e) => {
                EventUtils.stopPropagation(e);
                ClipboardService.copy(codeText, copyBtn);
            });
            
            // 设置相对定位
            if (getComputedStyle(pre).position === 'static') {
                pre.style.position = 'relative';
            }
            
            DOMUtils.append(pre, copyBtn);
        });
    }
}

