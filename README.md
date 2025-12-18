# 多模型对话系统核心层（Core）

[![standard-readme compliant](https://img.shields.io/badge/standard--readme-OK-green.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

本项目最初是一个短网址小应用，目前已经演化为一个**多 LLM 对话系统**，并在此基础上抽象出一套与 Web 框架无关的**核心层（`app/core`）**：

- 领域模型：`Conversation`、`Message`、`MessageRole`
- 持久化层：基于原生 SQLAlchemy 的 `ConversationOp`、`MessageOp`
- 聊天服务：`ChatManager` + LangChain + 302.ai / 兼容 OpenAI API
- 命令行工具：`core_manage.py`，用于在 IPython 中直接与核心层交互

你可以只把 `app/core` + `core_manage.py` 当成一个独立的“多模型对话内核库”，嵌入到任意 Web / CLI / Agent 项目中。


## 目录

- [背景](#背景)
- [安装](#安装)
- [用法](#用法)
- [设计思路](#设计思路)
- [核心代码](#核心代码)
- [维护者](#维护者)
- [如何贡献](#如何贡献)
- [许可证](#许可证)


## 背景

重构的目标是：

- 把原来强绑定 Flask 的业务模型和数据库访问逻辑，抽离成**纯 Python 的领域模型 + SQLAlchemy 持久化层**
- 让 `Conversation` / `Message` 这些模型不依赖 Flask，也不依赖 Web 请求上下文
- 能在 IPython / 脚本 / 后台任务里，直接拿一个 `Conversation` 实例调用 `send_message()`，就能完成一次完整对话流程（包括写库、调 LLM、流式打印结果）

因此，`app/core` 目录是整个项目的新“心脏”，Web 层只是外围适配。


## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/notfresh/shorturl_service multi-llm
cd multi-llm
```

### 2. （推荐）创建并激活虚拟环境

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# 或
source venv/bin/activate  # macOS / Linux
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境 / API Key

项目通过 `config.py` 读取 `env/env.yml`：

- **LLM 相关**
  - `API_302_AI_KEY`：302.ai 或兼容 OpenAI 接口的 API Key
- **数据库**
  - 可在 `env.yml` 中配置 `SQLALCHEMY_DATABASE_URI`
  - 若不配置，则默认使用项目根目录下的 `app.sqlite`

只想体验核心层，保持默认 sqlite 即可。


## 用法

### 1. 启动核心层交互 Shell

```bash
python core_manage.py shell
```

进入后会自动注入：

- `Conversation`, `Message`, `MessageRole`
- `ConversationOp`, `MessageOp`
- `create_conversation`, `get_conversation_by_id`, `create_message` 等便捷函数
- `get_llm`, `get_default_llm`

### 2. 在 IPython 中直接对话

```python
# 创建会话
conv = Conversation.create(title='测试对话', user_id=1)
print(conv.id, conv.title)

# 使用会话实例直接聊天（流式输出）
conv.send_message('你好，帮我解释一下多模型对话系统？', model_name='deepseek-chat')
```

这一次调用会：

- 写入一条用户消息到数据库
- 使用 `ChatManager` 调用 LLM，流式打印 AI 输出
- 保存助手回复，并更新 `Conversation.updated_at`、`order_index` 等

### 3. 浏览和管理历史会话 / 消息

```python
# 列出所有会话
for c in Conversation.list():
    print(c.id, c.title, c.updated_at)

# 按用户过滤
my_convs = Conversation.list(user_id=1)

# 查看某个会话的消息
msgs = Message.list(conversation_id=conv.id)
for m in msgs:
    print(m.role, m.content[:30])
```

如需更细粒度控制，可直接使用 `ConversationOp` / `MessageOp`。


## 设计思路

- **框架无关（Framework Agnostic）**
  - `app/core` 不依赖 Flask / Request / 蓝图等任何 Web 概念
  - 可以像使用普通 Python 包一样，在任意环境下导入使用

- **领域模型 + 持久化解耦**
  - `coremodels.py` 中的 `Conversation` / `Message` 是纯 `dataclass`，只关心业务含义与行为
  - `db.py` 中的 `ConversationDBModel` / `MessageDBModel` 负责 ORM 映射和 CRUD
  - 通过 `to_core()` / `from_core()` 完成两者之间的转换

- **服务层负责“流程编排”**
  - `ChatManager` 负责：构建对话历史、调用 LangChain + LLM、处理普通/流式输出
  - 支持 Peer 架构等更复杂的上下文选择策略（按模型选择回答）

- **交互友好**
  - `core_manage.py` 提供 `shell` 命令，一行起 IPython，所有核心对象已注入
  - 针对 Windows + IPython 的异步告警、颜色问题做了定制处理，体验更干净


## 核心代码

- `app/core/coremodels.py`
  - `MessageRole`：消息角色枚举（user / assistant / system）
  - `Message`：消息领域模型，提供便捷的静态方法/类方法（`create`, `list`, `get_by_id` 等）
  - `Conversation`：会话模型，内置 `create/list/get/save/delete/send_message` 等高层操作

- `app/core/db.py`
  - `ConversationDBModel` / `MessageDBModel`：SQLAlchemy ORM 映射
  - `ConversationOp` / `MessageOp`：封装会话和消息的 CRUD、list、上下文管理等

- `app/core/llm_config.py`
  - 统一创建 302.ai / 兼容 OpenAI 接口的 `ChatOpenAI` 实例
  - 提供 `get_llm`、`get_default_llm`

- `app/core/chat_manager.py`
  - 使用 LangChain 的 `ConversationBufferMemory` + `ConversationChain`
  - 支持普通回答和流式回答
  - 为 Peer 架构提供面向“指定用户消息”的上下文构建方法

- `core_manage.py`
  - 提供 `shell` / `list` 等命令
  - 是调试核心层、做交互实验的主要入口


## 维护者

[@notfresh](https://github.com/notfresh)


## 如何贡献

PRs accepted.

如果你对抽象核心层、对话管理、LangChain 集成等有改进建议，欢迎直接提 Issue 或 PR。


## 许可证

MIT © 2020–2025 notfresh


