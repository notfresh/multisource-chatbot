# 启动服务器

## 简单启动

```bash
python run_server.py
```

## 服务器地址

- http://localhost:8000

## 测试 API

```bash
python test_api_simple.py <用户名> <密码>
```

## 已修复的问题

- ✅ Werkzeug 版本兼容性（已降级到 2.3.8）
- ✅ Flask-WTF 版本兼容性（已降级到 0.15.1）
- ✅ API Key 配置（从 env/env.yml 读取）

## 如果启动失败

1. 确保虚拟环境已激活
2. 检查端口 8000 是否被占用
3. 查看错误信息，检查依赖是否安装完整

