"""
Project Management API
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..models.project import Project, ProjectStatus, ProjectInput
from ..utils.storage import ProjectStorage
from ..utils.logger import get_logger
from config.app_config import app_config

logger = get_logger(__name__)
storage = ProjectStorage()


def api_create_project(project_data) -> Dict[str, Any]:
    """创建新项目"""
    try:
        # 处理输入参数
        if isinstance(project_data, dict):
            name = project_data.get("name", "")
            description = project_data.get("description", "")
            initial_idea = project_data.get("initial_idea", "")
            domain = project_data.get("domain", "general")
        else:
            # 兼容旧的字符串参数
            name = str(project_data) if project_data else ""
            description = ""
            initial_idea = ""
            domain = "general"

        # 验证输入
        if not name or not name.strip():
            return {
                "success": False,
                "error": "项目名称不能为空"
            }
        
        # 创建项目输入
        project_input = ProjectInput(
            original_idea=initial_idea if initial_idea else "",
            documents=[],
            requirements=[],
            constraints=[],
            metadata={}
        )

        # 创建项目
        project = Project(
            name=name.strip(),
            description=description.strip() if description else "",
            input=project_input,
            status=ProjectStatus.DRAFT
        )
        
        # 保存项目
        success = storage.save_project(project)
        if not success:
            return {
                "success": False,
                "error": "保存项目失败"
            }
        
        logger.info(f"创建项目成功: {project.name} (ID: {project.id})")
        
        return {
            "success": True,
            "project_id": project.id,
            "data": project.to_dict()
        }
        
    except Exception as e:
        logger.error(f"创建项目失败: {e}")
        return {
            "success": False,
            "error": f"创建项目时发生错误: {str(e)}"
        }


def api_load_project(project_id: str) -> Dict[str, Any]:
    """加载项目"""
    try:
        project = storage.load_project(project_id)
        if not project:
            return {
                "success": False,
                "error": "项目不存在"
            }
        
        logger.info(f"加载项目成功: {project.name} (ID: {project_id})")
        
        return {
            "success": True,
            "data": project.to_dict()
        }
        
    except Exception as e:
        logger.error(f"加载项目失败: {e}")
        return {
            "success": False,
            "error": f"加载项目时发生错误: {str(e)}"
        }


def api_save_project(project_data: Dict[str, Any]) -> Dict[str, Any]:
    """保存项目"""
    try:
        # 从字典创建项目对象
        project = Project.from_dict(project_data)
        project.update_timestamp()
        
        # 保存项目
        success = storage.save_project(project)
        if not success:
            return {
                "success": False,
                "error": "保存项目失败"
            }
        
        logger.info(f"保存项目成功: {project.name} (ID: {project.id})")
        
        return {
            "success": True,
            "data": project.to_dict()
        }
        
    except Exception as e:
        logger.error(f"保存项目失败: {e}")
        return {
            "success": False,
            "error": f"保存项目时发生错误: {str(e)}"
        }


def api_list_projects() -> Dict[str, Any]:
    """列出所有项目"""
    try:
        projects = storage.list_projects()
        
        # 转换为摘要格式
        project_summaries = []
        for project in projects:
            project_summaries.append(project.get_summary())
        
        # 按更新时间排序
        project_summaries.sort(key=lambda x: x['updated_at'], reverse=True)
        
        logger.info(f"列出项目成功: 共 {len(project_summaries)} 个项目")
        
        return {
            "success": True,
            "data": project_summaries
        }
        
    except Exception as e:
        logger.error(f"列出项目失败: {e}")
        return {
            "success": False,
            "error": f"列出项目时发生错误: {str(e)}"
        }


def api_delete_project(project_id: str) -> Dict[str, Any]:
    """删除项目"""
    try:
        # 检查项目是否存在
        project = storage.load_project(project_id)
        if not project:
            return {
                "success": False,
                "error": "项目不存在"
            }
        
        # 删除项目
        success = storage.delete_project(project_id)
        if not success:
            return {
                "success": False,
                "error": "删除项目失败"
            }
        
        logger.info(f"删除项目成功: {project.name} (ID: {project_id})")
        
        return {
            "success": True,
            "message": f"项目 '{project.name}' 已删除"
        }
        
    except Exception as e:
        logger.error(f"删除项目失败: {e}")
        return {
            "success": False,
            "error": f"删除项目时发生错误: {str(e)}"
        }
