"""
Agent Management API
"""

from typing import Dict, List, Any
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)

# 简化的智能体存储
agents = {
    "search_agent": {
        "id": "search_agent",
        "name": "搜索智能体",
        "role": "search",
        "status": "idle",
        "description": "负责网络搜索和信息收集",
        "model": "gpt-4",
        "created_at": datetime.now().isoformat()
    },
    "critic_agent": {
        "id": "critic_agent", 
        "name": "批评智能体",
        "role": "critic",
        "status": "idle",
        "description": "负责批判性分析和质疑",
        "model": "claude-3-sonnet",
        "created_at": datetime.now().isoformat()
    },
    "expert_agent": {
        "id": "expert_agent",
        "name": "领域专家",
        "role": "domain_expert", 
        "status": "idle",
        "description": "提供专业领域知识和建议",
        "model": "gpt-4",
        "created_at": datetime.now().isoformat()
    }
}


def api_list_agents() -> Dict[str, Any]:
    """列出所有智能体"""
    try:
        agent_list = list(agents.values())
        
        logger.info(f"列出智能体成功: 共 {len(agent_list)} 个智能体")
        
        return {
            "success": True,
            "data": agent_list
        }
        
    except Exception as e:
        logger.error(f"列出智能体失败: {e}")
        return {
            "success": False,
            "error": f"列出智能体时发生错误: {str(e)}"
        }


def api_create_agent(name: str, role: str, model: str = "gpt-4", description: str = "") -> Dict[str, Any]:
    """创建新智能体"""
    try:
        agent_id = f"{role}_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        agent = {
            "id": agent_id,
            "name": name,
            "role": role,
            "status": "idle",
            "description": description,
            "model": model,
            "created_at": datetime.now().isoformat()
        }
        
        agents[agent_id] = agent
        
        logger.info(f"创建智能体成功: {name} (ID: {agent_id})")
        
        return {
            "success": True,
            "data": agent
        }
        
    except Exception as e:
        logger.error(f"创建智能体失败: {e}")
        return {
            "success": False,
            "error": f"创建智能体时发生错误: {str(e)}"
        }


def api_get_agent_status(agent_id: str) -> Dict[str, Any]:
    """获取智能体状态"""
    try:
        if agent_id not in agents:
            return {
                "success": False,
                "error": "智能体不存在"
            }
        
        agent = agents[agent_id]
        
        return {
            "success": True,
            "data": agent
        }
        
    except Exception as e:
        logger.error(f"获取智能体状态失败: {e}")
        return {
            "success": False,
            "error": f"获取智能体状态时发生错误: {str(e)}"
        }


def api_configure_agent(agent_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """配置智能体"""
    try:
        if agent_id not in agents:
            return {
                "success": False,
                "error": "智能体不存在"
            }
        
        agent = agents[agent_id]
        
        # 更新配置
        if "name" in config:
            agent["name"] = config["name"]
        if "description" in config:
            agent["description"] = config["description"]
        if "model" in config:
            agent["model"] = config["model"]
        
        agent["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"配置智能体成功: {agent_id}")
        
        return {
            "success": True,
            "data": agent
        }
        
    except Exception as e:
        logger.error(f"配置智能体失败: {e}")
        return {
            "success": False,
            "error": f"配置智能体时发生错误: {str(e)}"
        }
