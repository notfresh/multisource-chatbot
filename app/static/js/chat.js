/**
 * 聊天界面主入口
 * 职责：组装所有模块，处理事件绑定和业务逻辑协调
 * 
 * 注意：由于使用传统 script 标签加载，模块通过全局命名空间访问
 * 需要在模板中按顺序加载所有依赖模块
 */

// ==================== DOM 元素（在 DOMContentLoaded 中初始化）====================
let conversationList;
let chatMessages;
let welcomeMessage;
let messageInput;
let sendButton;
let stopButton;
let btnNewConversation;

// ==================== 全局服务实例 ====================
let conversationController;
let chatService;

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', function() {
    // 检查必要的全局对象是否已加载
    const requiredModules = {
        'ConversationAPI': typeof window.ConversationAPI !== 'undefined',
        'MessageAPI': typeof window.MessageAPI !== 'undefined',
        'ConversationUI': typeof window.ConversationUI !== 'undefined',
        'MessageUI': typeof window.MessageUI !== 'undefined',
        'InputUI': typeof window.InputUI !== 'undefined',
        'StreamingService': typeof window.StreamingService !== 'undefined',
        'StreamHandler': typeof window.StreamHandler !== 'undefined',
        'chatState': typeof window.chatState !== 'undefined',
        'MessageService': typeof window.MessageService !== 'undefined',
        'ConversationController': typeof window.ConversationController !== 'undefined',
        'ChatService': typeof window.ChatService !== 'undefined'
    };
    
    // 调试信息：显示所有模块的加载状态
    console.log('模块加载状态:', requiredModules);
    
    const missingModules = Object.entries(requiredModules)
        .filter(([name, loaded]) => !loaded)
        .map(([name]) => name);
    
    if (missingModules.length > 0) {
        console.error('缺少必要的模块:', missingModules);
        console.error('当前 window 对象上的属性:', Object.keys(window).filter(k => k.includes('API') || k.includes('UI') || k.includes('Service') || k.includes('Handler') || k === 'chatState' || k.includes('Organizer')));
        alert('页面加载失败：缺少必要的模块。请刷新页面重试。\n缺少的模块: ' + missingModules.join(', '));
        return;
    }
    
    // 初始化 DOM 元素引用
    conversationList = document.getElementById('conversationList');
    chatMessages = document.getElementById('chatMessages');
    welcomeMessage = document.getElementById('welcomeMessage');
    messageInput = document.getElementById('messageInput');
    sendButton = document.getElementById('sendButton');
    stopButton = document.getElementById('stopButton');
    btnNewConversation = document.getElementById('btnNewConversation');
    
    // 将 DOM 元素挂载到 window 上，供其他模块访问
    window.chatMessages = chatMessages;
    window.messageInput = messageInput;
    window.sendButton = sendButton;
    window.stopButton = stopButton;
    
    // 检查必要的 DOM 元素是否存在
    if (!conversationList || !chatMessages || !welcomeMessage || 
        !messageInput || !sendButton || !stopButton || !btnNewConversation) {
        console.error('无法找到必要的 DOM 元素，请检查 HTML 结构');
        return;
    }
    
    // 初始化会话控制器
    conversationController = new ConversationController({
        conversationList: conversationList,
        chatMessages: chatMessages,
        welcomeMessage: welcomeMessage,
        messageInput: messageInput
    });
    
    // 初始化聊天服务（传入会话控制器）
    chatService = new ChatService(conversationController);
    
    // 将 chatService 挂载到 window 上，供其他模块访问
    window.chatService = chatService;
    
    // 加载会话列表
    conversationController.loadConversations();
    
    // 事件监听
    sendButton.addEventListener('click', () => chatService.sendMessage());
    stopButton.addEventListener('click', () => {
        // stopStreaming 现在是异步的，但不需等待
        chatService.stopStreaming().catch(err => {
            console.error('停止流式输出失败:', err);
        });
    });
    btnNewConversation.addEventListener('click', () => conversationController.createNewConversation());
    
    // Enter 发送，Shift+Enter 换行
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatService.sendMessage();
        }
    });
    
    // 自动调整输入框高度
    messageInput.addEventListener('input', function() {
        InputUI.autoResizeInput(this);
    });
});
