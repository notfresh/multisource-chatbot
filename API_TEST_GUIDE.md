# API 测试指南

## 服务器状态

- **地址**: http://localhost:8000
- **状态**: 运行中（使用 `python run_server.py` 启动）

## 快速测试

### 方法1: 使用 Python 脚本测试

```bash
# 需要先有用户账号，如果没有请访问 http://localhost:8000/auth/register 注册
python test_api_simple.py <username> <password>
```

### 方法2: 使用浏览器

1. 访问 http://localhost:8000
2. 登录或注册账号
3. 使用浏览器开发者工具（F12）测试 API

### 方法3: 使用 curl

```bash
# 1. 登录（保存 cookies）
curl -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=YOUR_USERNAME&password=YOUR_PASSWORD' \
  -c cookies.txt -v

# 2. 创建会话
curl -X POST http://localhost:8000/api/conversations \
  -H 'Content-Type: application/json' \
  -b cookies.txt \
  -d '{"title":"测试对话"}'

# 3. 发送消息（假设会话ID为1）
curl -X POST http://localhost:8000/api/conversations/1/messages \
  -H 'Content-Type: application/json' \
  -b cookies.txt \
  -d '{"content":"你好，请介绍一下你自己"}'

# 4. 获取会话详情
curl -X GET http://localhost:8000/api/conversations/1 \
  -b cookies.txt

# 5. 获取会话列表
curl -X GET http://localhost:8000/api/conversations \
  -b cookies.txt
```

## API 端点列表

### 会话管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/conversations` | 获取会话列表 |
| POST | `/api/conversations` | 创建新会话 |
| GET | `/api/conversations/<id>` | 获取会话详情 |
| PUT | `/api/conversations/<id>` | 更新会话标题 |
| DELETE | `/api/conversations/<id>` | 删除会话 |

### 消息管理

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/conversations/<id>/messages` | 发送消息并获取AI回答 |

## 请求示例

### 创建会话

```json
POST /api/conversations
Content-Type: application/json

{
  "title": "新对话"
}
```

**响应:**
```json
{
  "id": 1,
  "title": "新对话",
  "created_at": "2025-12-12T12:00:00",
  "updated_at": "2025-12-12T12:00:00"
}
```

### 发送消息

```json
POST /api/conversations/1/messages
Content-Type: application/json

{
  "content": "你好"
}
```

**响应:**
```json
{
  "user_message": {
    "id": 1,
    "role": "user",
    "content": "你好",
    "created_at": "2025-12-12T12:00:00"
  },
  "assistant_message": {
    "id": 2,
    "role": "assistant",
    "content": "你好！我是AI助手...",
    "created_at": "2025-12-12T12:00:01"
  }
}
```

## 配置说明

- **API Key**: 配置在 `env/env.yml` 中的 `API_302_AI_KEY`
- **模型**: 使用 302.ai 的 `deepseek-chat` 模型
- **数据库**: SQLite (`app.sqlite`)

## 注意事项

1. 所有 API 都需要登录（使用 Flask-Login session）
2. 用户只能访问自己的会话
3. 第一条消息会自动生成会话标题（基于消息内容的前20个字符）

