# -*- coding:utf-8 -*-
"""
Flask CLI 管理脚本

使用方法：
    python manage.py db upgrade      # 数据库升级
    python manage.py db migrate      # 创建迁移
    python manage.py run              # 运行开发服务器（Flask 内置命令）
    python manage.py shell            # 打开 Python shell
"""
import os
from flask.cli import FlaskGroup
from app import create_app

def create_app_for_cli(info=None):
    """为 Flask CLI 创建应用实例"""
    return create_app('development')

# 创建 Flask CLI 组
cli = FlaskGroup(create_app=create_app_for_cli)

# 为了支持 gunicorn，需要直接创建 app 实例
if __name__ != '__main__':
    flask_config = os.environ.get('FLASK_ENV', 'development')
    app = create_app(flask_config)

if __name__ == '__main__':
    os.environ['FLASK_APP'] = 'manage:app'
    cli()



