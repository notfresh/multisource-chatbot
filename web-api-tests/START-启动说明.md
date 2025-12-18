# 启动说明

## 启动服务器

使用以下命令启动服务器：

```bash
python run_server.py
```

或者：

```bash
.\venv\Scripts\python.exe run_server.py
```

## 访问地址

- 服务器地址: http://localhost:8000
- 登录页面: http://localhost:8000/auth/login
- 注册页面: http://localhost:8000/auth/register

## 测试 API

### 方法1: 使用测试脚本

```bash
python test_api_simple.py <用户名> <密码>
```

### 方法2: 浏览器测试

1. 访问 http://localhost:8000
2. 注册/登录账号
3. 使用浏览器开发者工具（F12）测试 API

## 常见问题

### 问题1: 启动失败，提示模块找不到

**解决**: 确保已激活虚拟环境
```bash
.\venv\Scripts\Activate.ps1
```

### 问题2: 端口被占用

**解决**: 修改 `run_server.py` 中的端口号，或关闭占用 8000 端口的程序

### 问题3: API Key 未配置

**解决**: 在 `env/env.yml` 中配置 `API_302_AI_KEY`

