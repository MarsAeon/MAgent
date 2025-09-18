import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { invoke, listen } from '../utils/eel-api';
import { 
  Brain, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  Play, 
  Pause,
  RotateCcw,
  Activity,
  Users,
  MessageSquare,
  FileText,
  TrendingUp,
  Shield
} from 'lucide-react';
import { AgentState, AgentStatus } from '../types';

const WorkspacePage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session');
  const wfParam = searchParams.get('wf');
  
  // 使用 any 以兼容后端 session.summary 的动态结构（title/refined_idea 等）
  const [session, setSession] = useState<any | null>(null);
  const [agentStates, setAgentStates] = useState<AgentState[]>([
    { name: 'Clarifier', status: 'pending', progress: 0, message: '等待启动...' },
    { name: 'Innovator', status: 'pending', progress: 0, message: '等待启动...' },
    { name: 'Critic', status: 'pending', progress: 0, message: '等待启动...' },
    { name: 'Synthesizer', status: 'pending', progress: 0, message: '等待启动...' },
    { name: 'Verifier', status: 'pending', progress: 0, message: '等待启动...' },
    { name: 'Summarizer', status: 'pending', progress: 0, message: '等待启动...' }
  ]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<'workflow' | 'summary'>('workflow');
  const [workflowSessionId, setWorkflowSessionId] = useState<string | null>(wfParam);
  const navigate = useNavigate();

  useEffect(() => {
    if (sessionId) { loadSession(sessionId); }
    if (wfParam) { setWorkflowSessionId(wfParam); }
    
    // 监听后端事件（使用全局事件总线：workflow.progress_updated）
    const unlisten = listen('workflow.progress_updated', (ev: any) => {
      // ev: { id, type, data:{session_id, stage, progress, message}, source, timestamp }
      try {
        if (ev && ev.data) {
          // 若指定了 workflowSessionId，仅处理匹配该会话的事件
          if (workflowSessionId && ev.data.session_id && ev.data.session_id !== workflowSessionId) {
            return;
          }
          const { stage, progress, message } = ev.data;
          setLogs(prev => [...prev, `${new Date().toLocaleTimeString()}: [${stage}] ${message} (${progress}%)`]);
          // 简单策略：用全局进度刷新每个 Agent 卡片的进度与状态
          setAgentStates(prev => prev.map((agent) => {
            const nextProgress = Math.max(agent.progress, Number(progress) || 0);
            const status: AgentStatus = nextProgress >= 100 ? 'completed' : (nextProgress > 0 ? 'running' : 'pending');
            return { ...agent, status, progress: Math.min(nextProgress, 100), message };
          }));
        }
      } catch (e) {
        console.error('handle workflow.progress_updated failed:', e);
      }
    });

    return () => { if (typeof unlisten === 'function') unlisten(); };
  }, [sessionId, wfParam, workflowSessionId]);

  const loadSession = async (id: string) => {
    try {
      const res = await invoke<any>('get_clarification_status', { session_id: id });
      if (res && res.success && res.data) {
        setSession(res.data);
        // 根据会话状态简单推断处理标记
        setIsProcessing(res.data.status === 'running');
        // 若会话已完成或已有总结，默认切到“澄清总结”
        if (res.data.status === 'completed' || (res.data.summary && Object.keys(res.data.summary).length > 0)) {
          setActiveTab('summary');
        }
      } else {
        console.warn('get_clarification_status returned no data:', res);
      }
    } catch (error) {
      console.error('Failed to load session:', error);
    }
  };



  const startOptimization = async () => {
    if (!workflowSessionId) return;
    
    setIsProcessing(true);
    
    try {
      await invoke('start_agent_workflow', { sessionId: workflowSessionId });
      setLogs(prev => [...prev, `${new Date().toLocaleTimeString()}: 开始 Agent 工作流`]);
    } catch (error) {
      console.error('Failed to start optimization:', error);
      setLogs(prev => [...prev, `${new Date().toLocaleTimeString()}: 启动失败 - ${error}`]);
    }
  };

  const pauseOptimization = async () => {
    try {
      if (!workflowSessionId) return;
      await invoke('pause_agent_workflow', { sessionId: workflowSessionId });
      setIsProcessing(false);
      setLogs(prev => [...prev, `${new Date().toLocaleTimeString()}: 暂停工作流`]);
    } catch (error) {
      console.error('Failed to pause optimization:', error);
    }
  };

  const resetOptimization = async () => {
    try {
      if (!workflowSessionId) return;
      await invoke('reset_agent_workflow', { sessionId: workflowSessionId });
      setIsProcessing(false);
      setAgentStates(prev => prev.map(agent => ({ 
        ...agent, 
        status: 'pending', 
        progress: 0, 
        message: '等待启动...' 
      })));
      setLogs([]);
    } catch (error) {
      console.error('Failed to reset optimization:', error);
    }
  };

  const getStatusIcon = (status: AgentStatus) => {
    switch (status) {
      case 'running':
        return <Activity className="w-5 h-5 text-blue-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getAgentIcon = (agentName: string) => {
    switch (agentName) {
      case 'Clarifier':
        return <MessageSquare className="w-6 h-6" />;
      case 'Innovator':
        return <TrendingUp className="w-6 h-6" />;
      case 'Critic':
        return <AlertCircle className="w-6 h-6" />;
      case 'Synthesizer':
        return <Users className="w-6 h-6" />;
      case 'Verifier':
        return <Shield className="w-6 h-6" />;
      case 'Summarizer':
        return <FileText className="w-6 h-6" />;
      default:
        return <Brain className="w-6 h-6" />;
    }
  };

  const getAgentDescription = (agentName: string) => {
    switch (agentName) {
      case 'Clarifier':
        return '澄清想法，提取关键信息槽位';
      case 'Innovator':
        return '生成创新建议和改进方案';
      case 'Critic':
        return '批评分析，识别问题和风险';
      case 'Synthesizer':
        return '综合优化，生成迭代版本';
      case 'Verifier':
        return '验证可行性和合规性';
      case 'Summarizer':
        return '生成最终报告和建议';
      default:
        return 'AI 智能体';
    }
  };

  const SummaryView = () => {
    const sum = session?.summary || {};
    const [edit, setEdit] = useState<any>({
      title: sum.title || sum.idea_title || '',
      refined_idea: sum.refined_idea || sum.summary || sum.refined || '',
      user_segments: Array.isArray(sum.user_segments) ? sum.user_segments : [],
      core_pain_points: Array.isArray(sum.core_pain_points) ? sum.core_pain_points : [],
      key_features: Array.isArray(sum.key_features) ? sum.key_features : [],
      constraints: Array.isArray(sum.constraints) ? sum.constraints : [],
      success_metrics: Array.isArray(sum.success_metrics) ? sum.success_metrics : [],
      risks: Array.isArray(sum.risks) ? sum.risks : [],
      next_steps: Array.isArray(sum.next_steps) ? sum.next_steps : [],
    });
    const [submitting, setSubmitting] = useState(false);
  // 由 edit 表单状态承载可编辑的标题与概述
    const asList = (v: any): string[] => Array.isArray(v) ? v : (typeof v === 'string' && v ? [v] : []);
    const userSeg = asList(sum.user_segments);
    const pains = asList(sum.core_pain_points);
    const feats = asList(sum.key_features);
    const cons = asList(sum.constraints);
    const metrics = asList(sum.success_metrics);
    const risks = asList(sum.risks);
    const steps = asList(sum.next_steps);
    // 回答过的 Q&A（若 summary 自带 qa_pairs，可优先展示该字段）
    const qaPairs: string[] = Array.isArray(sum.qa_pairs) && sum.qa_pairs.length > 0
      ? sum.qa_pairs
      : (session?.questions || [])
          .filter((q: any) => q.answer)
          .map((q: any) => `${q.question} -> ${q.answer}`);

    const toText = (arr: any[]) => (Array.isArray(arr) ? arr.join('\n') : '');
    const toArray = (text: string) => (text.split('\n').map(s => s.trim()).filter(Boolean));

    const handleSubmit = async () => {
      if (!session?.id) return;
      setSubmitting(true);
      try {
        const payload = {
          title: edit.title?.trim(),
          refined_idea: edit.refined_idea?.trim(),
          user_segments: toArray(toText(edit.user_segments)),
          core_pain_points: toArray(toText(edit.core_pain_points)),
          key_features: toArray(toText(edit.key_features)),
          constraints: toArray(toText(edit.constraints)),
          success_metrics: toArray(toText(edit.success_metrics)),
          risks: toArray(toText(edit.risks)),
          next_steps: toArray(toText(edit.next_steps)),
        };
        const res = await invoke<any>('submit_summary', { session_id: session.id, summary: payload, restart: true });
        if (res?.success) {
          const wf = res.workflow_session_id || session?.workflow_session_id || session?.id;
          setWorkflowSessionId(wf || null);
          // 自动切回工作流 Tab 观察运行
          setActiveTab('workflow');
          // 跳转到工作流视图（同页路由但附带会话参数）
          if (wf) {
            navigate(`/workspace?session=${session.id}&wf=${wf}`);
          } else {
            navigate(`/workspace?session=${session.id}`);
          }
        } else {
          console.warn('提交总结失败:', res?.error);
        }
      } catch (e) {
        console.warn('submit_summary 调用异常:', e);
      } finally {
        setSubmitting(false);
      }
    };

    return (
      <div className="space-y-6">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">澄清总结</h2>
          {Object.keys(sum).length === 0 ? (
            <p className="text-gray-600 dark:text-gray-400">尚未生成总结。请在澄清环节完成后再查看。</p>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">标题</label>
                <input
                  value={edit.title}
                  onChange={e => setEdit({ ...edit, title: e.target.value })}
                  className="mt-1 w-full px-3 py-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                  placeholder="请输入总结标题"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">精炼概述</label>
                <textarea
                  value={edit.refined_idea}
                  onChange={e => setEdit({ ...edit, refined_idea: e.target.value })}
                  className="mt-1 w-full h-32 px-3 py-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 whitespace-pre-wrap"
                  placeholder="请输入精炼概述"
                />
              </div>

              {userSeg.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">目标用户</label>
                  <textarea
                    value={toText(edit.user_segments)}
                    onChange={e => setEdit({ ...edit, user_segments: e.target.value.split('\n') })}
                    className="mt-1 w-full h-20 px-3 py-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                    placeholder="每行一个目标用户"
                  />
                </div>
              )}

              {pains.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">核心痛点</label>
                  <textarea
                    value={toText(edit.core_pain_points)}
                    onChange={e => setEdit({ ...edit, core_pain_points: e.target.value.split('\n') })}
                    className="mt-1 w-full h-24 px-3 py-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                    placeholder="每行一个痛点"
                  />
                </div>
              )}

              {feats.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">关键特性</label>
                  <textarea
                    value={toText(edit.key_features)}
                    onChange={e => setEdit({ ...edit, key_features: e.target.value.split('\n') })}
                    className="mt-1 w-full h-24 px-3 py-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                    placeholder="每行一个特性"
                  />
                </div>
              )}

              {cons.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">约束条件</label>
                  <textarea
                    value={toText(edit.constraints)}
                    onChange={e => setEdit({ ...edit, constraints: e.target.value.split('\n') })}
                    className="mt-1 w-full h-20 px-3 py-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                    placeholder="每行一个约束"
                  />
                </div>
              )}

              {metrics.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">成功指标</label>
                  <textarea
                    value={toText(edit.success_metrics)}
                    onChange={e => setEdit({ ...edit, success_metrics: e.target.value.split('\n') })}
                    className="mt-1 w-full h-24 px-3 py-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                    placeholder="每行一个指标"
                  />
                </div>
              )}

              {risks.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">风险</label>
                  <textarea
                    value={toText(edit.risks)}
                    onChange={e => setEdit({ ...edit, risks: e.target.value.split('\n') })}
                    className="mt-1 w-full h-24 px-3 py-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                    placeholder="每行一个风险"
                  />
                </div>
              )}

              {steps.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">下一步</label>
                  <textarea
                    value={toText(edit.next_steps)}
                    onChange={e => setEdit({ ...edit, next_steps: e.target.value.split('\n') })}
                    className="mt-1 w-full h-24 px-3 py-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                    placeholder="每行一个下一步"
                  />
                </div>
              )}

              <div className="pt-2">
                <button
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {submitting ? '提交中…' : '提交总结并启动/重启工作流'}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">已回答的澄清问答</h2>
          {qaPairs.length === 0 ? (
            <p className="text-gray-600 dark:text-gray-400">暂无问答记录</p>
          ) : (
            <ul className="list-decimal pl-6 space-y-2 text-gray-900 dark:text-white">
              {qaPairs.map((line, idx) => (
                <li key={idx} className="whitespace-pre-wrap">{line}</li>
              ))}
            </ul>
          )}
        </div>
      </div>
    );
  };

  if (!session) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Brain className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-700 mb-2">未找到会话</h2>
          <p className="text-gray-500">请从想法输入页面开始创建新的优化会话</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 页面标题和控制 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            AI 工作区
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            多智能体协作优化进行中
          </p>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={startOptimization}
            disabled={isProcessing || !workflowSessionId}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Play className="w-4 h-4 mr-2" />
            开始
          </button>
          
          <button
            onClick={pauseOptimization}
            disabled={!isProcessing || !workflowSessionId}
            className="flex items-center px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Pause className="w-4 h-4 mr-2" />
            暂停
          </button>
          
          <button
            onClick={resetOptimization}
            disabled={!workflowSessionId}
            className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            重置
          </button>
        </div>
      </div>

      {/* 顶部 Tab */}
      <div className="flex space-x-2 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setActiveTab('workflow')}
          className={`px-4 py-2 -mb-px border-b-2 text-sm font-medium transition-colors ${
            activeTab === 'workflow'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
          }`}
        >
          工作流
        </button>
        <button
          onClick={() => setActiveTab('summary')}
          className={`px-4 py-2 -mb-px border-b-2 text-sm font-medium transition-colors ${
            activeTab === 'summary'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
          }`}
        >
          澄清总结
        </button>
      </div>

      {activeTab === 'workflow' && (
        <>
          {/* 会话信息 */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              当前会话信息
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">想法描述</label>
                <p className="text-gray-900 dark:text-white mt-1">{session.idea_seed?.raw_text || '—'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">领域</label>
                <p className="text-gray-900 dark:text-white mt-1">{session.idea_seed?.domain || '未指定'}</p>
              </div>
              {(session.idea_seed?.context_hints || []).length > 0 && (
                <div className="md:col-span-2">
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">上下文提示</label>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {session.idea_seed.context_hints.map((hint: string, index: number) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-sm rounded-md"
                      >
                        {hint}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Agent 状态面板 */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
              Agent 执行状态
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {agentStates.map((agent) => (
                <div
                  key={agent.name}
                  className={`
                    p-4 rounded-lg border-2 transition-all duration-200
                    ${agent.status === 'running' ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : ''}
                    ${agent.status === 'completed' ? 'border-green-500 bg-green-50 dark:bg-green-900/20' : ''}
                    ${agent.status === 'error' ? 'border-red-500 bg-red-50 dark:bg-red-900/20' : ''}
                    ${agent.status === 'pending' ? 'border-gray-200 dark:border-gray-700' : ''}
                  `}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <div className={`
                        p-2 rounded-lg
                        ${agent.status === 'running' ? 'bg-blue-500 text-white' : ''}
                        ${agent.status === 'completed' ? 'bg-green-500 text-white' : ''}
                        ${agent.status === 'error' ? 'bg-red-500 text-white' : ''}
                        ${agent.status === 'pending' ? 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300' : ''}
                      `}>
                        {getAgentIcon(agent.name)}
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900 dark:text-white">
                          {agent.name}
                        </h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {getAgentDescription(agent.name)}
                        </p>
                      </div>
                    </div>
                    {getStatusIcon(agent.status)}
                  </div>
                  
                  <div className="mb-2">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm text-gray-600 dark:text-gray-400">进度</span>
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {agent.progress}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className={`
                          h-2 rounded-full transition-all duration-300
                          ${agent.status === 'running' ? 'bg-blue-500' : ''}
                          ${agent.status === 'completed' ? 'bg-green-500' : ''}
                          ${agent.status === 'error' ? 'bg-red-500' : ''}
                          ${agent.status === 'pending' ? 'bg-gray-300 dark:bg-gray-600' : ''}
                        `}
                        style={{ width: `${agent.progress}%` }}
                      ></div>
                    </div>
                  </div>
                  
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {agent.message}
                  </p>
                  
                  {agent.startTime && (
                    <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                      开始时间: {new Date(agent.startTime).toLocaleTimeString()}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* 实时日志 */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              执行日志
            </h2>
            
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 h-64 overflow-y-auto font-mono text-sm">
              {logs.length === 0 ? (
                <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
                  暂无日志信息
                </div>
              ) : (
                <div className="space-y-1">
                  {logs.map((log, index) => (
                    <div key={index} className="text-gray-700 dark:text-gray-300">
                      {log}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {activeTab === 'summary' && (
        <SummaryView />
      )}
    </div>
  );
};

export default WorkspacePage;
