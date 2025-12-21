# -*- coding:utf-8 -*-
"""运行数据库迁移的脚本"""
from app import create_app
from flask_migrate import Migrate, migrate, upgrade
from app.db import db

app = create_app('development')

if __name__ == '__main__':
    with app.app_context():
        # 先升级到最新版本
        try:
            upgrade()
        except Exception as e:
            print(f"Upgrade error (may be expected): {e}")
        
        # 创建新迁移
        migrate(message='Add conversation and message models for v0')
