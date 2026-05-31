"""Pre-LLM signal scoring using regex patterns.

Scores each post 0-100 across 4 dimensions without any LLM call.
Posts below SIGNAL_THRESHOLD_LOW (30) are skipped entirely.
Posts above SIGNAL_THRESHOLD_HIGH (60) get priority analysis.
"""

from __future__ import annotations

import math
import re

# ── Emotion signals ──────────────────────────────────────────────
_EMOTION_STRONG = [
    r"\bhate\b", r"\bterrible\b", r"\bnightmare\b", r"\bhorrible\b",
    r"\bawful\b", r"\bdisaster\b", r"\bgarbage\b", r"\buseless\b",
    r"\bbroken\b", r"\binfuriating\b", r"\bunbearable\b", r"\bpathetic\b",
    r"\bhopeless\b", r"\bwtf\b", r"\bdreadful\b",
]
_EMOTION_MEDIUM = [
    r"\bfrustrat(?:ing|ed|ion)\b", r"\bannoying\b", r"\bpainful\b",
    r"\bstruggling\b", r"\bsucks?\b", r"\bwaste\s+of\b",
    r"\btired\s+of\b", r"\bsick\s+of\b", r"\bfed\s+up\b",
    r"\bdrives?\s+me\s+crazy\b", r"\bpisses?\s+me\s+off\b",
    r"\bso\s+bad\b", r"\btoo\s+hard\b", r"\bovercomplicated\b",
    r"\bpain\s+in\s+the\b", r"\bdriving\s+me\s+nuts\b",
]
_EMOTION_MILD = [
    r"\bslow\b", r"\bclunky\b", r"\boutdated\b", r"\bmissing\b",
    r"\bshould\s+be\s+easier\b", r"\btoo\s+complicated\b",
    r"\bnot\s+great\b", r"\bdisappointing\b", r"\black(?:ing|s)\b",
    r"\bneeds?\s+improvement\b", r"\bcould\s+be\s+better\b",
]

# ── Money signals ─────────────────────────────────────────────────
_MONEY_PATTERNS = [
    r"\bpay\b", r"\bpaid\b", r"\bpaying\b", r"\bspen(?:t|ding)\b",
    r"\bwaste\s+of\s+money\b", r"\boverpriced\b", r"\bsubscription\b",
    r"\bpricing\b", r"\bcosts?\s+too\s+much\b", r"\bexpensive\b",
    r"\bcheaper\b", r"\bnot\s+worth\b", r"\broi\b", r"\bbudget\b",
    r"\bafford\b", r"\bbill(?:ed|ing)\b", r"\bcharg(?:e|ing)\b",
    r"\$\d+", r"\d+\s*dollars\b", r"\d+\s*usd\b",
    r"\bwilling\s+to\s+pay\b", r"\bwould\s+pay\b",
]

# ── Tool / replacement signals ────────────────────────────────────
_TOOL_PATTERNS = [
    r"\b(tool|software|app|platform|solution|service|product)\b",
    r"\balternative\s+to\b", r"\breplace\b", r"\bswitch\s+(?:from|away)\b",
    r"\bmigrat(?:e|ing)\b", r"\blooking\s+for\s+(?:a|an)\b",
    r"\bneed\s+a\s+better\b", r"\banyone\s+know\s+(?:a|of)\b",
    r"\brecommend(?:ation|ing|me)?\b", r"\bsuggest\s+(?:me|a)\b",
    r"\bi\s+(?:built|made|created|launched)\b", r"\bi(?:'m|\s+am)\s+building\b",
    r"\bhas\s+anyone\s+(?:built|tried|used)\b",
]

# ── Manual / repetitive work signals ──────────────────────────────
_BURNOUT_PATTERNS = [
    r"\brepetitive\b", r"\bmanual\b", r"\bevery\s+day\b",
    r"\bevery\s+time\b", r"\bover\s+and\s+over\b",
    r"\bcopy[\s-]*past(?:e|ing)\b", r"\bspreadsheet\b", r"\bexcel\b",
    r"\bdata\s+entry\b", r"\bbusy\s*work\b", r"\bgrunt\s*work\b",
    r"\btedious\b", r"\bmonotonous\b", r"\bboring\b",
    r"\bdoing\s+(?:this|it|the\s+same)\s+manually\b",
]

SIGNAL_THRESHOLD_HIGH = 60
SIGNAL_THRESHOLD_LOW = 30


def _count_matches(text: str, patterns: list[str]) -> int:
    return sum(1 for p in patterns if re.search(p, text))


def score_post(title: str, body: str, upvotes: int, num_comments: int) -> float:
    """Score a post 0-100 based on cheap regex signals.

    Components:
      - Engagement (0-25): log-scaled upvotes + comments
      - Emotion (0-30):  strong=8pts, medium=5pts, mild=2pts each
      - Money (0-25):   5pts per money-pattern match
      - Tool (0-20):    4pts per tool/replacement-pattern match
    """
    text = f"{title} {body}".lower()

    eng = math.log2(upvotes + 1) * 3.0 + math.log2(num_comments + 1) * 4.0
    eng_score = min(25.0, eng)

    strong = _count_matches(text, _EMOTION_STRONG)
    medium = _count_matches(text, _EMOTION_MEDIUM)
    mild = _count_matches(text, _EMOTION_MILD)
    emotion_score = min(30.0, strong * 8.0 + medium * 5.0 + mild * 2.0)

    money_hits = _count_matches(text, _MONEY_PATTERNS)
    money_score = min(25.0, money_hits * 5.0)

    tool_hits = _count_matches(text, _TOOL_PATTERNS)
    tool_score = min(20.0, tool_hits * 4.0)

    return round(eng_score + emotion_score + money_score + tool_score, 1)
