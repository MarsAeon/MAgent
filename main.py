#!/usr/bin/env python3
"""
IdeaArchitect - 多智能体想法完成引擎
主程序入口
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import eel
from config.app_config import app_config, ensure_directories
from src.utils.logger import get_logger, setup_logging
from src.utils.event_bus import event_bus, EventTypes
from src.api import *
# 为了类型检查与静态分析友好，显式导入关键API符号
try:
    from src.api import (
        run_clarification_ai,
        api_start_clarification_session,
        api_submit_clarification_answer,
        api_get_clarification_status,
        api_finish_clarification,
    )
except Exception:
    # 允许在部分模块缺失时继续运行（在 expose 时再做保护）
    pass

logger = get_logger(__name__)


def setup_eel():
    """设置Eel框架（生产优先使用构建后的 dist 目录）"""
    # 优先使用 React 构建输出目录 dist
    dist_dir = project_root / 'dist'
    if dist_dir.exists():
        web_dir = dist_dir
        logger.info(f"检测到生产构建目录: {dist_dir}")
    else:
        # 回退：使用项目根目录（仅用于开发调试）
        web_dir = project_root
        logger.warning("未找到 dist 目录，回退到项目根目录（开发模式）")

    # 初始化Eel，指向前端资源目录
    eel.init(str(web_dir))
    logger.info(f"Eel框架初始化完成，前端目录: {web_dir}")


def register_api_endpoints():
    """注册API端点"""
    
    # 项目管理API
    eel.expose(api_create_project)
    eel.expose(api_load_project)
    eel.expose(api_save_project)
    eel.expose(api_list_projects)
    eel.expose(api_delete_project)
    
    # 工作流API
    eel.expose(api_start_workflow)
    eel.expose(api_get_workflow_status)
    eel.expose(api_pause_workflow)
    eel.expose(api_resume_workflow)
    eel.expose(api_stop_workflow)
    
    # 智能体API
    eel.expose(api_list_agents)
    eel.expose(api_create_agent)
    eel.expose(api_get_agent_status)
    eel.expose(api_configure_agent)
    
    # 模型API
    eel.expose(api_call_ai_model)
    eel.expose(api_test_model_connection)
    eel.expose(api_list_available_models)
    eel.expose(api_get_model_config)

    # 澄清/智能问答 API
    try:
        eel.expose(run_clarification_ai)
    except NameError:
        # 兼容未导入情况
        pass
    # 新的澄清会话式API
    try:
        eel.expose(api_start_clarification_session)
        eel.expose(api_submit_clarification_answer)
        eel.expose(api_get_clarification_status)
        eel.expose(api_finish_clarification)
    except NameError:
        pass
    
    logger.info("API端点注册完成")


@eel.expose
def get_app_info():
    """获取应用信息"""
    return {
        "name": app_config.app_name,
        "version": app_config.app_version,
        "debug": app_config.debug
    }


@eel.expose
def get_app_config():
    """获取应用配置"""
    return {
        "workflow_mode": app_config.default_workflow_mode.value,
        "max_discussion_rounds": app_config.max_discussion_rounds,
        "convergence_threshold": app_config.convergence_threshold,
        "max_concurrent_agents": app_config.max_concurrent_agents
    }


@eel.expose
def ping():
    """健康检查"""
    return {"status": "ok", "timestamp": str(datetime.now())}


def setup_event_handlers():
    """设置事件处理器"""
    
    def on_system_error(event):
        """系统错误处理"""
        logger.error(f"系统错误: {event.data}")
    
    def on_workflow_progress(event):
        """工作流进度更新"""
        logger.info(f"工作流进度: {event.data}")
    
    # 订阅系统事件
    event_bus.subscribe(EventTypes.SYSTEM_ERROR, on_system_error)
    event_bus.subscribe(EventTypes.WORKFLOW_PROGRESS_UPDATED, on_workflow_progress)
    
    logger.info("事件处理器设置完成")


def check_dependencies():
    """检查依赖"""
    try:
        # 检查必要的目录
        ensure_directories()
        
        # 检查AI模型配置（任一可用即可）
        if not any([
            app_config.openai_api_key,
            app_config.anthropic_api_key,
            getattr(app_config, 'deepseek_api_key', None),
            getattr(app_config, 'qwen_api_key', None),
        ]):
            logger.warning("未配置AI模型API密钥，某些功能可能不可用")
        
        logger.info("依赖检查完成")
        return True
        
    except Exception as e:
        logger.error(f"依赖检查失败: {e}")
        return False


def main():
    """主函数"""
    try:
        logger.info(f"启动 {app_config.app_name} v{app_config.app_version}")
        
        # 检查依赖
        if not check_dependencies():
            logger.error("依赖检查失败，程序退出")
            sys.exit(1)
        
        # 设置Eel
        setup_eel()
        
        # 注册API端点
        register_api_endpoints()
        
        # 设置事件处理器
        setup_event_handlers()
        
        # 发布启动事件
        event_bus.emit(EventTypes.SYSTEM_INFO, "应用程序启动完成")
        
        # 启动Eel应用
        logger.info(f"启动Web服务器: http://{app_config.eel_host}:{app_config.eel_port}")

        # 检查是否为纯Python模式
        python_only_mode = os.environ.get('IDEAARCHITECT_MODE') == 'python_only'

        if python_only_mode:
            logger.info("纯Python模式启动 - 仅启动API服务器")
            logger.info(f"API服务器运行在: http://{app_config.eel_host}:{app_config.eel_port}")
            logger.info("按 Ctrl+C 停止服务器")

            # 启动Eel但不打开浏览器
            eel.start(
                'index.html',
                mode=None,  # 不自动打开浏览器
                host=app_config.eel_host,
                port=app_config.eel_port,
                block=True,  # 阻塞主线程
                close_callback=on_close
            )
        else:
            # [生产][0m 优先从 dist/index.html 启动
            start_file = 'index.html'
            eel.start(
                start_file,
                mode='chrome-app',  # Windows [desktop][0m
                host=app_config.eel_host,
                port=app_config.eel_port,
                size=app_config.eel_size,
                position=(100, 100),
                disable_cache=not app_config.debug,
                close_callback=on_close
            )
        
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        sys.exit(1)


def on_close(page=None, sockets=None):
    """应用关闭回调"""
    logger.info("应用程序正在关闭...")

    # 发布关闭事件
    event_bus.emit(EventTypes.SYSTEM_INFO, "应用程序正在关闭")

    # 清理资源
    # TODO: 添加清理逻辑

    logger.info("应用程序已关闭")


if __name__ == "__main__":
    main()
