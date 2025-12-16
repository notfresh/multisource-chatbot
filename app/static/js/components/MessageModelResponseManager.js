/**
 * 消息-模型回答管理器
 * 组件层：管理多个模型回答
 */

class MessageModelResponseManager {
    /**
     * 构造函数
     */
    constructor() {
        this.responses = new Map(); // Map<modelName, ModelResponse>
        this.views = new Map();     // Map<modelName, MessageModelResponseView>
    }
    
    /**
     * 添加模型回答
     * @param {string} model - 模型名称
     * @param {string} content - 回答内容
     * @param {number|null} messageId - 消息ID
     * @param {boolean} isExpanded - 是否展开
     * @returns {MessageModelResponseView}
     */
    add(model, content = '', messageId = null, isExpanded = false) {
        // 如果已存在，更新它
        if (this.responses.has(model)) {
            this.update(model, content, messageId);
            return this.views.get(model);
        }
        
        // 创建模型回答对象
        const response = new ModelResponse(model, content, messageId);
        if (isExpanded) {
            response.expand();
        }
        
        this.responses.set(model, response);
        
        // 创建视图
        const view = new MessageModelResponseView(response);
        this.views.set(model, view);
        
        return view;
    }
    
    /**
     * 更新模型回答
     * @param {string} model - 模型名称
     * @param {string} content - 新内容
     * @param {number|null} messageId - 消息ID（可选）
     */
    update(model, content, messageId = null) {
        console.log(`开始更新模型回答内容：${model} - ${content}`);
        const response = this.responses.get(model);
        if (response) {
            console.log(`更新原有的 ${model} - ${content}`);
            response.updateContent(content);
            if (messageId !== null) {
                response.messageId = messageId;
            }
            
            const view = this.views.get(model);
            if (view) {
                view.updateContent(content);
                if (messageId !== null && view.element) {
                    view.element.dataset.messageId = messageId;
                }
            }
        } else {
            console.log("新建一个");
            // 如果不存在，创建一个
            this.add(model, content, messageId);
        }
    }
    
    /**
     * 切换模型回答的展开/折叠状态
     * @param {string} model - 模型名称
     */
    toggle(model) {
        const view = this.views.get(model);
        if (view) {
            view.toggle();
        }
    }
    
    /**
     * 获取当前展开的模型回答
     * @returns {ModelResponse|null}
     */
    getExpanded() {
        for (const [model, response] of this.responses) {
            if (response.isExpanded) {
                return response;
            }
        }
        return null;
    }
    
    /**
     * 获取所有模型回答
     * @returns {Array<ModelResponse>}
     */
    getAll() {
        return Array.from(this.responses.values());
    }
    
    /**
     * 获取所有模型名称
     * @returns {Array<string>}
     */
    getModelNames() {
        return Array.from(this.responses.keys());
    }
    
    /**
     * 检查是否有模型回答
     * @param {string} model - 模型名称
     * @returns {boolean}
     */
    has(model) {
        return this.responses.has(model);
    }
    
    /**
     * 获取模型回答
     * @param {string} model - 模型名称
     * @returns {ModelResponse|null}
     */
    get(model) {
        return this.responses.get(model) || null;
    }
    
    /**
     * 获取模型回答视图
     * @param {string} model - 模型名称
     * @returns {MessageModelResponseView|null}
     */
    getView(model) {
        return this.views.get(model) || null;
    }
    
    /**
     * 销毁管理器
     */
    destroy() {
        this.views.forEach(view => {
            view.destroy();
        });
        this.views.clear();
        this.responses.clear();
    }
}

