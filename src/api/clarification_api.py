"""
Clarification (Questioning) API
提供基于用户输入想法的多轮澄清问题生成（最小可用版）。
"""

from typing import Dict, Any, List
from ..utils.logger import get_logger

logger = get_logger(__name__)


def _heuristic_questions(idea: str) -> List[Dict[str, Any]]:
    """根据想法内容启发式地产生一组澄清问题。"""
    base = [
        {"question": "这个想法的目标用户是谁？", "type": "target", "priority": "high"},
        {"question": "这个想法要解决的核心痛点是什么？", "type": "problem", "priority": "high"},
        {"question": "预期的核心功能模块有哪些？", "type": "features", "priority": "medium"},
        {"question": "可用的数据来源或先决条件是什么？", "type": "data", "priority": "medium"},
        {"question": "成功的评估标准或关键指标是什么？", "type": "metrics", "priority": "medium"},
        {"question": "预算/时间/合规方面有无约束？", "type": "constraints", "priority": "low"},
    ]
    idea_l = idea.lower()
    if any(k in idea_l for k in ["教育", "学习", "student", "education", "learning"]):
        base.insert(0, {"question": "面向哪个学段/年龄层？", "type": "domain_specific", "priority": "high"})
        base.append({"question": "个性化策略基于哪些学习风格理论？", "type": "method", "priority": "medium"})
    if any(k in idea_l for k in ["平台", "platform"]):
        base.append({"question": "平台的商业模式与收费方式是什么？", "type": "business", "priority": "medium"})
    return base[:8]


def run_clarification_ai(ideaContent: str) -> Dict[str, Any]:  # noqa: N802 (for eel name stability)
    """生成澄清问题集合（兼容前端 QuestioningPage 预期返回结构）。

    返回结构：
    {
      "status": "completed",
      "clarification": {
         "questions": [{"question","type","priority"}, ...],
         "confidence": 0.7,
         "missing_slots": [],
         "structured_idea": {}
      }
    }
    """
    try:
        idea = (ideaContent or "").strip()
        if not idea:
            raise ValueError("ideaContent is empty")

        questions = _heuristic_questions(idea)
        result = {
            "status": "completed",
            "clarification": {
                "questions": questions,
                "confidence": 0.7,
                "missing_slots": [],
                "structured_idea": {"summary": idea[:200]}
            }
        }
        logger.info(f"clarification generated: {len(questions)} questions")
        return result
    except Exception as e:
        logger.error(f"run_clarification_ai failed: {e}")
        return {
            "status": "error",
            "error": str(e),
        }
