/**
 * 代码块组件
 * 组件层：表达代码块是什么
 */

class CodeBlock {
    /**
     * 构造函数
     * @param {string} code - 代码内容
     * @param {string} language - 编程语言
     */
    constructor(code, language = '') {
        this.code = code;
        this.language = language;
        this.element = null;
    }
    
    /**
     * 渲染代码块
     * @returns {HTMLElement}
     */
    render() {
        const pre = DOMUtils.createElement('pre');
        const code = DOMUtils.createElement('code', {
            textContent: this.code,
            className: this.language ? `language-${this.language}` : ''
        });
        
        DOMUtils.append(pre, code);
        
        // 添加复制按钮
        this._addCopyButton(pre);
        
        // 设置相对定位以便按钮定位
        if (getComputedStyle(pre).position === 'static') {
            pre.style.position = 'relative';
        }
        
        this.element = pre;
        return pre;
    }
    
    /**
     * 添加复制按钮
     * @private
     */
    _addCopyButton(pre) {
        // 检查是否已有复制按钮
        if (DOMUtils.find(pre, '.code-copy-btn')) {
            return;
        }
        
        const copyBtn = DOMUtils.createElement('button', {
            className: 'code-copy-btn',
            textContent: '📋',
            title: '复制代码'
        });
        
        EventUtils.on(copyBtn, 'click', (e) => {
            EventUtils.stopPropagation(e);
            ClipboardService.copy(this.code, copyBtn);
        });
        
        DOMUtils.append(pre, copyBtn);
    }
    
    /**
     * 销毁代码块
     */
    destroy() {
        this.element = null;
    }
}

