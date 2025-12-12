# -*- coding:utf-8 -*-
"""初始化数据库表"""
from app import create_app
from app.db import db
from app.models import Conversation, Message

app = create_app('development')

if __name__ == '__main__':
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库表创建成功！")
        print(f"已创建表: {db.metadata.tables.keys()}")

