# -*- coding:utf-8 -*-
"""
API 蓝图定义
"""
from flask import Blueprint

# 创建主 API 蓝图
api = Blueprint('api', __name__, url_prefix='/api')

