"""
AI Model API
"""

import asyncio
from typing import Dict, List, Any
from datetime import datetime

from ..utils.logger import get_logger
from config.app_config import ModelConfig

logger = get_logger(__name__)


def api_list_available_models() -> Dict[str, Any]:
    """列出可用的AI模型"""
    try:
        models = []
        
        for provider, config in ModelConfig.PROVIDERS.items():
            for model in config["models"]:
                models.append({
                    "provider": provider,
                    "model": model,
                    "api_base": config["api_base"],
                    "supports_streaming": config["supports_streaming"]
                })
        
        return {
            "success": True,
            "data": models
        }
        
    except Exception as e:
        logger.error(f"列出可用模型失败: {e}")
        return {
            "success": False,
            "error": f"列出可用模型时发生错误: {str(e)}"
        }


def api_get_model_config(provider: str, model: str) -> Dict[str, Any]:
    """获取模型配置"""
    try:
        if provider not in ModelConfig.PROVIDERS:
            return {
                "success": False,
                "error": f"不支持的提供商: {provider}"
            }
        
        provider_config = ModelConfig.PROVIDERS[provider]
        if model not in provider_config["models"]:
            return {
                "success": False,
                "error": f"提供商 {provider} 不支持模型 {model}"
            }
        
        config = {
            "provider": provider,
            "model": model,
            "api_base": provider_config["api_base"],
            "supports_streaming": provider_config["supports_streaming"]
        }
        
        return {
            "success": True,
            "data": config
        }
        
    except Exception as e:
        logger.error(f"获取模型配置失败: {e}")
        return {
            "success": False,
            "error": f"获取模型配置时发生错误: {str(e)}"
        }


async def api_call_ai_model(provider: str, model: str, messages: List[Dict[str, str]], config: Dict[str, Any] = None) -> Dict[str, Any]:
    """调用AI模型"""
    try:
        # 验证提供商和模型
        if provider not in ModelConfig.PROVIDERS:
            return {
                "success": False,
                "error": f"不支持的提供商: {provider}"
            }
        
        provider_config = ModelConfig.PROVIDERS[provider]
        if model not in provider_config["models"]:
            return {
                "success": False,
                "error": f"提供商 {provider} 不支持模型 {model}"
            }
        
        # 模拟AI模型调用
        await asyncio.sleep(1)  # 模拟网络延迟
        
        # 生成模拟响应
        last_message = messages[-1]["content"] if messages else ""
        
        mock_responses = {
            "search": f"基于您的问题 '{last_message}'，我找到了以下相关信息...",
            "critic": f"对于 '{last_message}' 这个想法，我认为需要考虑以下几个问题...",
            "expert": f"作为领域专家，对于 '{last_message}'，我的建议是..."
        }
        
        # 根据消息内容选择响应
        response = mock_responses.get("expert", f"这是一个关于 '{last_message}' 的AI响应。")
        
        logger.info(f"AI模型调用成功: {provider}/{model}")
        
        return {
            "success": True,
            "data": response,
            "metadata": {
                "provider": provider,
                "model": model,
                "timestamp": datetime.now().isoformat(),
                "token_count": len(response.split())
            }
        }
        
    except Exception as e:
        logger.error(f"AI模型调用失败: {e}")
        return {
            "success": False,
            "error": f"AI模型调用时发生错误: {str(e)}"
        }


async def api_test_model_connection(provider: str, model: str) -> Dict[str, Any]:
    """测试模型连接"""
    try:
        # 模拟连接测试
        await asyncio.sleep(0.5)
        
        # 简单的连接测试
        test_messages = [{"role": "user", "content": "Hello"}]
        result = await api_call_ai_model(provider, model, test_messages)
        
        if result["success"]:
            return {
                "success": True,
                "data": {
                    "provider": provider,
                    "model": model,
                    "status": "connected",
                    "response_time": 0.5
                }
            }
        else:
            return {
                "success": False,
                "error": f"连接测试失败: {result['error']}"
            }
        
    except Exception as e:
        logger.error(f"模型连接测试失败: {e}")
        return {
            "success": False,
            "error": f"模型连接测试时发生错误: {str(e)}"
        }
