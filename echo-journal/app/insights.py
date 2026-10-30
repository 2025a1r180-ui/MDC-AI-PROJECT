"""
Insights and Hybrid Retrieval Blueprint for Echo Journal (Milestone 3).

Non-Negotiable Rules Enforced:
1. Self-reflection, NOT medicine or diagnosis. Never claim causation ("co-occurs with", not "causes").
2. Grounded generation: Every insight cites specific dates/titles/excerpts, stating uncertainty.
3. Strict Account Isolation: All queries and indices strictly scoped to authenticated user_id.
4. Privacy Consent Gate: Zero journal text is processed by external AI without explicit user opt-in.
5. Minimum Threshold Invariant: Longitudinal pattern analysis requires at least 10 journal entries.
"""

import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

try:
    from flask import Blueprint, render_template, request, session, jsonify, flash, redirect, url_for
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

from .safety import check_safety
from .llm_client import SwappableLLMClient, SYSTEM_PROMPT_TEMPLATE

if HAS_FLASK:
    from .auth import login_required
    from .repository import JournalRepository, UserRepository
    from .db import get_db

    insights_bp = Blueprint("insights", __name__, url_prefix="/insights")
else:
    insights_bp = None


# Common English stopwords for BM25 keyword retrieval
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing",
    "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself",
    "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is",
    "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should",
    "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", "them",
    "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd",
    "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's", "where", "where's",
    "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you",
    "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
}


def tokenize(text: str) -> List[str]:
    """Tokenize and normalize text into alphanumeric words."""
    if not text:
        return []
    words = re.findall(r"\b[a-zA-Z0-9_']+\b", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 1]


def compute_char_trigrams(text: str) -> Counter:
    """Generate normalized character 3-grams for semantic n-gram dense matching."""
    norm = re.sub(r"\s+", " ", text.lower().strip())
    trigrams = [norm[i:i+3] for i in range(len(norm) - 2)]
    return Counter(trigrams)


def cosine_similarity(vec_a: Counter, vec_b: Counter) -> float:
    """Calculate cosine similarity between two sparse vector counters."""
    intersection = set(vec_a.keys()) & set(vec_b.keys())
    if not intersection:
        return 0.0
    dot_product = sum(vec_a[x] * vec_b[x] for x in intersection)
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot_product / (mag_a * mag_b)


class HybridRetriever:
    """
    Hybrid Search Engine combining BM25 keyword frequency and dense semantic n-gram matching.
    STRICTLY scoped to the authenticated user's entries.
    """

    def __init__(self, entries: List[Dict[str, Any]], k1: float = 1.5, b: float = 0.75):
        self.entries = entries
        self.k1 = k1
        self.b = b
        self.N = len(entries)
        self.corpus_tokens: List[List[str]] = []
        self.corpus_trigrams: List[Counter] = []
        self.doc_lengths: List[int] = []
        self.doc_freqs: Dict[str, int] = Counter()

        for entry in self.entries:
            combined_text = f"{entry.get('title', '')} {entry.get('content', '')} {' '.join(entry.get('tags', []))}"
            tokens = tokenize(combined_text)
            self.corpus_tokens.append(tokens)
            self.doc_lengths.append(len(tokens))
            self.corpus_trigrams.append(compute_char_trigrams(combined_text))

            # Count unique documents containing each term
            unique_terms = set(tokens)
            for t in unique_terms:
                self.doc_freqs[t] += 1

        self.avg_doc_len = sum(self.doc_lengths) / max(1, self.N) if self.N > 0 else 1.0

    def _idf(self, term: str) -> float:
        n_q = self.doc_freqs.get(term, 0)
        return math.log(1.0 + (self.N - n_q + 0.5) / (n_q + 0.5))

    def _bm25_score(self, query_tokens: List[str], doc_idx: int) -> float:
        if self.N == 0:
            return 0.0
        doc_tokens = self.corpus_tokens[doc_idx]
        doc_len = self.doc_lengths[doc_idx]
        score = 0.0
        token_counts = Counter(doc_tokens)

        for qt in query_tokens:
            f = token_counts.get(qt, 0)
            if f == 0:
                continue
            idf = self._idf(qt)
            num = f * (self.k1 + 1.0)
            denom = f + self.k1 * (1.0 - self.b + self.b * (doc_len / max(1.0, self.avg_doc_len)))
            score += idf * (num / denom)
        return score

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval using Reciprocal Rank Fusion (RRF).
        Returns top_k entries with relevance scores and matching citations.
        """
        if not self.entries or not query.strip():
            return []

        query_tokens = tokenize(query)
        query_trigrams = compute_char_trigrams(query)

        # 1. BM25 Ranking
        bm25_scores = []
        for idx in range(self.N):
            s = self._bm25_score(query_tokens, idx)
            bm25_scores.append((idx, s))
        bm25_ranked = sorted(bm25_scores, key=lambda x: x[1], reverse=True)
        bm25_rank_map = {idx: rank + 1 for rank, (idx, _) in enumerate(bm25_ranked)}

        # 2. Semantic Ranking (Character Trigram Cosine Similarity)
        semantic_scores = []
        for idx in range(self.N):
            s = cosine_similarity(query_trigrams, self.corpus_trigrams[idx])
            semantic_scores.append((idx, s))
        semantic_ranked = sorted(semantic_scores, key=lambda x: x[1], reverse=True)
        semantic_rank_map = {idx: rank + 1 for rank, (idx, _) in enumerate(semantic_ranked)}

        # 3. Reciprocal Rank Fusion (RRF) with constant k=60
        fused_results = []
        for idx, entry in enumerate(self.entries):
            r_bm25 = bm25_rank_map[idx]
            r_sem = semantic_rank_map[idx]
            raw_bm25 = bm25_scores[idx][1]
            raw_sem = semantic_scores[idx][1]

            # Only include if there is some textual or semantic overlap
            if raw_bm25 > 0.0 or raw_sem > 0.05:
                rrf_score = (1.0 / (60.0 + r_bm25)) + (1.0 / (60.0 + r_sem))
                fused_results.append({
                    "entry": entry,
                    "rrf_score": round(rrf_score, 4),
                    "bm25_score": round(raw_bm25, 3),
                    "semantic_score": round(raw_sem, 3),
                    "matched_tokens": list(set(query_tokens) & set(self.corpus_tokens[idx])),
                })

        fused_results.sort(key=lambda x: x["rrf_score"], reverse=True)
        return fused_results[:top_k]


class PatternAnalyzer:
    """
    Analyzes longitudinal temporal patterns, mood trends, and tag-emotion co-occurrences.
    Enforces the 10-entry minimum invariant to avoid pseudo-scientific conclusions.
    """
    MINIMUM_ENTRIES_THRESHOLD = 10

    @classmethod
    def analyze_patterns(cls, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        count = len(entries)
        if count < cls.MINIMUM_ENTRIES_THRESHOLD:
            return {
                "eligible": False,
                "entry_count": count,
                "required_count": cls.MINIMUM_ENTRIES_THRESHOLD,
                "message": (
                    f"Pattern detection requires a minimum of {cls.MINIMUM_ENTRIES_THRESHOLD} journal entries "
                    f"to prevent spurious patterns and over-generalization (currently {count}/{cls.MINIMUM_ENTRIES_THRESHOLD}). "
                    "Please continue recording entries to unlock longitudinal trends."
                ),
                "disclaimer": "Echo Journal never draws conclusions from small sample sizes."
            }

        # 1. Emotion and Mood Distributions
        emotion_counts: Dict[str, int] = Counter()
        mood_counts: Dict[str, int] = Counter()
        tag_emotion_map: Dict[str, Counter] = defaultdict(Counter)
        tag_mood_map: Dict[str, Counter] = defaultdict(Counter)

        for entry in entries:
            # Mood
            mood = entry.get("mood")
            if mood:
                mood_counts[mood.lower()] += 1

            # Analysis Emotion (if available)
            primary_emo = entry.get("primary_emotion")
            if not primary_emo and "analysis" in entry and entry["analysis"]:
                primary_emo = entry["analysis"].get("primary_emotion")
            if primary_emo:
                emotion_counts[primary_emo.lower()] += 1

            # Tags co-occurrence
            tags = entry.get("tags", [])
            for tag in tags:
                clean_tag = tag.lower().strip()
                if primary_emo:
                    tag_emotion_map[clean_tag][primary_emo.lower()] += 1
                if mood:
                    tag_mood_map[clean_tag][mood.lower()] += 1

        # 2. Derive tag-emotion co-occurrence insights (NON-CAUSAL LANGUAGE ONLY)
        co_occurrences = []
        for tag, emo_counter in tag_emotion_map.items():
            total_tag_instances = sum(emo_counter.values())
            if total_tag_instances >= 2:
                top_emo, top_cnt = emo_counter.most_common(1)[0]
                pct = round((top_cnt / total_tag_instances) * 100)
                co_occurrences.append({
                    "tag": tag,
                    "co_occurring_emotion": top_emo,
                    "sample_size": total_tag_instances,
                    "percentage": pct,
                    # Non-causal observation statement
                    "observation": (
                        f"When writing with tag '#{tag}', entries frequently co-occur with {top_emo} "
                        f"({pct}% of {total_tag_instances} entries). Observed correlation, not causation."
                    )
                })

        # 3. Derive timeline trends (chronological grouping)
        sorted_entries = sorted(entries, key=lambda x: str(x.get("created_at", "")))
        timeline_trend = []
        for e in sorted_entries:
            timeline_trend.append({
                "id": e.get("id"),
                "date": str(e.get("created_at", ""))[:10],
                "title": e.get("title", ""),
                "mood": e.get("mood") or "unspecified",
                "primary_emotion": e.get("primary_emotion") or (e.get("analysis") or {}).get("primary_emotion") or "unrecorded",
            })

        return {
            "eligible": True,
            "entry_count": count,
            "required_count": cls.MINIMUM_ENTRIES_THRESHOLD,
            "emotion_distribution": dict(emotion_counts),
            "mood_distribution": dict(mood_counts),
            "co_occurrences": co_occurrences,
            "timeline_trend": timeline_trend,
            "non_causal_notice": (
                "Scientific Notice: All patterns represent linguistic co-occurrence in your personal entries. "
                "Echo Journal never asserts causation or provides psychological diagnoses."
            )
        }


def answer_grounded_query(
    query: str,
    user_entries: List[Dict[str, Any]],
    user_opted_in: bool
) -> Dict[str, Any]:
    """
    Executes the 'Ask Your Journal' pipeline:
    1. Safety & Crisis Interceptor check.
    2. Account Privacy Consent Gate check.
    3. Hybrid retrieval over user's entries strictly.
    4. Grounded citation synthesis stating uncertainty.
    """
    # Step 1: Safety & Crisis Interceptor
    is_crisis, crisis_data = check_safety(query)
    if is_crisis:
        return {
            "status": "crisis_detected",
            "message": crisis_data["message"],
            "helplines": crisis_data["helplines"],
            "disclaimer": crisis_data["disclaimer"],
            "citations": [],
            "grounded_text": None,
        }

    # Step 2: Privacy Consent Gate
    if not user_opted_in:
        return {
            "status": "consent_required",
            "message": (
                "Privacy Gate: Echo Journal strictly forbids sending journal text to external reflection models "
                "without explicit consent. You can enable this feature at any time in Account Settings."
            ),
            "citations": [],
            "grounded_text": None,
        }

    # Step 3: Hybrid Retrieval
    retriever = HybridRetriever(user_entries)
    retrieved_results = retriever.search(query, top_k=3)

    if not retrieved_results:
        return {
            "status": "insufficient_evidence",
            "message": "There is not enough evidence in your recorded entries to reflect on this topic.",
            "citations": [],
            "grounded_text": "I examined your journal archive, but found no matching entries or relevant context for this inquiry.",
            "uncertainty_notice": "Reflections require explicit textual evidence to maintain ground truth."
        }

    # Step 4: Extract Citations and Construct Grounded Reflection
    citations = []
    context_summaries = []
    earliest_date = "9999"
    latest_date = "0000"

    for item in retrieved_results:
        entry = item["entry"]
        created = str(entry.get("created_at", ""))
        date_str = created[:10] if created else "Unknown Date"
        if date_str < earliest_date:
            earliest_date = date_str
        if date_str > latest_date:
            latest_date = date_str

        # Generate a concise excerpt around the matched terms or first 160 characters
        content = entry.get("content", "")
        excerpt = content[:160] + ("..." if len(content) > 160 else "")

        citation_entry = {
            "entry_id": entry.get("id"),
            "title": entry.get("title", "Untitled"),
            "date": date_str,
            "excerpt": excerpt,
            "relevance_score": item["rrf_score"],
            "mood": entry.get("mood"),
            "matched_tokens": item["matched_tokens"],
        }
        citations.append(citation_entry)
        context_summaries.append(
            f"• [{date_str} - '{citation_entry['title']}'] \"{excerpt}\" (Recorded mood: {entry.get('mood') or 'none'})"
        )

    # Synthesis with explicit citations and uncertainty
    citations_text = "\n".join(context_summaries)
    reflection_body = (
        f"Based on your entries between {earliest_date} and {latest_date}, here is what you noted:\n\n"
        f"{citations_text}\n\n"
        f"Pattern observation: The retrieved entries show reflections connected to your question. "
        f"This synthesis is strictly limited to these {len(citations)} recorded moments."
    )

    return {
        "status": "success",
        "grounded_text": reflection_body,
        "citations": citations,
        "uncertainty_notice": (
            f"Synthesized strictly from {len(citations)} retrieved entries ({earliest_date} to {latest_date}). "
            "Patterns represent recorded self-observations, not psychological or causal claims."
        )
    }


# --- Flask Route Handlers (When Flask is available) ---
if HAS_FLASK:
    @insights_bp.route("/", methods=["GET"])
    @login_required
    def index():
        conn = get_db()
        journal_repo = JournalRepository(conn)
        user_repo = UserRepository(conn)

        user_id = session["user_id"]
        user = user_repo.get_by_id(user_id)
        raw_entries = journal_repo.get_user_entries(user_id, limit=500)

        # Convert sqlite rows to dictionaries
        entries = []
        for r in raw_entries:
            entries.append({
                "id": r["id"],
                "title": r["title"],
                "content": r["content"],
                "mood": r["mood"],
                "tags": [t for t in (r["tags"] or "").split(",") if t],
                "primary_emotion": r["primary_emotion"],
                "created_at": r["created_at"],
            })

        pattern_data = PatternAnalyzer.analyze_patterns(entries)
        opted_in = bool(user["opt_in_external_ai"]) if user else False

        return render_template(
            "insights/index.html",
            patterns=pattern_data,
            opted_in=opted_in,
            entry_count=len(entries)
        )

    @insights_bp.route("/ask", methods=["POST"])
    @login_required
    def ask_journal():
        conn = get_db()
        journal_repo = JournalRepository(conn)
        user_repo = UserRepository(conn)

        user_id = session["user_id"]
        user = user_repo.get_by_id(user_id)
        opted_in = bool(user["opt_in_external_ai"]) if user else False

        data = request.get_json() or {}
        query = data.get("query", "").strip()

        if not query:
            return jsonify({"error": "Query cannot be blank."}), 400

        raw_entries = journal_repo.get_user_entries(user_id, limit=500)
        entries = []
        for r in raw_entries:
            entries.append({
                "id": r["id"],
                "title": r["title"],
                "content": r["content"],
                "mood": r["mood"],
                "tags": [t for t in (r["tags"] or "").split(",") if t],
                "primary_emotion": r["primary_emotion"],
                "created_at": r["created_at"],
            })

        result = answer_grounded_query(query, entries, user_opted_in=opted_in)
        return jsonify(result)
