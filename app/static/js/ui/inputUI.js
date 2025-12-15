/**
 * 输入框 UI
 * 职责：处理输入框相关的 UI 操作
 */

// 使用全局命名空间
window.InputUI = window.InputUI || {};

/**
 * 设置输入框状态
 * @param {HTMLElement} input - 输入框元素
 * @param {HTMLElement} sendButton - 发送按钮
 * @param {HTMLElement} stopButton - 停止按钮
 * @param {boolean} enabled - 是否启用
 */
InputUI.setInputEnabled = function(input, sendButton, stopButton, enabled) {
    input.disabled = !enabled;
    sendButton.disabled = !enabled;
    
    if (enabled) {
        stopButton.style.display = 'none';
        input.focus();
    }
};

/**
 * 设置停止按钮状态
 * @param {HTMLElement} stopButton - 停止按钮
 * @param {Object} options - 选项
 * @param {boolean} options.visible - 是否显示
 * @param {boolean} options.disabled - 是否禁用
 * @param {string} options.text - 按钮文本
 */
InputUI.setStopButtonState = function(stopButton, options = {}) {
    const { visible = false, disabled = false, text = '⏹ 停止' } = options;
    
    stopButton.style.display = visible ? 'block' : 'none';
    stopButton.disabled = disabled;
    stopButton.textContent = text;
};

/**
 * 清空输入框
 * @param {HTMLElement} input - 输入框元素
 */
InputUI.clearInput = function(input) {
    input.value = '';
    input.style.height = 'auto';
};

/**
 * 自动调整输入框高度
 * @param {HTMLElement} input - 输入框元素
 */
InputUI.autoResizeInput = function(input) {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 200) + 'px';
};

