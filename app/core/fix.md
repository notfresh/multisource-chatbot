分析 `ChatManager` 类的职责和方法关系：

## 方法职责分析

### 1. 构建内存（Memory Building）

done

### 2. 生成回答（Response Generation）
- `generate_response` (111行)
  - 职责：生成回答（简单版本）
  - 使用：`build_memory_from_conversation`
  - 返回：str 或 Generator

- `generate_response_for_user_message` (332行)
  - 职责：为特定用户消息生成回答（Peer 架构）
  - 使用：`build_memory_for_user_message`
  - 返回：str 或 Generator

- `generate_and_save_assistant_response` (463行)
  - 职责：生成并保存助手回答（完整工作流）
  - 内部调用：`generate_response_for_user_message`
  - 额外功能：保存消息、更新会话、自动标题

职责近似：
- `generate_and_save_assistant_response` 是 `generate_response_for_user_message` 的扩展版本

### 3. 内部辅助方法
- `_generate_with_conversation` (77行) - 通用生成方法
- `_generate_normal` (140行) - 普通回答
- `_generate_stream` (249行) - 流式回答
- `_stream_from_llm` (165行) - LLM 流式输出
- `_build_messages_from_conversation` (203行) - 构建消息列表

## 发现的问题


### 2. 职责近似的方法对


## 重构建议

1. 移除重复的 datetime 导入
2. 统一内存构建方法：将两个 `build_memory_*` 合并为一个，通过参数控制策略
3. 统一生成回答方法：让 `generate_response` 内部调用 `generate_response_for_user_message`
4. 明确职责边界：`generate_and_save_assistant_response` 作为工作流方法保留，但可以考虑拆分

