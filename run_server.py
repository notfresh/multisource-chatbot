# -*- coding:utf-8 -*-
"""启动 Flask 开发服务器"""
from app import create_app

app = create_app('development')

if __name__ == '__main__':
    print("=" * 50)
    print("启动 Flask 开发服务器...")
    print("=" * 50)
    print("\n服务器地址: http://localhost:8000")
    print("API 文档: 查看 test_api.py 了解 API 使用方法")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 50 + "\n")
    
    app.run(host='0.0.0.0', port=8000, debug=True)

