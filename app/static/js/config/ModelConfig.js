/**
 * 模型配置
 * 组件层：模型配置信息
 */

const ModelConfig = {
    /**
     * 可用模型列表
     */
    available: ['deepseek-chat', 'qwen-max'],
    
    /**
     * 默认模型
     */
    default: 'deepseek-chat',
    
    /**
     * 获取模型显示名称
     * @param {string} model - 模型名称
     * @returns {string}
     */
    getDisplayName(model) {
        return Utils.getModelDisplayName(model);
    },
    
    /**
     * 检查模型是否可用
     * @param {string} model - 模型名称
     * @returns {boolean}
     */
    isAvailable(model) {
        return this.available.includes(model);
    }
};

