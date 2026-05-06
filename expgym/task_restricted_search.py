"""Restricted search scenario using Phantom Wiki corpus."""
from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Callable, Dict, List, Optional, Set, Tuple

import pyarrow.parquet as pq

from expgym.react_loop import build_system_prompt as build_react_system_prompt

# ---------------------------------------------------------------------------
# Data paths
# ---------------------------------------------------------------------------

_PHANTOM_WIKI_ROOT = os.environ.get(
    "PHANTOM_WIKI_ROOT",
    os.path.join(os.path.dirname(__file__), "..", "data", "phantom-wiki"),
)
PHANTOM_WIKI_SNAPSHOT = os.path.join(
    _PHANTOM_WIKI_ROOT,
    "datasets--kilian-group--phantom-wiki-v1",
    "snapshots",
    "9369f9c64655f4e8146afee75ae5d3e3a95d7df5",
)
QA_DIR = os.path.join(PHANTOM_WIKI_SNAPSHOT, "question-answer")
CORPUS_DIR = os.path.join(PHANTOM_WIKI_SNAPSHOT, "text-corpus")

# Question types 11-12 = 3 relation hops (sweet spot for EEI).
# Lower types (6-10) have more hops but fail at reasoning even without budget.
# Higher types (13-16) have fewer hops but need too few searches to show EEI sensitivity.
SWEET_SPOT_TYPES = [11, 12]
MAX_ANSWER_COUNT = 20  # Filter out questions with >20 gold answers

# Overhead per search: 300 +/- 20s
SEARCH_OVERHEAD_LOW = 280.0
SEARCH_OVERHEAD_HIGH = 320.0

TOKEN_RE = re.compile(r"\b\w+\b")

# ---------------------------------------------------------------------------
# Module-level caches
# ---------------------------------------------------------------------------

_CORPUS_CACHE: Dict[int, Dict[str, str]] = {}  # seed -> {title: article}
_QA_CACHE: Dict[int, List[dict]] = {}           # seed -> filtered QA rows


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stable_float(seed_str: str, low: float, high: float) -> float:
    digest = hashlib.sha256(seed_str.encode("utf-8")).digest()
    raw = int.from_bytes(digest[:4], "big") / 2**32
    return low + (high - low) * raw


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


def _parse_payload(payload: str) -> Dict[str, object]:
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("Payload must be a JSON object.")
    return data


# ---------------------------------------------------------------------------
# Data source parsing & loading
# ---------------------------------------------------------------------------

DEFAULT_SEED = 1


def _parse_data_source(data_source: str) -> int:
    """Parse 'phantom_seed1' -> seed int."""
    m = re.match(r"^phantom_seed(\d+)$", data_source)
    if not m:
        raise ValueError(
            f"Invalid data_source: {data_source!r}. "
            "Expected phantom_seed1, phantom_seed2, or phantom_seed3."
        )
    return int(m.group(1))


def _resolve_seed(data_source: Optional[str]) -> int:
    """Parse data_source to seed, defaulting to DEFAULT_SEED if None."""
    return _parse_data_source(data_source) if data_source else DEFAULT_SEED


def _load_corpus(seed: int) -> Dict[str, str]:
    """Load title->article mapping for a seed. Cached at module level."""
    if seed in _CORPUS_CACHE:
        return _CORPUS_CACHE[seed]
    path = os.path.join(
        CORPUS_DIR,
        f"depth_20_size_5000_seed_{seed}-00000-of-00001.parquet",
    )
    table = pq.read_table(path, columns=["title", "article"])
    corpus = {row["title"]: row["article"] for row in table.to_pylist()}
    _CORPUS_CACHE[seed] = corpus
    return corpus


def _load_qa(seed: int) -> List[dict]:
    """Load filtered QA rows (sweet-spot types, <=MAX_ANSWER_COUNT answers).

    Returns a stable-sorted list by (type, difficulty).
    """
    if seed in _QA_CACHE:
        return _QA_CACHE[seed]
    path = os.path.join(
        QA_DIR,
        f"depth_20_size_5000_seed_{seed}-00000-of-00001.parquet",
    )
    table = pq.read_table(path, columns=["question", "answer", "type", "difficulty"])
    all_rows = table.to_pylist()
    filtered = [
        r for r in all_rows
        if r["type"] in SWEET_SPOT_TYPES and len(r["answer"]) <= MAX_ANSWER_COUNT
    ]
    filtered.sort(key=lambda r: (r["type"], r["difficulty"]))
    _QA_CACHE[seed] = filtered
    return filtered


def get_source_count(data_source: str) -> int:
    """Return the number of usable questions for a data source."""
    seed = _parse_data_source(data_source)
    return len(_load_qa(seed))


# ---------------------------------------------------------------------------
# Answer evaluation (name-level F1)
# ---------------------------------------------------------------------------

def _normalize_name(name: str) -> str:
    return " ".join(name.lower().split())


def _extract_names(text: str) -> Set[str]:
    """Extract person names from LLM prediction text.

    Handles: comma-separated, newline-separated, JSON arrays, numbered lists.
    """
    if not text or not text.strip():
        return set()

    # Try JSON array first
    try:
        parsed = json.loads(text.strip())
        if isinstance(parsed, list):
            return {_normalize_name(str(n)) for n in parsed if str(n).strip()}
    except (json.JSONDecodeError, TypeError):
        pass

    # Split by commas, newlines, semicolons
    parts = re.split(r"[,;\n]", text)
    names = set()
    for part in parts:
        # Strip list markers like "1.", "-", "*", "•"
        cleaned = re.sub(r"^\s*[\d]+[.)]\s*", "", part)
        cleaned = cleaned.strip().strip("-*•").strip()
        if not cleaned:
            continue
        words = cleaned.split()
        # Names are typically 2-3 words (Firstname Lastname)
        if 1 <= len(words) <= 5:
            names.add(_normalize_name(cleaned))
    return names


def _name_f1(prediction: str, gold_answers: List[str]) -> float:
    """Compute name-level F1 between prediction and gold answer set."""
    pred_names = _extract_names(prediction)
    gold_names = {_normalize_name(a) for a in gold_answers}

    if not gold_names:
        return 1.0 if not pred_names else 0.0
    if not pred_names:
        return 0.0

    tp = len(pred_names & gold_names)
    precision = tp / len(pred_names)
    recall = tp / len(gold_names)

    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


# ---------------------------------------------------------------------------
# Search tool
# ---------------------------------------------------------------------------

class PhantomSearchTools:
    """Single search tool over Phantom Wiki corpus."""

    def __init__(self, corpus: Dict[str, str]) -> None:
        self._corpus = corpus
        self._title_lower: Dict[str, str] = {t.lower(): t for t in corpus}
        # Pre-compute token sets for keyword search (avoids re-tokenizing
        # all ~5K articles on every non-title-match call)
        self._title_tokens: Dict[str, Set[str]] = {t: set(_tokenize(t)) for t in corpus}
        self._body_tokens: Dict[str, Set[str]] = {t: set(_tokenize(a)) for t, a in corpus.items()}
        self._query_cache: Dict[str, str] = {}  # lowered query -> result text
        self._seen_titles: Set[str] = set()      # titles already returned

    def search(self, payload: str) -> Tuple[str, float]:
        """Search the Phantom Wiki corpus.

        Returns (article_text, overhead_seconds).
        Exact title match is tried first; falls back to keyword search.
        Re-searching a query whose article was already returned is free.
        """
        data = _parse_payload(payload)
        query = str(data.get("query", "")).strip()
        if not query:
            return "Error: No query provided.", 0.0

        query_key = query.lower()

        # Exact same query repeated -> free
        if query_key in self._query_cache:
            return self._query_cache[query_key], 0.0

        # Try exact title match (case-insensitive)
        result_title = self._title_lower.get(query_key)

        if result_title is None:
            # Keyword search: score articles by token overlap
            result_title = self._keyword_search(query)

        if result_title is None:
            result = "No matching article found."
            self._query_cache[query_key] = result
            return result, 0.0

        article = self._corpus[result_title]
        result = f"Article: {result_title}\n\n{article}"
        self._query_cache[query_key] = result

        # Overhead: 300±20s for NEW articles, free for already-seen
        if result_title in self._seen_titles:
            return result, 0.0
        self._seen_titles.add(result_title)
        overhead = _stable_float(f"search:{result_title}", SEARCH_OVERHEAD_LOW, SEARCH_OVERHEAD_HIGH)
        return result, overhead

    def _keyword_search(self, query: str) -> Optional[str]:
        """Score articles by token overlap, return best-matching title."""
        q_tokens = set(_tokenize(query))
        if not q_tokens:
            return None

        best_score = 0
        best_title = None
        for title in self._corpus:
            # Title tokens weighted 5x
            score = (len(q_tokens & self._title_tokens[title]) * 5
                     + len(q_tokens & self._body_tokens[title]))
            if score > best_score:
                best_score = score
                best_title = title

        return best_title if best_score > 0 else None


def preload(data_source: str) -> None:
    """Eagerly load corpus + QA for the given data source into cache."""
    seed = _parse_data_source(data_source)
    _load_corpus(seed)
    _load_qa(seed)


# ---------------------------------------------------------------------------
# SCENARIO hooks
# ---------------------------------------------------------------------------

def build_tools(
    *, data_source: Optional[str] = None
) -> Dict[str, Callable[[str], Tuple[str, float]]]:
    seed = _resolve_seed(data_source)
    corpus = _load_corpus(seed)
    tools = PhantomSearchTools(corpus)
    return {"search": tools.search}


def build_context(
    include_overhead: bool,
    *,
    row_index: int = 0,
    data_source: Optional[str] = None,
) -> str:
    seed = _resolve_seed(data_source)
    qa_rows = _load_qa(seed)
    if row_index < 0 or row_index >= len(qa_rows):
        raise IndexError(
            f"row_index {row_index} outside [0, {len(qa_rows)}) "
            f"for data_source={data_source}"
        )
    question = qa_rows[row_index]["question"]
    n_gold = len(qa_rows[row_index]["answer"])

    lines = [
        "You are answering a question by searching a wiki of fictional characters.",
        "",
        "Tool:",
        "- search: look up information in the wiki.",
        '  Input: {"query": "Person Name"} or {"query": "keyword phrase"}',
        "  If the query exactly matches an article title, that article is returned.",
        "  Otherwise, the most relevant article is returned based on keyword matching.",
        "",
        "Strategy:",
        "1. The wiki contains articles about fictional people, each with Family, Friends, and Attributes sections.",
        "2. Questions ask about relationship chains (e.g., 'Who is the friend of the parent of X?').",
        "3. Start from the person named (or described) in the question, then follow the chain step by step.",
        "4. Each search returns one full article. Re-searching a previously returned article is free.",
        "5. Your answer should list ALL matching names, separated by commas.",
        "",
        "Action format:",
        '  Action: search {"query": "Person Name"}',
        f"  Answer: Name1, Name2, ...  (there may be 1 to {n_gold} correct answers)",
        "",
        f"Question: {question}",
    ]
    # Note: V16+ controls cost/budget visibility via include_cost_in_observation
    # in the react loop, not via context injection. include_overhead is kept for
    # backward compat but is effectively unused.
    return "\n".join(lines)


def build_instruction_notes(include_overhead: bool) -> List[str]:
    return []


def build_system_prompt(include_overhead: bool) -> str:
    # V16+: cost/budget info is shown in observations via include_cost_in_observation,
    # not injected into the system prompt. include_overhead kept for backward compat.
    return build_react_system_prompt()


def build_fake_plan(
    probes: int,
    *,
    row_index: int = 0,
    data_source: Optional[str] = None,
) -> List[Tuple[str, str]]:
    seed = _resolve_seed(data_source)
    qa_rows = _load_qa(seed)
    question = qa_rows[row_index]["question"]
    # For FakeLLM: just search with the question text
    return [("search", json.dumps({"query": question}))]


def build_answer_evaluator(
    row_index: int, data_source: Optional[str] = None
) -> Callable[[str], float]:
    seed = _resolve_seed(data_source)
    qa_rows = _load_qa(seed)
    if row_index < 0 or row_index >= len(qa_rows):
        raise IndexError(
            f"row_index {row_index} outside [0, {len(qa_rows)}) "
            f"for data_source={data_source}"
        )
    gold_answers = qa_rows[row_index]["answer"]

    def _evaluator(prediction: str) -> float:
        return _name_f1(prediction, gold_answers)

    return _evaluator


# ---------------------------------------------------------------------------
# Scenario export
# ---------------------------------------------------------------------------

SCENARIO = {
    "name": "restricted_search",
    "tools": build_tools,
    "build_context": build_context,
    "build_instruction_notes": build_instruction_notes,
    "build_fake_plan": build_fake_plan,
    "build_answer_evaluator": build_answer_evaluator,
    "build_system_prompt": build_system_prompt,
}
