/**
 * 剪贴板服务
 * 基础设施层：统一的剪贴板操作
 */

class ClipboardService {
    /**
     * 复制文本到剪贴板
     * @param {string} text - 要复制的文本
     * @param {HTMLElement|null} feedbackElement - 用于显示反馈的元素（可选）
     * @returns {Promise<void>}
     */
    static async copy(text, feedbackElement = null) {
        if (!text) {
            return;
        }
        
        const originalText = feedbackElement ? feedbackElement.textContent : '';
        const originalTitle = feedbackElement ? feedbackElement.title : '';
        
        try {
            // 使用 Clipboard API
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(text);
                this._showFeedback(feedbackElement, originalText, originalTitle);
            } else {
                // 降级方案
                this._fallbackCopy(text, feedbackElement, originalText, originalTitle);
            }
        } catch (err) {
            console.error('复制失败:', err);
            this._fallbackCopy(text, feedbackElement, originalText, originalTitle);
        }
    }
    
    /**
     * 显示复制成功反馈
     * @private
     */
    static _showFeedback(element, originalText, originalTitle) {
        if (!element) return;
        
        const isCopyButton = element.textContent.includes('📋');
        element.textContent = isCopyButton ? '✓' : '✓ 已复制';
        element.title = '已复制';
        
        setTimeout(() => {
            element.textContent = originalText;
            element.title = originalTitle;
        }, 2000);
    }
    
    /**
     * 降级复制方案（兼容旧浏览器）
     * @private
     */
    static _fallbackCopy(text, feedbackElement, originalText, originalTitle) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            const successful = document.execCommand('copy');
            if (successful) {
                this._showFeedback(feedbackElement, originalText, originalTitle);
            } else {
                console.error('复制失败');
                alert('复制失败，请手动复制');
            }
        } catch (err) {
            console.error('复制失败:', err);
            alert('复制失败，请手动复制');
        } finally {
            document.body.removeChild(textArea);
        }
    }
}

