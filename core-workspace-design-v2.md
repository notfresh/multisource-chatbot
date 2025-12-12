# 核心工作区功能设计 V2

## 一、核心定位

**工作区 = 可编辑的文章草稿区，目标是写文章**

工作区不是简单的素材收集箱，而是一个**可编辑的文档编辑器**，用户可以直接在工作区中编辑文章，也可以通过对话指令让AI操作文章。

---

## 二、核心结构

### 2.1 双区设计

```
工作区
├── 骨架区（文章本身，可编辑）
│   ├── 初始来源：手动创建 或 AI生成
│   ├── 编辑方式：对话指令 或 直接编辑
│   └── 格式：就是最终产出，用户负责
└── 素材区（参考库，仅供参考和待融合）
    └── 5星内容自动进入
```

### 2.2 关键设计点

1. **骨架 = 文章本身**
   - 骨架不是大纲，就是文章
   - 用户可以直接编辑骨架（像编辑器）
   - 也可以在对话中说"把第一段改成..."，AI修改骨架
   - 骨架就是最终产出

2. **素材 = 参考库**
   - 素材仅供参考，不会自动填充
   - 用户可以选择性地将素材融合到骨架中
   - 或者让AI基于素材修改骨架
   - 素材永远仅供参考和待融合

3. **用户完全掌控**
   - 骨架的格式、结构、内容，用户自己决定
   - 可以手动编辑，也可以用AI指令
   - 最终产出就是骨架本身

---

## 三、工作流程

### 3.1 完整流程

```
1. 创建工作区（或自动创建）
   ↓
2. 设置骨架（手动写 或 让AI生成初始骨架）
   ↓
3. 对话中标记5星内容 → 进入素材区
   ↓
4. 在对话中说："把第一段改成..." → AI修改骨架
   或直接在工作区编辑骨架
   ↓
5. 需要时，让AI参考素材修改骨架
   ↓
6. 骨架就是最终文章，导出即可
```

### 3.2 使用场景示例

**场景1：从零开始写文章**
```
1. 用户："总结成一篇技术文章"
2. AI：生成初始骨架（文章框架）
3. 用户：标记相关5星内容进入素材区
4. 用户："把第一章改成介绍LangChain"
5. AI：修改骨架
6. 用户："参考素材，完善第二章"
7. AI：基于素材修改骨架
8. 用户：直接编辑骨架，调整细节
9. 导出骨架 = 最终文章
```

**场景2：手动创建骨架**
```
1. 用户：手动在工作区创建骨架（写文章框架）
2. 用户：对话中标记5星内容进入素材区
3. 用户："把第一段改成..."（对话指令）
4. AI：修改骨架
5. 用户：直接编辑骨架，完善内容
6. 导出骨架 = 最终文章
```

---

## 四、数据结构

### 4.1 工作区模型

```python
class Workspace(db.Model):
    """
    核心工作区
    """
    __tablename__ = 'workspaces'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # 工作区名称
    description = db.Column(db.Text)  # 工作区描述（可选）
    
    # 骨架内容（文章本身）
    skeleton = db.Column(db.Text)  # Markdown格式，就是文章内容
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # 关联关系
    conversations = db.relationship('Conversation', backref='workspace', lazy='dynamic')
    
    def get_materials(self):
        """
        获取该工作区的所有素材（5星消息）
        """
        conversation_ids = [c.id for c in self.conversations.filter_by(is_deleted=False).all()]
        return Message.query.filter(
            Message.conversation_id.in_(conversation_ids),
            Message.weight == 5,
            Message.is_deleted == False
        ).order_by(Message.created_at.desc()).all()
```

### 4.2 会话模型

```python
class Conversation(db.Model):
    """
    会话模型
    """
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspaces.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = db.Column(db.Boolean, default=False)
    
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
```

---

## 五、API 设计

### 5.1 工作区管理

#### 创建工作区
```
POST /api/workspaces
Request Body: {
    "name": "AI学习文章",
    "description": "关于AI学习的文章"  # 可选
}
Response: {
    "id": 1,
    "name": "AI学习文章",
    "skeleton": "",  # 初始为空
    "created_at": "..."
}
```

#### 获取工作区列表
```
GET /api/workspaces
Response: [
    {
        "id": 1,
        "name": "AI学习文章",
        "material_count": 25,  # 素材数量
        "skeleton_length": 1500,  # 骨架字数
        "updated_at": "..."
    }
]
```

#### 获取工作区详情
```
GET /api/workspaces/<workspace_id>
Response: {
    "id": 1,
    "name": "AI学习文章",
    "skeleton": "# 文章标题\n\n...",  # 骨架内容
    "materials": [  # 素材列表
        {
            "id": 1,
            "content": "...",
            "role": "user",
            "created_at": "..."
        }
    ],
    "updated_at": "..."
}
```

### 5.2 骨架操作

#### 更新骨架（直接编辑）
```
PUT /api/workspaces/<workspace_id>/skeleton
Request Body: {
    "skeleton": "# 新的文章内容\n\n..."
}
Response: {
    "id": 1,
    "skeleton": "# 新的文章内容\n\n..."
}
```

#### 通过对话指令修改骨架
```
POST /api/workspaces/<workspace_id>/edit-skeleton
Request Body: {
    "instruction": "把第一段改成介绍LangChain",
    "use_materials": true  # 是否参考素材
}
Response: {
    "id": 1,
    "skeleton": "# 修改后的文章内容\n\n...",
    "changes": "已修改第一段"  # 说明修改了什么
}
```

#### 生成初始骨架
```
POST /api/workspaces/<workspace_id>/generate-skeleton
Request Body: {
    "prompt": "总结成一篇技术文章",  # 用户指令
    "use_materials": true  # 是否基于现有素材生成
}
Response: {
    "id": 1,
    "skeleton": "# 生成的文章框架\n\n..."
}
```

### 5.3 素材管理

#### 获取工作区素材
```
GET /api/workspaces/<workspace_id>/materials
Response: {
    "total": 25,
    "materials": [
        {
            "id": 1,
            "conversation_id": 5,
            "conversation_title": "关于LangChain的讨论",
            "role": "user",
            "content": "什么是LangChain？",
            "created_at": "..."
        }
    ]
}
```

#### 将素材融合到骨架
```
POST /api/workspaces/<workspace_id>/merge-material
Request Body: {
    "material_id": 1,
    "instruction": "把这个内容加到第二章"  # 可选，告诉AI如何融合
}
Response: {
    "id": 1,
    "skeleton": "# 融合后的文章内容\n\n..."
}
```

### 5.4 自动创建工作区

#### 更新消息权重时自动创建
```
PUT /api/messages/<message_id>/weight
Request Body: { "weight": 5 }

逻辑：
1. 如果权重为5，检查会话是否有关联工作区
2. 如果没有，自动创建工作区
3. 工作区名称：会话标题 或 消息内容前20字符
4. 骨架初始为空（用户后续设置）

Response: {
    "id": 1,
    "weight": 5,
    "workspace_created": true,
    "workspace": {
        "id": 3,
        "name": "关于LangChain的讨论"
    }
}
```

---

## 六、对话中的骨架操作

### 6.1 对话指令识别

用户可以在对话中说：
- "把第一段改成..."
- "在第二章后面加一节..."
- "删除第三章"
- "参考素材，完善第一章"
- "把骨架改成..."

系统需要识别这些指令，并调用相应的API修改骨架。

### 6.2 实现逻辑

```python
def process_skeleton_instruction(conversation_id, user_message):
    """
    处理对话中的骨架操作指令
    """
    conversation = Conversation.query.get(conversation_id)
    if not conversation or not conversation.workspace_id:
        return None
    
    workspace = conversation.workspace
    
    # 识别指令类型
    if "骨架" in user_message or "文章" in user_message:
        # 判断是修改指令还是生成指令
        if "生成" in user_message or "创建" in user_message:
            # 生成初始骨架
            return generate_skeleton(workspace, user_message)
        else:
            # 修改骨架
            return edit_skeleton(workspace, user_message)
    
    return None

def edit_skeleton(workspace, instruction):
    """
    根据指令修改骨架
    """
    # 获取当前骨架和素材
    current_skeleton = workspace.skeleton
    materials = workspace.get_materials()
    
    # 构建提示词
    prompt = f"""
当前文章内容：
{current_skeleton}

用户指令：
{instruction}

可用素材：
{format_materials(materials)}

请根据用户指令修改文章内容，返回修改后的完整文章。
"""
    
    # 调用AI修改
    from app.ai import ChatManager
    manager = ChatManager()
    new_skeleton = manager.generate_response(
        conversation_id=None,  # 不需要对话历史
        user_message=prompt,
        stream=False
    )
    
    # 更新骨架
    workspace.skeleton = new_skeleton
    db.session.commit()
    
    return new_skeleton
```

---

## 七、UI 设计

### 7.1 工作区编辑视图

```
┌─────────────────────────────────────────────────────────┐
│  ← 返回  工作区：AI学习文章        [保存] [导出] [素材]  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  【骨架区 - 文章内容】                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ # 关于LangChain的技术文章                        │   │
│  │                                                  │   │
│  │ ## 第一章：介绍                                  │   │
│  │ LangChain是...                                  │   │
│  │                                                  │   │
│  │ ## 第二章：核心概念                              │   │
│  │ ...                                             │   │
│  │                                                  │   │
│  │ [可编辑的Markdown编辑器]                         │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  【素材区 - 参考库】                                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 📎 25条素材                                      │   │
│  │                                                  │   │
│  │ [展开查看素材列表]                               │   │
│  │ [融合到骨架] [参考素材修改骨架]                  │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 7.2 对话中的操作提示

```
用户：[标记5星] "什么是LangChain？"
系统：✅ 已加入工作区「AI学习文章」的素材区

用户："把第一段改成介绍LangChain"
系统：✅ 已修改工作区「AI学习文章」的骨架

用户："参考素材，完善第二章"
系统：✅ 已基于素材完善工作区「AI学习文章」的第二章
```

---

## 八、核心设计原则

### 8.1 用户完全掌控

- 骨架的格式、结构、内容，用户自己决定
- 可以手动编辑，也可以用AI指令
- 最终产出就是骨架本身

### 8.2 灵活编辑

- 支持两种编辑方式：对话指令 + 直接编辑
- 用户可以选择最适合的方式
- 两种方式可以混合使用

### 8.3 素材辅助

- 素材仅供参考，不会自动填充
- 用户可以选择性地将素材融合到骨架中
- 或者让AI基于素材修改骨架

### 8.4 简单直接

- 骨架就是最终产出，无需额外生成步骤
- 工作区 = 文章编辑器
- 导出骨架 = 导出文章

---

## 九、与V1的主要区别

| 特性 | V1 | V2 |
|------|----|----|
| 工作区结构 | 只有素材区 | 骨架区 + 素材区 |
| 骨架概念 | 无 | 骨架 = 文章本身 |
| 编辑方式 | 只能生成 | 可编辑 + AI指令 |
| 最终产出 | 生成的文章 | 骨架本身 |
| 用户控制 | 较少 | 完全掌控 |
| 素材作用 | 自动填充 | 仅供参考 |

---

## 十、实现优先级

### MVP（最小可行产品）
1. ✅ 工作区双区结构（骨架区 + 素材区）
2. ✅ 骨架的直接编辑功能
3. ✅ 5星内容自动进入素材区
4. ✅ 骨架的导出功能

### 后续迭代
5. 对话中的骨架操作指令
6. 基于素材修改骨架
7. 生成初始骨架功能
8. 素材融合功能
9. 骨架版本管理
10. 协作编辑功能

---

## 总结

**V2版本的核心改进：**

1. **骨架 = 文章本身**：不再是生成的概念，而是可编辑的文档
2. **用户完全掌控**：可以手动编辑，也可以用AI指令
3. **素材仅供参考**：不会自动填充，用户选择性使用
4. **简单直接**：骨架就是最终产出，无需额外步骤

**工作区 = 可编辑的文章编辑器，目标是写文章。**

