"""
Questioning (Clarification) API with LLM integration, session persistence and resume.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests

from ..utils.logger import get_logger
from ..utils.storage import SessionStorage

logger = get_logger(__name__)


@dataclass
class ClarificationQuestion:
    slot_name: str
    question: str
    priority: int = 7  # 1-10
    type: str = "general"
    answer: Optional[str] = None


class ClarificationSessionManager:
    def __init__(self):
        self.storage = SessionStorage()

    def create_session(self, idea_seed: Dict[str, Any]) -> str:
        session_id = f"clar_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        data = {
            "id": session_id,
            "status": "running",
            "idea_seed": idea_seed,
            "project_id": None,
            "questions": [],  # list of ClarificationQuestion as dict
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": [],
        }
        self.storage.save_session(session_id, data)
        return session_id

    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.storage.load_session(session_id)

    def save(self, session: Dict[str, Any]) -> None:
        session["updated_at"] = datetime.now().isoformat()
        self.storage.save_session(session["id"], session)

    def set_questions(self, session: Dict[str, Any], questions: List[ClarificationQuestion]) -> None:
        session["questions"] = [asdict(q) for q in questions]
        self.save(session)

    def next_unanswered(self, session: Dict[str, Any]) -> Optional[ClarificationQuestion]:
        pending = [ClarificationQuestion(**q) for q in session.get("questions", []) if not q.get("answer")]
        if not pending:
            return None
        pending.sort(key=lambda q: q.priority, reverse=True)
        return pending[0]

    def submit_answer(self, session: Dict[str, Any], slot_name: str, answer: str) -> None:
        for q in session.get("questions", []):
            if q["slot_name"] == slot_name and not q.get("answer"):
                q["answer"] = answer
                break
        self.save(session)


def _format_summary_text(summary: Dict[str, Any]) -> str:
    """Format a structured summary dict into a readable handoff section."""
    if not isinstance(summary, dict):
        return str(summary)
    lines: List[str] = []
    title = summary.get('title') or summary.get('idea_title') or ''
    if title:
        lines.append(f"标题：{title}")
    refined = summary.get('refined_idea') or summary.get('summary') or summary.get('refined') or ''
    if refined:
        lines.append(f"精炼概述：{refined}")
    if summary.get('user_segments'):
        segs = summary.get('user_segments')
        if isinstance(segs, list):
            segs = '；'.join(str(x) for x in segs)
        lines.append(f"目标用户：{segs}")
    if summary.get('core_pain_points'):
        pains = summary.get('core_pain_points')
        if isinstance(pains, list):
            pains = '；'.join(str(x) for x in pains)
        lines.append(f"核心痛点：{pains}")
    if summary.get('key_features'):
        feats = summary.get('key_features')
        if isinstance(feats, list):
            feats = '；'.join(str(x) for x in feats)
        lines.append(f"关键特性：{feats}")
    if summary.get('constraints'):
        cons = summary.get('constraints')
        if isinstance(cons, list):
            cons = '；'.join(str(x) for x in cons)
        lines.append(f"约束条件：{cons}")
    if summary.get('success_metrics'):
        mets = summary.get('success_metrics')
        if isinstance(mets, list):
            mets = '；'.join(str(x) for x in mets)
        lines.append(f"成功指标：{mets}")
    if summary.get('risks'):
        risks = summary.get('risks')
        if isinstance(risks, list):
            risks = '；'.join(str(x) for x in risks)
        lines.append(f"风险：{risks}")
    if summary.get('next_steps'):
        steps = summary.get('next_steps')
        if isinstance(steps, list):
            steps = '；'.join(str(x) for x in steps)
        lines.append(f"下一步：{steps}")
    return "\n".join(lines)


def _heuristic_summary(session: Dict[str, Any]) -> Dict[str, Any]:
    seed = session.get('idea_seed', {})
    base = seed.get('raw_text', '')
    qa: List[str] = []
    answered: List[Dict[str, Any]] = []
    for q in session.get('questions', []):
        if q.get('answer'):
            answered.append(q)
            qa.append(f"{q['question']} -> {q['answer']}")
    return {
        "title": (seed.get('domain') or '概念') + "总结",
        "refined_idea": base,
        "key_features": [],
        "user_segments": [],
        "core_pain_points": [],
        "constraints": [],
        "success_metrics": [],
        "risks": [],
        "next_steps": ["进入多智能体协作讨论，细化方案与里程碑"],
        "qa_pairs": qa,
    }


def _call_openai_style_completion(base: str, api_key_header_name: str, api_key: str, model: str, system_prompt: str, user_content: str, extra_headers: Optional[Dict[str, str]] = None) -> Optional[str]:
    headers = {api_key_header_name: api_key, "Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.3,
    }
    resp = requests.post(base + '/v1/chat/completions', headers=headers, json=body, timeout=45)
    resp.raise_for_status()
    data = resp.json()
    return data['choices'][0]['message']['content']


def _summarize_with_qwen(enriched_text: str) -> Optional[Dict[str, Any]]:
    _bootstrap_provider_env_from_toml()
    api_key = os.getenv('DASHSCOPE_API_KEY') or os.getenv('QWEN_API_KEY')
    if not api_key:
        return None
    try:
        model = os.getenv('QWEN_SUMMARY_MODEL', os.getenv('QWEN_MODEL', 'qwen-plus'))
        base = _normalize_api_base(os.getenv('QWEN_API_BASE') or 'https://dashscope.aliyuncs.com/compatible-mode', strip_v1=True)
        logger.info(f"Clarification summary provider=Qwen(DashScope) model={model} base={base}")
        system_prompt = (
            "You are a product strategist. Summarize and refine the idea based on the given enriched idea (original idea + Q&A). "
            "Return strict JSON with keys: title, refined_idea, user_segments[], core_pain_points[], key_features[], constraints[], success_metrics[], risks[], next_steps[]"
        )
        content = _call_openai_style_completion(base, 'Authorization', f'Bearer {api_key}', model, system_prompt, enriched_text)
        obj = _extract_json(content or '')
        return obj or {"refined_idea": (content or '').strip()}
    except Exception as e:
        logger.warning(f"Qwen summary failed: {e}")
        return None


def _summarize_with_deepseek(enriched_text: str) -> Optional[Dict[str, Any]]:
    _bootstrap_provider_env_from_toml()
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        return None
    try:
        model = os.getenv('DEEPSEEK_SUMMARY_MODEL', os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'))
        base = _normalize_api_base(os.getenv('DEEPSEEK_API_BASE') or 'https://api.deepseek.com', strip_v1=True)
        logger.info(f"Clarification summary provider=DeepSeek model={model} base={base}")
        system_prompt = (
            "You are a product strategist. Summarize and refine the idea based on the given enriched idea (original idea + Q&A). "
            "Return strict JSON with keys: title, refined_idea, user_segments[], core_pain_points[], key_features[], constraints[], success_metrics[], risks[], next_steps[]"
        )
        content = _call_openai_style_completion(base, 'Authorization', f'Bearer {api_key}', model, system_prompt, enriched_text)
        obj = _extract_json(content or '')
        return obj or {"refined_idea": (content or '').strip()}
    except Exception as e:
        logger.warning(f"DeepSeek summary failed: {e}")
        return None


def _summarize_with_openai(enriched_text: str) -> Optional[Dict[str, Any]]:
    _bootstrap_provider_env_from_toml()
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return None
    try:
        model = os.getenv('OPENAI_SUMMARY_MODEL', os.getenv('OPENAI_MODEL', 'gpt-4o-mini'))
        base = _normalize_api_base(os.getenv('OPENAI_API_BASE') or 'https://api.openai.com', strip_v1=True)
        logger.info(f"Clarification summary provider=OpenAI model={model} base={base}")
        system_prompt = (
            "You are a product strategist. Summarize and refine the idea based on the given enriched idea (original idea + Q&A). "
            "Return strict JSON with keys: title, refined_idea, user_segments[], core_pain_points[], key_features[], constraints[], success_metrics[], risks[], next_steps[]"
        )
        content = _call_openai_style_completion(base, 'Authorization', f'Bearer {api_key}', model, system_prompt, enriched_text)
        obj = _extract_json(content or '')
        return obj or {"refined_idea": (content or '').strip()}
    except Exception as e:
        logger.warning(f"OpenAI summary failed: {e}")
        return None


def _summarize_with_anthropic(enriched_text: str) -> Optional[Dict[str, Any]]:
    _bootstrap_provider_env_from_toml()
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return None
    try:
        model = os.getenv('ANTHROPIC_SUMMARY_MODEL', os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20240620'))
        base = _normalize_api_base(os.getenv('ANTHROPIC_API_BASE') or 'https://api.anthropic.com', strip_v1=False)
        logger.info(f"Clarification summary provider=Anthropic model={model} base={base}")
        # Anthropic uses different headers
        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        }
        body = {
            'model': model,
            'max_tokens': 1200,
            'messages': [
                {"role": "user", "content": (
                    "You are a product strategist. Summarize and refine the idea based on the given enriched idea (original idea + Q&A). "
                    "Return strict JSON with keys: title, refined_idea, user_segments[], core_pain_points[], key_features[], constraints[], success_metrics[], risks[], next_steps[]\n\n"
                    + enriched_text
                )}
            ]
        }
        resp = requests.post(base + '/v1/messages', headers=headers, json=body, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        content = ''.join(part.get('text', '') for part in data.get('content', []) if isinstance(part, dict))
        obj = _extract_json(content or '')
        return obj or {"refined_idea": (content or '').strip()}
    except Exception as e:
        logger.warning(f"Anthropic summary failed: {e}")
        return None


def _generate_summary(session: Dict[str, Any]) -> Dict[str, Any]:
    enriched = _build_enriched_idea(session)
    # Provider order: Qwen -> DeepSeek -> OpenAI -> Anthropic -> heuristic
    summary = (
        _summarize_with_qwen(enriched)
        or _summarize_with_deepseek(enriched)
        or _summarize_with_openai(enriched)
        or _summarize_with_anthropic(enriched)
    )
    if summary:
        logger.info("Clarification summary generated via LLM")
        return summary
    logger.info("Clarification summary fallback to heuristic")
    return _heuristic_summary(session)


def _extract_json(text: str) -> Optional[dict]:
    """Try best to extract a JSON object from model output."""
    # Try code block first
    m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # Find first balanced braces (simple heuristic)
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
        except Exception:
            return None
    return None


def _normalize_api_base(base: str, strip_v1: bool = True) -> str:
    if not base:
        return base
    b = base.strip().rstrip('/')
    if strip_v1 and b.endswith('/v1'):
        b = b[:-3]
    return b


def _bootstrap_provider_env_from_toml() -> None:
    """If env vars are missing, try load from MAgent/config.toml and set os.environ accordingly.
    Only sets variables that are currently missing.
    """
    try:
        import tomllib  # Python 3.11+
        # Locate config.toml under MAgent/
        here = os.path.dirname(os.path.abspath(__file__))
        # __file__ -> .../MAgent/src/api/questioning_api.py; go up to MAgent/
        magent_dir = os.path.abspath(os.path.join(here, '..', '..'))
        cfg_path = os.path.join(magent_dir, 'config.toml')
        if not os.path.exists(cfg_path):
            return
        with open(cfg_path, 'rb') as f:
            data = tomllib.load(f)
        ai = data.get('ai', {}) if isinstance(data, dict) else {}
        # Map keys -> env if missing
        mapping: List[Tuple[str, str]] = [
            ('OPENAI_API_KEY', ai.get('openai_api_key') or ''),
            ('ANTHROPIC_API_KEY', ai.get('claude_api_key') or ''),
            ('DEEPSEEK_API_KEY', ai.get('deepseek_api_key') or ''),
            ('QWEN_API_KEY', ai.get('qwen_api_key') or ''),
        ]
        for env_name, value in mapping:
            if value and not os.getenv(env_name):
                os.environ[env_name] = value
        # Normalize and set OPENAI_API_BASE if provided in toml
        openai_base = ai.get('openai_base_url') or ''
        if openai_base and not os.getenv('OPENAI_API_BASE'):
            os.environ['OPENAI_API_BASE'] = _normalize_api_base(openai_base, strip_v1=True)
    except Exception as e:
        logger.debug(f"config.toml bootstrap skipped or failed: {e}")


def _normalize_question(text: str) -> str:
    """Normalize question text for deduplication: trim, lowercase, remove common punctuations and extra spaces.
    Keep CJK characters; strip ASCII and CJK punctuations.
    """
    if not isinstance(text, str):
        return ''
    s = text.strip().lower()
    # Remove common ASCII and CJK punctuations, bullets, dashes; collapse spaces
    s = re.sub(r"[\s\t\n\r]+", " ", s)
    s = re.sub(r"[，。！？、；：:;\-—…·•\.,!\?\(\)\[\]\{\}<>“”‘’\"'《》【】]+", "", s)
    return s


def _heuristic_questions(idea: str) -> List[ClarificationQuestion]:
    base: List[ClarificationQuestion] = [
        ClarificationQuestion(slot_name="target_user", question="这个想法的目标用户是谁？", priority=9, type="target"),
        ClarificationQuestion(slot_name="core_pain", question="它要解决的核心痛点是什么？", priority=9, type="problem"),
        ClarificationQuestion(slot_name="key_features", question="预期的核心功能模块有哪些？", priority=8, type="features"),
        ClarificationQuestion(slot_name="data_sources", question="可用的数据来源或先决条件是什么？", priority=7, type="data"),
        ClarificationQuestion(slot_name="success_metrics", question="成功的评估标准或关键指标是什么？", priority=7, type="metrics"),
        ClarificationQuestion(slot_name="constraints", question="预算/时间/合规方面有无约束？", priority=6, type="constraints"),
    ]
    idea_l = idea.lower()
    if any(k in idea_l for k in ["education", "learning", "学习", "教育"]):
        base.insert(0, ClarificationQuestion(slot_name="education_stage", question="面向哪个学段/年龄层？", priority=10, type="domain"))
        base.append(ClarificationQuestion(slot_name="personalization_basis", question="个性化策略基于哪些学习风格理论？", priority=7, type="method"))
    if any(k in idea_l for k in ["platform", "平台"]):
        base.append(ClarificationQuestion(slot_name="business_model", question="平台的商业模式与收费方式是什么？", priority=7, type="business"))
    # Deduplicate slot names
    seen = set()
    uniq: List[ClarificationQuestion] = []
    for q in base:
        if q.slot_name not in seen:
            uniq.append(q)
            seen.add(q.slot_name)
    return uniq[:10]


def _call_openai_for_questions(idea: str) -> Optional[List[ClarificationQuestion]]:
    # Ensure env possibly loaded from toml
    _bootstrap_provider_env_from_toml()
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return None
    try:
        body = {
            "model": os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            "messages": [
                {"role": "system", "content": "You generate a concise list of 6-10 clarification questions for the idea. Return strict JSON with fields: questions:[{question, type, priority(1-10), slot_name}]"},
                {"role": "user", "content": f"Idea: {idea}\nReturn JSON only."}
            ],
            "temperature": 0.3,
        }
        base = _normalize_api_base(os.getenv('OPENAI_API_BASE') or 'https://api.openai.com', strip_v1=True)
        logger.info(f"Clarifier provider=OpenAI model={body['model']} base={base}")
        resp = requests.post(
            base + '/v1/chat/completions',
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data['choices'][0]['message']['content']
        obj = _extract_json(content) or {}
        questions = obj.get('questions', [])
        out: List[ClarificationQuestion] = []
        for i, q in enumerate(questions):
            slot = q.get('slot_name') or f"slot_{i}"
            pri = int(q.get('priority', 7))
            typ = q.get('type', 'general')
            out.append(ClarificationQuestion(slot_name=slot, question=q.get('question', '').strip(), priority=max(1, min(10, pri)), type=typ))
        return [q for q in out if q.question]
    except Exception as e:
        logger.warning(f"OpenAI question generation failed, fallback: {e}")
        return None


def _call_anthropic_for_questions(idea: str) -> Optional[List[ClarificationQuestion]]:
    _bootstrap_provider_env_from_toml()
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return None
    try:
        body = {
            "model": os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20240620'),
            "max_tokens": 800,
            "messages": [
                {"role": "user", "content": f"You generate a concise list of 6-10 clarification questions for the idea, return JSON: {{\"questions\":[{{question,type,priority,slot_name}}]}}. Idea: {idea}"}
            ]
        }
        base = _normalize_api_base(os.getenv('ANTHROPIC_API_BASE') or 'https://api.anthropic.com', strip_v1=False)
        logger.info(f"Clarifier provider=Anthropic model={body['model']} base={base}")
        resp = requests.post(
            base + '/v1/messages',
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        # Anthropic content can be array with text
        content = ''.join(part.get('text', '') for part in data.get('content', []) if isinstance(part, dict))
        obj = _extract_json(content) or {}
        questions = obj.get('questions', [])
        out: List[ClarificationQuestion] = []
        for i, q in enumerate(questions):
            slot = q.get('slot_name') or f"slot_{i}"
            pri = int(q.get('priority', 7))
            typ = q.get('type', 'general')
            out.append(ClarificationQuestion(slot_name=slot, question=q.get('question', '').strip(), priority=max(1, min(10, pri)), type=typ))
        return [q for q in out if q.question]
    except Exception as e:
        logger.warning(f"Anthropic question generation failed, fallback: {e}")
        return None


def _generate_questions(idea: str) -> List[ClarificationQuestion]:
    # Try providers in order: Qwen(DashScope) -> DeepSeek -> OpenAI -> Anthropic -> heuristic
    qs = (
        _call_qwen_for_questions(idea)
        or _call_deepseek_for_questions(idea)
        or _call_openai_for_questions(idea)
        or _call_anthropic_for_questions(idea)
    )
    if qs and len(qs) >= 4:
        return qs
    return _heuristic_questions(idea)


def _call_deepseek_for_questions(idea: str) -> Optional[List[ClarificationQuestion]]:
    """Use DeepSeek OpenAI-compatible API: https://api.deepseek.com/v1/chat/completions"""
    _bootstrap_provider_env_from_toml()
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        return None
    try:
        model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        base = os.getenv('DEEPSEEK_API_BASE') or 'https://api.deepseek.com'
        body = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You generate a concise list of 6-10 clarification questions for the idea. Return strict JSON with fields: questions:[{question, type, priority(1-10), slot_name}]",
                },
                {"role": "user", "content": f"Idea: {idea}\nReturn JSON only."},
            ],
            "temperature": 0.3,
        }
        base = _normalize_api_base(base, strip_v1=True) or 'https://api.deepseek.com'
        logger.info(f"Clarifier provider=DeepSeek model={model} base={base}")
        resp = requests.post(
            base + '/v1/chat/completions',
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data['choices'][0]['message']['content']
        obj = _extract_json(content) or {}
        questions = obj.get('questions', [])
        out: List[ClarificationQuestion] = []
        for i, q in enumerate(questions):
            slot = q.get('slot_name') or f"slot_{i}"
            try:
                pri = int(q.get('priority', 7))
            except Exception:
                pri = 7
            typ = q.get('type', 'general')
            out.append(ClarificationQuestion(slot_name=slot, question=q.get('question', '').strip(), priority=max(1, min(10, pri)), type=typ))
        return [q for q in out if q.question]
    except Exception as e:
        logger.warning(f"DeepSeek question generation failed, fallback: {e}")
        return None


def _call_qwen_for_questions(idea: str) -> Optional[List[ClarificationQuestion]]:
    """Use DashScope Qwen OpenAI-compatible API: https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
    Requires DASHSCOPE_API_KEY (or QWEN_API_KEY).
    """
    _bootstrap_provider_env_from_toml()
    api_key = os.getenv('DASHSCOPE_API_KEY') or os.getenv('QWEN_API_KEY')
    if not api_key:
        return None
    try:
        model = os.getenv('QWEN_MODEL', 'qwen-plus')  # 可根据需要改为 qwen2.5 具体型号
        # 兼容模式基地址：拼接我们已有的 /v1/chat/completions
        base = os.getenv('QWEN_API_BASE') or 'https://dashscope.aliyuncs.com/compatible-mode'
        body = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You generate a concise list of 6-10 clarification questions for the idea. Return strict JSON with fields: questions:[{question, type, priority(1-10), slot_name}]",
                },
                {"role": "user", "content": f"Idea: {idea}\nReturn JSON only."},
            ],
            "temperature": 0.3,
        }
        base = _normalize_api_base(base, strip_v1=True) or 'https://dashscope.aliyuncs.com/compatible-mode'
        logger.info(f"Clarifier provider=Qwen(DashScope) model={model} base={base}")
        resp = requests.post(
            base + '/v1/chat/completions',
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        # 兼容 OpenAI 格式
        content = data['choices'][0]['message']['content']
        obj = _extract_json(content) or {}
        questions = obj.get('questions', [])
        out: List[ClarificationQuestion] = []
        for i, q in enumerate(questions):
            slot = q.get('slot_name') or f"slot_{i}"
            try:
                pri = int(q.get('priority', 7))
            except Exception:
                pri = 7
            typ = q.get('type', 'general')
            out.append(ClarificationQuestion(slot_name=slot, question=q.get('question', '').strip(), priority=max(1, min(10, pri)), type=typ))
        return [q for q in out if q.question]
    except Exception as e:
        logger.warning(f"Qwen(DashScope) question generation failed, fallback: {e}")
        return None


def api_start_clarification_session(seed: Dict[str, Any]) -> Dict[str, Any]:
    """Create a clarification session and generate questions using LLMs or fallback.
    seed: { raw_text: str, context_hints:[], domain?: str }
    """
    try:
        idea = (seed or {}).get('raw_text') or ''
        if not idea.strip():
            return {"success": False, "error": "empty idea"}

        # 记录当前可用的提供商密钥与基础地址，辅助诊断
        _bootstrap_provider_env_from_toml()
        has_openai = bool(os.getenv('OPENAI_API_KEY'))
        has_anthropic = bool(os.getenv('ANTHROPIC_API_KEY'))
        has_deepseek = bool(os.getenv('DEEPSEEK_API_KEY'))
        has_qwen = bool(os.getenv('DASHSCOPE_API_KEY') or os.getenv('QWEN_API_KEY'))
        logger.info(
            "Clarification session start: providers availability -> "
            f"openai={has_openai}, anthropic={has_anthropic}, deepseek={has_deepseek}, qwen={has_qwen}; "
            f"bases: openai={_normalize_api_base(os.getenv('OPENAI_API_BASE') or 'https://api.openai.com')}, "
            f"anthropic={_normalize_api_base(os.getenv('ANTHROPIC_API_BASE') or 'https://api.anthropic.com', strip_v1=False)}, "
            f"deepseek={_normalize_api_base(os.getenv('DEEPSEEK_API_BASE') or 'https://api.deepseek.com')}, "
            f"qwen={_normalize_api_base(os.getenv('QWEN_API_BASE') or 'https://dashscope.aliyuncs.com/compatible-mode')}"
        )

        mgr = ClarificationSessionManager()
        session_id = mgr.create_session(seed)
        questions = _generate_questions(idea)
        if questions and len(questions) >= 4:
            logger.info(f"Clarification questions generated via LLM: count={len(questions)}")
        else:
            logger.info("Clarification questions fallback to heuristic generator")
        # Fill missing slot_name and normalize priorities first
        for idx, q in enumerate(questions):
            if not q.slot_name:
                q.slot_name = f"slot_{idx}"
            try:
                q.priority = max(1, min(10, int(q.priority)))
            except Exception:
                q.priority = 7

        # Deduplicate by normalized question text; and ensure slot_name uniqueness
        seen_texts: set[str] = set()
        seen_slots: set[str] = set()
        unique: List[ClarificationQuestion] = []
        for q in questions:
            norm = _normalize_question(q.question)
            if not norm:
                continue
            if norm in seen_texts:
                # skip exact/similar duplicate question
                continue
            # ensure unique slot name
            base_slot = q.slot_name or "slot"
            slot = base_slot
            suffix = 1
            while slot in seen_slots:
                slot = f"{base_slot}_{suffix}"
                suffix += 1
            q.slot_name = slot
            seen_texts.add(norm)
            seen_slots.add(slot)
            unique.append(q)

        # Cap number of questions to a reasonable amount
        questions = unique[:10]
        session = mgr.load(session_id)
        assert session
        mgr.set_questions(session, questions)
        first = mgr.next_unanswered(session)
        # 记录首个问题到会话消息历史
        if first:
            session = mgr.load(session_id) or {}
            msgs = session.get('messages') or []
            msgs.append({
                "role": "bot",
                "slot_name": first.slot_name,
                "content": first.question,
                "timestamp": datetime.now().isoformat(),
            })
            session['messages'] = msgs
            mgr.save(session)
        return {
            "success": True,
            "session_id": session_id,
            "questions": [asdict(q) for q in questions],
            "next_question": asdict(first) if first else None,
        }
    except Exception as e:
        logger.error(f"start_clarification_session failed: {e}")
        return {"success": False, "error": str(e)}


def api_submit_clarification_answer(session_id: str, slot_name: str, answer: str) -> Dict[str, Any]:
    try:
        mgr = ClarificationSessionManager()
        session = mgr.load(session_id)
        if not session:
            return {"success": False, "error": "session not found"}
        mgr.submit_answer(session, slot_name, answer)

        # 记录用户回答到消息历史
        session = mgr.load(session_id) or {}
        msgs = session.get('messages') or []
        msgs.append({
            "role": "user",
            "slot_name": slot_name,
            "content": answer,
            "timestamp": datetime.now().isoformat(),
        })
        session['messages'] = msgs
        mgr.save(session)

        # Optionally adjust priorities dynamically (simple example: unanswered keep original)
        next_q = mgr.next_unanswered(session)
        # 若有下一题，将问题也记录进消息历史
        if next_q:
            session = mgr.load(session_id) or {}
            msgs = session.get('messages') or []
            msgs.append({
                "role": "bot",
                "slot_name": next_q.slot_name,
                "content": next_q.question,
                "timestamp": datetime.now().isoformat(),
            })
            session['messages'] = msgs
            mgr.save(session)
        completed = next_q is None
        return {
            "success": True,
            "completed": completed,
            "next_question": asdict(next_q) if next_q else None,
            "pending": len([1 for q in session["questions"] if not q.get("answer")]),
        }
    except Exception as e:
        logger.error(f"submit_clarification_answer failed: {e}")
        return {"success": False, "error": str(e)}


def api_get_clarification_status(session_id: str) -> Dict[str, Any]:
    try:
        mgr = ClarificationSessionManager()
        session = mgr.load(session_id)
        if not session:
            return {"success": False, "error": "session not found"}
        return {"success": True, "data": session}
    except Exception as e:
        logger.error(f"get_clarification_status failed: {e}")
        return {"success": False, "error": str(e)}


def _build_enriched_idea(session: Dict[str, Any]) -> str:
    seed = session.get('idea_seed', {})
    base = seed.get('raw_text', '')
    qa_lines = []
    for q in session.get('questions', []):
        if q.get('answer'):
            qa_lines.append(f"- {q['question']}\n  答：{q['answer']}")
    enriched = base + "\n\n澄清结果：\n" + "\n".join(qa_lines)
    return enriched


def api_finish_clarification(session_id: str) -> Dict[str, Any]:
    """Finish clarification session and auto start workflow; return workflow session id."""
    try:
        from .project_api import api_create_project
        from .workflow_api import api_start_workflow

        mgr = ClarificationSessionManager()
        session = mgr.load(session_id)
        if not session:
            return {"success": False, "error": "session not found"}

        # If not all answered, still allow finishing; build enriched and LLM summary
        enriched_idea = _build_enriched_idea(session)
        summary = _generate_summary(session)
        session['summary'] = summary
        mgr.save(session)
        summary_text = _format_summary_text(summary)
        handoff_text = "【总结】\n" + summary_text + "\n\n" + enriched_idea

        # Create project if not exists
        if not session.get('project_id'):
            project_res = api_create_project({
                "name": f"想法优化 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "description": "澄清→多智能体优化",
                "initial_idea": handoff_text,
                "domain": (session.get('idea_seed') or {}).get('domain') or 'general',
            })
            if not project_res.get('success'):
                return {"success": False, "error": project_res.get('error', 'create project failed')}
            project_id = project_res.get('project_id') or project_res.get('data', {}).get('id')
            session['project_id'] = project_id
            mgr.save(session)
        else:
            project_id = session['project_id']

        wf_res = api_start_workflow(project_id, handoff_text, 'balanced')
        if not wf_res.get('success'):
            return {"success": False, "error": wf_res.get('error', 'start workflow failed')}

        session['status'] = 'completed'
        # 尝试记录工作流会话ID
        workflow_session_id = wf_res.get('session_id') or wf_res.get('data', {}).get('session_id')
        if workflow_session_id:
            session['workflow_session_id'] = workflow_session_id
        mgr.save(session)

        return {"success": True, "workflow_session_id": workflow_session_id}
    except Exception as e:
        logger.error(f"finish_clarification failed: {e}")
        return {"success": False, "error": str(e)}


def api_submit_summary(session_id: str, summary: Dict[str, Any], restart: bool = False) -> Dict[str, Any]:
    """Update session summary with user edits and start (or restart) workflow.
    Returns: { success, workflow_session_id }
    """
    try:
        from .project_api import api_create_project
        from .workflow_api import api_start_workflow

        mgr = ClarificationSessionManager()
        session = mgr.load(session_id)
        if not session:
            return {"success": False, "error": "session not found"}

        # 保存用户编辑后的总结
        session['summary'] = summary or {}
        mgr.save(session)

        # 组装交接文本
        enriched_idea = _build_enriched_idea(session)
        summary_text = _format_summary_text(summary or {})
        handoff_text = "【总结】\n" + summary_text + "\n\n" + enriched_idea

        # 创建项目（若尚无）
        if not session.get('project_id'):
            project_res = api_create_project({
                "name": f"想法优化 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "description": "澄清→多智能体优化（用户编辑提交）",
                "initial_idea": handoff_text,
                "domain": (session.get('idea_seed') or {}).get('domain') or 'general',
            })
            if not project_res.get('success'):
                return {"success": False, "error": project_res.get('error', 'create project failed')}
            project_id = project_res.get('project_id') or project_res.get('data', {}).get('id')
            session['project_id'] = project_id
            mgr.save(session)
        else:
            project_id = session['project_id']

        # 启动新的工作流实例（即使已有旧的，也启动新会话，前端会按 wf 参数订阅对应会话）
        wf_res = api_start_workflow(project_id, handoff_text, 'balanced')
        if not wf_res.get('success'):
            return {"success": False, "error": wf_res.get('error', 'start workflow failed')}

        session['status'] = 'completed'
        workflow_session_id = wf_res.get('session_id') or wf_res.get('data', {}).get('session_id')
        if workflow_session_id:
            session['workflow_session_id'] = workflow_session_id
        mgr.save(session)

        return {"success": True, "workflow_session_id": workflow_session_id}
    except Exception as e:
        logger.error(f"submit_summary failed: {e}")
        return {"success": False, "error": str(e)}
