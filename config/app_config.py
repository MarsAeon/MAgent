"""
IdeaArchitect Application Configuration
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class WorkflowMode(str, Enum):
    CREATIVE = "creative"
    BALANCED = "balanced"
    RIGOROUS = "rigorous"


class AppConfig(BaseModel):
    """应用程序配置"""

    # 应用基础配置
    app_name: str = "IdeaArchitect"
    app_version: str = "1.0.0"
    debug: bool = False

    # Eel配置
    eel_port: int = 8000
    eel_host: str = "localhost"
    eel_size: tuple = (1200, 800)

    # 数据存储配置
    data_dir: Path = Path("data")
    projects_dir: Path = Path("data/projects")
    cache_dir: Path = Path("data/cache")
    logs_dir: Path = Path("data/logs")

    # 日志配置
    log_level: LogLevel = LogLevel.INFO
    log_file: str = "ideaarchitect.log"

    # AI模型配置
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    qwen_api_key: Optional[str] = None
    default_model_provider: str = "openai"
    default_model_name: str = "gpt-4"

    # 工作流配置
    default_workflow_mode: WorkflowMode = WorkflowMode.BALANCED
    max_discussion_rounds: int = 10
    convergence_threshold: float = 0.8

    # 智能体配置
    max_concurrent_agents: int = 5
    agent_timeout: int = 300  # 5分钟

    # 网络配置
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 从环境变量加载配置
        self.eel_port = int(os.getenv("EEL_PORT", self.eel_port))
        self.eel_host = os.getenv("EEL_HOST", self.eel_host)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", self.anthropic_api_key)
        # 支持 DeepSeek 与 Qwen(DashScope)
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", self.deepseek_api_key)
        # Qwen 同时兼容 DASHSCOPE_API_KEY 与 QWEN_API_KEY
        self.qwen_api_key = os.getenv("QWEN_API_KEY", os.getenv("DASHSCOPE_API_KEY", self.qwen_api_key))
        self.debug = os.getenv("DEBUG", "false").lower() == "true"


class ModelConfig:
    """AI模型配置"""
    
    PROVIDERS = {
        "openai": {
            "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            "api_base": "https://api.openai.com/v1",
            "supports_streaming": True
        },
        "anthropic": {
            "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            "api_base": "https://api.anthropic.com",
            "supports_streaming": True
        },
        "ollama": {
            "models": ["llama2", "codellama", "mistral"],
            "api_base": "http://localhost:11434",
            "supports_streaming": True
        }
    }
    
    MODE_SETTINGS = {
        WorkflowMode.CREATIVE: {
            "temperature": 0.9,
            "top_p": 0.95,
            "max_tokens": 2048
        },
        WorkflowMode.BALANCED: {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 1024
        },
        WorkflowMode.RIGOROUS: {
            "temperature": 0.3,
            "top_p": 0.8,
            "max_tokens": 1024
        }
    }


# 全局配置实例
app_config = AppConfig()


def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        app_config.data_dir,
        app_config.projects_dir,
        app_config.cache_dir,
        app_config.logs_dir
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def get_model_config(provider: str, model: str, mode: WorkflowMode) -> Dict[str, Any]:
    """获取模型配置"""
    if provider not in ModelConfig.PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")
    
    provider_config = ModelConfig.PROVIDERS[provider]
    if model not in provider_config["models"]:
        raise ValueError(f"Unsupported model {model} for provider {provider}")
    
    mode_settings = ModelConfig.MODE_SETTINGS[mode]
    
    return {
        "provider": provider,
        "model": model,
        "api_base": provider_config["api_base"],
        "supports_streaming": provider_config["supports_streaming"],
        **mode_settings
    }
