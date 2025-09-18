/**
 * Eel API Adapter
 * 替换Tauri API调用，使用Eel与Python后端通信
 */

// 声明Eel全局对象
declare global {
  interface Window {
    eel: {
      // 项目管理API
      api_create_project: (name: string, description?: string, initial_idea?: string) => Promise<any>;
      api_load_project: (project_id: string) => Promise<any>;
      api_save_project: (project_data: any) => Promise<any>;
      api_list_projects: () => Promise<any>;
      api_delete_project: (project_id: string) => Promise<any>;
      
      // 工作流API
      api_start_workflow: (project_id: string, initial_idea: string, workflow_mode?: string) => Promise<any>;
      api_get_workflow_status: (session_id: string) => Promise<any>;
      api_pause_workflow: (session_id: string) => Promise<any>;
      api_resume_workflow: (session_id: string) => Promise<any>;
      api_stop_workflow: (session_id: string) => Promise<any>;
      
      // 智能体API
      api_list_agents: () => Promise<any>;
      api_create_agent: (name: string, role: string, model?: string, description?: string) => Promise<any>;
      api_get_agent_status: (agent_id: string) => Promise<any>;
      api_configure_agent: (agent_id: string, config: any) => Promise<any>;
      
      // 模型API
      api_call_ai_model: (provider: string, model: string, messages: any[], config?: any) => Promise<any>;
      api_test_model_connection: (provider: string, model: string) => Promise<any>;
      api_list_available_models: () => Promise<any>;
      api_get_model_config: (provider: string, model: string) => Promise<any>;

  // 澄清会话API
  api_start_clarification_session: (seed: any) => Promise<any>;
  api_submit_clarification_answer: (session_id: string, slot_name: string, answer: string) => Promise<any>;
  api_get_clarification_status: (session_id: string) => Promise<any>;
  api_finish_clarification: (session_id: string) => Promise<any>;
  api_submit_summary: (session_id: string, summary: any, restart?: boolean) => Promise<any>;
      
      // 应用信息API
      get_app_info: () => Promise<any>;
      get_app_config: () => Promise<any>;
      ping: () => Promise<any>;
      
      // 事件API
      get_event_history: (event_type?: string, limit?: number) => Promise<any>;
      clear_event_history: () => Promise<any>;
      
      // 设置事件回调
      set_host: (host: string) => void;
      expose: (func: Function, name: string) => void;
    };
  }
}

/**
 * Eel API包装器，提供与Tauri API兼容的接口
 */
export class EelAPI {
  
  /**
   * 检查Eel是否可用
   */
  static isAvailable(): boolean {
    return typeof window !== 'undefined' && window.eel !== undefined;
  }
  
  /**
   * 调用Python函数（替换Tauri的invoke）
   */
  static async invoke<T>(command: string, args?: any): Promise<T> {
    if (!EelAPI.isAvailable()) {
      throw new Error('Eel is not available');
    }
    
    try {
      // 将Tauri命令映射到Eel函数
      const result = await EelAPI.mapTauriCommand(command, args);
      return result;
    } catch (error) {
      console.error(`Eel invoke error for command ${command}:`, error);
      throw error;
    }
  }
  
  /**
   * 映射Tauri命令到Eel函数
   */
  private static async call(name: string, ...args: any[]): Promise<any> {
    // 兼容 Eel 的双调用风格：eel.func(...args)()
    const ret = (window.eel as any)[name](...args);
    if (typeof ret === 'function') {
      return await ret();
    }
    return await ret;
  }

  private static async mapTauriCommand(command: string, args?: any): Promise<any> {
    switch (command) {
      case 'run_clarification_ai':
        return await EelAPI.call('run_clarification_ai', args.ideaContent ?? args.text ?? '');
      case 'start_clarification_session':
        return await EelAPI.call('api_start_clarification_session', args.seed ?? { raw_text: args.text ?? '' });
      case 'submit_clarification_answer':
        return await EelAPI.call('api_submit_clarification_answer', args.session_id, args.slot_name, args.answer);
      case 'get_clarification_status':
        return await EelAPI.call('api_get_clarification_status', args.session_id);
      case 'finish_clarification':
        return await EelAPI.call('api_finish_clarification', args.session_id);
      case 'submit_summary':
        return await EelAPI.call('api_submit_summary', args.session_id, args.summary, args.restart ?? true);
      // 项目管理命令
      case 'create_project':
        // Python 端期望一个 dict 参数，这里按对象传递，避免参数数量不匹配
        return await EelAPI.call('api_create_project', {
          name: args.name,
          description: args.description,
          initial_idea: args.initial_idea,
          domain: args.domain ?? 'general',
        });

      case 'load_project':
        return await EelAPI.call('api_load_project', args.project_id);

      case 'save_project':
        return await EelAPI.call('api_save_project', args.project_data);

      case 'list_projects':
        return await EelAPI.call('api_list_projects');

      case 'delete_project':
        return await EelAPI.call('api_delete_project', args.project_id);

      // 工作流命令
      case 'start_concept_optimization':
        // 创建项目并启动工作流（按后端期望传入对象参数）
        const projectResult = await EelAPI.call(
          'api_create_project',
          {
            name: `想法优化 ${new Date().toLocaleString()}`,
            description: '通过多智能体协作优化的想法',
            initial_idea: args.seed.raw_text,
            domain: 'general',
          }
        );

        if (projectResult.success) {
          const projectId = projectResult.project_id ?? projectResult.data?.id;
          const workflowResult = await EelAPI.call(
            'api_start_workflow',
            projectId,
            args.seed.raw_text,
            'balanced'
          );

          if (workflowResult.success) {
            return workflowResult.session_id ?? workflowResult.data?.session_id;
          }
          throw new Error(workflowResult.error);
        }
        throw new Error(projectResult.error);

      case 'get_workflow_status':
        return await EelAPI.call('api_get_workflow_status', args.session_id);

      case 'pause_workflow':
        return await EelAPI.call('api_pause_workflow', args.session_id);

      case 'resume_workflow':
        return await EelAPI.call('api_resume_workflow', args.session_id);

      case 'stop_workflow':
        return await EelAPI.call('api_stop_workflow', args.session_id);

      // 兼容工作区页面的按键命令（映射到工作流控制）
      case 'start_agent_workflow':
        // 将“开始”映射为恢复运行
        return await EelAPI.call('api_resume_workflow', args.sessionId ?? args.session_id);

      case 'pause_agent_workflow':
        return await EelAPI.call('api_pause_workflow', args.sessionId ?? args.session_id);

      case 'reset_agent_workflow':
        // 简化逻辑：映射为停止工作流；前端本地重置UI状态
        return await EelAPI.call('api_stop_workflow', args.sessionId ?? args.session_id);

      // 智能体命令
      case 'list_agents':
        return await EelAPI.call('api_list_agents');

      case 'create_agent':
        return await EelAPI.call('api_create_agent', args.name, args.role, args.model, args.description);

      case 'get_agent_status':
        return await EelAPI.call('api_get_agent_status', args.agent_id);

      // 模型命令
      case 'call_ai_model':
        return await EelAPI.call('api_call_ai_model', args.provider, args.model, args.messages, args.config);

      case 'test_model_connection':
        return await EelAPI.call('api_test_model_connection', args.provider, args.model);

      case 'list_available_models':
        return await EelAPI.call('api_list_available_models');

      // 应用信息命令
      case 'get_app_info':
        return await EelAPI.call('get_app_info');

      case 'get_app_config':
        return await EelAPI.call('get_app_config');
      
      default:
        throw new Error(`Unknown command: ${command}`);
    }
  }
  
  /**
   * 监听事件（替换Tauri的事件监听）
   * 优先使用 eel.onEvent 实时推送；辅以轮询补齐遗漏事件
   */
  static listen(event: string | undefined, callback: (ev: any) => void): () => void {
    const handlers: Array<() => void> = [];

    // 1) 监听从 Python 推送到前端的实时事件
    const onEelEvent = (e: CustomEvent) => {
      const ev = (e as any).detail; // { id, type, data, source, timestamp }
      if (!event || ev.type === event) {
        try { callback(ev); } catch (err) { console.error('listen callback error:', err); }
      }
    };
    const bound = onEelEvent as EventListener;
    window.addEventListener('eel-event', bound);
    handlers.push(() => window.removeEventListener('eel-event', bound));

    // 2) 轮询事件历史，避免漏事件
    const interval = setInterval(async () => {
      try {
        const events = await EelAPI.call('get_event_history', event, 10);
        if (Array.isArray(events)) {
          for (const ev of events) {
            if (!event || ev.type === event) {
              try { callback(ev); } catch (err) { console.error('listen callback error:', err); }
            }
          }
        }
      } catch (error) {
        // 仅记录，不中断
        // console.debug('poll events error:', error);
      }
    }, 2000);
    handlers.push(() => clearInterval(interval));

    // 返回取消函数
    return () => { handlers.forEach(h => h()); };
  }
}

/**
 * 替换Tauri的invoke函数
 */
export const invoke = EelAPI.invoke;

/**
 * 替换Tauri的事件监听
 */
export const listen = EelAPI.listen;

/**
 * 初始化Eel连接
 */
export function initializeEel(): Promise<void> {
  return new Promise((resolve) => {
    // 等待Eel加载完成
    if (EelAPI.isAvailable()) {
      resolve();
    } else {
      // 等待Eel脚本加载
      const checkEel = () => {
        if (EelAPI.isAvailable()) {
          resolve();
        } else {
          setTimeout(checkEel, 100);
        }
      };
      checkEel();
    }
  });
}

// 设置全局事件处理器
if (typeof window !== 'undefined') {
  // 当Eel可用时设置事件处理器
  window.addEventListener('load', () => {
    if (EelAPI.isAvailable()) {
      // 设置Python到JavaScript的事件回调
      window.eel.expose((event: any) => {
        // 处理从Python发送的事件
        console.log('Received event from Python:', event);
        
        // 触发自定义事件
        const customEvent = new CustomEvent('eel-event', { detail: event });
        window.dispatchEvent(customEvent);
      }, 'onEvent');
    }
  });
}
