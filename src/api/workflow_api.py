"""
Workflow Management API
"""

import asyncio
from typing import Dict, Any
from datetime import datetime

from ..utils.logger import get_logger
from ..utils.event_bus import event_bus, EventTypes

logger = get_logger(__name__)

# 简化的工作流状态存储
workflow_sessions = {}


def api_start_workflow(project_id: str, initial_idea: str, workflow_mode: str = "balanced") -> Dict[str, Any]:
    """启动工作流"""
    try:
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{project_id[:8]}"
        
        # 创建工作流会话
        session = {
            "id": session_id,
            "project_id": project_id,
            "initial_idea": initial_idea,
            "workflow_mode": workflow_mode,
            "stage": "questioning",
            "progress": 0.0,
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "results": {}
        }
        
        workflow_sessions[session_id] = session
        
        # 发布事件
        event_bus.emit(EventTypes.WORKFLOW_STARTED, {
            "session_id": session_id,
            "project_id": project_id,
            "initial_idea": initial_idea
        })
        
        # 模拟工作流进度（在后台线程中运行）
        import threading
        def run_simulation():
            import asyncio
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(simulate_workflow_progress(session_id))
                loop.close()
            except Exception as e:
                logger.error(f"工作流模拟失败: {e}")

        thread = threading.Thread(target=run_simulation, daemon=True)
        thread.start()
        
        logger.info(f"工作流启动成功: {session_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "data": {
                "session_id": session_id,
                "status": "started",
                "stage": "questioning"
            }
        }
        
    except Exception as e:
        logger.error(f"启动工作流失败: {e}")
        return {
            "success": False,
            "error": f"启动工作流时发生错误: {str(e)}"
        }


def api_get_workflow_status(session_id: str) -> Dict[str, Any]:
    """获取工作流状态"""
    try:
        if session_id not in workflow_sessions:
            return {
                "success": False,
                "error": "工作流会话不存在"
            }
        
        session = workflow_sessions[session_id]
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "stage": session["stage"],
                "progress": session["progress"],
                "status": session["status"],
                "messages": session["messages"][-5:],  # 最近5条消息
                "results": session["results"]
            }
        }
        
    except Exception as e:
        logger.error(f"获取工作流状态失败: {e}")
        return {
            "success": False,
            "error": f"获取工作流状态时发生错误: {str(e)}"
        }


def api_pause_workflow(session_id: str) -> Dict[str, Any]:
    """暂停工作流"""
    try:
        if session_id not in workflow_sessions:
            return {
                "success": False,
                "error": "工作流会话不存在"
            }
        
        workflow_sessions[session_id]["status"] = "paused"
        
        logger.info(f"工作流已暂停: {session_id}")
        
        return {
            "success": True,
            "message": "工作流已暂停"
        }
        
    except Exception as e:
        logger.error(f"暂停工作流失败: {e}")
        return {
            "success": False,
            "error": f"暂停工作流时发生错误: {str(e)}"
        }


def api_resume_workflow(session_id: str) -> Dict[str, Any]:
    """恢复工作流"""
    try:
        if session_id not in workflow_sessions:
            return {
                "success": False,
                "error": "工作流会话不存在"
            }
        
        workflow_sessions[session_id]["status"] = "running"
        
        logger.info(f"工作流已恢复: {session_id}")
        
        return {
            "success": True,
            "message": "工作流已恢复"
        }
        
    except Exception as e:
        logger.error(f"恢复工作流失败: {e}")
        return {
            "success": False,
            "error": f"恢复工作流时发生错误: {str(e)}"
        }


def api_stop_workflow(session_id: str) -> Dict[str, Any]:
    """停止工作流"""
    try:
        if session_id not in workflow_sessions:
            return {
                "success": False,
                "error": "工作流会话不存在"
            }
        
        workflow_sessions[session_id]["status"] = "stopped"
        
        logger.info(f"工作流已停止: {session_id}")
        
        return {
            "success": True,
            "message": "工作流已停止"
        }
        
    except Exception as e:
        logger.error(f"停止工作流失败: {e}")
        return {
            "success": False,
            "error": f"停止工作流时发生错误: {str(e)}"
        }


async def simulate_workflow_progress(session_id: str):
    """模拟工作流进度"""
    try:
        session = workflow_sessions.get(session_id)
        if not session:
            return
        
        stages = [
            ("questioning", "正在分析想法并生成反问...", 25),
            ("iterating", "智能体正在讨论和迭代方案...", 50),
            ("verifying", "正在验证和评估方案...", 75),
            ("summarizing", "正在生成最终总结...", 90),
            ("completed", "工作流已完成", 100)
        ]
        
        for stage, message, progress in stages:
            if session["status"] != "running":
                break
            
            # 更新会话状态
            session["stage"] = stage
            session["progress"] = progress
            session["messages"].append({
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "type": "system"
            })
            
            # 发布进度事件
            event_bus.emit(EventTypes.WORKFLOW_PROGRESS_UPDATED, {
                "session_id": session_id,
                "stage": stage,
                "progress": progress,
                "message": message
            })
            
            # 模拟处理时间
            await asyncio.sleep(3)
        
        # 完成工作流
        if session["status"] == "running":
            session["status"] = "completed"
            session["results"] = {
                "final_solution": "这是一个模拟的解决方案，展示了多智能体协作的结果。",
                "implementation_plan": "详细的实施计划将在这里显示。",
                "risk_analysis": "风险分析和缓解策略。"
            }
            
            event_bus.emit(EventTypes.WORKFLOW_COMPLETED, {
                "session_id": session_id,
                "results": session["results"]
            })
        
    except Exception as e:
        logger.error(f"工作流进度模拟失败: {e}")
        if session_id in workflow_sessions:
            workflow_sessions[session_id]["status"] = "failed"
