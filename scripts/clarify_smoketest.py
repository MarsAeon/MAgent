import os
import sys
from pathlib import Path

# Ensure MAgent package is importable
BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from src.api.questioning_api import api_start_clarification_session


def main():
    seed = {
        "raw_text": "我有一个面向中学生的个性化学习平台的想法，根据学习风格推荐内容和练习，未来做成SaaS。",
        "context_hints": ["education", "platform"],
        "domain": "education",
    }
    res = api_start_clarification_session(seed)
    print("success:", res.get("success"))
    print("session_id:", res.get("session_id"))
    nq = (res.get("next_question") or {}).get("question")
    print("next_question:", nq)


if __name__ == "__main__":
    main()
