"""
Event Bus for Real-time Communication
"""

import uuid
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from collections import defaultdict

# 简化版本，不依赖eel
try:
    import eel
    EEL_AVAILABLE = True
except ImportError:
    EEL_AVAILABLE = False

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Event:
    """事件数据类"""
    id: str
    type: str
    data: Any
    source: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp.isoformat()
        }


class EventTypes:
    """事件类型常量"""
    # 系统事件
    SYSTEM_INFO = "system.info"
    SYSTEM_WARNING = "system.warning"
    SYSTEM_ERROR = "system.error"
    
    # 项目事件
    PROJECT_CREATED = "project.created"
    PROJECT_LOADED = "project.loaded"
    PROJECT_SAVED = "project.saved"
    PROJECT_DELETED = "project.deleted"
    
    # 工作流事件
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_PROGRESS_UPDATED = "workflow.progress_updated"
    WORKFLOW_STAGE_CHANGED = "workflow.stage_changed"
    WORKFLOW_PAUSED = "workflow.paused"
    WORKFLOW_RESUMED = "workflow.resumed"
    WORKFLOW_STOPPED = "workflow.stopped"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    
    # 智能体事件
    AGENT_CREATED = "agent.created"
    AGENT_STATUS_CHANGED = "agent.status_changed"
    AGENT_MESSAGE_SENT = "agent.message_sent"
    AGENT_MESSAGE_RECEIVED = "agent.message_received"
    
    # 讨论事件
    DISCUSSION_STARTED = "discussion.started"
    DISCUSSION_ROUND_COMPLETED = "discussion.round_completed"
    DISCUSSION_CONVERGED = "discussion.converged"
    DISCUSSION_ENDED = "discussion.ended"


class EventBus:
    """事件总线"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.event_history: List[Event] = []
        self.max_history = 1000
    
    def subscribe(self, event_type: str, callback: Callable[[Event], None]):
        """订阅事件"""
        self.subscribers[event_type].append(callback)
        logger.debug(f"订阅事件: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable[[Event], None]):
        """取消订阅事件"""
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(callback)
                logger.debug(f"取消订阅事件: {event_type}")
            except ValueError:
                pass
    
    def emit(self, event_type: str, data: Any, source: str = "system") -> Event:
        """发布事件"""
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            data=data,
            source=source,
            timestamp=datetime.now()
        )
        
        # 添加到历史记录
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # 通知订阅者
        for callback in self.subscribers.get(event_type, []):
            try:
                callback(event)
            except Exception as e:
                logger.error(f"事件回调执行失败: {e}")
        
        # 推送到前端
        self._push_to_frontend(event)
        
        logger.debug(f"发布事件: {event_type}")
        return event
    
    def _push_to_frontend(self, event: Event):
        """推送事件到前端"""
        if EEL_AVAILABLE:
            try:
                # 使用Eel推送事件到前端
                eel.onEvent(event.to_dict())
            except Exception as e:
                logger.debug(f"推送事件到前端失败: {e}")
        else:
            # 如果Eel不可用，只记录日志
            logger.debug(f"事件: {event.type} - {event.data}")
    
    def get_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Event]:
        """获取事件历史"""
        if event_type:
            filtered_events = [e for e in self.event_history if e.type == event_type]
        else:
            filtered_events = self.event_history
        
        return filtered_events[-limit:]
    
    def clear_history(self):
        """清空事件历史"""
        self.event_history.clear()
        logger.info("事件历史已清空")


# 全局事件总线实例
event_bus = EventBus()


# Eel暴露的事件相关函数（如果可用）
if EEL_AVAILABLE:
    @eel.expose
    def get_event_history(event_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取事件历史（前端调用）"""
        events = event_bus.get_history(event_type, limit)
        return [event.to_dict() for event in events]

    @eel.expose
    def clear_event_history():
        """清空事件历史（前端调用）"""
        event_bus.clear_history()
        return {"success": True, "message": "事件历史已清空"}
else:
    # 提供备用函数
    def get_event_history(event_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取事件历史（备用版本）"""
        events = event_bus.get_history(event_type, limit)
        return [event.to_dict() for event in events]

    def clear_event_history():
        """清空事件历史（备用版本）"""
        event_bus.clear_history()
        return {"success": True, "message": "事件历史已清空"}
