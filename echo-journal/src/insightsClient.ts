/**
 * Client-Side Hybrid Retrieval, Pattern Detection, and Grounded Reflection (Milestone 3).
 * Pairs with app/insights.py.
 */

import { JournalEntry } from './storage';
import { checkSafetyClient, CrisisCheckResult } from './safetyClient';

const STOPWORDS = new Set([
  'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren',
  'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
  'can', 'could', 'did', 'do', 'does', 'doing', 'down', 'during', 'each', 'few', 'for', 'from',
  'further', 'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 'himself',
  'his', 'how', 'i', 'if', 'in', 'into', 'is', 'it', 'its', 'itself', 'just', 'me', 'more', 'most',
  'my', 'myself', 'no', 'nor', 'not', 'now', 'of', 'off', 'on', 'once', 'only', 'or', 'other',
  'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', 'she', 'should', 'so', 'some', 'such',
  'than', 'that', 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'these', 'they',
  'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'we', 'were',
  'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'with', 'you', 'your', 'yours'
]);

function tokenize(text: string): string[] {
  if (!text) return [];
  const words = text.toLowerCase().match(/\b[a-z0-9_']+\b/g) || [];
  return words.filter(w => !STOPWORDS.has(w) && w.length > 1);
}

function getCharTrigrams(text: string): Map<string, number> {
  const norm = text.toLowerCase().replace(/\s+/g, ' ').trim();
  const map = new Map<string, number>();
  for (let i = 0; i < norm.length - 2; i++) {
    const tri = norm.slice(i, i + 3);
    map.set(tri, (map.get(tri) || 0) + 1);
  }
  return map;
}

function cosineSimTrigrams(a: Map<string, number>, b: Map<string, number>): number {
  let dot = 0;
  for (const [key, valA] of a.entries()) {
    const valB = b.get(key);
    if (valB) {
      dot += valA * valB;
    }
  }
  let magA = 0;
  for (const v of a.values()) magA += v * v;
  let magB = 0;
  for (const v of b.values()) magB += v * v;

  if (magA === 0 || magB === 0) return 0;
  return dot / (Math.sqrt(magA) * Math.sqrt(magB));
}

export interface HybridSearchResult {
  entry: JournalEntry;
  rrfScore: number;
  bm25Score: number;
  semanticScore: number;
  matchedTokens: string[];
}

export class HybridRetrieverClient {
  private entries: JournalEntry[];
  private corpusTokens: string[][];
  private corpusTrigrams: Map<string, number>[];
  private docLengths: number[];
  private docFreqs: Map<string, number>;
  private avgDocLen: number;
  private k1 = 1.5;
  private b = 0.75;

  constructor(entries: JournalEntry[]) {
    this.entries = entries;
    this.corpusTokens = [];
    this.corpusTrigrams = [];
    this.docLengths = [];
    this.docFreqs = new Map();

    for (const e of entries) {
      const combined = `${e.title} ${e.content} ${e.tags.join(' ')}`;
      const tokens = tokenize(combined);
      this.corpusTokens.push(tokens);
      this.docLengths.push(tokens.length);
      this.corpusTrigrams.push(getCharTrigrams(combined));

      const uniqueTerms = new Set(tokens);
      for (const t of uniqueTerms) {
        this.docFreqs.set(t, (this.docFreqs.get(t) || 0) + 1);
      }
    }

    const totalLen = this.docLengths.reduce((acc, l) => acc + l, 0);
    this.avgDocLen = this.docLengths.length > 0 ? totalLen / this.docLengths.length : 1;
  }

  private idf(term: string): number {
    const n = this.docFreqs.get(term) || 0;
    const N = this.entries.length;
    return Math.log(1.0 + (N - n + 0.5) / (n + 0.5));
  }

  private bm25(queryTokens: string[], docIdx: number): number {
    const docTokens = this.corpusTokens[docIdx];
    const docLen = this.docLengths[docIdx];
    let score = 0;

    const termCounts = new Map<string, number>();
    for (const t of docTokens) {
      termCounts.set(t, (termCounts.get(t) || 0) + 1);
    }

    for (const qt of queryTokens) {
      const f = termCounts.get(qt) || 0;
      if (f === 0) continue;
      const idfVal = this.idf(qt);
      const num = f * (this.k1 + 1.0);
      const denom = f + this.k1 * (1.0 - this.b + this.b * (docLen / Math.max(1, this.avgDocLen)));
      score += idfVal * (num / denom);
    }
    return score;
  }

  search(query: string, topK: number = 5): HybridSearchResult[] {
    if (!query.trim() || this.entries.length === 0) return [];
    const queryTokens = tokenize(query);
    const queryTrigrams = getCharTrigrams(query);

    // 1. BM25 scores
    const bm25List = this.entries.map((_, idx) => ({
      idx,
      score: this.bm25(queryTokens, idx),
    }));
    bm25List.sort((a, b) => b.score - a.score);
    const bm25Ranks = new Map<number, number>();
    bm25List.forEach((item, r) => bm25Ranks.set(item.idx, r + 1));

    // 2. Semantic scores
    const semList = this.entries.map((_, idx) => ({
      idx,
      score: cosineSimTrigrams(queryTrigrams, this.corpusTrigrams[idx]),
    }));
    semList.sort((a, b) => b.score - a.score);
    const semRanks = new Map<number, number>();
    semList.forEach((item, r) => semRanks.set(item.idx, r + 1));

    // 3. RRF Fusion
    const fused: HybridSearchResult[] = [];
    for (let idx = 0; idx < this.entries.length; idx++) {
      const rawBm25 = bm25List.find(x => x.idx === idx)?.score || 0;
      const rawSem = semList.find(x => x.idx === idx)?.score || 0;

      if (rawBm25 > 0 || rawSem > 0.05) {
        const rBm25 = bm25Ranks.get(idx) || 999;
        const rSem = semRanks.get(idx) || 999;
        const rrf = 1 / (60 + rBm25) + 1 / (60 + rSem);

        const matched = queryTokens.filter(qt => this.corpusTokens[idx].includes(qt));

        fused.push({
          entry: this.entries[idx],
          rrfScore: Number(rrf.toFixed(4)),
          bm25Score: Number(rawBm25.toFixed(2)),
          semanticScore: Number(rawSem.toFixed(2)),
          matchedTokens: Array.from(new Set(matched)),
        });
      }
    }

    fused.sort((a, b) => b.rrfScore - a.rrfScore);
    return fused.slice(0, topK);
  }
}

export interface PatternAnalysisResult {
  eligible: boolean;
  entryCount: number;
  requiredCount: number;
  message?: string;
  disclaimer?: string;
  emotionDistribution?: Record<string, number>;
  moodDistribution?: Record<string, number>;
  coOccurrences?: Array<{
    tag: string;
    coOccurringEmotion: string;
    sampleSize: number;
    percentage: number;
    observation: string;
  }>;
  timelineTrend?: Array<{
    id: number;
    date: string;
    title: string;
    mood: string;
    primaryEmotion: string;
  }>;
  nonCausalNotice?: string;
}

export function analyzePatternsClient(entries: JournalEntry[]): PatternAnalysisResult {
  const count = entries.length;
  const MIN = 10;

  if (count < MIN) {
    return {
      eligible: false,
      entryCount: count,
      requiredCount: MIN,
      message: `Pattern detection requires at least ${MIN} entries to avoid pseudo-scientific conclusions and spurious correlations (currently ${count}/${MIN}). Keep journaling to unlock longitudinal reflections.`,
      disclaimer: 'Echo Journal strictly refuses to generalize from insufficient personal data.',
    };
  }

  const emotionDist: Record<string, number> = {};
  const moodDist: Record<string, number> = {};
  const tagEmotionMap: Record<string, Record<string, number>> = {};

  for (const e of entries) {
    if (e.mood) {
      moodDist[e.mood] = (moodDist[e.mood] || 0) + 1;
    }
    const emo = e.analysis?.primaryEmotion || e.analysis?.primary_emotion;
    if (emo) {
      emotionDist[emo] = (emotionDist[emo] || 0) + 1;
    }

    for (const tag of e.tags) {
      const clean = tag.toLowerCase().trim();
      if (!tagEmotionMap[clean]) tagEmotionMap[clean] = {};
      if (emo) {
        tagEmotionMap[clean][emo] = (tagEmotionMap[clean][emo] || 0) + 1;
      }
    }
  }

  const coOccurrences: Array<{
    tag: string;
    coOccurringEmotion: string;
    sampleSize: number;
    percentage: number;
    observation: string;
  }> = [];

  for (const [tag, emoCounts] of Object.entries(tagEmotionMap)) {
    const pairs = Object.entries(emoCounts);
    const total = pairs.reduce((acc, [, c]) => acc + c, 0);
    if (total >= 2) {
      pairs.sort((a, b) => b[1] - a[1]);
      const [topEmo, topCount] = pairs[0];
      const pct = Math.round((topCount / total) * 100);
      coOccurrences.push({
        tag,
        coOccurringEmotion: topEmo,
        sampleSize: total,
        percentage: pct,
        observation: `When writing with tag '#${tag}', entries frequently co-occur with ${topEmo} (${pct}% of ${total} entries). Observed correlation, not causation.`,
      });
    }
  }

  const timelineTrend = [...entries]
    .sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime())
    .map(e => ({
      id: e.id,
      date: e.createdAt.slice(0, 10),
      title: e.title,
      mood: e.mood || 'unspecified',
      primaryEmotion: e.analysis?.primaryEmotion || e.analysis?.primary_emotion || 'unrecorded',
    }));

  return {
    eligible: true,
    entryCount: count,
    requiredCount: MIN,
    emotionDistribution: emotionDist,
    moodDistribution: moodDist,
    coOccurrences,
    timelineTrend,
    nonCausalNotice:
      'Scientific Notice: All patterns represent linguistic co-occurrence in your personal entries. Echo Journal never asserts causation or provides psychological diagnoses.',
  };
}

export interface GroundedQueryResponse {
  status: 'crisis_detected' | 'consent_required' | 'insufficient_evidence' | 'success';
  groundedText?: string;
  citations: Array<{
    entryId: number;
    title: string;
    date: string;
    excerpt: string;
    relevanceScore: number;
    mood?: string | null;
  }>;
  uncertaintyNotice?: string;
  crisisData?: CrisisCheckResult;
}

export function answerGroundedQueryClient(
  query: string,
  userEntries: JournalEntry[],
  optedIn: boolean
): GroundedQueryResponse {
  // 1. Safety & Crisis Interceptor
  const safety = checkSafetyClient(query);
  if (safety.isCrisis) {
    return {
      status: 'crisis_detected',
      citations: [],
      crisisData: safety,
    };
  }

  // 2. Privacy Consent Gate
  if (!optedIn) {
    return {
      status: 'consent_required',
      citations: [],
      groundedText:
        'Privacy Gate: Echo Journal strictly forbids sending journal text to external reflection models without explicit consent. You can enable this feature under Account Settings at any time.',
    };
  }

  // 3. Hybrid Retrieval
  const retriever = new HybridRetrieverClient(userEntries);
  const hits = retriever.search(query, 3);

  if (hits.length === 0) {
    return {
      status: 'insufficient_evidence',
      groundedText: 'There is not enough evidence in your recorded entries to reflect on this topic.',
      citations: [],
      uncertaintyNotice: 'Reflections require explicit textual evidence to maintain ground truth.',
    };
  }

  // 4. Citations & Grounded Synthesis
  const citations = hits.map(h => ({
    entryId: h.entry.id,
    title: h.entry.title,
    date: h.entry.createdAt.slice(0, 10),
    excerpt: h.entry.content.slice(0, 160) + (h.entry.content.length > 160 ? '...' : ''),
    relevanceScore: h.rrfScore,
    mood: h.entry.mood,
  }));

  const dates = citations.map(c => c.date).sort();
  const earliest = dates[0];
  const latest = dates[dates.length - 1];

  const excerptBullets = citations
    .map(c => `• [${c.date} — "${c.title}"] "${c.excerpt}" (Mood: ${c.mood || 'unrecorded'})`)
    .join('\n\n');

  const groundedText = `Based on your journal records between ${earliest} and ${latest}, here are the relevant reflections found:\n\n${excerptBullets}\n\nObservation: These retrieved entries reflect your thoughts and state at those times. This synthesis does not infer future events or hidden clinical meanings.`;

  return {
    status: 'success',
    groundedText,
    citations,
    uncertaintyNotice: `Synthesized strictly from ${citations.length} retrieved entries (${earliest} to ${latest}). Patterns represent recorded moments, not permanent diagnoses or causal relationships.`,
  };
}
