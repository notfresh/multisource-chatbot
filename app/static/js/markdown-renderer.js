/**
 * Markdown 渲染模块
 * 使用 marked.js 库渲染 Markdown 内容
 */

// 检测文本是否包含 Markdown 语法
function containsMarkdown(text) {
    if (!text || typeof text !== 'string') {
        return false;
    }
    
    // Markdown 常见语法模式
    const markdownPatterns = [
        /^#{1,6}\s+.+$/m,                    // 标题 (# ## ###)
        /\*\*.*?\*\*/,                       // 粗体 (**text**)
        /\*.*?\*/,                           // 斜体 (*text*)
        /`[^`]+`/,                           // 行内代码 (`code`)
        /```[\s\S]*?```/,                    // 代码块 (```code```)
        /\[.*?\]\(.*?\)/,                    // 链接 ([text](url))
        /^\s*[-*+]\s+.+$/m,                  // 无序列表 (- * +)
        /^\s*\d+\.\s+.+$/m,                  // 有序列表 (1. 2. 3.)
        /^>\s+.+$/m,                         // 引用 (> text)
        /^\s*\|.+\|.+\|/m,                   // 表格 (| col | col |)
        /!\[.*?\]\(.*?\)/,                   // 图片 (![alt](url))
        /~~.*?~~/,                           // 删除线 (~~text~~)
        /^---+$/m,                           // 分隔线 (---)
    ];
    
    return markdownPatterns.some(pattern => pattern.test(text));
}

// 渲染 Markdown 内容为 HTML
function renderMarkdown(text) {
    if (!text || typeof text !== 'string') {
        return '';
    }
    
    // 检查是否包含 Markdown
    if (!containsMarkdown(text)) {
        // 如果不包含 Markdown，直接返回转义后的纯文本
        return escapeHtml(text);
    }
    
    // 使用 marked.js 渲染 Markdown
    if (typeof marked !== 'undefined') {
        try {
            // 配置 marked 选项
            marked.setOptions({
                breaks: true,        // 支持 GitHub 风格的换行
                gfm: true,          // 启用 GitHub Flavored Markdown
                headerIds: false,   // 不生成标题 ID
                mangle: false,      // 不混淆邮箱地址
            });
            
            return marked.parse(text);
        } catch (error) {
            console.error('Markdown 渲染失败:', error);
            // 如果渲染失败，返回转义后的文本
            return escapeHtml(text);
        }
    } else {
        console.warn('marked.js 未加载，使用纯文本显示');
        return escapeHtml(text);
    }
}

// HTML 转义函数（用于纯文本内容）
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 导出函数（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        containsMarkdown,
        renderMarkdown,
        escapeHtml
    };
}

