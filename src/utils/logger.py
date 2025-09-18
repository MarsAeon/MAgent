"""
Logging Utilities
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


# 简化的日志系统
class SimpleLogger:
    """简化的日志器"""

    def __init__(self, name: str = "IdeaArchitect"):
        self.name = name
        self.setup_logging()

    def setup_logging(self):
        """设置日志"""
        # 创建日志目录
        log_dir = Path("data/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        # 配置标准库日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)-8s | %(name)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_dir / "ideaarchitect.log", encoding='utf-8')
            ]
        )

        self.logger = logging.getLogger(self.name)

    def info(self, message: str):
        """信息日志"""
        self.logger.info(message)

    def warning(self, message: str):
        """警告日志"""
        self.logger.warning(message)

    def error(self, message: str):
        """错误日志"""
        self.logger.error(message)

    def debug(self, message: str):
        """调试日志"""
        self.logger.debug(message)


# 全局日志器实例
_global_logger = SimpleLogger()


def setup_logging():
    """设置日志系统"""
    global _global_logger
    _global_logger = SimpleLogger()
    _global_logger.info("日志系统初始化完成")


def get_logger(name: Optional[str] = None) -> SimpleLogger:
    """获取日志器"""
    if name:
        return SimpleLogger(name)
    return _global_logger
