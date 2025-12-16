`@dataclass` 是 Python 3.7+ 的装饰器，用于简化数据类的定义。下面是对比：

## `@dataclass` 的作用

### 传统方式（不用 `@dataclass`）

```python
class Message:
    def __init__(self, conversation_id=None, role="user", content="", 
                 order_index=None, model="deepseek-chat", 
                 id=None, created_at=None):
        self.conversation_id = conversation_id
        self.role = role
        self.content = content
        self.order_index = order_index
        self.model = model
        self.id = id
        self.created_at = created_at or datetime.now()
    
    def __repr__(self):
        return f"Message(id={self.id}, role={self.role}, content={self.content[:30]}...)"
    
    def __eq__(self, other):
        if not isinstance(other, Message):
            return False
        return self.id == other.id and self.role == other.role
    
    # ... 还需要实现 __hash__, __lt__ 等方法
```

### 使用 `@dataclass` 的方式

```python
@dataclass
class Message:
    conversation_id: Optional[int] = None
    role: str = "user"
    content: str = ""
    order_index: Optional[int] = None
    model: str = "deepseek-chat"
    id: Optional[int] = None
    created_at: Optional[datetime] = None
```

`@dataclass` 会自动生成：
- `__init__()` 方法
- `__repr__()` 方法
- `__eq__()` 方法（比较所有字段）

## 实际使用示例

```python
# 创建对象 - 自动生成 __init__
msg1 = Message(
    conversation_id=1,
    role="user",
    content="你好",
    model="deepseek-chat"
)

# 自动生成 __repr__ - 打印时显示所有字段
print(msg1)  # Message(conversation_id=1, role='user', content='你好', ...)

# 自动生成 __eq__ - 可以比较两个对象
msg2 = Message(conversation_id=1, role="user", content="你好")
print(msg1 == msg2)  # True（如果所有字段都相同）
```

## 注意事项

1. 类型提示：字段需要类型提示（如 `str`, `Optional[int]`）
2. 默认值：有默认值的字段必须放在没有默认值的字段后面
3. `__post_init__()`：可以在初始化后执行额外逻辑



