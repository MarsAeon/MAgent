"""
IdeaArchitect API Layer
"""

from .project_api import (
    api_create_project,
    api_load_project,
    api_save_project,
    api_list_projects,
    api_delete_project
)

from .workflow_api import (
    api_start_workflow,
    api_get_workflow_status,
    api_pause_workflow,
    api_resume_workflow,
    api_stop_workflow
)

from .agent_api import (
    api_list_agents,
    api_create_agent,
    api_get_agent_status,
    api_configure_agent
)

from .questioning_api import (
    api_start_clarification_session,
    api_submit_clarification_answer,
    api_get_clarification_status,
    api_finish_clarification,
    api_submit_summary,
)

from .model_api import (
    api_call_ai_model,
    api_test_model_connection,
    api_list_available_models,
    api_get_model_config
)

from .clarification_api import (
    run_clarification_ai,
)

__all__ = [
    # Project API
    "api_create_project",
    "api_load_project", 
    "api_save_project",
    "api_list_projects",
    "api_delete_project",
    
    # Workflow API
    "api_start_workflow",
    "api_get_workflow_status",
    "api_pause_workflow",
    "api_resume_workflow",
    "api_stop_workflow",
    
    # Questioning API
    "api_start_clarification_session",
    "api_submit_clarification_answer",
    "api_get_clarification_status",
    "api_finish_clarification",
    "api_submit_summary",
    # Agent API
    "api_list_agents",
    "api_create_agent",
    "api_get_agent_status",
    "api_configure_agent",
    
    # Model API
    "api_call_ai_model",
    "api_test_model_connection",
    "api_list_available_models",
    "api_get_model_config"
    ,
    # Clarification API
    "run_clarification_ai"
]
