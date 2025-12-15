/**
 * DOM 工具类
 * 基础设施层：封装所有 DOM 操作
 */

class DOMUtils {
    /**
     * 创建 DOM 元素
     * @param {string} tag - 标签名
     * @param {Object} attrs - 属性对象 { className, id, textContent, innerHTML, dataset, style }
     * @param {Array|HTMLElement} children - 子元素数组或单个元素
     * @returns {HTMLElement}
     */
    static createElement(tag, attrs = {}, children = null) {
        const element = document.createElement(tag);
        
        // 设置属性
        if (attrs.className) {
            element.className = attrs.className;
        }
        if (attrs.id) {
            element.id = attrs.id;
        }
        if (attrs.textContent !== undefined) {
            element.textContent = attrs.textContent;
        }
        if (attrs.innerHTML !== undefined) {
            element.innerHTML = attrs.innerHTML;
        }
        if (attrs.dataset) {
            Object.keys(attrs.dataset).forEach(key => {
                element.dataset[key] = attrs.dataset[key];
            });
        }
        if (attrs.style) {
            Object.assign(element.style, attrs.style);
        }
        
        // 添加子元素
        if (children) {
            if (Array.isArray(children)) {
                children.forEach(child => {
                    if (child) {
                        element.appendChild(child);
                    }
                });
            } else {
                element.appendChild(children);
            }
        }
        
        return element;
    }
    
    /**
     * 添加子元素
     * @param {HTMLElement} parent - 父元素
     * @param {HTMLElement|Array} children - 子元素或子元素数组
     */
    static append(parent, children) {
        if (!parent) return;
        
        if (Array.isArray(children)) {
            children.forEach(child => {
                if (child) {
                    parent.appendChild(child);
                }
            });
        } else if (children) {
            parent.appendChild(children);
        }
    }
    
    /**
     * 查找元素
     * @param {HTMLElement} parent - 父元素
     * @param {string} selector - 选择器
     * @returns {HTMLElement|null}
     */
    static find(parent, selector) {
        if (!parent) return null;
        return parent.querySelector(selector);
    }
    
    /**
     * 查找所有元素
     * @param {HTMLElement} parent - 父元素
     * @param {string} selector - 选择器
     * @returns {NodeList}
     */
    static findAll(parent, selector) {
        if (!parent) return [];
        return parent.querySelectorAll(selector);
    }
    
    /**
     * 添加类名
     * @param {HTMLElement} element - 元素
     * @param {string} className - 类名
     */
    static addClass(element, className) {
        if (element && className) {
            element.classList.add(className);
        }
    }
    
    /**
     * 移除类名
     * @param {HTMLElement} element - 元素
     * @param {string} className - 类名
     */
    static removeClass(element, className) {
        if (element && className) {
            element.classList.remove(className);
        }
    }
    
    /**
     * 切换类名
     * @param {HTMLElement} element - 元素
     * @param {string} className - 类名
     */
    static toggleClass(element, className) {
        if (element && className) {
            element.classList.toggle(className);
        }
    }
    
    /**
     * 检查是否有类名
     * @param {HTMLElement} element - 元素
     * @param {string} className - 类名
     * @returns {boolean}
     */
    static hasClass(element, className) {
        if (!element || !className) return false;
        return element.classList.contains(className);
    }
    
    /**
     * 移除元素
     * @param {HTMLElement} element - 要移除的元素
     */
    static remove(element) {
        if (element && element.parentNode) {
            element.parentNode.removeChild(element);
        }
    }
    
    /**
     * 在指定元素前插入
     * @param {HTMLElement} parent - 父元素
     * @param {HTMLElement} newElement - 新元素
     * @param {HTMLElement} referenceElement - 参考元素
     */
    static insertBefore(parent, newElement, referenceElement) {
        if (parent && newElement && referenceElement) {
            parent.insertBefore(newElement, referenceElement);
        }
    }
}

