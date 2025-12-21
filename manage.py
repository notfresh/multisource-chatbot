# -*- coding:utf-8 -*-
"""
Flask CLI 管理脚本
替代了旧的 Flask-Script，使用 Flask 2.0+ 内置的 CLI 支持

使用方法：
    python manage.py db upgrade      # 数据库升级
    python manage.py db migrate      # 创建迁移
    python manage.py runserver       # 运行开发服务器
    python manage.py shell           # 打开 Python shell
"""
import os
import sys
from flask.cli import FlaskGroup, with_appcontext
from flask import current_app
import click
from app import create_app
from app.models import ShortURL, User
from app.core.db import ConversationDBModel, MessageDBModel
from app.db import db

def create_app_for_cli(info=None):
    """为 Flask CLI 创建应用实例"""
    app = create_app('development')
    
    # 在应用实例上注册 shell 上下文处理器
    @app.shell_context_processor
    def make_shell_context():
        """为 Flask shell 命令提供上下文"""
        return dict(
            app=app,
            db=db,
            ShortURL=ShortURL,
            User=User,
            # 原生 SQLAlchemy 模型（来自 app/core/db.py）
            ConversationDBModel=ConversationDBModel,
            MessageDBModel=MessageDBModel,
            # 为了向后兼容，提供别名
            Conversation=ConversationDBModel,
            Message=MessageDBModel
        )
    
    return app

# 创建 Flask CLI 组
cli = FlaskGroup(create_app=create_app_for_cli)

# 为了支持 gunicorn，需要直接创建 app 实例
# 但避免在 CLI 模式下重复创建（CLI 会通过 create_app_for_cli 创建）
# 检查是否是通过 gunicorn 或其他 WSGI 服务器导入
# 如果是直接运行 python manage.py，则不创建 app（使用 CLI）
if __name__ != '__main__':
    # gunicorn 或其他 WSGI 服务器导入时创建 app
    # 优先使用 FLASK_DEBUG，向后兼容 FLASK_ENV
    flask_debug = os.environ.get('FLASK_DEBUG')
    if flask_debug is not None:
        flask_config = 'development' if flask_debug.lower() in ('1', 'true', 'yes', 'on') else 'production'
    else:
        flask_config = os.environ.get('FLASK_ENV', 'development')
    app = create_app(flask_config)
else:
    # 直接运行 python manage.py 时，不创建 app，由 create_app_for_cli 处理
    app = None

# 添加自定义 runserver 命令以保持向后兼容
@cli.command('runserver')
@click.option('--host', '-h', default='0.0.0.0', help='服务器主机地址')
@click.option('--port', '-p', default=8000, type=int, help='服务器端口')
@with_appcontext
def runserver(host, port):
    """运行开发服务器"""
    # 使用 Werkzeug 的 run_simple 而不是 app.run()，避免 Flask CLI 警告
    from werkzeug.serving import run_simple
    run_simple(host, port, current_app, use_reloader=True, use_debugger=True)

if __name__ == '__main__':
    # 设置 FLASK_APP 环境变量以便 Flask-Migrate 能找到应用
    os.environ['FLASK_APP'] = 'manage:app'
    cli()



