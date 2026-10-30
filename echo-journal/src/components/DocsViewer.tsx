import React, { useState } from 'react';
import { FileText, Shield, Cpu, ListCheck, BookOpen } from 'lucide-react';

interface DocItem {
  id: string;
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  content: string;
}

export const DocsViewer: React.FC = () => {
  const docs: DocItem[] = [
    {
      id: 'architecture',
      title: 'Architecture & System Design',
      subtitle: 'Flask Blueprints, Repository Pattern & Account Isolation',
      icon: <Cpu className="w-4 h-4" />,
      content: `# Architecture Documentation — Echo Journal

## 1. System Overview
Echo Journal uses a strict layered design:
- Client: HTML5 / Vanilla JS / Calm Archival styling
- Application: Flask application factory with Blueprints (auth, journal, account, insights, admin)
- Repository Layer: Abstract persistence interface with strictly isolated queries
- Storage Engine: SQLite (dev) / PostgreSQL (prod) via standard configuration
- ML Pipeline: PyTorch BiLSTM (6-class Ekman) + HuggingFace comparator

## 2. Strict Account Isolation (Rule 4)
- Every single query to journal tables takes user_id as an explicit argument.
- Cross-user lookups return 404 (None).
- Formally verified via tests/test_isolation.py (100% pass rate).

## 3. Cryptographic Invariants
- Password KDF: scrypt (N=16384, r=8, p=1, 16-byte random salt).
- Constant-time verification prevents side-channel timing attacks.
- CSRF: 32-byte cryptographically secure random token per session.
- Signed session cookies: HMAC-SHA256 with HttpOnly and SameSite=Lax.`,
    },
    {
      id: 'privacy',
      title: 'Privacy & Ethical Charter',
      subtitle: 'Non-diagnostic boundaries, zero external data leakage, crisis handling',
      icon: <Shield className="w-4 h-4" />,
      content: `# Privacy Policy & Ethical Charter — Echo Journal

## 1. Non-Diagnostic Medical Boundary (Rule 1)
Echo Journal is a self-reflection tool, NOT a diagnostic or medical system.
- Never diagnose mental health conditions.
- Never claim causation from journal patterns.
- Always use non-causal phrasing ("appears together", not "causes").

## 2. Server Boundary & External Opt-In (Rule 5)
- Default: 100% of journal text stays strictly on your local server.
- External AI features require explicit, revocable opt-in under Account Settings.
- When enabled, only the top retrieved relevant passages are forwarded to the model.

## 3. Crisis & Self-Harm Safety (app/safety.py)
If an entry or query indicates acute psychological crisis or self-harm:
- Generative AI inference is immediately suppressed.
- Supportive, verified 24/7 crisis helplines are surfaced (e.g. 988 Lifeline, Samaritans, Tele-MANAS).`,
    },
    {
      id: 'model_card',
      title: 'Model Card & ML Specs',
      subtitle: 'BiLSTM 6-class classifier, GoEmotions mapping, held-out evaluation',
      icon: <BookOpen className="w-4 h-4" />,
      content: `# Model Card — Echo Journal Emotion Classifier

## Model Overview
- Architecture: Tokenizer -> Vocab (Train Split) -> GloVe-initialized Embedding -> BiLSTM (2-layer, 128 hidden) -> Dropout (0.3) -> Linear (6)
- Target Classes: sadness, joy, love, anger, fear, surprise
- Baseline Comparator: j-hartmann/emotion-english-distilroberta-base

## Data Mapping & Taxonomy
- Source: GoEmotions (Reddit comments mapped to 6 Ekman classes)
- Held-out evaluation set: 100+ long-form journal entries annotated by group members
- Honest reporting: Model is reported as "in progress" until trained in Milestone 2B.`,
    },
    {
      id: 'milestones',
      title: 'Milestones Roadmap',
      subtitle: 'Status table for Milestone 1 through 6',
      icon: <ListCheck className="w-4 h-4" />,
      content: `# Project Milestones Tracker

- Milestone 1: Private Journaling Foundation [COMPLETED — 17 Tests Passing]
- Milestone 2: Pretrained Emotion & Sentiment Analysis (Local RoBERTa) [In Progress]
- Milestone 2B: Custom BiLSTM Emotion Classifier & Reports [In Progress]
- Milestone 3: Memory, Semantic Search & 'Ask your journal' [In Progress]
- Milestone 4: Admin Dashboard (Aggregate Only) [In Progress]
- Milestone 5: GitHub Submission & CI Workflow [In Progress]
- Milestone 6: Production Hardening & Deployment [In Progress]`,
    },
  ];

  const [selectedId, setSelectedId] = useState<string>('architecture');
  const activeDoc = docs.find(d => d.id === selectedId) || docs[0];

  return (
    <div className="max-w-4xl mx-auto bg-white border border-stone-200 rounded-lg overflow-hidden shadow-xs">
      <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-stone-200">
        {/* Navigation Sidebar */}
        <div className="p-4 bg-[#faf9f5] space-y-1">
          <div className="text-xs uppercase tracking-wider text-stone-500 font-mono px-3 py-2">
            Technical Documents
          </div>
          {docs.map(doc => (
            <button
              key={doc.id}
              onClick={() => setSelectedId(doc.id)}
              className={`w-full text-left p-3 rounded text-xs transition-colors flex items-start gap-2.5 ${
                selectedId === doc.id
                  ? 'bg-white shadow-xs font-semibold text-stone-900 border border-stone-200'
                  : 'text-stone-600 hover:text-stone-900 hover:bg-stone-100/60'
              }`}
            >
              <div className="mt-0.5 text-stone-700">{doc.icon}</div>
              <div>
                <div>{doc.title}</div>
                <div className="text-[11px] text-stone-400 font-normal line-clamp-1">{doc.subtitle}</div>
              </div>
            </button>
          ))}
        </div>

        {/* Content Viewport */}
        <div className="p-6 md:col-span-2 overflow-y-auto max-h-[600px]">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-stone-100">
            {activeDoc.icon}
            <h2 className="text-lg font-serif font-semibold text-stone-900">{activeDoc.title}</h2>
          </div>
          <pre className="font-mono text-xs text-stone-700 whitespace-pre-wrap leading-relaxed bg-[#fbf9f5] p-4 rounded border border-stone-200">
            {activeDoc.content}
          </pre>
        </div>
      </div>
    </div>
  );
};
