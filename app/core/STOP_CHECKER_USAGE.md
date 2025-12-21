# 停止检查器使用说明

## 一、设计概述

`Conversation.send_message()` 是第一个接收中断信号的地方：
- **CLI 模式**：如果没有传入 `should_stop` 参数，自动创建基于 Ctrl+C 信号的检查器
- **Web 模式**：通过 `should_stop` 参数传递停止检查器（由 Web API 创建）

## 二、CLI/IPython 使用方式

### 基本使用（自动支持 Ctrl+C）

```python
from app.core.coremodels import Conversation

# 获取会话
conv = Conversation.get_by_id(1)

# 直接使用，自动支持 Ctrl+C 中断
for result in conv.send_message("你好", return_iterator=True):
    if result['type'] == 'chunk':
        print(result['chunk'], end='', flush=True)
    elif result['type'] == 'interrupted':
        print("\n已中断")
        break
    elif result['type'] == 'done':
        print("\n完成")
        break
```

### 手动创建检查器（高级用法）

```python
from app.core.coremodels import Conversation
from app.core.stop_checker import create_cli_stop_checker

# 创建检查器
checker = create_cli_stop_checker()
checker.reset()  # 重置状态

# 使用检查器
conv = Conversation.get_by_id(1)
for result in conv.send_message(
    "你好",
    return_iterator=True,
    should_stop=checker.should_stop
):
    if result['type'] == 'chunk':
        print(result['chunk'], end='', flush=True)
    elif result['type'] == 'interrupted':
        print("\n已中断")
        break
```

## 三、Web API 使用方式

### 在 API 中创建停止检查器

```python
from app.core.stop_checker import WebStopChecker
from flask import request

# 创建检查器（可以存储在请求上下文或全局字典中）
stop_checker = WebStopChecker()

# 传递给 send_message
for result in conversation.send_message(
    user_content=user_content,
    return_iterator=True,
    should_stop=stop_checker.should_stop
):
    # 处理结果
    pass

# 在另一个 API 端点中停止
# POST /api/conversations/<id>/stop
stop_checker.set_stop()
```

## 四、参数传递链

```
Conversation.send_message(should_stop=...)
    ↓
ConversationOp.send_message(should_stop=...)
    ↓
ChatManager.generate_and_save_assistant_response(should_stop=...)
    ↓
ChatManager.generate_response_for_user_message(should_stop=...)
    ↓
ChatManager._generate_with_conversation(should_stop=...)
    ↓
ChatManager.__generate_stream(should_stop=...)
    ↓
在每个 chunk 前检查 should_stop()
```

## 五、中断检查点

1. **Conversation.send_message**：在生成器循环中检查
2. **ConversationOp.send_message**：在生成器循环中检查
3. **ChatManager.generate_and_save_assistant_response**：在生成器循环中检查
4. **ChatManager.__generate_stream**：在每个 chunk 前检查
5. **异常捕获**：捕获 `KeyboardInterrupt` 作为双重保险

## 六、返回类型

当用户中断时，生成器会 yield：

```python
{'type': 'interrupted', 'message': '用户中断生成'}
```

或

```python
{'type': 'interrupted', 'message': '检测到 Ctrl+C，已中断生成'}
```

## 七、注意事项

1. **CLI 模式**：自动创建检查器，无需手动传递参数
2. **Web 模式**：需要手动创建 `WebStopChecker` 并传递
3. **信号注册**：`SignalStopChecker` 会自动注册信号处理器
4. **线程安全**：所有检查器都是线程安全的
5. **重置状态**：开始新的生成前，建议调用 `checker.reset()`

