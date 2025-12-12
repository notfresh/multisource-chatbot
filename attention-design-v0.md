# MindLog v0 - 简化版技术方案

## 一、项目概述

**v0 版本目标：**
- ✅ 会话管理：创建、查看、切换、删除会话
- ✅ 对话历史：保存和显示用户与AI的对话记录
- ✅ 基础聊天：发送消息，获取AI回答

**暂不包含：**
- ❌ 权重系统（1-5星）
- ❌ 核心工作区
- ❌ 消息删除功能
- ❌ 流式输出
- ❌ 高级上下文管理

---

## 二、数据库设计

### 2.1 数据模型

#### 1. Conversation（会话表）
```python
class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))  # 会话标题（自动生成）
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
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
    created_at = db.Column(db.DateTime, default=datetime.now)
    order_index = db.Column(db.Integer)  # 消息在会话中的顺序
    
    def __repr__(self):
        return f'<Message {self.id}: {self.role}>'
```

**简化说明：**
- 移除了 `weight` 字段（权重功能）
- 移除了 `is_deleted` 字段（删除功能）
- 保留了核心字段：会话ID、角色、内容、时间、顺序

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

#### 获取单个会话详情（包含所有消息）
```
GET /api/conversations/<conversation_id>
Response: {
    "id": 1,
    "title": "对话1",
    "messages": [
        { "id": 1, "role": "user", "content": "...", "created_at": "..." },
        { "id": 2, "role": "assistant", "content": "...", "created_at": "..." }
    ]
}
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
    "content": "用户的问题"
}
Response: {
    "user_message": { "id": 1, "role": "user", "content": "...", "created_at": "..." },
    "assistant_message": { "id": 2, "role": "assistant", "content": "...", "created_at": "..." }
}

后端处理逻辑：
1. 创建用户消息并保存
2. 调用AI API生成回答（使用LangChain，包含所有历史消息）
3. 创建AI回答消息并保存
4. 返回两条消息
```

---

## 四、前端界面设计

### 4.1 整体布局

```
┌─────────────────────────────────────────────────────────┐
│  [Logo]  MindLog                    [用户菜单] [登出]   │
├──────────┬──────────────────────────────────────────────┤
│          │                                              │
│  会话列表│           聊天区域                            │
│          │  ┌──────────────────────────────────────┐   │
│  [+ 新对话]│  │ 消息1 (用户)                        │   │
│          │  │ 消息2 (AI)                           │   │
│  对话1   │  │ ...                                  │   │
│  对话2   │  └──────────────────────────────────────┘   │
│  对话3   │  ┌──────────────────────────────────────┐   │
│          │  │ [输入框]                    [发送]    │   │
│          │  └──────────────────────────────────────┘   │
└──────────┴──────────────────────────────────────────────┘
```

### 4.2 主要组件

#### 1. 会话侧边栏（左侧）
- **新建会话按钮**：点击创建新会话
- **会话列表**：显示所有会话
  - 显示会话标题
  - 显示最后更新时间
  - 显示消息数量（可选）
  - 点击切换会话
  - 右键菜单：重命名、删除

#### 2. 聊天主区域（中间）
- **消息列表**：显示当前会话的所有消息
  - 用户消息：右侧显示，带用户头像
  - AI消息：左侧显示，带AI头像
  - 消息内容：支持 Markdown 渲染（可选）
  - 按时间顺序显示
- **输入框区域**：
  - 多行文本输入
  - 发送按钮
  - 支持 Enter 发送，Shift+Enter 换行

---

## 五、技术栈

### 5.1 后端
- **框架**：Flask（保持现有）
- **AI集成**：LangChain + 302.ai API
  - 使用 `ConversationBufferMemory` 管理对话历史
  - 通过 LangChain 的 `ChatOpenAI` 配置自定义 `base_url` 使用 302.ai
  - 302.ai 提供兼容 OpenAI 格式的 API，模型：`deepseek-chat`
  - 支持 OpenAI、Anthropic、302.ai、模拟LLM
- **数据库**：SQLite（保持现有）

### 5.2 前端
- **基础框架**：Flask + Jinja2 模板
- **UI**：原生 CSS + 现代设计
- **JavaScript**：原生 JS（轻量级）
- **Markdown渲染**：marked.js（可选）

---

## 六、AI集成（使用 LangChain + 302.ai）

### 6.1 302.ai API 说明

302.ai 提供兼容 OpenAI 格式的 API，可以通过 LangChain 的 `ChatOpenAI` 直接使用。

**API 端点：**
```
https://api.302.ai/v1/chat/completions
```

**模型名称：**
```
deepseek-chat
```

**配置方式：**
LangChain 的 `ChatOpenAI` 支持通过 `base_url` 参数指定自定义 API 端点，这样就可以使用 302.ai 的服务。

### 6.2 LLM 配置（支持 302.ai）

```python
# app/ai/llm_config.py
import os
from typing import Optional

def get_llm(provider: str = 'mock', model_name: Optional[str] = None):
    """
    获取配置好的 LLM 实例
    
    Args:
        provider: LLM提供商，可选值：
            - 'openai': OpenAI GPT 模型
            - 'anthropic': Anthropic Claude 模型
            - '302ai': 302.ai 服务（兼容 OpenAI 格式）
            - 'mock': 模拟 LLM（用于开发测试）
        model_name: 模型名称
            - OpenAI: 'gpt-3.5-turbo', 'gpt-4' 等
            - Anthropic: 'claude-3-opus-20240229' 等
            - 302.ai: 'deepseek-chat'
    """
    if provider == 'openai':
        try:
            from langchain_openai import ChatOpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY 环境变量未设置")
            
            return ChatOpenAI(
                model_name=model_name or 'gpt-3.5-turbo',
                temperature=0.7,
                openai_api_key=api_key
            )
        except ImportError:
            raise ImportError("请安装 langchain-openai: pip install langchain-openai")
    
    elif provider == '302ai':
        try:
            from langchain_openai import ChatOpenAI
            api_key = os.getenv('API_302_AI_KEY')
            if not api_key:
                raise ValueError("API_302_AI_KEY 环境变量未设置")
            
            # 使用 base_url 指定 302.ai 的 API 端点
            return ChatOpenAI(
                model_name=model_name or 'deepseek-chat',
                temperature=0.7,
                openai_api_key=api_key,
                base_url="https://api.302.ai/v1"  # 关键：指定 302.ai 的 API 端点
            )
        except ImportError:
            raise ImportError("请安装 langchain-openai: pip install langchain-openai")
    
    elif provider == 'anthropic':
        try:
            from langchain_anthropic import ChatAnthropic
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY 环境变量未设置")
            
            return ChatAnthropic(
                model=model_name or 'claude-3-sonnet-20240229',
                temperature=0.7,
                anthropic_api_key=api_key
            )
        except ImportError:
            raise ImportError("请安装 langchain-anthropic: pip install langchain-anthropic")
    
    else:
        # 使用模拟 LLM（开发测试用）
        try:
            from langchain.llms.fake import FakeListLLM
            return FakeListLLM(responses=[
                "这是一个很好的问题。让我来帮你分析一下...",
                "根据你的问题，我认为...",
                "关于这个问题，我有以下建议..."
            ])
        except ImportError:
            # 如果 FakeListLLM 不可用，创建一个简单的模拟类
            class MockLLM:
                def predict(self, input_text):
                    return f"这是模拟回答。你刚才问的是：{input_text}"
            
            return MockLLM()


def get_default_llm():
    """
    获取默认的 LLM 实例
    
    优先级：
    1. 如果设置了 API_302_AI_KEY，使用 302.ai
    2. 如果设置了 OPENAI_API_KEY，使用 OpenAI
    3. 如果设置了 ANTHROPIC_API_KEY，使用 Anthropic
    4. 否则使用模拟 LLM
    """
    if os.getenv('API_302_AI_KEY'):
        return get_llm('302ai')
    elif os.getenv('OPENAI_API_KEY'):
        return get_llm('openai')
    elif os.getenv('ANTHROPIC_API_KEY'):
        return get_llm('anthropic')
    else:
        return get_llm('mock')
```

### 6.3 ChatManager 简化实现

```python
# app/ai/chat_manager.py
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from app.models import Message

class ChatManager:
    def __init__(self, llm=None):
        """初始化聊天管理器"""
        if llm is None:
            # 使用模拟 LLM（开发阶段）
            from langchain.llms.fake import FakeListLLM
            self.llm = FakeListLLM(responses=[
                "这是一个很好的问题。让我来帮你分析一下...",
                "根据你的问题，我认为...",
                "关于这个问题，我有以下建议..."
            ])
        else:
            self.llm = llm
    
    def build_memory_from_conversation(self, conversation_id):
        """从数据库构建 LangChain 的 ConversationBufferMemory"""
        # 获取所有消息（按顺序）
        messages = Message.query.filter_by(
            conversation_id=conversation_id
        ).order_by(Message.order_index.asc()).all()
        
        # 创建内存对象
        memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history"
        )
        
        # 将数据库消息转换为 LangChain 消息格式
        for msg in messages:
            if msg.role == "user":
                memory.chat_memory.add_user_message(msg.content)
            elif msg.role == "assistant":
                memory.chat_memory.add_ai_message(msg.content)
        
        return memory
    
    def generate_response(self, conversation_id, user_message):
        """生成AI回答"""
        # 构建对话历史
        memory = self.build_memory_from_conversation(conversation_id)
        
        # 创建对话链
        conversation = ConversationChain(
            llm=self.llm,
            memory=memory,
            verbose=True
        )
        
        # 生成回答
        return conversation.predict(input=user_message)
```

### 6.4 环境变量配置

在 `env/env.yml` 或环境变量中配置：

```yaml
# 使用 302.ai（推荐）
API_302_AI_KEY: "your-api-key-here"

# 或者使用 OpenAI
OPENAI_API_KEY: "your-openai-api-key"

# 或者使用 Anthropic
ANTHROPIC_API_KEY: "your-anthropic-api-key"
```

### 6.5 API 路由实现

```python
# app/api/messages.py
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.ai.chat_manager import ChatManager
from app.models import Message, Conversation, db

api = Blueprint('api', __name__, url_prefix='/api')
chat_manager = ChatManager()  # 全局聊天管理器

@api.route('/conversations/<int:conversation_id>/messages', methods=['POST'])
@login_required
def send_message(conversation_id):
    """发送消息并获取AI回答"""
    # 验证会话所有权
    conversation = Conversation.query.get_or_404(conversation_id)
    if conversation.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    user_content = data.get('content', '')
    
    if not user_content:
        return jsonify({'error': 'Content is required'}), 400
    
    # 获取当前消息数量，用于设置 order_index
    message_count = Message.query.filter_by(
        conversation_id=conversation_id
    ).count()
    
    # 创建用户消息
    user_message = Message(
        conversation_id=conversation_id,
        role='user',
        content=user_content,
        order_index=message_count * 2
    )
    db.session.add(user_message)
    db.session.commit()
    
    # 生成AI回答（使用 LangChain）
    assistant_content = chat_manager.generate_response(
        conversation_id,
        user_content
    )
    
    # 保存AI回答
    assistant_message = Message(
        conversation_id=conversation_id,
        role='assistant',
        content=assistant_content,
        order_index=message_count * 2 + 1
    )
    db.session.add(assistant_message)
    db.session.commit()
    
    # 更新会话的 updated_at
    conversation.updated_at = datetime.now()
    db.session.commit()
    
    return jsonify({
        'user_message': {
            'id': user_message.id,
            'role': 'user',
            'content': user_content,
            'created_at': user_message.created_at.isoformat()
        },
        'assistant_message': {
            'id': assistant_message.id,
            'role': 'assistant',
            'content': assistant_content,
            'created_at': assistant_message.created_at.isoformat()
        }
    })
```

---

## 七、实现步骤

### Phase 1: 数据库和模型（1天）
1. ✅ 创建 `Conversation` 和 `Message` 模型（简化版）
2. ✅ 创建数据库迁移
3. ✅ 测试模型关系

### Phase 2: 后端API（1-2天）
1. ✅ 实现会话管理API（创建、列表、详情、更新、删除）
2. ✅ 实现消息发送API（创建用户消息 + AI回答）
3. ✅ 集成 LangChain + 302.ai（使用 ChatManager）
4. ✅ 添加权限验证（确保用户只能访问自己的会话）

### Phase 3: 前端界面（2-3天）
1. ✅ 设计并实现会话侧边栏
2. ✅ 设计并实现聊天主区域
3. ✅ 实现消息发送和显示
4. ✅ 实现会话切换功能

### Phase 4: 测试和优化（1天）
1. ✅ 功能测试
2. ✅ 基础错误处理
3. ✅ UI优化

---

## 八、文件结构

```
app/
├── models.py              # 添加 Conversation, Message 模型（简化版）
├── ai/                    # AI模块（LangChain + 302.ai集成）
│   ├── __init__.py
│   ├── llm_config.py      # LLM配置（支持 302.ai、OpenAI、Anthropic）
│   └── chat_manager.py    # 聊天管理器（简化版）
├── api/                   # API模块
│   ├── __init__.py
│   ├── conversations.py   # 会话相关API
│   └── messages.py        # 消息相关API
├── templates/
│   ├── chat.html          # 聊天页面
│   └── components/        # 组件模板（可选）
│       └── sidebar.html   # 会话侧边栏
└── static/
    ├── css/
    │   └── chat.css       # 聊天界面样式
    └── js/
        └── chat.js        # 聊天交互逻辑
```

---

## 九、核心功能清单

### 必须实现（MVP）
- [x] 创建新会话
- [x] 查看会话列表
- [x] 切换会话
- [x] 删除会话
- [x] 重命名会话
- [x] 发送消息
- [x] 显示对话历史
- [x] AI回答生成

### 可选实现
- [ ] Markdown渲染
- [ ] 会话标题自动生成（基于第一条消息）
- [ ] 加载状态提示
- [ ] 错误提示

---

## 十、开发优先级

**第一优先级（核心功能）：**
1. 会话创建和列表
2. 消息发送和显示
3. AI回答生成

**第二优先级（体验优化）：**
4. 会话切换
5. 会话删除和重命名
6. 基础UI美化

**第三优先级（可选）：**
7. Markdown渲染
8. 加载状态
9. 错误处理

---

## 总结

v0 版本专注于核心功能：**会话管理 + 对话历史**。

- **简单**：只包含必要的功能，不涉及复杂的权重、工作区等
- **快速**：预计 5-7 个工作日完成
- **可扩展**：为后续版本（权重、工作区等）打好基础

完成 v0 后，可以在此基础上逐步添加：
- v1: 权重系统
- v2: 消息删除功能
- v3: 核心工作区
- v4: 流式输出
- ...


