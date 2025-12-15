/**
 * 按钮组件
 * 组件层：表达按钮是什么
 */

class Button {
    /**
     * 构造函数
     * @param {Object} config - 按钮配置
     * @param {string} config.text - 按钮文本
     * @param {Function} config.onClick - 点击处理函数
     * @param {boolean} config.disabled - 是否禁用
     * @param {string} config.className - 样式类名
     * @param {string} config.title - 提示文本
     * @param {string} config.id - 按钮ID
     */
    constructor(config = {}) {
        this.text = config.text || '';
        this.onClick = config.onClick || null;
        this.disabled = config.disabled || false;
        this.className = config.className || 'button';
        this.title = config.title || '';
        this.id = config.id || null;
        
        this.element = null;
        this.unbind = null;
    }
    
    /**
     * 渲染按钮
     * @returns {HTMLElement}
     */
    render() {
        this.element = DOMUtils.createElement('button', {
            className: this.className,
            textContent: this.text,
            title: this.title,
            dataset: this.id ? { id: this.id } : {}
        });
        
        if (this.disabled) {
            this.element.disabled = true;
        }
        
        // 绑定点击事件
        if (this.onClick) {
            this.unbind = EventUtils.on(this.element, 'click', (e) => {
                EventUtils.stopPropagation(e);
                this.onClick(e);
            });
        }
        
        return this.element;
    }
    
    /**
     * 更新按钮状态
     * @param {Object} updates - 更新内容 { text, disabled, title }
     */
    update(updates = {}) {
        if (!this.element) return;
        
        if (updates.text !== undefined) {
            this.text = updates.text;
            this.element.textContent = updates.text;
        }
        if (updates.disabled !== undefined) {
            this.disabled = updates.disabled;
            this.element.disabled = updates.disabled;
        }
        if (updates.title !== undefined) {
            this.title = updates.title;
            this.element.title = updates.title;
        }
    }
    
    /**
     * 销毁按钮
     */
    destroy() {
        if (this.unbind) {
            this.unbind();
        }
        if (this.element && this.element.parentNode) {
            DOMUtils.remove(this.element);
        }
        this.element = null;
    }
}

