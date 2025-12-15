/**
 * 事件工具类
 * 基础设施层：统一的事件管理
 */

class EventUtils {
    /**
     * 绑定事件
     * @param {HTMLElement} element - 元素
     * @param {string} event - 事件类型
     * @param {Function} handler - 事件处理函数
     * @param {Object} options - 选项 { once, capture, passive }
     * @returns {Function} 返回解绑函数
     */
    static on(element, event, handler, options = {}) {
        if (!element || !handler) return () => {};
        
        element.addEventListener(event, handler, options);
        
        // 返回解绑函数
        return () => {
            element.removeEventListener(event, handler, options);
        };
    }
    
    /**
     * 解绑事件
     * @param {HTMLElement} element - 元素
     * @param {string} event - 事件类型
     * @param {Function} handler - 事件处理函数
     * @param {Object} options - 选项
     */
    static off(element, event, handler, options = {}) {
        if (!element || !handler) return;
        element.removeEventListener(event, handler, options);
    }
    
    /**
     * 绑定一次性事件
     * @param {HTMLElement} element - 元素
     * @param {string} event - 事件类型
     * @param {Function} handler - 事件处理函数
     * @returns {Function} 返回解绑函数
     */
    static once(element, event, handler) {
        return this.on(element, event, handler, { once: true });
    }
    
    /**
     * 阻止事件冒泡
     * @param {Event} event - 事件对象
     */
    static stopPropagation(event) {
        if (event) {
            event.stopPropagation();
        }
    }
    
    /**
     * 阻止默认行为
     * @param {Event} event - 事件对象
     */
    static preventDefault(event) {
        if (event) {
            event.preventDefault();
        }
    }
}

