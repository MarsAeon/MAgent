import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { invoke } from '@tauri-apps/api/core';
import { 
  MessageSquare, 
  Send, 
  Bot, 
  User,
  CheckCircle2,
  Clock,
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

  useEffect(() => {
    // 从本地存储或 URL 参数获取当前想法
    loadCurrentIdea();
    
    // 开始澄清过程
    startClarificationProcess();
  }, []);

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
      console.log("Starting AI clarification process...");
      
      // 调用实际的AI澄清分析
      const result = await invoke<{
        status: string,
        clarification: {
          questions: Array<{
            question: string,
            type: string,
            priority: string
          }>,
          confidence: number,
          missing_slots: string[],
          structured_idea: any
        }
      }>('run_clarification_ai', {
        ideaContent: currentIdea.raw_text
      });
      
      console.log("AI clarification result:", result);
      
      if (result.status === 'completed') {
        // 转换AI返回的问题格式为前端格式
        const clarifications: Clarification[] = result.clarification.questions.map((q, index) => ({
          question: q.question,
          slot_name: `slot_${index}`,
          importance: q.priority === 'high' ? 9 : 7,
          suggested_answers: ["是", "否", "需要更多信息"]
        }));
        
        setClarifications(clarifications);
        
        // 添加机器人初始消息
        const initialMessage: ChatMessage = {
          id: Date.now().toString(),
          type: 'bot',
          content: `我已经分析了您的想法，有 ${clarifications.length} 个问题需要澄清。让我们开始吧！`,
          timestamp: new Date(),
          isImportant: true
        };
        setMessages([initialMessage]);
        
        // 发送第一个问题
        if (clarifications.length > 0) {
          setTimeout(() => {
            const firstQuestion: ChatMessage = {
              id: (Date.now() + 1).toString(),
              type: 'bot',
              content: clarifications[0].question,
              timestamp: new Date(),
              clarificationId: clarifications[0].slot_name
            };
            setMessages(prev => [...prev, firstQuestion]);
          }, 1000);
        }
      } else {
        throw new Error('AI澄清分析失败');
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
      setIsProcessing(false);
    }
  };

  const askNextQuestion = () => {
    const unansweredClarifications = clarifications.filter(c => !completedSlots.has(c.slot_name));
    
    if (unansweredClarifications.length === 0) {
      // 所有问题已回答，结束澄清过程
      finishClarification();
      return;
    }

    // 按重要性排序，询问下一个问题
    const nextClarification = unansweredClarifications.sort((a, b) => b.importance - a.importance)[0];
    
    const questionMessage: ChatMessage = {
      id: `question-${nextClarification.slot_name}`,
      type: 'bot',
      content: nextClarification.question,
      timestamp: new Date(),
      clarificationId: nextClarification.slot_name
    };
    
    setMessages(prev => [...prev, questionMessage]);
    
    // 如果有建议答案，也显示它们
    if (nextClarification.suggested_answers && nextClarification.suggested_answers.length > 0) {
      setTimeout(() => {
        const suggestionsMessage: ChatMessage = {
          id: `suggestions-${nextClarification.slot_name}`,
          type: 'bot',
          content: `💡 建议选项：\n${nextClarification.suggested_answers!.map((ans, idx) => `${idx + 1}. ${ans}`).join('\n')}`,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, suggestionsMessage]);
      }, 500);
    }
  };

  const handleSendMessage = async () => {
    if (!currentInput.trim() || isProcessing) return;

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
    
    if (lastBotMessage?.clarificationId) {
      // 更新澄清答案
      setClarifications(prev => prev.map(c => 
        c.slot_name === lastBotMessage.clarificationId
          ? { ...c, answer: currentInput.trim() }
          : c
      ));
      
      // 标记槽位已完成
      setCompletedSlots(prev => new Set([...prev, lastBotMessage.clarificationId!]));
      
      // 添加确认消息
      const confirmMessage: ChatMessage = {
        id: `confirm-${Date.now()}`,
        type: 'bot',
        content: '✅ 收到！让我继续下一个问题...',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, confirmMessage]);
    }
    
    setCurrentInput('');
    setIsProcessing(true);
    
    // 延迟询问下一个问题
    setTimeout(() => {
      askNextQuestion();
      setIsProcessing(false);
    }, 1500);
  };

  const finishClarification = () => {
    const completionMessage: ChatMessage = {
      id: 'completion',
      type: 'bot',
      content: '🎉 太好了！我已经收集到足够的信息。现在我将把您的想法和澄清信息发送给AI团队进行深度优化。',
      timestamp: new Date(),
      isImportant: true
    };
    
    setMessages(prev => [...prev, completionMessage]);
    
    // 延迟跳转到工作区
    setTimeout(() => {
      navigate(`/workspace?session=${sessionId}`);
    }, 2000);
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

  const getProgressPercentage = () => {
    if (clarifications.length === 0) return 0;
    return Math.round((completedSlots.size / clarifications.length) * 100);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
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

      {/* 进度指示器 */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">澄清进度</h2>
          <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
            {completedSlots.size} / {clarifications.length} 完成
          </span>
        </div>
        
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 mb-4">
          <div
            className="bg-gradient-to-r from-green-500 to-blue-500 h-3 rounded-full transition-all duration-500"
            style={{ width: `${getProgressPercentage()}%` }}
          ></div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {clarifications.map((clarification) => (
            <div
              key={clarification.slot_name}
              className={`
                flex items-center space-x-2 p-2 rounded-lg
                ${completedSlots.has(clarification.slot_name)
                  ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300'
                  : 'bg-gray-50 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                }
              `}
            >
              {completedSlots.has(clarification.slot_name) ? (
                <CheckCircle2 className="w-4 h-4" />
              ) : (
                <Clock className="w-4 h-4" />
              )}
              <span className="text-sm font-medium truncate">
                {clarification.slot_name.replace('_', ' ')}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* 当前想法摘要 */}
      {currentIdea && (
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-6 border border-blue-200 dark:border-blue-800">
          <div className="flex items-start space-x-3">
            <Lightbulb className="w-6 h-6 text-blue-600 dark:text-blue-400 mt-1 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">当前想法</h3>
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
          </div>
        </div>
      )}

      {/* 对话区域 */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
        {/* 对话历史 */}
        <div className="h-96 overflow-y-auto p-6 space-y-4">
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
                max-w-xs lg:max-w-md xl:max-w-lg p-3 rounded-lg
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
        </div>

        {/* 输入区域 */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-4">
          <div className="flex space-x-2">
            <input
              type="text"
              value={currentInput}
              onChange={(e) => setCurrentInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="输入您的回答..."
              disabled={isProcessing}
              className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white disabled:opacity-50"
            />
            <button
              onClick={handleSendMessage}
              disabled={!currentInput.trim() || isProcessing}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          
          {/* 快速回答建议 */}
          {messages.length > 0 && 
           messages[messages.length - 1]?.content.includes('建议选项') &&
           !completedSlots.has(messages.find(m => m.clarificationId)?.clarificationId || '') && (
            <div className="mt-3 flex flex-wrap gap-2">
              {clarifications
                .find(c => c.slot_name === messages.find(m => m.clarificationId)?.clarificationId)
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
        </div>
      </div>

      {/* 底部提示 */}
      <div className="text-center text-gray-500 dark:text-gray-400 text-sm">
        <div className="flex items-center justify-center space-x-2">
          <Target className="w-4 h-4" />
          <span>详细的回答将帮助AI更好地优化您的想法</span>
        </div>
      </div>
    </div>
  );
};

export default QuestioningPage;
