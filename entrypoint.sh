#!/bin/bash
set -e

echo "=========================================="
echo "容器启动脚本开始执行..."
echo "=========================================="

echo "设置 Flask 环境变量..."
export FLASK_APP=manage:app

echo "初始化数据库..."
python manage.py db upgrade || echo "数据库升级失败或已是最新版本（这可能是正常的）"

echo "=========================================="
echo "数据库初始化完成，启动应用..."
echo "接收到的命令参数: $@"
echo "=========================================="

# 执行 docker-compose.yml 中 command 指定的命令
# "$@" 会接收所有传递给 entrypoint 的参数
exec "$@"

