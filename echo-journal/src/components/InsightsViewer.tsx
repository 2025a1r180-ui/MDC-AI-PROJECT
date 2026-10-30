import React, { useState, useMemo } from 'react';
import { JournalEntry, User, StorageService } from '../storage';
import {
  analyzePatternsClient,
  answerGroundedQueryClient,
  GroundedQueryResponse,
  PatternAnalysisResult,
} from '../insightsClient';
import {
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  BookOpen,
  Calendar,
  Tag,
  ArrowRight,
  HelpCircle,
  TrendingUp,
  Brain,
  Lock,
  Layers,
  HeartPulse,
  PhoneCall,
  Info,
} from 'lucide-react';

interface InsightsViewerProps {
  currentUser: User;
  entries: JournalEntry[];
  onOpenEntry: (id: number) => void;
  onNavigateToSettings: () => void;
  onRefreshEntries: () => void;
}

export function InsightsViewer({
  currentUser,
  entries,
  onOpenEntry,
  onNavigateToSettings,
  onRefreshEntries,
}: InsightsViewerProps) {
  const [queryInput, setQueryInput] = useState<string>('');
  const [queryResponse, setQueryResponse] = useState<GroundedQueryResponse | null>(null);
  const [isQuerying, setIsQuerying] = useState<boolean>(false);

  // Compute pattern analysis
  const patternResult: PatternAnalysisResult = useMemo(() => {
    return analyzePatternsClient(entries);
  }, [entries]);

  const handleSeedTen = () => {
    StorageService.seedTenEntriesForUser(currentUser.id);
    onRefreshEntries();
  };

  const handleResetEntries = () => {
    StorageService.resetToDefaults();
    onRefreshEntries();
  };

  const handleRunQuery = (queryText: string) => {
    if (!queryText.trim()) return;
    setIsQuerying(true);
    setQueryInput(queryText);

    // Simulate standard prompt processing
    setTimeout(() => {
      const resp = answerGroundedQueryClient(queryText, entries, currentUser.optInExternalAi);
      setQueryResponse(resp);
      setIsQuerying(false);
    }, 250);
  };

  const sampleQuestions = [
    'What did I write about my college project?',
    'What did I note during my walks in nature?',
    'What stressed me out during study sessions?',
    'I want to end my life (Test Crisis Interceptor)',
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      {/* Page Header */}
      <div className="border-b border-stone-200 pb-5">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center space-x-2 text-stone-500 text-xs font-mono tracking-wider uppercase mb-1">
              <Brain className="w-4 h-4 text-emerald-600" />
              <span>Milestone 3 · Memory & Pattern Analytics</span>
            </div>
            <h1 className="text-2xl font-serif text-stone-800 tracking-tight">
              Personal Reflections & Patterns
            </h1>
            <p className="text-sm text-stone-600 mt-1">
              Grounded memory retrieval, longitudinal emotional trajectories, and non-causal self-reflections.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleSeedTen}
              className="text-xs px-3 py-1.5 border border-emerald-600 text-emerald-700 hover:bg-emerald-50 rounded transition-colors font-medium cursor-pointer"
              title="Loads 10 authenticated student study and reflection entries spanning 2 weeks"
            >
              Seed 10 Sample Entries
            </button>
            <button
              onClick={handleResetEntries}
              className="text-xs px-3 py-1.5 border border-stone-300 text-stone-600 hover:bg-stone-100 rounded transition-colors cursor-pointer"
            >
              Reset Archive
            </button>
          </div>
        </div>
      </div>

      {/* Non-Negotiable Medical Disclaimer */}
      <div className="bg-amber-50/70 border-l-4 border-amber-500 p-4 rounded-r text-xs text-amber-900 leading-relaxed flex items-start space-x-3">
        <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold">Non-Negotiable Rule 1 & 2:</span> Echo Journal is a self-reflection tool,
          <strong> NOT a medical or diagnostic system</strong>. It will never diagnose a condition, nor claim that
          one event in your life caused an emotional state. All patterns describe observed linguistic co-occurrence
          over time, backed by citations from your authentic entries.
        </div>
      </div>

      {/* Threshold Status Card */}
      {!patternResult.eligible ? (
        <div className="bg-white border border-stone-200 rounded-lg p-6 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
              Sample Size Invariant ({patternResult.entryCount} / {patternResult.requiredCount} entries)
            </span>
            <span className="text-xs text-stone-400 font-mono">Statistical Threshold Required</span>
          </div>
          <h2 className="text-base font-medium text-stone-800 mb-2">
            Longitudinal Pattern Analysis Requires 10 Entries
          </h2>
          <p className="text-sm text-stone-600 leading-relaxed mb-4">
            {patternResult.message}
          </p>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleSeedTen}
              className="text-xs px-3.5 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded font-medium transition-colors cursor-pointer"
            >
              Load 10 Authenticated Entries to Unlock
            </button>
            <span className="text-xs text-stone-500 italic">
              {patternResult.disclaimer}
            </span>
          </div>
        </div>
      ) : (
        /* Eligible Patterns Display */
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Emotion Distribution */}
            <div className="bg-white border border-stone-200 rounded-lg p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-stone-800">
                  Primary Emotion Trajectory
                </h3>
                <span className="text-xs font-mono text-stone-400">
                  {entries.length} entries analyzed
                </span>
              </div>
              <p className="text-xs text-stone-500 mb-4">
                Distribution of primary emotions identified across your authentic writing by the BiLSTM classifier.
              </p>

              <div className="space-y-2.5">
                {Object.entries(patternResult.emotionDistribution || {}).map(([emo, count]) => {
                  const pct = Math.round((count / entries.length) * 100);
                  return (
                    <div key={emo} className="space-y-1">
                      <div className="flex justify-between text-xs text-stone-700">
                        <span className="capitalize font-mono">{emo}</span>
                        <span className="font-mono text-stone-500">
                          {count} ({pct}%)
                        </span>
                      </div>
                      <div className="w-full h-2 bg-stone-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-stone-600 transition-all duration-300"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Observed Co-Occurrences (Non-Causal) */}
            <div className="bg-white border border-stone-200 rounded-lg p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-stone-800">
                  Observed Topic Co-Occurrences
                </h3>
                <span className="text-xs font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  Non-Causal
                </span>
              </div>
              <p className="text-xs text-stone-500 mb-4">
                Empirical associations between journal tags and emotion states.
              </p>

              <div className="space-y-3">
                {patternResult.coOccurrences && patternResult.coOccurrences.length > 0 ? (
                  patternResult.coOccurrences.map((co, idx) => (
                    <div
                      key={idx}
                      className="text-xs p-3 bg-stone-50 border border-stone-200 rounded leading-relaxed text-stone-700"
                    >
                      <div className="font-medium text-stone-800 mb-0.5 flex items-center space-x-1.5">
                        <Tag className="w-3.5 h-3.5 text-stone-500" />
                        <span>#{co.tag}</span>
                        <span className="text-stone-400 font-normal">· {co.percentage}% co-occurrence with {co.coOccurringEmotion}</span>
                      </div>
                      <p className="text-stone-600 mt-1 italic font-serif">
                        "{co.observation}"
                      </p>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-stone-400 italic">
                    Not enough recurring tags to form co-occurrence insights.
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Timeline Stream */}
          <div className="bg-white border border-stone-200 rounded-lg p-5 shadow-xs">
            <h3 className="text-sm font-medium text-stone-800 mb-2">
              Timeline Progression
            </h3>
            <p className="text-xs text-stone-500 mb-4">
              Chronological sequence of moods and analyzed emotions.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
              {patternResult.timelineTrend?.slice(-10).map(t => (
                <div
                  key={t.id}
                  onClick={() => onOpenEntry(t.id)}
                  className="p-2 border border-stone-200 hover:border-stone-400 rounded cursor-pointer transition-colors text-xs"
                >
                  <div className="font-mono text-stone-400 text-[10px]">{t.date}</div>
                  <div className="font-medium text-stone-800 truncate mt-0.5">{t.title}</div>
                  <div className="flex items-center justify-between mt-1 text-[11px] text-stone-500">
                    <span>Mood: {t.mood}</span>
                    <span className="capitalize font-mono text-stone-600">{t.primaryEmotion}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* "Ask Your Journal" — Conversational Grounded RAG Reflection */}
      <div className="bg-white border border-stone-200 rounded-lg p-6 shadow-xs space-y-5">
        <div className="flex items-center justify-between flex-wrap gap-3 border-b border-stone-100 pb-4">
          <div>
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-emerald-600" />
              <h2 className="text-base font-serif font-medium text-stone-800">
                Ask Your Journal
              </h2>
            </div>
            <p className="text-xs text-stone-500 mt-0.5">
              Reflective Q&A powered by BM25 + dense semantic hybrid retrieval. Every statement must cite its exact entry.
            </p>
          </div>

          {/* Privacy Consent Badge */}
          <div className="flex items-center space-x-2">
            {currentUser.optInExternalAi ? (
              <span className="inline-flex items-center space-x-1.5 text-xs text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded border border-emerald-200">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                <span>External AI Reflection Opted-In</span>
              </span>
            ) : (
              <span className="inline-flex items-center space-x-1.5 text-xs text-stone-600 bg-stone-100 px-2.5 py-1 rounded border border-stone-200">
                <Lock className="w-3.5 h-3.5 text-stone-500" />
                <span>Strict Local Storage (External AI Disabled)</span>
              </span>
            )}
          </div>
        </div>

        {/* Privacy Consent Notice if un-opted */}
        {!currentUser.optInExternalAi && (
          <div className="bg-stone-50 border border-stone-200 p-3.5 rounded text-xs text-stone-600 flex items-start justify-between">
            <div>
              <span className="font-semibold text-stone-800">Privacy Gate Active:</span> In accordance with
              Non-Negotiable Rule 5, no journal text leaves your local machine unless you explicitly opt in.
            </div>
            <button
              onClick={onNavigateToSettings}
              className="text-emerald-700 hover:text-emerald-900 underline font-medium ml-3 shrink-0 cursor-pointer"
            >
              Account Settings
            </button>
          </div>
        )}

        {/* Query Form */}
        <div className="space-y-3">
          <div className="flex gap-2">
            <input
              type="text"
              value={queryInput}
              onChange={e => setQueryInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter') handleRunQuery(queryInput);
              }}
              placeholder="e.g. What did I write about my college project?"
              className="flex-1 px-3.5 py-2 text-sm border border-stone-300 rounded focus:outline-none focus:ring-1 focus:ring-stone-600"
            />
            <button
              onClick={() => handleRunQuery(queryInput)}
              disabled={isQuerying || !queryInput.trim()}
              className="px-4 py-2 bg-stone-800 hover:bg-stone-900 text-white text-xs font-medium rounded transition-colors disabled:opacity-50 cursor-pointer"
            >
              {isQuerying ? 'Searching...' : 'Reflect'}
            </button>
          </div>

          {/* Quick Prompts */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[11px] text-stone-400">Try asking:</span>
            {sampleQuestions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleRunQuery(q)}
                className={`text-[11px] px-2 py-1 rounded border transition-colors cursor-pointer ${
                  q.includes('Crisis')
                    ? 'border-red-200 text-red-700 hover:bg-red-50 bg-red-50/30'
                    : 'border-stone-200 text-stone-600 hover:bg-stone-50'
                }`}
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Query Output Display */}
        {queryResponse && (
          <div className="mt-4 pt-4 border-t border-stone-100 space-y-4">
            {/* Status: Crisis Interceptor Activated */}
            {queryResponse.status === 'crisis_detected' && queryResponse.crisisData && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-5 space-y-4">
                <div className="flex items-center space-x-2 text-red-800 font-semibold text-sm">
                  <HeartPulse className="w-5 h-5 text-red-600" />
                  <span>Support & Crisis Assistance</span>
                </div>
                <p className="text-xs text-red-900 leading-relaxed">
                  {queryResponse.crisisData.message}
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  {Object.entries(queryResponse.crisisData.helplines || {}).map(([region, help]) => (
                    <div
                      key={region}
                      className="bg-white p-3 border border-red-200 rounded shadow-2xs space-y-1"
                    >
                      <div className="font-semibold text-stone-800">{help.service}</div>
                      <div className="text-red-700 font-mono font-medium flex items-center space-x-1">
                        <PhoneCall className="w-3.5 h-3.5" />
                        <span>{help.contact}</span>
                      </div>
                      <div className="text-stone-500 text-[11px]">{help.availability}</div>
                    </div>
                  ))}
                </div>
                <p className="text-[11px] text-stone-500 italic">
                  {queryResponse.crisisData.disclaimer}
                </p>
              </div>
            )}

            {/* Status: Consent Required */}
            {queryResponse.status === 'consent_required' && (
              <div className="bg-amber-50 border border-amber-200 rounded p-4 text-xs text-amber-900 space-y-2">
                <div className="font-semibold flex items-center space-x-1.5">
                  <Lock className="w-4 h-4 text-amber-600" />
                  <span>External AI Consent Required</span>
                </div>
                <p>{queryResponse.groundedText}</p>
                <button
                  onClick={onNavigateToSettings}
                  className="mt-1 inline-flex items-center space-x-1 text-xs text-emerald-800 hover:text-emerald-950 underline font-medium cursor-pointer"
                >
                  <span>Go to Account Settings to enable AI Reflection</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            )}

            {/* Status: Insufficient Evidence */}
            {queryResponse.status === 'insufficient_evidence' && (
              <div className="bg-stone-50 border border-stone-200 rounded p-4 text-xs text-stone-700 space-y-1">
                <div className="font-semibold text-stone-800">No Ground Truth Found</div>
                <p>{queryResponse.groundedText}</p>
                <div className="text-stone-400 text-[11px] italic">
                  {queryResponse.uncertaintyNotice}
                </div>
              </div>
            )}

            {/* Status: Success (Grounded Synthesis + Citations) */}
            {queryResponse.status === 'success' && (
              <div className="space-y-4">
                {/* Synthesis Box */}
                <div className="bg-stone-50 border border-stone-200 rounded-lg p-5">
                  <div className="flex items-center justify-between text-xs text-stone-500 mb-2 font-mono">
                    <span>Grounded Reflection Synthesis</span>
                    <span>{queryResponse.citations.length} Citations Used</span>
                  </div>
                  <p className="text-sm font-serif text-stone-800 whitespace-pre-line leading-relaxed">
                    {queryResponse.groundedText}
                  </p>
                </div>

                {/* Uncertainty Notice */}
                {queryResponse.uncertaintyNotice && (
                  <div className="text-xs text-stone-500 italic bg-amber-50/50 border border-amber-100 p-2.5 rounded">
                    <strong>Confidence & Scope Notice:</strong> {queryResponse.uncertaintyNotice}
                  </div>
                )}

                {/* Evidence Citations Cards */}
                <div className="space-y-2">
                  <h4 className="text-xs font-mono uppercase tracking-wider text-stone-500">
                    Retrieved Evidence Citations ({queryResponse.citations.length})
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {queryResponse.citations.map((c, i) => (
                      <div
                        key={i}
                        onClick={() => onOpenEntry(c.entryId)}
                        className="bg-white border border-stone-200 hover:border-stone-400 p-3 rounded cursor-pointer transition-colors text-xs flex flex-col justify-between"
                      >
                        <div>
                          <div className="flex items-center justify-between text-stone-400 text-[10px] font-mono mb-1">
                            <span>{c.date}</span>
                            <span>Score: {c.relevanceScore}</span>
                          </div>
                          <div className="font-medium text-stone-800 line-clamp-1 mb-1">
                            {c.title}
                          </div>
                          <p className="text-stone-600 line-clamp-3 italic font-serif text-[11px]">
                            "{c.excerpt}"
                          </p>
                        </div>
                        <div className="mt-2 text-[10px] text-emerald-700 flex items-center space-x-1 font-medium">
                          <span>View Entry</span>
                          <ArrowRight className="w-2.5 h-2.5" />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
