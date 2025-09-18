# -*- coding: utf-8 -*-
import json, time
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.api.agent_api import api_list_agents, api_create_agent, api_get_agent_status
from src.api.project_api import api_create_project, api_list_projects
from src.api.workflow_api import api_start_workflow, api_get_workflow_status

print('--- Agent API ---')
print(json.dumps(api_list_agents(), ensure_ascii=False))
ra = api_create_agent('测试Agent', 'tester', 'gpt-4o', '用于集成测试')
print(json.dumps(ra, ensure_ascii=False))
print(json.dumps(api_get_agent_status(ra['data']['id']), ensure_ascii=False))

print('\n--- Project & Workflow ---')
rp = api_create_project({'name':'生产集成测试项目','description':'用于Eel集成测试','initial_idea':'一个AI学习平台','domain':'edtech'})
print('create_project.success =', rp.get('success'), 'project_id =', rp.get('project_id'))
project_id = rp['project_id']
rs = api_start_workflow(project_id, '一个AI学习平台', 'balanced')
print('start_workflow.success =', rs.get('success'), 'session_id =', rs.get('session_id'))
session_id = rs.get('session_id')

for i in range(2):
    time.sleep(1)
    st = api_get_workflow_status(session_id)
    print('status', i, json.dumps(st, ensure_ascii=False, default=str))

