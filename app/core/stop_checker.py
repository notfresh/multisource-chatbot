# -*- coding:utf-8 -*-
"""
停止检查器模块
用于 CLI 和 Web 环境的中断信号处理
"""
import signal
import threading
from typing import Callable, Optional


class SignalStopChecker:
    """
    基于信号的停止检查器（用于 CLI/IPython）
    
    使用方式：
        # 在 IPython 中
        from app.core.stop_checker import SignalStopChecker
        
        checker = SignalStopChecker()
        checker.reset()  # 重置状态
        
        # 使用 checker.should_stop 作为回调
        for result in conv.send_message("你好", should_stop=checker.should_stop):
            ...
    """
    
    def __init__(self):
        self.interrupted = False
        self.lock = threading.Lock()
        self._original_handler = None
        self._registered = False
    
    def register(self):
        """注册信号处理器"""
        if self._registered:
            return
        
        # 保存原始处理器
        try:
            self._original_handler = signal.signal(signal.SIGINT, self._signal_handler)
            self._registered = True
        except (ValueError, OSError):
            # 在某些环境中可能无法注册信号（如某些线程环境）
            pass
    
    def unregister(self):
        """取消注册信号处理器"""
        if not self._registered:
            return
        
        try:
            if self._original_handler:
                signal.signal(signal.SIGINT, self._original_handler)
            self._original_handler = None
            self._registered = False
        except (ValueError, OSError):
            pass
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        with self.lock:
            self.interrupted = True
        print("\n⏹️  检测到中断信号（Ctrl+C），正在停止...")
    
    def should_stop(self) -> bool:
        """检查是否应该停止"""
        with self.lock:
            return self.interrupted
    
    def reset(self):
        """重置停止标志（开始新的生成前调用）"""
        with self.lock:
            self.interrupted = False
    
    def is_interrupted(self) -> bool:
        """检查是否已中断"""
        return self.should_stop()


class WebStopChecker:
    """
    基于线程事件的停止检查器（用于 Web 环境）
    
    使用方式：
        checker = WebStopChecker()
        
        # 在另一个线程或请求中设置停止
        checker.set_stop()
        
        # 在生成器中使用
        should_stop=checker.should_stop
    """
    
    def __init__(self):
        self.stop_event = threading.Event()
    
    def set_stop(self):
        """设置停止标志"""
        self.stop_event.set()
    
    def reset(self):
        """重置停止标志"""
        self.stop_event.clear()
    
    def should_stop(self) -> bool:
        """检查是否应该停止"""
        return self.stop_event.is_set()


def create_cli_stop_checker() -> SignalStopChecker:
    """
    创建 CLI 环境的停止检查器（自动注册信号）
    
    Returns:
        SignalStopChecker: 已注册信号的停止检查器
    """
    checker = SignalStopChecker()
    checker.register()
    return checker

