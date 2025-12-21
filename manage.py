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

# 添加自定义 runserver 命令以保持向后兼容
@cli.command('runserver')
@click.option('--host', '-h', default='0.0.0.0', help='服务器主机地址')
@click.option('--port', '-p', default=8000, type=int, help='服务器端口')
@with_appcontext
def runserver(host, port):
    """运行开发服务器"""
    current_app.run(host=host, port=port, debug=True)

if __name__ == '__main__':
    # 设置 FLASK_APP 环境变量以便 Flask-Migrate 能找到应用
    os.environ['FLASK_APP'] = 'manage:app'
    cli()



