import { AnalysisPayload } from './mlClient';

export interface User {
  id: number;
  username: string;
  email: string;
  passwordHash: string;
  role: string;
  optInExternalAi: boolean;
  createdAt: string;
}

export interface JournalEntry {
  id: number;
  userId: number;
  title: string;
  content: string;
  mood: string | null;
  tags: string[];
  wordCount: number;
  readingTimeMinutes: number;
  analysis?: AnalysisPayload | Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

const STORAGE_USERS_KEY = 'echo_journal_users_v1';
const STORAGE_ENTRIES_KEY = 'echo_journal_entries_v1';

// Seed data demonstrating account isolation
const INITIAL_USERS: User[] = [
  {
    id: 1,
    username: 'maya',
    email: 'maya@example.com',
    passwordHash: 'scrypt$16384$8$1$7f92a34c9103e5ba1c9018471209acbf$e481b9e02c011928471902847192847192048102948192048102948102948102',
    role: 'user',
    optInExternalAi: false,
    createdAt: '2026-10-28 09:15:00',
  },
  {
    id: 2,
    username: 'alex',
    email: 'alex@example.com',
    passwordHash: 'scrypt$16384$8$1$2b83a74c9103e5ba1c9018471209acbf$a192b8e02c011928471902847192847192048102948192048102948102948102',
    role: 'user',
    optInExternalAi: false,
    createdAt: '2026-10-29 11:20:00',
  },
];

const INITIAL_ENTRIES: JournalEntry[] = [
  {
    id: 101,
    userId: 1, // Maya
    title: "Maya's Field Notes on Quantum Cryptography",
    content: "Spent three hours in the campus library reading about lattice-based cryptography and post-quantum security. The symmetry between algebraic rings and geometric nearest-vector problems is astonishing. Feeling energized about our college research paper.",
    mood: 'reflective',
    tags: ['research', 'college', 'security'],
    wordCount: 38,
    readingTimeMinutes: 1,
    createdAt: '2026-10-29 14:30:00',
    updatedAt: '2026-10-29 14:30:00',
  },
  {
    id: 102,
    userId: 1, // Maya
    title: 'Morning Forest Walk',
    content: 'Crisp morning air along the campus pine trail. Took ten minutes to simply sit by the stone bench and listen to the wind. Reminded myself that steady progress is more sustainable than frantic late-night sprints.',
    mood: 'calm',
    tags: ['nature', 'morning', 'mindfulness'],
    wordCount: 37,
    readingTimeMinutes: 1,
    createdAt: '2026-10-30 08:00:00',
    updatedAt: '2026-10-30 08:00:00',
  },
  {
    id: 201,
    userId: 2, // Alex
    title: "Alex's Exam Preparation & Midterm Anxiety",
    content: 'Reviewing database normalization forms (1NF through BCNF) and concurrency locks. Feeling overwhelmed with the volume of material, but breaking study sessions into 25-minute Pomodoro cycles helped restore focus.',
    mood: 'anxious',
    tags: ['exam', 'databases', 'study'],
    wordCount: 33,
    readingTimeMinutes: 1,
    createdAt: '2026-10-29 16:45:00',
    updatedAt: '2026-10-29 16:45:00',
  },
  {
    id: 202,
    userId: 2, // Alex
    title: 'Evening Meditation and Tea',
    content: 'Chamomile tea and twenty minutes of breath meditation after dinner. The tightness in my shoulders is slowly easing. Ready for a good night of rest.',
    mood: 'calm',
    tags: ['meditation', 'evening'],
    wordCount: 28,
    readingTimeMinutes: 1,
    createdAt: '2026-10-29 21:30:00',
    updatedAt: '2026-10-29 21:30:00',
  },
];

export class StorageService {
  private static loadUsers(): User[] {
    const raw = localStorage.getItem(STORAGE_USERS_KEY);
    if (!raw) {
      localStorage.setItem(STORAGE_USERS_KEY, JSON.stringify(INITIAL_USERS));
      return INITIAL_USERS;
    }
    try {
      return JSON.parse(raw);
    } catch {
      return INITIAL_USERS;
    }
  }

  private static saveUsers(users: User[]): void {
    localStorage.setItem(STORAGE_USERS_KEY, JSON.stringify(users));
  }

  private static loadEntries(): JournalEntry[] {
    const raw = localStorage.getItem(STORAGE_ENTRIES_KEY);
    if (!raw) {
      localStorage.setItem(STORAGE_ENTRIES_KEY, JSON.stringify(INITIAL_ENTRIES));
      return INITIAL_ENTRIES;
    }
    try {
      return JSON.parse(raw);
    } catch {
      return INITIAL_ENTRIES;
    }
  }

  private static saveEntries(entries: JournalEntry[]): void {
    localStorage.setItem(STORAGE_ENTRIES_KEY, JSON.stringify(entries));
  }

  // --- User Repository ---
  static getUsers(): User[] {
    return this.loadUsers();
  }

  static getUserById(id: number): User | null {
    return this.loadUsers().find(u => u.id === id) || null;
  }

  static getUserByEmail(email: string): User | null {
    return this.loadUsers().find(u => u.email.toLowerCase() === email.toLowerCase().trim()) || null;
  }

  static getUserByUsername(username: string): User | null {
    return this.loadUsers().find(u => u.username.toLowerCase() === username.toLowerCase().trim()) || null;
  }

  static createUser(username: string, email: string, passwordHash: string): User {
    const users = this.loadUsers();
    const newUser: User = {
      id: Date.now(),
      username: username.trim(),
      email: email.trim().toLowerCase(),
      passwordHash,
      role: 'user',
      optInExternalAi: false,
      createdAt: new Date().toISOString().replace('T', ' ').slice(0, 19),
    };
    users.push(newUser);
    this.saveUsers(users);
    return newUser;
  }

  static setAiOptIn(userId: number, optIn: boolean): void {
    const users = this.loadUsers();
    const idx = users.findIndex(u => u.id === userId);
    if (idx !== -1) {
      users[idx].optInExternalAi = optIn;
      this.saveUsers(users);
    }
  }

  static deleteAccount(userId: number): boolean {
    const users = this.loadUsers().filter(u => u.id !== userId);
    this.saveUsers(users);
    // Cascade delete all entries
    const entries = this.loadEntries().filter(e => e.userId !== userId);
    this.saveEntries(entries);
    return true;
  }

  // --- Journal Repository (Strict Account Isolation) ---
  static getUserEntries(
    userId: number,
    mood?: string | null,
    tag?: string | null,
    searchQuery?: string | null
  ): JournalEntry[] {
    let entries = this.loadEntries().filter(e => e.userId === userId);

    if (mood && mood !== 'all') {
      entries = entries.filter(e => e.mood?.toLowerCase() === mood.toLowerCase());
    }

    if (tag) {
      const cleanTag = tag.toLowerCase().replace(/^#/, '');
      entries = entries.filter(e => e.tags.some(t => t.toLowerCase() === cleanTag));
    }

    if (searchQuery && searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      entries = entries.filter(
        e =>
          e.title.toLowerCase().includes(q) ||
          e.content.toLowerCase().includes(q) ||
          e.tags.some(t => t.toLowerCase().includes(q))
      );
    }

    return entries.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
  }

  static getEntry(entryId: number, userId: number): JournalEntry | null {
    // Strictly requires both entryId AND userId
    return this.loadEntries().find(e => e.id === entryId && e.userId === userId) || null;
  }

  static createEntry(
    userId: number,
    title: string,
    content: string,
    mood?: string | null,
    tags?: string[]
  ): JournalEntry {
    const entries = this.loadEntries();
    const words = content.trim().split(/\s+/).filter(Boolean).length;
    const readingTime = Math.max(1, Math.round(words / 200));

    const newEntry: JournalEntry = {
      id: Date.now(),
      userId,
      title: title.trim(),
      content: content.trim(),
      mood: mood ? mood.toLowerCase() : null,
      tags: tags ? Array.from(new Set(tags.map(t => t.toLowerCase().trim()).filter(Boolean))) : [],
      wordCount: words,
      readingTimeMinutes: readingTime,
      createdAt: new Date().toISOString().replace('T', ' ').slice(0, 19),
      updatedAt: new Date().toISOString().replace('T', ' ').slice(0, 19),
    };

    entries.push(newEntry);
    this.saveEntries(entries);
    return newEntry;
  }

  static updateEntry(
    entryId: number,
    userId: number,
    title: string,
    content: string,
    mood?: string | null,
    tags?: string[]
  ): boolean {
    const entries = this.loadEntries();
    const idx = entries.findIndex(e => e.id === entryId && e.userId === userId);
    if (idx === -1) return false;

    const words = content.trim().split(/\s+/).filter(Boolean).length;
    const readingTime = Math.max(1, Math.round(words / 200));

    entries[idx] = {
      ...entries[idx],
      title: title.trim(),
      content: content.trim(),
      mood: mood ? mood.toLowerCase() : null,
      tags: tags ? Array.from(new Set(tags.map(t => t.toLowerCase().trim()).filter(Boolean))) : [],
      wordCount: words,
      readingTimeMinutes: readingTime,
      updatedAt: new Date().toISOString().replace('T', ' ').slice(0, 19),
    };

    this.saveEntries(entries);
    return true;
  }

  static saveEntryAnalysis(
    entryId: number,
    userId: number,
    analysis: AnalysisPayload
  ): boolean {
    const entries = this.loadEntries();
    const idx = entries.findIndex(e => e.id === entryId && e.userId === userId);
    if (idx === -1) return false;

    entries[idx] = {
      ...entries[idx],
      analysis,
      updatedAt: new Date().toISOString().replace('T', ' ').slice(0, 19),
    };

    this.saveEntries(entries);
    return true;
  }

  static deleteEntry(entryId: number, userId: number): boolean {
    const entries = this.loadEntries();
    const initialLen = entries.length;
    const filtered = entries.filter(e => !(e.id === entryId && e.userId === userId));
    if (filtered.length === initialLen) return false;
    this.saveEntries(filtered);
    return true;
  }

  static exportJson(userId: number): string {
    const entries = this.getUserEntries(userId);
    return JSON.stringify(
      {
        exportedAt: new Date().toISOString(),
        userId,
        totalEntries: entries.length,
        entries,
      },
      null,
      2
    );
  }

  static exportMarkdown(userId: number): string {
    const entries = this.getUserEntries(userId);
    let md = `# Echo Journal Archive\n`;
    md += `Exported: ${new Date().toISOString()}\n`;
    md += `Total Entries: ${entries.length}\n\n---\n\n`;

    for (const e of entries) {
      const tagStr = e.tags.map(t => `#${t}`).join(' ');
      md += `## ${e.title}\n`;
      md += `**Date:** ${e.createdAt}  \n`;
      md += `**Mood:** ${e.mood || 'Unspecified'}  \n`;
      md += `**Tags:** ${tagStr || 'None'}  \n`;
      md += `**Word Count:** ${e.wordCount} words (${e.readingTimeMinutes} min read)  \n\n`;
      md += `${e.content}\n\n---\n\n`;
    }
    return md;
  }

  static resetToDefaults(): void {
    localStorage.setItem(STORAGE_USERS_KEY, JSON.stringify(INITIAL_USERS));
    localStorage.setItem(STORAGE_ENTRIES_KEY, JSON.stringify(INITIAL_ENTRIES));
  }

  static seedTenEntriesForUser(userId: number): JournalEntry[] {
    const sampleEntries: Omit<JournalEntry, 'id' | 'userId'>[] = [
      {
        title: "Campus Library Quantum Lattice Notes",
        content: "Spent three hours studying shortest-vector algorithms and lattice cryptography in the university library. The mathematical elegance of n-dimensional torus spaces was deeply invigorating. Feeling focused and confident about our group semester project.",
        mood: "reflective",
        tags: ["college", "research", "math"],
        wordCount: 39,
        readingTimeMinutes: 1,
        analysis: {
          status: "completed",
          primary_emotion: "joy",
          emotion_scores: { sadness: 0.04, joy: 0.72, love: 0.12, anger: 0.02, fear: 0.04, surprise: 0.06 },
          sentiment_label: "positive",
          sentiment_score: 0.88,
          model_name: "EchoJournal-BiLSTM-Ekman6",
          model_version: "2.1.0-weighted-bilstm",
          uncertainty_notice: "Emotion predictions reflect statistical text patterns, not medical states.",
          analyzed_at: "2026-10-14 11:30:00",
        },
        createdAt: "2026-10-14 11:30:00",
        updatedAt: "2026-10-14 11:30:00",
      },
      {
        title: "Morning Run Through South Woods",
        content: "Crisp autumn morning along the pine trails. The leaves are brilliant amber. Felt calm, grounded, and ready for whatever the engineering lab throws at me today.",
        mood: "calm",
        tags: ["nature", "morning", "mindfulness"],
        wordCount: 31,
        readingTimeMinutes: 1,
        analysis: {
          status: "completed",
          primary_emotion: "joy",
          emotion_scores: { sadness: 0.02, joy: 0.81, love: 0.08, anger: 0.01, fear: 0.03, surprise: 0.05 },
          sentiment_label: "positive",
          sentiment_score: 0.92,
          model_name: "EchoJournal-BiLSTM-Ekman6",
          model_version: "2.1.0-weighted-bilstm",
          uncertainty_notice: "Emotion predictions reflect statistical text patterns, not medical states.",
          analyzed_at: "2026-10-16 08:15:00",
        },
        createdAt: "2026-10-16 08:15:00",
        updatedAt: "2026-10-16 08:15:00",
      },
      {
        title: "Debugging Asynchronous WebSocket Handshake",
        content: "Ran into a race condition during client reconnection. Paced the dorm hallway trying to untangle why the state was dropped. Feeling somewhat frustrated, but stepping away for fifteen minutes helped locate the missing lock.",
        mood: "frustrated",
        tags: ["college", "coding", "study"],
        wordCount: 36,
        readingTimeMinutes: 1,
        analysis: {
          status: "completed",
          primary_emotion: "anger",
          emotion_scores: { sadness: 0.14, joy: 0.08, love: 0.02, anger: 0.65, fear: 0.07, surprise: 0.04 },
          sentiment_label: "negative",
          sentiment_score: 0.61,
          model_name: "EchoJournal-BiLSTM-Ekman6",
          model_version: "2.1.0-weighted-bilstm",
          uncertainty_notice: "Emotion predictions reflect statistical text patterns, not medical states.",
          analyzed_at: "2026-10-18 19:40:00",
        },
        createdAt: "2026-10-18 19:40:00",
        updatedAt: "2026-10-18 19:40:00",
      },
      {
        title: "Late Night Discrete Math Review",
        content: "Working through combinatorics generating functions until 2 AM. My eyes were burning and I started doubting whether I grasped the Catalan numbers proof. Feeling anxious about the upcoming midterm exam.",
        mood: "anxious",
        tags: ["college", "study", "exam"],
        wordCount: 35,
        readingTimeMinutes: 1,
        analysis: {
          status: "completed",
          primary_emotion: "fear",
          emotion_scores: { sadness: 0.18, joy: 0.03, love: 0.01, anger: 0.05, fear: 0.68, surprise: 0.05 },
          sentiment_label: "negative",
          sentiment_score: 0.73,
          model_name: "EchoJournal-BiLSTM-Ekman6",
          model_version: "2.1.0-weighted-bilstm",
          uncertainty_notice: "Emotion predictions reflect statistical text patterns, not medical states.",
          analyzed_at: "2026-10-20 02:15:00",
        },
        createdAt: "2026-10-20 02:15:00",
        updatedAt: "2026-10-20 02:15:00",
      },
      {
        title: "Tea and Listening to Rain",
        content: "A gentle autumn downpour outside the dorm window. Boiled peppermint tea and watched the raindrops stream down the glass. No laptop, no notifications. Just quiet breathing.",
        mood: "calm",
        tags: ["mindfulness", "evening", "rest"],
        wordCount: 29,
        readingTimeMinutes: 1,
        analysis: {
          status: "completed",
          primary_emotion: "joy",
          emotion_scores: { sadness: 0.06, joy: 0.64, love: 0.22, anger: 0.01, fear: 0.02, surprise: 0.05 },
          sentiment_label: "positive",
          sentiment_score: 0.84,
          model_name: "EchoJournal-BiLSTM-Ekman6",
          model_version: "2.1.0-weighted-bilstm",
          uncertainty_notice: "Emotion predictions reflect statistical text patterns, not medical states.",
          analyzed_at: "2026-10-21 21:00:00",
        },
        createdAt: "2026-10-21 21:00:00",
        updatedAt: "2026-10-21 21:00:00",
      },
      {
        title: "Peer Code Review Session",
        content: "Alex and I walked through each other's pull requests today. Discovered a subtle memory leak in the buffer pool. It was rewarding to see how our separate components fit together seamlessly.",
        mood: "reflective",
        tags: ["college", "collaboration", "coding"],
        wordCount: 34,
        readingTimeMinutes: 1,
        analysis: {
          status: "completed",
          primary_emotion: "joy",
          emotion_scores: { sadness: 0.05, joy: 0.74, love: 0.12, anger: 0.02, fear: 0.03, surprise: 0.04 },
          sentiment_label: "positive",
          sentiment_score: 0.89,
          model_name: "EchoJournal-BiLSTM-Ekman6",
          model_version: "2.1.0-weighted-bilstm",
          uncertainty_notice: "Emotion predictions reflect statistical text patterns, not medical states.",
          analyzed_at: "2026-10-23 15:20:00",
        },
        createdAt: "2026-10-23 15:20:00",
        updatedAt: "2026-10-23 15:20:00",
      },
      {
        title: "Midterm Study Fatigue",
        content: "Another six-hour stretch at the wooden desks. Memory is feeling overloaded. Kept mixing up B-tree indexing formulas with hash indexing. A bit demoralized, but I know rest will help consolidate it.",
        mood: "tired",
        tags: ["study", "exam", "college"],
        wordCount: 34,
        readingTimeMinutes: 1,
        analysis: {
          status: "completed",
          primary_emotion: "sadness",
          emotion_scores: { sadness: 0.69, joy: 0.05, love: 0.02, anger: 0.08, fear: 0.12, surprise: 0.04 },
          sentiment_label: "negative",
          sentiment_score: 0.65,
          model_name: "EchoJournal-BiLSTM-Ekman6",
          model_version: "2.1.0-weighted-bilstm",
          uncertainty_notice: "Emotion predictions reflect statistical text patterns, not medical states.",
          analyzed_at: "2026-10-25 18:30:00",
        },
        createdAt: "2026-10-25 18:30:00",
        updatedAt: "2026-10-25 18:30:00",
      },
      {
        title: "Campus Botanical Garden Visit",
        content: "Spent an hour wandering between the fern greenhouse and the succulent conservatory. The earthy smell of moist soil and leaves instantly lowered my shoulders. Nature always brings perspective.",
        mood: "calm",
        tags: ["nature", "mindfulness", "rest"],
        wordCount: 31,
        readingTimeMinutes: 1,
        analysis: {
          status: "completed",
          primary_emotion: "joy",
          emotion_scores: { sadness: 0.03, joy: 0.78, love: 0.14, anger: 0.01, fear: 0.01, surprise: 0.03 },
          sentiment_label: "positive",
          sentiment_score: 0.91,
          model_name: "EchoJournal-BiLSTM-Ekman6",
          model_version: "2.1.0-weighted-bilstm",
          uncertainty_notice: "Emotion predictions reflect statistical text patterns, not medical states.",
          analyzed_at: "2026-10-27 14:00:00",
        },
        createdAt: "2026-10-27 14:00:00",
        updatedAt: "2026-10-27 14:00:00",
      },
      {
        title: "Completed Milestone 2 ML Model Training",
        content: "Our BiLSTM model completed 15 training epochs on CUDA! Macro-F1 reached 78.9% on the held-out student journal test set, beating the pretrained baseline. Ecstatic to see our ML pipeline succeed.",
        mood: "joyful",
        tags: ["college", "ml", "milestone"],
        wordCount: 35,
        readingTimeMinutes: 1,
        analysis: {
          status: "completed",
          primary_emotion: "joy",
          emotion_scores: { sadness: 0.01, joy: 0.91, love: 0.04, anger: 0.01, fear: 0.01, surprise: 0.02 },
          sentiment_label: "positive",
          sentiment_score: 0.96,
          model_name: "EchoJournal-BiLSTM-Ekman6",
          model_version: "2.1.0-weighted-bilstm",
          uncertainty_notice: "Emotion predictions reflect statistical text patterns, not medical states.",
          analyzed_at: "2026-10-29 20:00:00",
        },
        createdAt: "2026-10-29 20:00:00",
        updatedAt: "2026-10-29 20:00:00",
      },
      {
        title: "End of Week Reflection on Balance",
        content: "Reflecting on the rhythm of the past two weeks. The high intensity of study sessions alongside the quiet walks in the woods. Learning to accept that stress and flow coexist.",
        mood: "reflective",
        tags: ["mindfulness", "college", "reflection"],
        wordCount: 33,
        readingTimeMinutes: 1,
        analysis: {
          status: "completed",
          primary_emotion: "joy",
          emotion_scores: { sadness: 0.07, joy: 0.65, love: 0.18, anger: 0.02, fear: 0.03, surprise: 0.05 },
          sentiment_label: "positive",
          sentiment_score: 0.85,
          model_name: "EchoJournal-BiLSTM-Ekman6",
          model_version: "2.1.0-weighted-bilstm",
          uncertainty_notice: "Emotion predictions reflect statistical text patterns, not medical states.",
          analyzed_at: "2026-10-30 09:00:00",
        },
        createdAt: "2026-10-30 09:00:00",
        updatedAt: "2026-10-30 09:00:00",
      },
    ];

    const currentEntries = this.loadEntries();
    // Remove existing entries for this user
    const otherEntries = currentEntries.filter(e => e.userId !== userId);
    
    let nextId = Date.now();
    const newEntries: JournalEntry[] = sampleEntries.map(s => ({
      ...s,
      id: nextId++,
      userId,
    }));

    const updated = [...otherEntries, ...newEntries];
    this.saveEntries(updated);
    return newEntries;
  }
}
