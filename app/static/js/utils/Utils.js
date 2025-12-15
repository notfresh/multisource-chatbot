/**
 * 工具函数
 * 基础设施层：通用工具函数
 */

class Utils {
    /**
     * 获取模型显示名称
     * @param {string} model - 模型名称
     * @returns {string}
     */
    static getModelDisplayName(model) {
        const modelNames = {
            'deepseek-chat': 'DeepSeek',
            'qwen-max': '通义千问'
        };
        return modelNames[model] || model;
    }
    
    /**
     * 检查内容是否包含 Markdown
     * @param {string} content - 内容
     * @returns {boolean}
     */
    static isMarkdown(content) {
        if (typeof containsMarkdown === 'function') {
            return containsMarkdown(content);
        }
        // 简单的 Markdown 检测
        return /[#*_`\[\]]/.test(content);
    }
    
    /**
     * 格式化日期
     * @param {string|Date} date - 日期
     * @returns {string}
     */
    static formatDate(date) {
        if (!date) return '';
        const d = new Date(date);
        return d.toLocaleString('zh-CN');
    }
}

