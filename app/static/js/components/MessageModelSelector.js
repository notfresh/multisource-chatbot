/**
 * 消息-模型选择器组件
 * 组件层：表达模型选择器是什么
 */

class MessageModelSelector {
    /**
     * 构造函数
     * @param {Array} availableModels - 可用模型列表
     * @param {Function} onModelSelect - 模型选择回调函数
     */
    constructor(availableModels, onModelSelect) {
        this.availableModels = availableModels || ModelConfig.available;
        this.onModelSelect = onModelSelect || null;
        this.buttons = new Map(); // Map<modelName, Button>
        this.modelStatus = new Map(); // Map<modelName, {hasResponse: boolean, isLoading: boolean}>
        this.element = null;
    }
    
    /**
     * 渲染模型选择器
     * @param {Array} existingModels - 已存在的模型列表
     * @returns {HTMLElement}
     */
    render(existingModels = []) {
        this.element = DOMUtils.createElement('div', {
            className: 'model-selector'
        });
        
        // 为每个可用模型创建按钮
        this.availableModels.forEach(modelName => {
            const hasResponse = existingModels.includes(modelName);
            const button = this._createModelButton(modelName, hasResponse);
            this.buttons.set(modelName, button);
            DOMUtils.append(this.element, button.render());
        });
        
        return this.element;
    }
    
    /**
     * 创建模型按钮
     * @private
     */
    _createModelButton(modelName, hasResponse) {
        // 初始化模型状态
        this.modelStatus.set(modelName, {
            hasResponse: hasResponse,
            isLoading: false
        });
        
        // 根据状态设置按钮文本和样式
        const displayName = ModelConfig.getDisplayName(modelName);
        const buttonText = hasResponse ? `✓ ${displayName}` : displayName;
        const buttonTitle = hasResponse ? '已生成，点击展开/折叠' : `请求 ${displayName} 回答`;
        
        const button = new Button({
            text: buttonText,
            className: `model-selector-btn ${hasResponse ? 'has-response' : ''}`,
            title: buttonTitle,
            onClick: () => {
                // 动态检查当前状态，而不是使用闭包中的旧值
                const status = this.modelStatus.get(modelName);
                if (!status) {
                    console.error(`模型 ${modelName} 的状态未找到`);
                    return;
                }
                
                // 如果正在加载，不允许点击
                if (status.isLoading) {
                    return;
                }
                
                if (status.hasResponse) {
                    // 如果已有回答，通知展开/折叠
                    if (this.onModelSelect) {
                        this.onModelSelect(modelName, 'toggle');
                    }
                } else {
                    // 如果没有回答，请求生成
                    if (this.onModelSelect) {
                        this.onModelSelect(modelName, 'request');
                    }
                }
            }
        });
        
        return button;
    }
    
    /**
     * 更新模型状态
     * @param {string} modelName - 模型名称
     * @param {boolean} hasResponse - 是否有回答
     * @param {boolean} isLoading - 是否正在加载
     */
    updateModelStatus(modelName, hasResponse, isLoading = false) {
        const button = this.buttons.get(modelName);
        if (!button) return;
        
        // 更新状态映射
        this.modelStatus.set(modelName, {
            hasResponse: hasResponse,
            isLoading: isLoading
        });
        
        const displayName = ModelConfig.getDisplayName(modelName);
        
        if (isLoading) {
            button.update({
                disabled: true,
                text: '⏳ 生成中...',
                title: '正在生成回答...'
            });
        } else if (hasResponse) {
            button.update({
                disabled: false,
                text: `✓ ${displayName}`,
                className: 'model-selector-btn has-response',
                title: '已生成，点击展开/折叠'
            });
        } else {
            button.update({
                disabled: false,
                text: displayName,
                className: 'model-selector-btn',
                title: `请求 ${displayName} 回答`
            });
        }
    }
    
    /**
     * 销毁选择器
     */
    destroy() {
        this.buttons.forEach(button => {
            button.destroy();
        });
        this.buttons.clear();
        this.modelStatus.clear();
        
        if (this.element && this.element.parentNode) {
            DOMUtils.remove(this.element);
        }
        this.element = null;
    }
}

