"""
Storage Utilities
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from ..models.project import Project
from ..utils.logger import get_logger
from config.app_config import app_config

logger = get_logger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理datetime对象"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class ProjectStorage:
    """项目存储管理"""
    
    def __init__(self):
        self.projects_dir = app_config.projects_dir
        self.projects_dir.mkdir(parents=True, exist_ok=True)
    
    def save_project(self, project: Project) -> bool:
        """保存项目"""
        try:
            project_file = self.projects_dir / f"{project.id}.json"

            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project.to_dict(), f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)

            logger.debug(f"项目已保存: {project_file}")
            return True

        except Exception as e:
            logger.error(f"保存项目失败: {e}")
            return False
    
    def load_project(self, project_id: str) -> Optional[Project]:
        """加载项目"""
        try:
            project_file = self.projects_dir / f"{project_id}.json"
            
            if not project_file.exists():
                return None
            
            with open(project_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            project = Project.from_dict(data)
            logger.debug(f"项目已加载: {project_file}")
            return project
            
        except Exception as e:
            logger.error(f"加载项目失败: {e}")
            return None
    
    def list_projects(self) -> List[Project]:
        """列出所有项目"""
        try:
            projects = []
            
            for project_file in self.projects_dir.glob("*.json"):
                try:
                    with open(project_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    project = Project.from_dict(data)
                    projects.append(project)
                    
                except Exception as e:
                    logger.warning(f"跳过损坏的项目文件 {project_file}: {e}")
                    continue
            
            logger.debug(f"列出项目: 共 {len(projects)} 个")
            return projects
            
        except Exception as e:
            logger.error(f"列出项目失败: {e}")
            return []
    
    def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        try:
            project_file = self.projects_dir / f"{project_id}.json"
            
            if project_file.exists():
                project_file.unlink()
                logger.debug(f"项目已删除: {project_file}")
                return True
            else:
                logger.warning(f"项目文件不存在: {project_file}")
                return False
                
        except Exception as e:
            logger.error(f"删除项目失败: {e}")
            return False


class SessionStorage:
    """会话存储管理"""
    
    def __init__(self):
        self.sessions_dir = app_config.data_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """保存会话"""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"会话已保存: {session_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存会话失败: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载会话"""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            
            if not session_file.exists():
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"会话已加载: {session_file}")
            return data
            
        except Exception as e:
            logger.error(f"加载会话失败: {e}")
            return None


class CacheStorage:
    """缓存存储管理"""
    
    def __init__(self):
        self.cache_dir = app_config.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = timedelta(hours=24)
    
    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> bool:
        """设置缓存"""
        try:
            if ttl is None:
                ttl = self.default_ttl
            
            cache_data = {
                "value": value,
                "expires_at": (datetime.now() + ttl).isoformat()
            }
            
            cache_file = self.cache_dir / f"{key}.json"
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"缓存已设置: {key}")
            return True
            
        except Exception as e:
            logger.error(f"设置缓存失败: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            cache_file = self.cache_dir / f"{key}.json"
            
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 检查是否过期
            expires_at = datetime.fromisoformat(cache_data["expires_at"])
            if datetime.now() > expires_at:
                # 删除过期缓存
                cache_file.unlink()
                logger.debug(f"缓存已过期并删除: {key}")
                return None
            
            logger.debug(f"缓存命中: {key}")
            return cache_data["value"]
            
        except Exception as e:
            logger.error(f"获取缓存失败: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            cache_file = self.cache_dir / f"{key}.json"
            
            if cache_file.exists():
                cache_file.unlink()
                logger.debug(f"缓存已删除: {key}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"删除缓存失败: {e}")
            return False
    
    def clear_expired(self) -> int:
        """清理过期缓存"""
        try:
            cleared_count = 0
            
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    expires_at = datetime.fromisoformat(cache_data["expires_at"])
                    if datetime.now() > expires_at:
                        cache_file.unlink()
                        cleared_count += 1
                        
                except Exception as e:
                    logger.warning(f"清理缓存文件失败 {cache_file}: {e}")
                    continue
            
            logger.info(f"清理过期缓存: {cleared_count} 个文件")
            return cleared_count
            
        except Exception as e:
            logger.error(f"清理过期缓存失败: {e}")
            return 0
