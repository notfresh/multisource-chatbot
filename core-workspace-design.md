# 核心工作区功能设计

## 一、核心概念

**核心工作区 = 用户创建的主题工作区，用于分类管理重要内容**

- **可创建多个工作区**：用户可以创建多个工作区，如"AI学习"、"项目规划"、"读书笔记"等
- **会话关联工作区**：每次开启新会话时，可以选择一个工作区
- **5星内容自动进入**：在该会话中标记为 5 星的内容，自动进入关联的工作区
- **跨会话聚合**：同一工作区下的所有会话的 5 星内容都聚合在一起
- **内容生成**：基于工作区内容生成文章、总结等

### 关键设计点

1. **工作区是独立的**：用户可以创建多个工作区，按主题分类
2. **会话选择工作区**：创建新会话时，选择关联的工作区（可选）
3. **5星 = 进入工作区**：标记为 5 星的内容自动进入当前会话关联的工作区
4. **自动创建工作区**：如果会话没有关联工作区，当标记第一条5星内容时，自动创建并关联工作区
5. **工作区视图**：可以查看每个工作区的所有 5 星内容

### 自动创建工作区逻辑

**场景：**
- 用户创建了一个新会话，但没有选择工作区
- 用户在对话中标记了一条内容为 5 星
- 系统检测到会话没有关联工作区

**处理流程：**
1. 检测到会话没有 `workspace_id`
2. 自动创建一个新工作区
3. 工作区名称：使用会话标题或第一条5星消息的前20个字符
4. 将工作区关联到该会话
5. 5星消息正常进入工作区
6. 提示用户："已自动创建工作区「XXX」，后续的5星内容将进入此工作区"

---

## 二、功能价值

### 2.1 解决的问题

**用户痛点：**
- 长期对话中积累了大量有价值的问答，但主题混杂
- 想要按主题分类整理，但手动分类耗时
- 不同主题的内容混在一起，难以生成针对性的文章

**解决方案：**
- **创建主题工作区**：如"AI学习"、"项目规划"、"读书笔记"
- **会话关联工作区**：开启会话时选择工作区，自动分类
- **5星自动进入**：标记为 5 星的内容自动进入关联的工作区
- **按工作区生成**：基于特定工作区生成主题文章

### 2.2 使用流程

**方式一：提前创建工作区**
```
1. 创建核心工作区（如"AI学习"）
   ↓
2. 开启新会话，选择"AI学习"工作区
   ↓
3. 在对话中遇到重要内容，标记为 5 星
   ↓
4. 5星内容自动进入"AI学习"工作区
   ↓
5. 在"AI学习"工作区中，点击"生成文章总结"
   ↓
6. 生成关于AI学习的主题文章
```

**方式二：自动创建工作区（更流畅）**
```
1. 开启新会话（不选择工作区）
   ↓
2. 在对话中遇到重要内容，标记为 5 星
   ↓
3. 系统自动创建工作区（名称基于会话标题或消息内容）
   ↓
4. 5星内容自动进入新创建的工作区
   ↓
5. 后续的5星内容继续进入该工作区
   ↓
6. 在工作区中，点击"生成文章总结"
   ↓
7. 生成主题文章
```

### 2.2 使用场景

1. **知识工作者**
   - 将重要对话整理成知识文档
   - 生成方法论总结
   - 创建个人知识库

2. **创作者**
   - 将灵感对话整理成文章
   - 生成内容大纲
   - 提取核心观点

3. **学习者**
   - 将学习要点整理成笔记
   - 生成复习材料
   - 创建知识卡片

---

## 三、数据结构

### 3.1 工作区模型

```python
class Workspace(db.Model):
    """
    核心工作区
    """
    __tablename__ = 'workspaces'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # 工作区名称，如"AI学习"
    description = db.Column(db.Text)  # 工作区描述（可选）
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = db.Column(db.Boolean, default=False)  # 软删除
    
    # 关联关系
    conversations = db.relationship('Conversation', backref='workspace', lazy='dynamic')
    
    def __repr__(self):
        return f'<Workspace {self.id}: {self.name}>'
    
    def get_core_messages(self):
        """
        获取该工作区下的所有5星消息
        """
        conversation_ids = [c.id for c in self.conversations.filter_by(is_deleted=False).all()]
        return Message.query.filter(
            Message.conversation_id.in_(conversation_ids),
            Message.weight == 5,
            Message.is_deleted == False
        ).order_by(Message.created_at.desc()).all()
```

### 3.2 会话模型更新

```python
class Conversation(db.Model):
    """
    会话模型（需要添加 workspace_id 字段）
    """
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspaces.id'), nullable=True)  # 新增：关联工作区
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # 关联关系
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
    # workspace 关系已通过 backref 定义
```

### 3.3 核心工作区视图（辅助类）

```python
class CoreWorkspace:
    """
    核心工作区辅助类
    """
    
    @staticmethod
    def get_workspace_messages(workspace_id):
        """
        获取指定工作区的所有5星消息
        """
        workspace = Workspace.query.get_or_404(workspace_id)
        return workspace.get_core_messages()
    
    @staticmethod
    def get_user_workspaces(user_id):
        """
        获取用户的所有工作区
        """
        return Workspace.query.filter_by(
            user_id=user_id,
            is_deleted=False
        ).order_by(Workspace.updated_at.desc()).all()
```

### 3.2 生成的文章/总结

```python
class GeneratedArticle(db.Model):
    """
    基于核心工作区生成的文章/总结
    """
    __tablename__ = 'generated_articles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)  # Markdown 格式
    article_type = db.Column(db.String(50))  # 'summary', 'article', 'card'
    source_message_ids = db.Column(db.Text)  # JSON: [1, 2, 3] 来源消息ID
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
```

---

## 四、API 设计

### 4.1 工作区管理

#### 创建工作区
```
POST /api/workspaces
Request Body: {
    "name": "AI学习",
    "description": "关于AI和机器学习的核心内容"  # 可选
}
Response: {
    "id": 1,
    "name": "AI学习",
    "description": "关于AI和机器学习的核心内容",
    "created_at": "..."
}
```

#### 获取用户的所有工作区
```
GET /api/workspaces
Response: [
    {
        "id": 1,
        "name": "AI学习",
        "description": "关于AI和机器学习的核心内容",
        "core_message_count": 25,  # 该工作区的5星消息数量
        "conversation_count": 8,    # 关联的会话数量
        "updated_at": "..."
    },
    {
        "id": 2,
        "name": "项目规划",
        "description": "项目相关的核心决策和规划",
        "core_message_count": 15,
        "conversation_count": 5,
        "updated_at": "..."
    }
]
```

#### 更新工作区
```
PUT /api/workspaces/<workspace_id>
Request Body: {
    "name": "AI与机器学习",  # 可选
    "description": "更新后的描述"  # 可选
}
Response: {
    "id": 1,
    "name": "AI与机器学习",
    "description": "更新后的描述"
}
```

#### 删除工作区
```
DELETE /api/workspaces/<workspace_id>
Response: {
    "success": true
}
注意：软删除，不会删除关联的消息
```

### 4.2 获取工作区内容

#### 获取指定工作区的所有5星内容
```
GET /api/workspaces/<workspace_id>/core-messages
Response: {
    "workspace": {
        "id": 1,
        "name": "AI学习",
        "description": "..."
    },
    "total": 25,
    "messages": [
        {
            "id": 1,
            "conversation_id": 5,
            "conversation_title": "关于LangChain的讨论",
            "role": "user",
            "content": "什么是LangChain？",
            "weight": 5,
            "created_at": "...",
            "assistant_reply": {
                "id": 2,
                "content": "LangChain是...",
                "weight": 5
            }
        },
        ...
    ]
}
```

### 4.3 会话关联工作区

#### 创建会话时选择工作区
```
POST /api/conversations
Request Body: {
    "title": "新对话",  # 可选
    "workspace_id": 1   # 可选，关联的工作区ID
}
Response: {
    "id": 1,
    "title": "新对话",
    "workspace_id": 1,
    "workspace_name": "AI学习",
    "created_at": "..."
}
```

#### 更新会话的工作区
```
PUT /api/conversations/<conversation_id>/workspace
Request Body: {
    "workspace_id": 2  # 切换到另一个工作区
}
Response: {
    "id": 1,
    "workspace_id": 2,
    "workspace_name": "项目规划"
}
```

### 4.4 更新消息权重（自动创建工作区）

#### 更新消息权重
```
PUT /api/messages/<message_id>/weight
Request Body: { "weight": 5 }  # 1-5
Response: {
    "id": 1,
    "weight": 5,
    "workspace_created": true,  # 如果自动创建了工作区，返回true
    "workspace": {              # 如果自动创建了工作区，返回工作区信息
        "id": 3,
        "name": "关于LangChain的讨论",
        "description": null
    }
}
```

**自动创建工作区逻辑：**
- 当消息权重更新为 5 时，检查会话是否有关联工作区
- 如果没有关联工作区，自动创建一个新工作区
- 工作区名称生成规则：
  1. 优先使用会话标题（如果存在且不为空）
  2. 否则使用该消息内容的前20个字符
  3. 如果消息是用户提问，使用提问内容
  4. 如果消息是AI回答，使用对应的用户提问内容
- 自动关联工作区到该会话
- 返回工作区信息，前端可以提示用户

### 4.5 生成文章总结

#### 基于工作区生成文章
```
POST /api/workspaces/<workspace_id>/generate-article
Request Body: {
    "title": "我的AI学习总结",  # 可选
    "type": "article",  # 'article', 'summary', 'card'
    "message_ids": [1, 2, 3],  # 可选，指定哪些消息，不传则使用工作区所有5星
    "prompt": "请将这些内容整理成一篇结构化的文章"  # 可选，自定义提示词
}
Response: {
    "article_id": 1,
    "title": "我的AI学习总结",
    "content": "# 我的AI学习总结\n\n...",
    "source_count": 25,
    "workspace_id": 1,
    "workspace_name": "AI学习"
}
```

### 4.6 获取生成的文章列表

```
GET /api/articles
Response: [
    {
        "id": 1,
        "title": "我的AI学习总结",
        "type": "article",
        "created_at": "...",
        "source_count": 25
    },
    ...
]
```

### 4.7 获取单篇文章

```
GET /api/articles/<article_id>
Response: {
    "id": 1,
    "title": "我的AI学习总结",
    "content": "# 我的AI学习总结\n\n...",
    "type": "article",
    "source_messages": [...],  # 来源消息
    "created_at": "..."
}
```

---

## 五、自动创建工作区实现

### 5.1 更新消息权重时的自动创建逻辑

```python
@api.route('/messages/<int:message_id>/weight', methods=['PUT'])
@login_required
def update_message_weight(message_id):
    """
    更新消息权重
    如果权重为5且会话没有关联工作区，自动创建工作区
    """
    message = Message.query.get_or_404(message_id)
    conversation = message.conversation
    
    # 权限检查
    if conversation.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    new_weight = data.get('weight', 1)
    
    if not (1 <= new_weight <= 5):
        return jsonify({'error': 'Weight must be between 1 and 5'}), 400
    
    # 更新权重
    message.weight = new_weight
    workspace_created = False
    new_workspace = None
    
    # 如果权重为5，且会话没有关联工作区，自动创建工作区
    if new_weight == 5 and conversation.workspace_id is None:
        # 生成工作区名称
        workspace_name = generate_workspace_name(conversation, message)
        
        # 创建工作区
        new_workspace = Workspace(
            user_id=current_user.id,
            name=workspace_name,
            description=None
        )
        db.session.add(new_workspace)
        db.session.flush()  # 获取ID
        
        # 关联工作区到会话
        conversation.workspace_id = new_workspace.id
        workspace_created = True
    
    db.session.commit()
    
    response = {
        'id': message.id,
        'weight': new_weight
    }
    
    if workspace_created:
        response['workspace_created'] = True
        response['workspace'] = {
            'id': new_workspace.id,
            'name': new_workspace.name,
            'description': new_workspace.description
        }
    
    return jsonify(response)


def generate_workspace_name(conversation, message):
    """
    生成工作区名称
    
    规则：
    1. 优先使用会话标题（如果存在且不为空）
    2. 否则使用消息内容的前20个字符
    3. 如果消息是AI回答，尝试找到对应的用户提问
    """
    # 规则1：使用会话标题
    if conversation.title and conversation.title.strip():
        return conversation.title.strip()[:50]  # 限制长度
    
    # 规则2：使用消息内容
    content = message.content.strip()
    
    # 规则3：如果是AI回答，尝试找到对应的用户提问
    if message.role == 'assistant':
        # 查找同会话中，该消息之前的最后一条用户消息
        user_message = Message.query.filter(
            Message.conversation_id == conversation.id,
            Message.role == 'user',
            Message.order_index < message.order_index,
            Message.is_deleted == False
        ).order_by(Message.order_index.desc()).first()
        
        if user_message:
            content = user_message.content.strip()
    
    # 取前20个字符，去除换行和多余空格
    name = content.replace('\n', ' ').replace('\r', ' ').strip()[:20]
    
    # 如果为空，使用默认名称
    if not name:
        name = f"工作区 {conversation.id}"
    
    return name
```

### 5.2 前端提示

当自动创建工作区时，前端应该显示提示：

```javascript
// 更新权重后
if (response.workspace_created) {
    showNotification(
        `已自动创建工作区「${response.workspace.name}」`,
        '后续的5星内容将进入此工作区',
        'info'
    );
}
```

---

## 六、生成逻辑

### 6.1 文章生成流程

```python
def generate_article_from_workspace(
    workspace_id,
    article_type='article',
    message_ids=None,
    custom_prompt=None
):
    """
    基于工作区生成文章
    
    Args:
        workspace_id: 工作区ID
        article_type: 文章类型
        message_ids: 指定的消息ID列表（可选）
        custom_prompt: 自定义提示词（可选）
    """
    # 1. 获取工作区
    workspace = Workspace.query.get_or_404(workspace_id)
    
    # 2. 获取工作区的核心内容（5星消息）
    if message_ids:
        # 指定消息ID，但需要验证这些消息属于该工作区
        messages = Message.query.filter(
            Message.id.in_(message_ids),
            Message.conversation.has(workspace_id=workspace_id),
            Message.weight == 5,
            Message.is_deleted == False
        ).all()
    else:
        # 使用工作区的所有5星消息
        messages = workspace.get_core_messages()
    
    # 2. 组织内容（按会话分组，保持问答对）
    organized_content = organize_messages_by_conversation(messages)
    
    # 3. 构建提示词
    if custom_prompt:
        prompt = custom_prompt
    else:
        prompt = build_default_prompt(article_type, organized_content)
    
    # 4. 调用AI生成文章
    from app.ai import ChatManager
    manager = ChatManager()
    article_content = manager.generate_article(prompt, organized_content)
    
    # 5. 保存文章
    article = GeneratedArticle(
        user_id=workspace.user_id,
        workspace_id=workspace_id,  # 关联工作区
        title=extract_title(article_content),
        content=article_content,
        article_type=article_type,
        source_message_ids=json.dumps([m.id for m in messages])
    )
    db.session.add(article)
    db.session.commit()
    
    return article
```

### 6.2 提示词模板

```python
def build_default_prompt(article_type, organized_content):
    """
    构建默认提示词
    """
    if article_type == 'article':
        return f"""
请将以下核心对话内容整理成一篇结构化的文章。

要求：
1. 标题清晰，层次分明
2. 保持问答的逻辑关系
3. 添加适当的过渡和连接
4. 使用 Markdown 格式
5. 突出关键观点

内容：
{format_messages_for_prompt(organized_content)}
"""
    elif article_type == 'summary':
        return f"""
请将以下内容整理成简洁的总结。

要求：
1. 提取核心观点
2. 保持简洁
3. 使用要点列表
4. Markdown 格式

内容：
{format_messages_for_prompt(organized_content)}
"""
    elif article_type == 'card':
        return f"""
请将以下内容整理成知识卡片格式。

要求：
1. 每个问答对一张卡片
2. 提取关键概念
3. 结构化展示
4. Markdown 格式

内容：
{format_messages_for_prompt(organized_content)}
"""
```

---

## 七、UI 设计

### 7.1 工作区列表页面

```
┌─────────────────────────────────────────────────────────┐
│  核心工作区                              [+ 新建工作区]   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 📁 AI学习                                        │   │
│  │ 关于AI和机器学习的核心内容                       │   │
│  │ 25条核心内容 | 8个会话 | 更新于 2024-01-20      │   │
│  │ [查看] [生成文章] [编辑] [删除]                  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 📁 项目规划                                      │   │
│  │ 项目相关的核心决策和规划                         │   │
│  │ 15条核心内容 | 5个会话 | 更新于 2024-01-18      │   │
│  │ [查看] [生成文章] [编辑] [删除]                  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 📁 读书笔记                                      │   │
│  │ 读书过程中的重要观点和思考                       │   │
│  │ 10条核心内容 | 3个会话 | 更新于 2024-01-15      │   │
│  │ [查看] [生成文章] [编辑] [删除]                  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 7.2 工作区详情页面（5星内容）

```
┌─────────────────────────────────────────────────────────┐
│  ← 返回  核心工作区：AI学习          [生成文章] [导出]    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📊 统计：共 25 条核心内容，来自 8 个会话                │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ [会话：LangChain学习] 2024-01-15                 │   │
│  │                                                  │   │
│  │ Q: 什么是LangChain？                            │   │
│  │ A: LangChain是...                               │   │
│  │                                                  │   │
│  │ [⭐5] [删除] [编辑]                             │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ [会话：权重系统设计] 2024-01-20                  │   │
│  │                                                  │   │
│  │ Q: 如何设计权重系统？                           │   │
│  │ A: 权重系统的核心是...                          │   │
│  │                                                  │   │
│  │ [⭐5] [删除] [编辑]                             │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ...                                                     │
└─────────────────────────────────────────────────────────┘
```

### 7.3 创建会话时选择工作区

```
┌─────────────────────────────────────────────────────────┐
│  新建会话                                                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  会话标题（可选）：                                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 关于LangChain的讨论                              │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  关联工作区（可选）：                                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │ ▼ AI学习                                         │   │
│  │   📁 AI学习                                      │   │
│  │   📁 项目规划                                    │   │
│  │   📁 读书笔记                                    │   │
│  │   [+ 新建工作区]                                 │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  💡 提示：选择工作区后，标记为5星的内容会自动进入该工作区│
│                                                          │
│  [创建会话] [取消]                                       │
└─────────────────────────────────────────────────────────┘
```

### 7.4 生成文章页面

```
┌─────────────────────────────────────────────────────────┐
│  生成文章总结                                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  文章类型：                                              │
│  ○ 文章总结  ○ 简洁总结  ○ 知识卡片                    │
│                                                          │
│  内容来源：                                              │
│  ☑ 使用所有核心工作区内容（25条）                       │
│  ☐ 选择特定内容                                          │
│                                                          │
│  自定义提示词（可选）：                                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 请将这些内容整理成一篇关于AI学习的文章...        │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  [生成文章] [取消]                                       │
└─────────────────────────────────────────────────────────┘
```

---

## 七、实现优先级

### MVP（最小可行产品）
1. ✅ 核心工作区视图（展示所有5星内容）
2. ✅ 基础文章生成（简单总结）
3. ✅ 导出为 Markdown

### 后续迭代
4. 多种文章类型（文章、总结、卡片）
5. 自定义提示词
6. 主题分类和筛选
7. 文章编辑和更新
8. 导出为 PDF
9. 关联图谱可视化

---

## 八、技术实现要点

### 8.1 消息组织

```python
def organize_messages_by_conversation(messages):
    """
    按会话组织消息，保持问答对
    """
    organized = {}
    for msg in messages:
        conv_id = msg.conversation_id
        if conv_id not in organized:
            organized[conv_id] = {
                'conversation': msg.conversation,
                'messages': []
            }
        organized[conv_id]['messages'].append(msg)
    
    # 按时间排序，保持问答对
    for conv_id in organized:
        organized[conv_id]['messages'].sort(key=lambda x: x.order_index)
    
    return organized
```

### 8.2 内容格式化

```python
def format_messages_for_prompt(organized_content):
    """
    将消息格式化为提示词
    """
    formatted = []
    for conv_id, data in organized_content.items():
        conv_title = data['conversation'].title
        formatted.append(f"\n## 会话：{conv_title}\n")
        
        for msg in data['messages']:
            if msg.role == 'user':
                formatted.append(f"**问题：** {msg.content}\n")
            elif msg.role == 'assistant':
                formatted.append(f"**回答：** {msg.content}\n\n")
    
    return "\n".join(formatted)
```

---

## 总结

**核心工作区（5星）功能的核心价值：**

1. **自动聚合**：重要内容自动收集，无需手动整理
2. **内容生成**：基于核心内容一键生成高质量文章
3. **知识沉淀**：将对话转化为可复用的知识资产
4. **持续更新**：随着新内容加入，文章可重新生成

**这是从"对话记录"到"知识资产"的关键转化功能。**

