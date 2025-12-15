# -*- coding:utf-8 -*-
"""
API 模块 - 统一导出 API 蓝图
"""
from .blueprint import api

# 导入各个模块的路由（这会注册路由到 api 蓝图）
# 注意：导入顺序很重要，确保蓝图先被导入
from . import conversations  # noqa: F401
from . import messages  # noqa: F401

# 导出 api 蓝图供外部使用
__all__ = ['api']
