/**
 * 模型标签组件
 * 组件层：表达模型标签是什么
 */

class ModelLabel {
    /**
     * 构造函数
     * @param {string} modelName - 模型名称
     * @param {boolean} isExpanded - 是否展开
     * @param {Function} onClick - 点击处理函数
     */
    constructor(modelName, isExpanded = false, onClick = null) {
        this.modelName = modelName;
        this.isExpanded = isExpanded;
        this.onClick = onClick;
        
        this.element = null;
        this.unbind = null;
    }
    
    /**
     * 渲染模型标签
     * @returns {HTMLElement}
     */
    render() {
        this.element = DOMUtils.createElement('div', {
            className: 'model-label clickable',
            innerHTML: `
                <span class="model-label-text">${ModelConfig.getDisplayName(this.modelName)}</span>
                <span class="expand-icon">${this.isExpanded ? '▲' : '▼'}</span>
            `
        });
        
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
     * 更新展开状态
     * @param {boolean} isExpanded - 是否展开
     */
    updateExpanded(isExpanded) {
        this.isExpanded = isExpanded;
        if (this.element) {
            const icon = DOMUtils.find(this.element, '.expand-icon');
            if (icon) {
                icon.textContent = isExpanded ? '▲' : '▼';
            }
        }
    }
    
    /**
     * 销毁标签
     */
    destroy() {
        if (this.unbind) {
            this.unbind();
        }
        this.element = null;
    }
}

