# 对话系统改造技术方案

## 一、项目概述

将现有的短网址服务改造成一个对话系统，支持：
1. **权重设置**：为每个聊天单元（问题/回答）设置 1-5 星权重
2. **删除功能**：删除任意聊天单元
3. **会话管理**：支持多会话创建、切换、删除
4. **现代化UI**：模仿 ChatGPT/Claude 等大模型官方网页界面

---

## 二、数据库设计

### 2.0 核心设计原则

**软删除消息的处理规则：**
- ✅ 软删除的消息（`is_deleted=True`）在数据库中保留，但**不会出现在任何查询结果中**
- ✅ 构建AI对话上下文时，**自动过滤掉已删除的消息**
- ✅ 前端显示时，**不显示已删除的消息**
- ✅ 这意味着：用户删除的消息不会影响后续的AI回答

### 2.1 新增数据模型

#### 1. Conversation（会话表）
```python
class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))  # 会话标题（自动生成或手动设置）
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = db.Column(db.Boolean, default=False)  # 软删除标记
    
    # 关联关系
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Conversation {self.id}: {self.title}>'
```

#### 2. Message（消息表）
```python
class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' 或 'assistant'
    content = db.Column(db.Text, nullable=False)  # 消息内容
    weight = db.Column(db.Integer, default=1)  # 权重 1-5，默认1
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_deleted = db.Column(db.Boolean, default=False)  # 软删除标记
    order_index = db.Column(db.Integer)  # 消息在会话中的顺序
    
    def __repr__(self):
        return f'<Message {self.id}: {self.role}>'
```

### 2.2 数据库迁移

需要创建新的迁移文件：
```bash
python manage.py db migrate -m "Add conversation and message models"
python manage.py db upgrade
```

---

## 三、后端API设计

### 3.1 会话管理API

#### 创建会话
```
POST /api/conversations
Request Body: { "title": "新对话" }  # 可选，不传则自动生成
Response: { "id": 1, "title": "新对话", "created_at": "..." }
```

#### 获取会话列表
```
GET /api/conversations
Response: [
    { "id": 1, "title": "对话1", "updated_at": "...", "message_count": 10 },
    { "id": 2, "title": "对话2", "updated_at": "...", "message_count": 5 }
]
```

#### 获取单个会话详情
```
GET /api/conversations/<conversation_id>?include_deleted=false
Response: {
    "id": 1,
    "title": "对话1",
    "messages": [
        { "id": 1, "role": "user", "content": "...", "weight": 3, "created_at": "...", "is_deleted": false },
        { "id": 2, "role": "assistant", "content": "...", "weight": 1, "created_at": "...", "is_deleted": false }
    ]
}
注意：默认不返回已删除的消息（include_deleted=false），除非明确指定
```

#### 更新会话标题
```
PUT /api/conversations/<conversation_id>
Request Body: { "title": "新标题" }
Response: { "id": 1, "title": "新标题" }
```

#### 删除会话
```
DELETE /api/conversations/<conversation_id>
Response: { "success": true }
```

### 3.2 消息管理API

#### 发送消息（创建用户消息 + AI回答）
```
POST /api/conversations/<conversation_id>/messages
Request Body: {
    "content": "用户的问题",
    "stream": false  # 是否流式返回（后续实现）
}
Response: {
    "user_message": { "id": 1, "role": "user", "content": "...", "weight": 1 },
    "assistant_message": { "id": 2, "role": "assistant", "content": "...", "weight": 1 }
}

后端处理逻辑：
1. 创建用户消息并保存
2. 调用 build_context_for_ai() 构建上下文（自动过滤已删除消息）
3. 调用AI API生成回答（使用过滤后的上下文）
4. 创建AI回答消息并保存
5. 返回两条消息
```

#### 更新消息权重
```
PUT /api/messages/<message_id>/weight
Request Body: { "weight": 5 }  # 1-5
Response: { "id": 1, "weight": 5 }
```

#### 删除消息
```
DELETE /api/messages/<message_id>
Response: { "success": true }
```

---

## 四、前端界面设计

### 4.1 整体布局

参考 ChatGPT 的布局：
```
┌─────────────────────────────────────────────────────────┐
│  [Logo]  MindLog                    [用户菜单] [登出]   │
├──────────┬──────────────────────────────────────────────┤
│          │                                              │
│  会话列表│           聊天区域                            │
│          │  ┌──────────────────────────────────────┐   │
│  [+ 新对话]│  │ 消息1 (用户)      [⭐3] [删除]      │   │
│          │  │ 消息2 (AI)         [⭐1] [删除]      │   │
│  对话1   │  │ ...                                  │   │
│  对话2   │  └──────────────────────────────────────┘   │
│  对话3   │  ┌──────────────────────────────────────┐   │
│          │  │ [输入框]                    [发送]    │   │
│          │  └──────────────────────────────────────┘   │
└──────────┴──────────────────────────────────────────────┘
```

### 4.2 主要组件

#### 1. 会话侧边栏（左侧）
- 新建会话按钮
- 会话列表（可滚动）
- 每个会话项显示：标题、最后更新时间、消息数量
- 点击会话项切换对话
- 右键菜单：重命名、删除

#### 2. 聊天主区域（中间）
- 消息列表（可滚动）
- 每条消息显示：
  - 用户头像/AI头像
  - 消息内容（支持 Markdown 渲染）
  - 操作按钮：权重选择器（1-5星）、删除按钮
- 输入框区域：
  - 多行文本输入
  - 发送按钮
  - 支持 Enter 发送，Shift+Enter 换行

#### 3. 权重选择器
- 点击消息旁的星标图标
- 弹出选择器：1-5星
- 已设置的权重高亮显示
- 点击数字更新权重

---

## 五、技术栈选择

### 5.1 前端技术
- **基础框架**：保持 Flask + Jinja2 模板
- **UI框架**：移除 Bootstrap，使用原生 CSS + 现代设计
- **JavaScript**：原生 JS 或 Vue.js（轻量级，仅用于交互）
- **Markdown渲染**：marked.js 或 marked
- **图标**：Font Awesome 或 Heroicons

### 5.2 后端技术
- **框架**：Flask（保持现有）
- **API**：Flask-RESTful 或 Flask 原生路由（推荐原生，更灵活）
- **AI集成**：**LangChain** - 用于管理对话历史、LLM集成、流式输出
  - LangChain 提供 `ChatMessageHistory` 管理对话历史
  - 支持 OpenAI、Claude、本地模型等多种 LLM
  - 内置流式输出支持
  - 自动处理上下文窗口和 token 限制
- **流式响应**：LangChain 的 `stream()` 方法 + Flask 的 `Response(stream_with_context())`

---

## 六、LangChain 快速开始

### 6.1 安装依赖

```bash
# 激活虚拟环境后
pip install -r requirements.txt
```

### 6.2 测试 LangChain 集成

已创建基础代码文件：
- `app/ai/__init__.py` - AI模块初始化
- `app/ai/llm_config.py` - LLM配置（支持OpenAI、Anthropic、模拟LLM）
- `app/ai/chat_manager.py` - 聊天管理器（使用LangChain）

**测试代码：**

```python
# 在 Python shell 中测试
from app import create_app
from app.ai import ChatManager
from app.db import db

app = create_app('development')
with app.app_context():
    # 创建聊天管理器（默认使用模拟LLM）
    manager = ChatManager()
    
    # 测试生成回答（需要先有会话和消息数据）
    # response = manager.generate_response(conversation_id=1, user_message="你好")
    # print(response)
```

### 6.3 配置真实 LLM（可选）

**使用 OpenAI：**
```bash
# 设置环境变量
export OPENAI_API_KEY="your-api-key-here"

# 或在 env/env.yml 中添加
OPENAI_API_KEY: your-api-key-here
```

**使用 Anthropic Claude：**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

**代码中使用：**
```python
from app.ai import get_llm, ChatManager

# 使用 OpenAI
llm = get_llm('openai', model_name='gpt-3.5-turbo')
manager = ChatManager(llm=llm)

# 使用 Anthropic
llm = get_llm('anthropic', model_name='claude-3-sonnet-20240229')
manager = ChatManager(llm=llm)
```

### 6.4 LangChain 核心优势

1. **自动管理对话历史**：`ConversationBufferMemory` 自动处理消息格式
2. **支持多种LLM**：OpenAI、Anthropic、本地模型等
3. **流式输出**：内置流式支持，无需手动实现
4. **上下文管理**：自动处理 token 限制和上下文窗口
5. **易于扩展**：可以轻松添加 RAG、工具调用等功能

---

## 七、实现步骤

### Phase 1: 数据库和模型（1-2天）
1. ✅ 创建 `Conversation` 和 `Message` 模型
2. ✅ 创建数据库迁移
3. ✅ 测试模型关系

### Phase 2: 后端API（2-3天）
1. ✅ 实现会话管理API（CRUD）
2. ✅ 实现消息管理API（创建、更新权重、删除）
3. ✅ **集成 LangChain**（已完成基础代码）
4. ✅ 实现AI回答API（使用 LangChain 的 ChatManager）
5. ✅ 添加权限验证（确保用户只能访问自己的会话）

### Phase 3: 前端界面（3-4天）
1. ✅ 设计并实现会话侧边栏
2. ✅ 设计并实现聊天主区域
3. ✅ 实现消息发送和显示
4. ✅ 实现权重设置UI和交互
5. ✅ 实现删除功能UI和交互
6. ✅ 实现会话切换功能

### Phase 4: 交互优化（1-2天）
1. ✅ 添加加载状态
2. ✅ 添加错误处理
3. ✅ 优化移动端响应式
4. ✅ 添加键盘快捷键

### Phase 5: 测试和优化（1天）
1. ✅ 功能测试
2. ✅ 性能优化
3. ✅ 代码重构

---

## 八、关键实现细节

### 7.1 权重设置交互

**前端实现：**
```javascript
// 点击星标图标
function showWeightSelector(messageId, currentWeight) {
    const selector = document.createElement('div');
    selector.className = 'weight-selector';
    for (let i = 1; i <= 5; i++) {
        const star = document.createElement('span');
        star.textContent = i <= currentWeight ? '★' : '☆';
        star.onclick = () => updateWeight(messageId, i);
        selector.appendChild(star);
    }
    // 显示在选择器位置
}

// 调用API更新权重
async function updateWeight(messageId, weight) {
    const response = await fetch(`/api/messages/${messageId}/weight`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ weight })
    });
    // 更新UI
}
```

### 7.2 删除功能

**软删除实现：**
- 数据库中使用 `is_deleted` 标记，不真正删除数据
- 前端删除后，消息从界面移除
- **核心规则：软删除的消息在构建对话历史时会被过滤，不会发送给大模型**
- 支持恢复功能（可选，后续实现）

**统一的查询方法（重要）：**
```python
# 在 models.py 中添加查询方法
class Message(db.Model):
    # ... 字段定义 ...
    
    @staticmethod
    def get_active_messages(conversation_id):
        """
        获取会话中所有未删除的消息
        这是标准查询方法，所有地方都应该使用这个方法
        """
        return Message.query.filter_by(
            conversation_id=conversation_id,
            is_deleted=False  # 关键：只返回未删除的消息
        ).order_by(Message.order_index.asc()).all()
    
    @staticmethod
    def get_all_messages(conversation_id, include_deleted=False):
        """
        获取所有消息（包括已删除的，用于管理后台等场景）
        """
        query = Message.query.filter_by(conversation_id=conversation_id)
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        return query.order_by(Message.order_index.asc()).all()
```

**删除消息的API实现：**
```python
@api.route('/messages/<int:message_id>', methods=['DELETE'])
@login_required
def delete_message(message_id):
    """
    软删除消息
    删除后，该消息不会出现在对话历史中，也不会发送给AI
    """
    message = Message.query.get_or_404(message_id)
    
    # 权限检查：只能删除自己的消息
    if message.conversation.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # 软删除
    message.is_deleted = True
    db.session.commit()
    
    return jsonify({'success': True, 'message': '消息已删除'})
```

### 7.3 会话管理

**会话切换：**
- 点击侧边栏会话项，加载该会话的所有消息
- 使用 AJAX 异步加载，不刷新页面
- 当前会话高亮显示

**会话标题自动生成：**
- 使用第一条用户消息的前20个字符
- 支持用户手动修改

### 7.4 AI回答生成（使用 LangChain）

**LangChain 集成架构：**

```python
# app/ai/chat_manager.py
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI  # 或其他 LLM
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.chains import ConversationChain
from app.models import Message, Conversation

class ChatManager:
    """
    使用 LangChain 管理对话和生成AI回答
    """
    
    def __init__(self, llm=None):
        """
        初始化聊天管理器
        
        Args:
            llm: LangChain LLM 实例，如果为 None 则使用默认配置
        """
        # 如果没有提供 LLM，使用模拟 LLM（开发阶段）
        if llm is None:
            from langchain.llms.fake import FakeListLLM
            self.llm = FakeListLLM(responses=[
                "这是一个很好的问题。让我来帮你分析一下...",
                "根据你的问题，我认为...",
                "关于这个问题，我有以下建议..."
            ])
        else:
            self.llm = llm
    
    def build_memory_from_conversation(self, conversation_id):
        """
        从数据库构建 LangChain 的 ConversationBufferMemory
        
        关键：只包含未删除的消息（is_deleted=False）
        
        Returns:
            ConversationBufferMemory: LangChain 内存对象
        """
        # 获取所有未删除的消息
        messages = Message.get_active_messages(conversation_id)
        
        # 创建内存对象
        memory = ConversationBufferMemory(
            return_messages=True,  # 返回消息对象而不是字符串
            memory_key="chat_history"
        )
        
        # 将数据库消息转换为 LangChain 消息格式
        for msg in messages:
            if msg.role == "user":
                memory.chat_memory.add_user_message(msg.content)
            elif msg.role == "assistant":
                memory.chat_memory.add_ai_message(msg.content)
        
        return memory
    
    def generate_response(self, conversation_id, user_message, stream=False):
        """
        生成AI回答
        
        Args:
            conversation_id: 会话ID
            user_message: 用户消息
            stream: 是否流式返回
        
        Returns:
            str 或 Generator: AI回答内容
        """
        # 构建对话历史（自动过滤已删除消息）
        memory = self.build_memory_from_conversation(conversation_id)
        
        # 创建对话链
        conversation = ConversationChain(
            llm=self.llm,
            memory=memory,
            verbose=True
        )
        
        # 生成回答
        if stream:
            # 流式输出
            return conversation.predict_stream(input=user_message)
        else:
            # 普通输出
            return conversation.predict(input=user_message)
    
    def generate_response_with_weight(self, conversation_id, user_message):
        """
        考虑权重的回答生成（高级功能）
        
        高权重消息优先保留在上下文中
        """
        # 获取所有未删除的消息，按权重排序
        messages = Message.get_active_messages(conversation_id)
        
        # 分离高权重消息（weight >= 4）和普通消息
        high_weight_messages = [m for m in messages if m.weight >= 4]
        normal_messages = [m for m in messages if m.weight < 4]
        
        # 构建内存：高权重消息 + 最近的普通消息
        memory = ConversationBufferMemory(return_messages=True)
        
        # 先添加高权重消息
        for msg in high_weight_messages:
            if msg.role == "user":
                memory.chat_memory.add_user_message(msg.content)
            elif msg.role == "assistant":
                memory.chat_memory.add_ai_message(msg.content)
        
        # 再添加最近的普通消息（限制数量）
        recent_normal = normal_messages[-20:]  # 最近20条
        for msg in recent_normal:
            if msg.role == "user":
                memory.chat_memory.add_user_message(msg.content)
            elif msg.role == "assistant":
                memory.chat_memory.add_ai_message(msg.content)
        
        # 生成回答
        conversation = ConversationChain(
            llm=self.llm,
            memory=memory,
            verbose=True
        )
        
        return conversation.predict(input=user_message)
```

**API 路由实现：**

```python
# app/api/messages.py
from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_login import login_required, current_user
from app.ai.chat_manager import ChatManager
from app.models import Message, Conversation, db
from app.db import db

api = Blueprint('api', __name__, url_prefix='/api')
chat_manager = ChatManager()  # 全局聊天管理器

@api.route('/conversations/<int:conversation_id>/messages', methods=['POST'])
@login_required
def send_message(conversation_id):
    """
    发送消息并获取AI回答
    """
    # 验证会话所有权
    conversation = Conversation.query.get_or_404(conversation_id)
    if conversation.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    user_content = data.get('content', '')
    stream = data.get('stream', False)
    
    if not user_content:
        return jsonify({'error': 'Content is required'}), 400
    
    # 获取当前消息数量，用于设置 order_index
    message_count = Message.query.filter_by(
        conversation_id=conversation_id,
        is_deleted=False
    ).count()
    
    # 创建用户消息
    user_message = Message(
        conversation_id=conversation_id,
        role='user',
        content=user_content,
        order_index=message_count * 2,
        weight=1
    )
    db.session.add(user_message)
    db.session.commit()
    
    # 生成AI回答（使用 LangChain）
    if stream:
        # 流式返回
        def generate():
            assistant_content = ""
            for chunk in chat_manager.generate_response(
                conversation_id, 
                user_content, 
                stream=True
            ):
                assistant_content += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
            # 保存完整的AI回答
            assistant_message = Message(
                conversation_id=conversation_id,
                role='assistant',
                content=assistant_content,
                order_index=message_count * 2 + 1,
                weight=1
            )
            db.session.add(assistant_message)
            db.session.commit()
            
            yield f"data: {json.dumps({'done': True})}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream'
        )
    else:
        # 普通返回
        assistant_content = chat_manager.generate_response(
            conversation_id,
            user_content,
            stream=False
        )
        
        # 保存AI回答
        assistant_message = Message(
            conversation_id=conversation_id,
            role='assistant',
            content=assistant_content,
            order_index=message_count * 2 + 1,
            weight=1
        )
        db.session.add(assistant_message)
        db.session.commit()
        
        return jsonify({
            'user_message': {
                'id': user_message.id,
                'role': 'user',
                'content': user_content,
                'weight': 1
            },
            'assistant_message': {
                'id': assistant_message.id,
                'role': 'assistant',
                'content': assistant_content,
                'weight': 1
            }
        })
```

**配置真实 LLM（可选）：**

```python
# app/ai/llm_config.py
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import os

def get_llm(provider='openai', model_name=None):
    """
    获取配置好的 LLM 实例
    
    Args:
        provider: 'openai', 'anthropic', 'mock'
        model_name: 模型名称，如 'gpt-3.5-turbo', 'claude-3-opus'
    """
    if provider == 'openai':
        return ChatOpenAI(
            model_name=model_name or 'gpt-3.5-turbo',
            temperature=0.7,
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
    elif provider == 'anthropic':
        return ChatAnthropic(
            model=model_name or 'claude-3-opus-20240229',
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY')
        )
    else:
        # 使用模拟 LLM（开发测试用）
        from langchain.llms.fake import FakeListLLM
        return FakeListLLM(responses=["这是模拟回答..."])
```

**关键点总结：**
- ✅ 使用 LangChain 的 `ConversationBufferMemory` 管理对话历史
- ✅ 构建内存时，只包含未删除的消息（`is_deleted=False`）
- ✅ 支持流式输出和普通输出
- ✅ 支持考虑权重的上下文构建（高权重消息优先）
- ✅ 易于切换不同的 LLM 提供商（OpenAI、Claude、本地模型等）
- ✅ 软删除的消息不会出现在 LangChain 的对话历史中

---

## 九、文件结构

```
app/
├── models.py              # 添加 Conversation, Message 模型
├── ai/                    # AI模块（LangChain集成）
│   ├── __init__.py        # ✅ 已创建
│   ├── llm_config.py      # ✅ 已创建 - LLM配置
│   └── chat_manager.py    # ✅ 已创建 - 聊天管理器
├── api/                   # 新建API模块
│   ├── __init__.py
│   ├── conversations.py   # 会话相关API
│   └── messages.py        # 消息相关API
├── templates/
│   ├── chat.html          # 新的聊天页面（替代index.html）
│   └── components/        # 组件模板
│       ├── sidebar.html   # 会话侧边栏
│       └── message.html   # 消息组件
└── static/
    ├── css/
    │   └── chat.css       # 聊天界面样式
    └── js/
        └── chat.js        # 聊天交互逻辑
```

---

## 十、UI设计参考

### 9.1 颜色方案
- **背景色**：浅灰 (#f7f7f8) 或深色模式 (#343541)
- **用户消息**：蓝色 (#19c37d) 或自定义
- **AI消息**：灰色 (#f0f0f0) 或白色
- **侧边栏**：深色 (#202123)

### 9.2 字体
- **消息内容**：系统默认字体，16px
- **代码块**：等宽字体（Monaco, Consolas）

### 9.3 交互反馈
- 发送消息时显示加载动画
- 权重设置后立即更新UI
- 删除消息时显示确认提示（可选）

---

## 十一、后续扩展功能

1. **流式输出**：AI回答逐字显示
2. **Markdown支持**：代码高亮、表格等
3. **消息编辑**：支持修改已发送的消息
4. **会话导出**：导出为 Markdown/PDF
5. **搜索功能**：在会话中搜索关键词
6. **标签系统**：为会话打标签分类
7. **真实AI集成**：接入 OpenAI/Claude API

---

## 十二、风险评估

1. **数据迁移**：现有短网址数据需要保留，新功能不影响旧功能
2. **性能**：大量消息时可能需要分页加载
3. **兼容性**：确保主流浏览器支持
4. **安全性**：API需要严格的权限验证

---

## 十三、开发优先级

**MVP（最小可行产品）：**
1. ✅ 会话创建和列表
2. ✅ 消息发送和显示
3. ✅ 权重设置
4. ✅ 消息删除
5. ✅ 基础UI

**后续迭代：**
- 会话重命名
- 流式输出
- Markdown渲染
- 移动端优化

---

## 总结

本方案将现有的短网址服务改造成一个功能完整的对话系统，重点实现权重设置和删除功能，并参考主流AI聊天工具的界面设计。采用渐进式开发，先实现核心功能，再逐步完善。

预计开发时间：**7-10个工作日**

