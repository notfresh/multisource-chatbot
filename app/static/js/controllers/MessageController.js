/**
 * 消息组件控制器
 * 控制层：协调 MessageComponent（视图）、领域模型和服务
 */

class MessageController {
    /**
     * @param {MessageComponent} component - 对应的消息视图组件
     */
    constructor(component) {
        this.component = component;
    }

    /**
     * 处理模型选择
     * @param {string} model - 模型名称
     * @param {string} action - 操作类型 ('toggle' | 'request')
     */
    handleModelSelect(model, action) {
        const cmp = this.component;

        if (action === 'toggle') {
            // 切换展开/折叠
            if (cmp.modelManager) {
                cmp.modelManager.toggle(model);
            }
        } else if (action === 'request') {
            // 请求生成模型回答
            this.requestModelResponse(model);
        }
    }

    /**
     * 请求模型回答
     * @param {string} modelName - 模型名称
     */
    requestModelResponse(modelName) {
        const cmp = this.component;

        // 检查是否已有该模型的回答
        if (cmp.modelManager && cmp.modelManager.has(modelName)) {
            const response = cmp.modelManager.get(modelName);
            // 如果已有回答且有内容，直接展开/折叠，不发送请求
            if (response && response.content && response.content.trim()) {
                console.log(`模型 ${modelName} 已有回答，直接展开/折叠`);
                cmp.modelManager.toggle(modelName);
                return;
            }
        }

        // 检查是否正在加载
        const status = cmp.modelSelector && cmp.modelSelector.modelStatus?.get(modelName);
        if (status && status.isLoading) {
            console.log(`模型 ${modelName} 正在生成中，忽略重复请求`);
            return;
        }

        // 更新模型选择器状态
        if (cmp.modelSelector) {
            cmp.modelSelector.updateModelStatus(modelName, false, true);
        }

        // 创建占位符视图
        const view = cmp.modelManager.add(modelName, '', null, false);
        const viewElement = view.render();

        // 插入到所有已有模型回答之后（actionBar 之前）
        const wrapper = DOMUtils.find(cmp.rootElement, '.message-content-wrapper');
        if (wrapper) {
            const actionBar = DOMUtils.find(wrapper, '.message-actions');
            if (actionBar) {
                // 插入到 actionBar 之前，这样就在所有模型回答之后
                DOMUtils.insertBefore(wrapper, viewElement, actionBar);
            } else {
                // 如果没有 actionBar，追加到末尾
                DOMUtils.append(wrapper, viewElement);
            }
        }

        // 调用外部 API
        const userMessageId = this.findUserMessageId();
        if (userMessageId) {
            // 使用 ChatService 实例而不是全局函数
            if (typeof window.chatService !== 'undefined' &&
                typeof window.chatService.requestModelResponse === 'function') {
                window.chatService.requestModelResponse(userMessageId, modelName, cmp);
            } else {
                console.error('chatService 或 requestModelResponse 方法未定义');
                if (cmp.modelSelector) {
                    cmp.modelSelector.updateModelStatus(modelName, false, false);
                }
            }
        } else {
            console.error('无法找到用户消息ID');
            if (typeof showError === 'function') {
                showError('无法找到对应的用户消息，请刷新页面后重试');
            } else {
                alert('无法找到对应的用户消息，请刷新页面后重试');
            }
            if (cmp.modelSelector) {
                cmp.modelSelector.updateModelStatus(modelName, false, false);
            }
        }
    }

    /**
     * 更新模型回答内容（用于流式输出）
     * @param {string} modelName - 模型名称
     * @param {string} content - 内容
     * @param {boolean} isComplete - 是否已完成生成（默认 false，表示流式生成中）
     */
    updateModelResponse(modelName, content, isComplete = false) {
        const cmp = this.component;
        console.log(`更新模型回答内容：${modelName} - ${content}`);
        if (!cmp.modelManager) return;
        console.log('执行到这');
        cmp.modelManager.update(modelName, content);

        // 如果还在生成中，保持 isLoading 状态；只有完成时才设置为已完成
        if (cmp.modelSelector) {
            if (isComplete) {
                cmp.modelSelector.updateModelStatus(modelName, true, false);
            } else {
                // 流式生成中，已经有回复内容，但仍在加载
                cmp.modelSelector.updateModelStatus(modelName, true, true);
            }
        }
    }

    /**
     * 添加模型回答（兼容旧接口）
     * @param {Object} response - 回答对象 { model, content, id }
     */
    addModelResponse(response) {
        const cmp = this.component;
        if (!cmp.modelManager) return;

        const view = cmp.modelManager.add(
            response.model,
            response.content || '',
            response.id || null,
            false
        );

        // 如果视图还没有添加到 DOM，添加它
        const existingView = DOMUtils.find(
            cmp.rootElement,
            `.model-response[data-model="${response.model}"]`
        );

        if (!existingView) {
            const viewElement = view.render();
            const wrapper = DOMUtils.find(cmp.rootElement, '.message-content-wrapper');
            if (wrapper) {
                const actionBar = DOMUtils.find(wrapper, '.message-actions');
                if (actionBar) {
                    DOMUtils.insertBefore(wrapper, viewElement, actionBar);
                } else {
                    DOMUtils.append(wrapper, viewElement);
                }
            }
        }

        if (cmp.modelSelector) {
            cmp.modelSelector.updateModelStatus(response.model, true, false);
        }
    }

    /**
     * 更新消息内容（用于流式输出，仅用户消息）
     * @param {string} newContent - 新内容
     */
    updateContent(newContent) {
        const cmp = this.component;

        cmp.message.content = newContent;

        if (cmp.rootElement) {
            cmp.rootElement.dataset.originalContent = newContent;
        }

        // 如果是用户消息，更新内容
        if (cmp.message.isUser()) {
            const contentElement = DOMUtils.find(cmp.rootElement, '.message-content');
            if (contentElement) {
                const newElement = cmp.contentRenderer.render(newContent);
                if (contentElement.parentNode) {
                    contentElement.parentNode.replaceChild(newElement, contentElement);
                }
            }
        }
    }

    /**
     * 复制内容
     */
    copyContent() {
        const cmp = this.component;
        let textToCopy = '';

        if (cmp.message.isUser()) {
            // 用户消息：复制原始内容
            textToCopy = cmp.message.content;
        } else {
            // 助手消息：复制当前展开的回答
            const expanded = cmp.modelManager ? cmp.modelManager.getExpanded() : null;
            if (expanded) {
                textToCopy = expanded.content;
            }
        }

        if (textToCopy && cmp.actionBar) {
            const copyButton = cmp.actionBar.getButton('copy');
            ClipboardService.copy(textToCopy, copyButton);
        }
    }

    /**
     * 查找用户消息ID
     * @returns {number|null}
     */
    findUserMessageId() {
        const cmp = this.component;

        // 优先使用显式注入的 userMessageId
        if (cmp.userMessageId) {
            return cmp.userMessageId;
        }
        // 兜底：如果当前就是用户消息，直接用自身 id
        if (cmp.message && cmp.message.isUser && cmp.message.isUser()) {
            return cmp.message.id || null;
        }
        // 再兜底：保持旧逻辑，从 DOM 结构中向上查找一次（兼容老数据）
        if (cmp.rootElement) {
            const prevElement = cmp.rootElement.previousElementSibling;
            if (prevElement && prevElement.dataset.messageId) {
                return parseInt(prevElement.dataset.messageId);
            }
        }
        // 最后兜底：返回自身 message.id（后端一般仍能处理）
        return cmp.message.id || null;
    }
}


