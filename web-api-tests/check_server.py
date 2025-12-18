# -*- coding:utf-8 -*-
"""Check if server is running"""
import requests
import sys

try:
    response = requests.get("http://localhost:8000", timeout=2, allow_redirects=False)
    if response.status_code in [200, 302]:
        print("[OK] Server is running!")
        print("URL: http://localhost:8000")
        sys.exit(0)
    else:
        print(f"[WARN] Server returned: {response.status_code}")
        sys.exit(1)
except requests.exceptions.ConnectionError:
    print("[ERROR] Server is not running")
    print("Please run: python run_server.py")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Check failed: {e}")
    sys.exit(1)

