/**
 * 操作栏组件
 * 组件层：表达操作栏是什么
 */

class ActionBar {
    /**
     * 构造函数
     * @param {Array} actions - 操作配置数组
     */
    constructor(actions = []) {
        this.actions = actions;
        this.buttons = new Map(); // Map<actionId, Button>
        this.element = null;
    }
    
    /**
     * 渲染操作栏
     * @returns {HTMLElement}
     */
    render() {
        this.element = DOMUtils.createElement('div', {
            className: 'message-actions'
        });
        
        // 渲染所有操作按钮
        this.actions.forEach(action => {
            this.addAction(action);
        });
        
        return this.element;
    }
    
    /**
     * 添加操作按钮
     * @param {Object} action - 操作配置
     * @param {string} action.id - 操作ID
     * @param {string} action.text - 按钮文本
     * @param {Function} action.onClick - 点击处理函数
     * @param {string} action.className - 样式类名
     * @param {string} action.title - 提示文本
     */
    addAction(action) {
        if (this.buttons.has(action.id)) {
            console.warn(`操作 ${action.id} 已存在，将被替换`);
            this.removeAction(action.id);
        }
        
        const button = new Button({
            id: action.id,
            text: action.text,
            onClick: action.onClick,
            className: action.className || 'message-action-btn',
            title: action.title || ''
        });
        
        this.buttons.set(action.id, button);
        DOMUtils.append(this.element, button.render());
    }
    
    /**
     * 移除操作按钮
     * @param {string} actionId - 操作ID
     */
    removeAction(actionId) {
        const button = this.buttons.get(actionId);
        if (button) {
            button.destroy();
            this.buttons.delete(actionId);
        }
    }
    
    /**
     * 获取按钮元素
     * @param {string} actionId - 操作ID
     * @returns {HTMLElement|null}
     */
    getButton(actionId) {
        const button = this.buttons.get(actionId);
        return button ? button.element : null;
    }
    
    /**
     * 销毁操作栏
     */
    destroy() {
        this.buttons.forEach(button => {
            button.destroy();
        });
        this.buttons.clear();
        
        if (this.element && this.element.parentNode) {
            DOMUtils.remove(this.element);
        }
        this.element = null;
    }
}

