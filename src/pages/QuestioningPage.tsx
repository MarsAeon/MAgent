import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { invoke } from '../utils/eel-api';
import { 
  MessageSquare, 
  Send, 
  Bot, 
  User,
  Lightbulb,
  Target
} from 'lucide-react';
import { Clarification, IdeaSeed } from '../types';

interface ChatMessage {
  id: string;
  type: 'bot' | 'user';
  content: string;
  timestamp: Date;
  clarificationId?: string;
  isImportant?: boolean;
}

const QuestioningPage: React.FC = () => {
  const navigate = useNavigate();
  const [currentIdea, setCurrentIdea] = useState<IdeaSeed | null>(null);
  const [clarifications, setClarifications] = useState<Clarification[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentInput, setCurrentInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [completedSlots, setCompletedSlots] = useState(new Set<string>());
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [askedSlots, setAskedSlots] = useState(new Set<string>());
  // 允许用户随时输入与发送（取消首问前禁用）
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const [isCompleted, setIsCompleted] = useState(false);
  // 默认折叠“当前想法摘要”，给对话区域更多空间
  const [showIdeaCard, setShowIdeaCard] = useState(false);

  // 当消息或加载状态变化时，自动滚动到底部
  useEffect(() => {
    try {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    } catch {}
  }, [messages, isProcessing]);

  // 规范化问题文本用于去重
  const normalize = (text: string) => (
    (text || '')
      .trim()
      .toLowerCase()
      .replace(/[\s\t\n\r]+/g, ' ')
      .replace(/[，。！？、；：:;\-—…·•\.,!\?\(\)\[\]\{\}<>“”‘’\"'《》【】]+/g, '')
  );

  // 仅在未问过/未完成且内容不重复时插入问题
  const pushQuestionIfNew = (slot: string, text: string) => {
    if (!slot || !text) return false;
    const norm = normalize(text);
    let inserted = false;
    setMessages(prev => {
      const alreadyAskedThisSlot = askedSlots.has(slot) || completedSlots.has(slot);
      const alreadyHasSameText = prev.some(m => m.type === 'bot' && !m.isImportant && normalize(m.content) === norm);
      if (alreadyAskedThisSlot || alreadyHasSameText) {
        return prev;
      }
      const questionMessage: ChatMessage = {
        id: `question-${slot}-${Date.now()}`,
        type: 'bot',
        content: text,
        timestamp: new Date(),
        clarificationId: slot,
      };
      inserted = true;
      return [...prev, questionMessage];
    });
    if (inserted) {
      setAskedSlots(prev => new Set([...prev, slot]));
    }
    return inserted;
  };

  useEffect(() => {
    // 优先从 sessionStorage 获取 idea（由 IdeaInputPage 传递）
    const saved = sessionStorage.getItem('currentIdeaSeed');
    if (saved) {
      try { setCurrentIdea(JSON.parse(saved)); } catch {}
    }
    // 兜底：加载默认示例
    if (!saved) loadCurrentIdea();
  }, []);

  useEffect(() => {
    if (currentIdea) {
      startClarificationProcess();
    }
  }, [currentIdea]);

  const loadCurrentIdea = () => {
    // TODO: 从上一页传递的数据或本地存储获取
    const mockIdea: IdeaSeed = {
      raw_text: "一个基于AI的智能学习平台，能够根据学生的学习风格和进度自动调整教学内容",
      context_hints: ["面向大学生", "在线教育"],
      domain: "教育科技"
    };
    setCurrentIdea(mockIdea);
  };

  const startClarificationProcess = async () => {
    if (!currentIdea) return;

    setIsProcessing(true);
    
    try {
      console.log("Starting Clarification Session...");

      const res = await invoke<any>('start_clarification_session', { seed: currentIdea });
      if (!res?.success) throw new Error(res?.error || '无法创建澄清会话');

      setSessionId(res.session_id);

      const qs = res.questions as Array<{ question: string; slot_name: string; priority?: number; type?: string }>;
      const normalized: Clarification[] = (qs || []).map(q => ({
        question: q.question,
        slot_name: q.slot_name,
        importance: Math.max(1, Math.min(10, (q.priority ?? 7))),
        suggested_answers: ["好的", "否", "需要更多信息"],
      }));
      setClarifications(normalized);

      const welcome: ChatMessage = {
        id: Date.now().toString(),
        type: 'bot',
        content: `我已为您的想法生成了 ${normalized.length} 个澄清问题。让我们开始吧！`,
        timestamp: new Date(),
        isImportant: true,
      };
      setMessages([welcome]);

      const first = res.next_question as { question: string; slot_name: string } | null;
      if (first) {
        setTimeout(() => {
          const inserted = pushQuestionIfNew(first.slot_name, first.question);
          if (inserted) {
            setIsProcessing(false);
          }
        }, 600);
      } else {
        // 后端未直接返回首问，则回退本地挑选并插入
        setTimeout(() => {
          askNextQuestion();
        }, 600);
      }
    } catch (error) {
      console.error("Clarification process failed:", error);
      // 回退到模拟数据
      const mockClarifications: Clarification[] = [
        {
          question: "您的学习平台主要面向哪个年龄段的学生？",
          slot_name: "target_audience",
          importance: 9,
          suggested_answers: ["高中生(15-18岁)", "大学生(18-25岁)", "成人学习者(25岁以上)", "所有年龄段"]
        },
        {
          question: "平台将提供哪些类型的课程内容？",
          slot_name: "course_content",
          importance: 8,
          suggested_answers: ["STEM课程", "语言学习", "职业技能", "通用教育", "所有类型"]
        },
        {
          question: "学习风格识别将基于什么数据？",
          slot_name: "learning_style_data",
          importance: 7,
          suggested_answers: ["学习行为分析", "测试结果", "用户自我评估", "综合多种数据源"]
        },
        {
          question: "平台的商业模式是什么？",
          slot_name: "business_model",
          importance: 6,
          suggested_answers: ["订阅制", "按课程付费", "免费+增值服务", "企业授权"]
        }
      ];

      setClarifications(mockClarifications);
      setSessionId("session-" + Date.now());
      
      // 添加欢迎消息
      const welcomeMessage: ChatMessage = {
        id: 'welcome',
        type: 'bot',
        content: '👋 您好！我是澄清助手。我需要询问几个问题来更好地理解您的想法。这将帮助后续的优化过程更加精准。',
        timestamp: new Date(),
        isImportant: true
      };
      
      setMessages([welcomeMessage]);
      
      // 延迟显示第一个问题
      setTimeout(() => {
        askNextQuestion();
      }, 1000);
    } finally {
      // 是否解除 processing 由首问插入时机控制，避免用户过早输入
    }
  };

  const askNextQuestion = async () => {
    const unansweredClarifications = clarifications.filter(c => !completedSlots.has(c.slot_name));
    
    if (unansweredClarifications.length === 0) {
      // 所有问题已回答，结束澄清过程
      await finishClarification();
      return;
    }

    // 按重要性排序，询问下一个问题
    const nextClarification = unansweredClarifications.sort((a, b) => b.importance - a.importance)[0];
    
    const inserted = pushQuestionIfNew(nextClarification.slot_name, nextClarification.question);
    if (inserted) {
      setIsProcessing(false);
    }
    // 如果确实插入了新问题且有建议答案，显示它们
    if (inserted && nextClarification.suggested_answers && nextClarification.suggested_answers.length > 0) {
      setTimeout(() => {
        setMessages(prev => {
          // 防止重复插入相同 suggestions
          const hasSuggestions = prev.some(m => m.id.startsWith(`suggestions-${nextClarification.slot_name}`));
          if (hasSuggestions) return prev;
          const suggestionsMessage: ChatMessage = {
            id: `suggestions-${nextClarification.slot_name}-${Date.now()}`,
            type: 'bot',
            content: `💡 建议选项：\n${nextClarification.suggested_answers!.map((ans, idx) => `${idx + 1}. ${ans}`).join('\n')}`,
            timestamp: new Date()
          };
          return [...prev, suggestionsMessage];
        });
      }, 500);
    }
  };

  const handleSendMessage = async () => {
    if (!currentInput.trim() || isCompleted) return;

    console.debug('[Clarify] send clicked:', {
      input: currentInput,
      isProcessing,
      sessionId,
      messagesCount: messages.length,
    });

    // 添加用户消息
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: currentInput.trim(),
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    // 找到当前正在回答的问题
    const lastBotMessage = messages.filter(m => m.type === 'bot' && m.clarificationId).pop();
    
  let backendProvidedNext = false;
  if (lastBotMessage?.clarificationId) {
      // 更新澄清答案
      setClarifications(prev => prev.map(c => 
        c.slot_name === lastBotMessage.clarificationId
          ? { ...c, answer: currentInput.trim() }
          : c
      ));
      
      // 标记槽位已完成
      setCompletedSlots(prev => new Set([...prev, lastBotMessage.clarificationId!]));

      // 推送回答到后端，获取下一题
      try {
        if (sessionId) {
          const submitRes = await invoke<any>('submit_clarification_answer', {
            session_id: sessionId,
            slot_name: lastBotMessage.clarificationId,
            answer: currentInput.trim(),
          });
          if (!submitRes?.success) {
            console.warn('提交答案失败:', submitRes?.error);
          } else if (submitRes?.next_question) {
            const next = submitRes.next_question as { question: string; slot_name: string };
            const inserted = pushQuestionIfNew(next.slot_name, next.question);
            backendProvidedNext = inserted; // 仅在确实插入了下一题时，阻止本地 fallback
          } else if (submitRes?.completed === true) {
            // 所有问题已完成：立即结束澄清并给出结束语
            await finishClarification();
            return;
          }
        }
      } catch (err) {
        console.warn('提交答案异常:', err);
      }
      
      // 直接进行下一题，不输出确认消息
    }
    
    setCurrentInput('');
    setIsProcessing(true);
    
    // 直接询问下一个问题（若后端未返回下一题且未完成）
    if (!backendProvidedNext && !isCompleted) {
      askNextQuestion();
    }
    setIsProcessing(false);
  };

  const finishClarification = async () => {
    setIsCompleted(true);
    const completionMessage: ChatMessage = {
      id: 'completion',
      type: 'bot',
      content: '🎉 太好了！我已经收集到足够的信息。现在我将把您的想法和澄清信息发送给AI团队进行深度优化。',
      timestamp: new Date(),
      isImportant: true
    };
    
    setMessages(prev => [...prev, completionMessage]);
    try {
      if (sessionId) {
        const finishRes = await invoke<any>('finish_clarification', { session_id: sessionId });
        if (finishRes?.success) {
          const wfSession = finishRes.workflow_session_id ?? sessionId;
          setTimeout(() => {
            // 携带 wf 参数，便于 Workspace 只监听对应的工作流事件
            navigate(`/workspace?session=${sessionId}&wf=${wfSession}`);
          }, 1200);
        } else {
          // 即便失败，仍跳转工作区但提示
          console.warn('结束澄清失败:', finishRes?.error);
          setTimeout(() => {
            navigate(`/workspace?session=${sessionId}&wf=${sessionId}`);
          }, 1200);
        }
      }
    } catch (err) {
      console.warn('finishClarification 调用异常:', err);
      setTimeout(() => {
        navigate(`/workspace?session=${sessionId}&wf=${sessionId}`);
      }, 1200);
    }
  };

  const handleQuickAnswer = (answer: string) => {
    setCurrentInput(answer);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // 某些浏览器/输入法场景更可靠地触发 onKeyDown
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getProgressPercentage = () => {
    if (clarifications.length === 0) return 0;
    return Math.round((completedSlots.size / clarifications.length) * 100);
  };

  return (
    <div className="max-w-4xl mx-auto h-screen overflow-hidden flex flex-col space-y-3" style={{ minHeight: 0 }}>
      {/* 页面标题 */}
      <div className="text-center mb-8">
        <div className="flex items-center justify-center mb-4">
          <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-blue-600 rounded-2xl flex items-center justify-center">
            <MessageSquare className="w-8 h-8 text-white" />
          </div>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          智能问答澄清
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          AI 助手将通过对话帮助完善您的想法细节
        </p>
      </div>

      {/* 进度指示器（紧凑/展开） */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-3 md:p-4 shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <h2 className="text-sm md:text-base font-semibold text-gray-900 dark:text-white">澄清进度</h2>
            <span className="text-xs md:text-sm font-medium text-blue-600 dark:text-blue-400">
              {completedSlots.size} / {clarifications.length}
            </span>
          </div>
          {/* 展开/收起按钮 */}
          <button
            onClick={() => setShowIdeaCard(v => v)}
            className="hidden"
          >toggle</button>
        </div>
        {/* 紧凑进度条 */}
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 md:h-2.5 mt-2">
          <div
            className="bg-gradient-to-r from-green-500 to-blue-500 h-full rounded-full transition-all duration-500"
            style={{ width: `${getProgressPercentage()}%` }}
          />
        </div>
      </div>

      {/* 当前想法摘要（默认折叠，可展开） */}
      {currentIdea && (
        <div className="rounded-xl border border-blue-200 dark:border-blue-800 bg-blue-50/60 dark:bg-blue-900/20">
          <div className="flex items-center justify-between px-4 py-2">
            <div className="flex items-center space-x-2 text-blue-800 dark:text-blue-200">
              <Lightbulb className="w-5 h-5" />
              <span className="text-sm font-medium">当前想法摘要</span>
            </div>
            <button
              onClick={() => setShowIdeaCard(v => !v)}
              className="text-xs px-2 py-1 rounded-md bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-200 hover:bg-blue-200 dark:hover:bg-blue-700"
            >
              {showIdeaCard ? '收起' : '展开'}
            </button>
          </div>
          {showIdeaCard && (
            <div className="px-6 pb-4">
              <p className="text-blue-800 dark:text-blue-200 text-sm">{currentIdea.raw_text}</p>
              {currentIdea.context_hints.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-3">
                  {currentIdea.context_hints.map((hint, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-200 text-xs rounded-md"
                    >
                      {hint}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

  {/* 对话区域（占据剩余高度，内部滚动；设置最小高度避免“被压缩”） */}
  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 flex flex-col flex-1 min-h-0" style={{ minHeight: '48vh' }}>
        {/* 对话历史 */}
        <div className="flex-1 min-h-0 overflow-y-auto p-6 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex items-start space-x-3 ${
                message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
              }`}
            >
              <div className={`
                w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                ${message.type === 'bot' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-500 text-white'
                }
              `}>
                {message.type === 'bot' ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
              </div>
              
              <div className={`
                max-w-[80%] p-3 rounded-lg
                ${message.type === 'user'
                  ? 'bg-blue-600 text-white'
                  : message.isImportant
                    ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-800 dark:text-green-200'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
                }
              `}>
                <div className="whitespace-pre-wrap text-sm">{message.content}</div>
                <div className={`text-xs mt-1 opacity-70`}>
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          
          {isProcessing && (
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="bg-gray-100 dark:bg-gray-700 p-3 rounded-lg">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}
          {/* 滚动锚点：保持列表在底部 */}
          <div ref={bottomRef} />
  </div>

  {/* 输入区域与提示 */}
  <div className="border-t border-gray-200 dark:border-gray-700 p-4" style={{ position: 'relative', zIndex: 20 }}>
          <div className="flex space-x-2">
            <input
              type="text"
              value={currentInput}
              onChange={(e) => setCurrentInput(e.target.value)}
              onKeyPress={handleKeyPress}
              onKeyDown={handleKeyDown}
              placeholder={isCompleted ? "澄清已完成，正在交给团队..." : "输入您的回答..."}
              // 允许随时输入，不受 isProcessing 影响
              disabled={isCompleted}
              autoFocus
              style={{ pointerEvents: 'auto', position: 'relative', zIndex: 10 }}
              className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white disabled:opacity-50"
            />
            <button
              onClick={handleSendMessage}
              disabled={!currentInput.trim() || isCompleted}
              style={{ pointerEvents: 'auto', position: 'relative', zIndex: 20 }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          {/* 快速回答建议 */}
          {messages.length > 0 && 
           messages[messages.length - 1]?.content.includes('建议选项') &&
           (() => {
             const lastBotQ = [...messages].reverse().find(m => m.type === 'bot' && m.clarificationId);
             return lastBotQ && !completedSlots.has(lastBotQ.clarificationId!);
           })() && (
            <div className="mt-3 flex flex-wrap gap-2">
              {(() => {
                  const lastBotQ = [...messages].reverse().find(m => m.type === 'bot' && m.clarificationId);
                  return clarifications.find(c => c.slot_name === (lastBotQ?.clarificationId || ''));
                })()
                ?.suggested_answers?.map((answer, index) => (
                <button
                  key={index}
                  onClick={() => handleQuickAnswer(answer)}
                  className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  {answer}
                </button>
              ))}
            </div>
          )}

          {/* 轻提示：嵌入输入区域底部，避免占页面高度 */}
          <div className="mt-2 text-center text-gray-500 dark:text-gray-400 text-xs">
            <div className="flex items-center justify-center space-x-2">
              <Target className="w-3 h-3" />
              <span>详细回答将帮助 AI 更好地优化您的想法</span>
            </div>
          </div>
        </div>
      </div>

      {/* 移除底部独立提示，避免占用垂直空间 */}
    </div>
  );
};

export default QuestioningPage;
