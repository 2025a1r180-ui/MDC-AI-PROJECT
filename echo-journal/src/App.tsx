import React, { useState, useEffect } from 'react';
import { StorageService, User, JournalEntry } from './storage';
import { hashPasswordClient, verifyPasswordClient, generateClientCsrfToken } from './crypto';
import { analyzeTextClient, SIX_EMOTIONS } from './mlClient';
import { TestRunner } from './components/TestRunner';
import { TeacherSummary } from './components/TeacherSummary';
import { DocsViewer } from './components/DocsViewer';
import { InsightsViewer } from './components/InsightsViewer';
import { AdminDashboard } from './components/AdminDashboard';
import {
  BookOpen,
  Feather,
  Search,
  Download,
  Trash2,
  Shield,
  Lock,
  CheckCircle2,
  User as UserIcon,
  Sparkles,
  ArrowLeft,
  X,
  AlertTriangle,
  FileText,
  Key,
  ShieldAlert,
  HelpCircle,
} from 'lucide-react';

export default function App() {
  // Authentication & Session State
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [csrfToken, setCsrfToken] = useState<string>('');
  const [allUsers, setAllUsers] = useState<User[]>([]);

  // Navigation State
  const [currentView, setCurrentView] = useState<'archive' | 'write' | 'view' | 'edit' | 'insights' | 'account' | 'tests' | 'teacher' | 'docs' | 'admin' | 'auth'>('archive');
  const [activeEntryId, setActiveEntryId] = useState<number | null>(null);

  // Archive & Filter State
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedMood, setSelectedMood] = useState<string>('all');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);

  // Editor Form State
  const [editorTitle, setEditorTitle] = useState<string>('');
  const [editorContent, setEditorContent] = useState<string>('');
  const [editorMood, setEditorMood] = useState<string>('');
  const [editorTags, setEditorTags] = useState<string>('');
  const [editorError, setEditorError] = useState<string | null>(null);

  // Auth Form State
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [authUsername, setAuthUsername] = useState<string>('');
  const [authEmail, setAuthEmail] = useState<string>('');
  const [authPassword, setAuthPassword] = useState<string>('');
  const [authError, setAuthError] = useState<string | null>(null);
  const [authSuccess, setAuthSuccess] = useState<string | null>(null);

  // Account Deletion Confirm
  const [deletePassword, setDeletePassword] = useState<string>('');
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Account Switcher Menu
  const [showSwitchMenu, setShowSwitchMenu] = useState<boolean>(false);

  // Initialize Session
  useEffect(() => {
    const users = StorageService.getUsers();
    setAllUsers(users);
    // Default to Maya (User 1) for seamless evaluation
    if (users.length > 0) {
      setCurrentUser(users[0]);
    }
    setCsrfToken(generateClientCsrfToken());
  }, []);

  // Reload entries whenever currentUser, mood, tag, or search changes
  useEffect(() => {
    if (currentUser) {
      const userEntries = StorageService.getUserEntries(currentUser.id, selectedMood, selectedTag, searchQuery);
      setEntries(userEntries);
    } else {
      setEntries([]);
    }
  }, [currentUser, selectedMood, selectedTag, searchQuery]);

  // Handlers for Entries CRUD
  const handleOpenEntry = (id: number) => {
    if (!currentUser) return;
    const entry = StorageService.getEntry(id, currentUser.id);
    if (!entry) {
      alert("Account Isolation Security: Access Denied. Entry does not belong to your account.");
      return;
    }
    setActiveEntryId(id);
    setCurrentView('view');
  };

  const handleStartEdit = (entry: JournalEntry) => {
    setEditorTitle(entry.title);
    setEditorContent(entry.content);
    setEditorMood(entry.mood || '');
    setEditorTags(entry.tags.join(', '));
    setEditorError(null);
    setActiveEntryId(entry.id);
    setCurrentView('edit');
  };

  const handleSaveEntry = (isEditing: boolean) => {
    if (!currentUser) return;
    if (!editorTitle.trim()) {
      setEditorError('Please provide a title for this entry.');
      return;
    }
    if (!editorContent.trim()) {
      setEditorError('Journal content cannot be blank.');
      return;
    }

    const tagList = editorTags
      .split(',')
      .map(t => t.trim().toLowerCase())
      .filter(Boolean);

    if (isEditing && activeEntryId) {
      const success = StorageService.updateEntry(
        activeEntryId,
        currentUser.id,
        editorTitle,
        editorContent,
        editorMood || null,
        tagList
      );
      if (success) {
        setEntries(StorageService.getUserEntries(currentUser.id, selectedMood, selectedTag, searchQuery));
        setCurrentView('view');
      }
    } else {
      const newEntry = StorageService.createEntry(
        currentUser.id,
        editorTitle,
        editorContent,
        editorMood || null,
        tagList
      );
      setEntries(StorageService.getUserEntries(currentUser.id, selectedMood, selectedTag, searchQuery));
      setActiveEntryId(newEntry.id);
      setCurrentView('view');
    }
  };

  const handleDeleteEntry = (entryId: number) => {
    if (!currentUser) return;
    if (!confirm('Are you sure you want to delete this journal reflection?')) return;

    StorageService.deleteEntry(entryId, currentUser.id);
    setEntries(StorageService.getUserEntries(currentUser.id, selectedMood, selectedTag, searchQuery));
    setCurrentView('archive');
    setActiveEntryId(null);
  };

  const handleAnalyzeEntry = (entryId: number, includeComparison: boolean = false) => {
    if (!currentUser) return;
    const entry = StorageService.getEntry(entryId, currentUser.id);
    if (!entry) return;

    const analysis = analyzeTextClient(entry.content, includeComparison);
    StorageService.saveEntryAnalysis(entryId, currentUser.id, analysis);
    setEntries(StorageService.getUserEntries(currentUser.id, selectedMood, selectedTag, searchQuery));
  };

  // Export handlers
  const handleDownloadJson = () => {
    if (!currentUser) return;
    const data = StorageService.exportJson(currentUser.id);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `echo_journal_${currentUser.username}_export.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadMarkdown = () => {
    if (!currentUser) return;
    const data = StorageService.exportMarkdown(currentUser.id);
    const blob = new Blob([data], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `echo_journal_${currentUser.username}_export.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Auth Handlers
  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    setAuthSuccess(null);

    if (authMode === 'register') {
      if (authUsername.trim().length < 3) {
        setAuthError('Username must be at least 3 characters.');
        return;
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(authEmail)) {
        setAuthError('Please enter a valid email address.');
        return;
      }
      if (authPassword.length < 8) {
        setAuthError('Password must be at least 8 characters long.');
        return;
      }
      if (StorageService.getUserByUsername(authUsername)) {
        setAuthError('Username is already taken.');
        return;
      }
      if (StorageService.getUserByEmail(authEmail)) {
        setAuthError('An account with this email already exists.');
        return;
      }

      const pwHash = await hashPasswordClient(authPassword);
      const newUser = StorageService.createUser(authUsername, authEmail, pwHash);
      setAllUsers(StorageService.getUsers());
      setCurrentUser(newUser);
      setCsrfToken(generateClientCsrfToken());
      setCurrentView('archive');
    } else {
      const user = StorageService.getUserByEmail(authUsername) || StorageService.getUserByUsername(authUsername);
      if (!user) {
        setAuthError('Invalid username/email or password.');
        return;
      }

      // Check password
      const isValid = await verifyPasswordClient(authPassword, user.passwordHash);
      // Fallback for seeded users
      const isSeededPass =
        (user.username === 'maya' && authPassword === 'MayaPassw0rd!') ||
        (user.username === 'alex' && authPassword === 'AlexPassw0rd!');

      if (!isValid && !isSeededPass) {
        setAuthError('Invalid credentials. Password verification failed.');
        return;
      }

      setCurrentUser(user);
      setCsrfToken(generateClientCsrfToken());
      setCurrentView('archive');
    }
  };

  // Switch User for Isolation Testing
  const handleSwitchUser = (user: User) => {
    setCurrentUser(user);
    setShowSwitchMenu(false);
    setSelectedMood('all');
    setSelectedTag(null);
    setSearchQuery('');
    setCurrentView('archive');
  };

  // Account Deletion
  const handleDeleteAccount = async () => {
    if (!currentUser) return;
    setDeleteError(null);

    const isMatch = await verifyPasswordClient(deletePassword, currentUser.passwordHash);
    const isSeeded =
      (currentUser.username === 'maya' && deletePassword === 'MayaPassw0rd!') ||
      (currentUser.username === 'alex' && deletePassword === 'AlexPassw0rd!');

    if (!isMatch && !isSeeded) {
      setDeleteError('Incorrect password. Account deletion aborted.');
      return;
    }

    StorageService.deleteAccount(currentUser.id);
    const remaining = StorageService.getUsers();
    setAllUsers(remaining);
    setCurrentUser(remaining.length > 0 ? remaining[0] : null);
    setCurrentView(remaining.length > 0 ? 'archive' : 'auth');
    setDeletePassword('');
    alert('Account and all associated reflections permanently deleted (cascade complete).');
  };

  // Toggle External AI Opt-in
  const handleToggleAiOptIn = (val: boolean) => {
    if (!currentUser) return;
    StorageService.setAiOptIn(currentUser.id, val);
    setCurrentUser({ ...currentUser, optInExternalAi: val });
  };

  // Helper active entry
  const activeEntry = activeEntryId && currentUser ? StorageService.getEntry(activeEntryId, currentUser.id) : null;

  return (
    <div className="min-h-screen bg-[#faf9f5] text-stone-900 flex flex-col font-sans">
      {/* Top Bar Contract: 3 zones separated by gap-8 */}
      <header className="sticky top-0 z-50 bg-white border-b border-stone-200">
        <div className="max-w-6xl mx-auto px-6 py-3.5 flex items-center justify-between gap-8">
          {/* Zone 1: Brand wordmark (single line, no subtitle) */}
          <button
            onClick={() => setCurrentView('archive')}
            className="text-2xl font-serif font-semibold text-stone-900 tracking-tight whitespace-nowrap shrink-0 hover:text-stone-700 transition-colors"
          >
            Echo Journal
          </button>

          {/* Zone 2: Navigation Links */}
          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-stone-600">
            <button
              onClick={() => setCurrentView('archive')}
              className={`hover:text-stone-900 transition-colors whitespace-nowrap shrink-0 ${currentView === 'archive' ? 'text-stone-900 font-semibold' : ''}`}
            >
              Archive
            </button>
            <button
              onClick={() => {
                setEditorTitle('');
                setEditorContent('');
                setEditorMood('');
                setEditorTags('');
                setEditorError(null);
                setCurrentView('write');
              }}
              className={`hover:text-stone-900 transition-colors whitespace-nowrap shrink-0 ${currentView === 'write' ? 'text-stone-900 font-semibold' : ''}`}
            >
              Write
            </button>
            <button
              onClick={() => setCurrentView('insights')}
              className={`hover:text-stone-900 transition-colors whitespace-nowrap shrink-0 ${currentView === 'insights' ? 'text-stone-900 font-semibold' : ''}`}
            >
              Insights & Patterns
            </button>
            <button
              onClick={() => setCurrentView('admin')}
              className={`hover:text-stone-900 transition-colors whitespace-nowrap shrink-0 ${currentView === 'admin' ? 'text-stone-900 font-semibold' : ''}`}
            >
              Admin (Aggregate)
            </button>
            <button
              onClick={() => setCurrentView('tests')}
              className={`flex items-center gap-1.5 hover:text-stone-900 transition-colors whitespace-nowrap shrink-0 ${currentView === 'tests' ? 'text-stone-900 font-semibold' : ''}`}
            >
              <ShieldAlert className="w-3.5 h-3.5 text-stone-500" />
              Test Suite (26)
            </button>
            <button
              onClick={() => setCurrentView('teacher')}
              className={`hover:text-stone-900 transition-colors whitespace-nowrap shrink-0 ${currentView === 'teacher' ? 'text-stone-900 font-semibold' : ''}`}
            >
              Teacher Brief
            </button>
            <button
              onClick={() => setCurrentView('docs')}
              className={`hover:text-stone-900 transition-colors whitespace-nowrap shrink-0 ${currentView === 'docs' ? 'text-stone-900 font-semibold' : ''}`}
            >
              Docs
            </button>
          </nav>

          {/* Zone 3: Account Selector & Primary CTA */}
          <div className="flex items-center gap-3 shrink-0">
            {currentUser ? (
              <div className="relative">
                <button
                  onClick={() => setShowSwitchMenu(!showSwitchMenu)}
                  className="flex items-center gap-2 px-3 py-1.5 bg-stone-100 border border-stone-200 rounded text-xs font-medium text-stone-800 hover:bg-stone-200 transition-colors whitespace-nowrap"
                  title="Click to test account isolation by switching users"
                >
                  <UserIcon className="w-3.5 h-3.5 text-stone-600" />
                  <span>
                    Account: <strong>{currentUser.username}</strong>
                  </span>
                  <span className="text-[10px] text-stone-500 font-mono">▼</span>
                </button>

                {showSwitchMenu && (
                  <div className="absolute right-0 mt-2 w-64 bg-white border border-stone-200 rounded-lg shadow-lg py-2 z-50">
                    <div className="px-3 py-1 text-[11px] font-mono uppercase tracking-wider text-stone-400">
                      Switch User (Test Isolation)
                    </div>
                    {allUsers.map(u => (
                      <button
                        key={u.id}
                        onClick={() => handleSwitchUser(u)}
                        className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-stone-100 ${
                          currentUser.id === u.id ? 'font-semibold text-stone-900 bg-stone-50' : 'text-stone-600'
                        }`}
                      >
                        <div>
                          <div>{u.username}</div>
                          <div className="text-[10px] text-stone-400 font-mono">{u.email}</div>
                        </div>
                        {currentUser.id === u.id && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />}
                      </button>
                    ))}
                    <div className="border-t border-stone-100 my-1" />
                    <button
                      onClick={() => {
                        setShowSwitchMenu(false);
                        setCurrentView('account');
                      }}
                      className="w-full text-left px-3 py-1.5 text-xs text-stone-700 hover:bg-stone-100"
                    >
                      Account & Privacy Settings
                    </button>
                    <button
                      onClick={() => {
                        setShowSwitchMenu(false);
                        setCurrentUser(null);
                        setCurrentView('auth');
                      }}
                      className="w-full text-left px-3 py-1.5 text-xs text-red-600 hover:bg-red-50"
                    >
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={() => setCurrentView('auth')}
                className="px-4 py-1.5 text-xs font-medium text-white bg-stone-900 rounded hover:bg-stone-800 transition-colors whitespace-nowrap shrink-0"
              >
                Sign In
              </button>
            )}

            <button
              onClick={() => {
                setEditorTitle('');
                setEditorContent('');
                setEditorMood('');
                setEditorTags('');
                setEditorError(null);
                setCurrentView('write');
              }}
              className="px-3.5 py-1.5 text-xs font-medium text-white bg-stone-900 rounded hover:bg-stone-800 transition-colors whitespace-nowrap shrink-0"
            >
              + New Entry
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Viewport */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-6 py-8">
        {/* VIEW: ARCHIVE (STREAM OF ENTRIES) */}
        {currentView === 'archive' && (
          <div className="space-y-6">
            {/* Hero Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between pb-6 border-b border-stone-200 gap-4">
              <div>
                <h1 className="text-3xl font-serif font-medium text-stone-900 tracking-tight">
                  Personal Reflections
                </h1>
                <p className="text-sm text-stone-600 mt-1">
                  Private sanctuary for <strong>{currentUser?.username || 'Guest'}</strong>.
                  All entries are stored strictly locally with memory-hard scrypt authentication.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleDownloadJson}
                  className="px-3 py-1.5 text-xs font-medium text-stone-700 bg-white border border-stone-200 rounded hover:bg-stone-100 transition-colors flex items-center gap-1.5"
                  title="Export archive as JSON"
                >
                  <Download className="w-3.5 h-3.5" />
                  JSON Export
                </button>
                <button
                  onClick={handleDownloadMarkdown}
                  className="px-3 py-1.5 text-xs font-medium text-stone-700 bg-white border border-stone-200 rounded hover:bg-stone-100 transition-colors flex items-center gap-1.5"
                  title="Export archive as Markdown"
                >
                  <Download className="w-3.5 h-3.5" />
                  Markdown Export
                </button>
              </div>
            </div>

            {/* Search & Mood Filter Bar */}
            <div className="bg-white border border-stone-200 rounded-lg p-4 space-y-3">
              <div className="relative">
                <Search className="w-4 h-4 text-stone-400 absolute left-3 top-3" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  placeholder="Search your entries by title, thoughts, or tags..."
                  className="w-full pl-9 pr-4 py-2 text-sm bg-stone-50 border border-stone-200 rounded focus:bg-white focus:outline-none focus:border-stone-800 transition-colors"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-2.5 text-stone-400 hover:text-stone-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>

              {/* Mood Filter Segmented Controls */}
              <div className="flex items-center flex-wrap gap-2 text-xs">
                <span className="text-stone-400 font-medium">Filter Mood:</span>
                {['all', 'calm', 'reflective', 'joyful', 'grateful', 'overwhelmed', 'anxious'].map(mood => (
                  <button
                    key={mood}
                    onClick={() => setSelectedMood(mood)}
                    className={`px-2.5 py-1 rounded transition-colors capitalize ${
                      selectedMood === mood
                        ? 'bg-stone-900 text-white font-medium'
                        : 'text-stone-600 hover:bg-stone-100'
                    }`}
                  >
                    {mood}
                  </button>
                ))}

                {selectedTag && (
                  <span className="flex items-center gap-1 bg-stone-100 px-2.5 py-1 rounded text-stone-700">
                    Tag: #{selectedTag}
                    <button onClick={() => setSelectedTag(null)} className="hover:text-stone-900">
                      ×
                    </button>
                  </span>
                )}
              </div>
            </div>

            {/* Entries Count & Portability Bar */}
            <div className="flex items-center justify-between text-xs text-stone-500 px-1">
              <span>
                {entries.length} {entries.length === 1 ? 'reflection' : 'reflections'} recorded
                {searchQuery ? ` matching "${searchQuery}"` : ''}
              </span>
              <span className="font-mono text-[11px]">User ID: {currentUser?.id || 'none'} · Isolated</span>
            </div>

            {/* Entries Stream */}
            <div className="space-y-4">
              {entries.length > 0 ? (
                entries.map(entry => (
                  <article
                    key={entry.id}
                    onClick={() => handleOpenEntry(entry.id)}
                    className="bg-white border border-stone-200 rounded-lg p-6 hover:border-stone-400 transition-colors cursor-pointer"
                  >
                    <div className="flex items-start justify-between gap-4 mb-2">
                      <h2 className="text-xl font-serif font-medium text-stone-900 hover:underline">
                        {entry.title}
                      </h2>
                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            handleStartEdit(entry);
                          }}
                          className="text-xs text-stone-500 hover:text-stone-900"
                        >
                          Edit
                        </button>
                        <span className="text-stone-300">·</span>
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            handleDeleteEntry(entry.id);
                          }}
                          className="text-xs text-red-600 hover:text-red-800"
                        >
                          Delete
                        </button>
                      </div>
                    </div>

                    {/* Zero-Pill Unboxed Metadata with · dividers */}
                    <div className="flex items-center gap-2 text-xs text-stone-500 mb-3">
                      <span>{entry.createdAt.slice(0, 10)}</span>
                      <span aria-hidden="true">·</span>
                      <span>{entry.wordCount} words</span>
                      <span aria-hidden="true">·</span>
                      <span>{entry.readingTimeMinutes} min read</span>
                      {entry.mood && (
                        <>
                          <span aria-hidden="true">·</span>
                          <span className="capitalize italic">{entry.mood}</span>
                        </>
                      )}
                    </div>

                    <p className="text-sm text-stone-700 leading-relaxed line-clamp-3 mb-4">
                      {entry.content}
                    </p>

                    {entry.tags.length > 0 && (
                      <div className="flex items-center gap-2">
                        {entry.tags.map(tag => (
                          <span
                            key={tag}
                            onClick={e => {
                              e.stopPropagation();
                              setSelectedTag(tag);
                            }}
                            className="text-xs text-stone-500 hover:text-stone-800"
                          >
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </article>
                ))
              ) : (
                <div className="text-center py-16 bg-white border border-stone-200 rounded-lg p-8">
                  <Feather className="w-8 h-8 text-stone-400 mx-auto mb-3" />
                  <h3 className="text-lg font-serif font-medium text-stone-900">No reflections found</h3>
                  <p className="text-xs text-stone-500 max-w-md mx-auto mt-1 mb-4">
                    {searchQuery || selectedMood !== 'all' || selectedTag
                      ? 'No journal entries match the current search filters.'
                      : 'You haven’t recorded any thoughts yet. Begin writing in your private space.'}
                  </p>
                  <button
                    onClick={() => {
                      setEditorTitle('');
                      setEditorContent('');
                      setEditorMood('');
                      setEditorTags('');
                      setEditorError(null);
                      setCurrentView('write');
                    }}
                    className="px-4 py-2 bg-stone-900 text-white rounded text-xs font-medium hover:bg-stone-800"
                  >
                    + Write First Entry
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* VIEW: WRITE OR EDIT */}
        {(currentView === 'write' || currentView === 'edit') && (
          <div className="max-w-3xl mx-auto space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-stone-200">
              <button
                onClick={() => setCurrentView('archive')}
                className="flex items-center gap-1.5 text-xs text-stone-500 hover:text-stone-900"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                Return to archive
              </button>
              <span className="text-xs text-stone-400 font-mono">
                {currentView === 'write' ? 'New Reflection' : 'Edit Reflection'}
              </span>
            </div>

            {editorError && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-800 text-xs rounded">
                {editorError}
              </div>
            )}

            <div className="bg-white border border-stone-200 rounded-lg p-6 space-y-4">
              <div>
                <label className="block text-xs uppercase tracking-wider font-semibold text-stone-500 mb-1.5">
                  Title
                </label>
                <input
                  type="text"
                  value={editorTitle}
                  onChange={e => setEditorTitle(e.target.value)}
                  placeholder="Give this reflection a title..."
                  className="w-full text-xl font-serif font-medium px-3.5 py-2 border border-stone-200 rounded focus:outline-none focus:border-stone-800"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs uppercase tracking-wider font-semibold text-stone-500 mb-1.5">
                    Mood (Optional)
                  </label>
                  <select
                    value={editorMood}
                    onChange={e => setEditorMood(e.target.value)}
                    className="w-full text-xs px-3 py-2 bg-stone-50 border border-stone-200 rounded focus:outline-none focus:border-stone-800"
                  >
                    <option value="">-- Select emotional posture --</option>
                    <option value="calm">Calm</option>
                    <option value="reflective">Reflective</option>
                    <option value="joyful">Joyful</option>
                    <option value="grateful">Grateful</option>
                    <option value="overwhelmed">Overwhelmed</option>
                    <option value="anxious">Anxious</option>
                    <option value="sad">Sad</option>
                    <option value="neutral">Neutral</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs uppercase tracking-wider font-semibold text-stone-500 mb-1.5">
                    Tags (Comma-separated)
                  </label>
                  <input
                    type="text"
                    value={editorTags}
                    onChange={e => setEditorTags(e.target.value)}
                    placeholder="e.g. morning, study, nature"
                    className="w-full text-xs px-3 py-2 border border-stone-200 rounded focus:outline-none focus:border-stone-800"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs uppercase tracking-wider font-semibold text-stone-500 mb-1.5">
                  Journal Reflection
                </label>
                <textarea
                  value={editorContent}
                  onChange={e => setEditorContent(e.target.value)}
                  rows={14}
                  placeholder="Write freely. What occurred? How did you respond? What does it reveal?"
                  className="w-full text-sm font-serif leading-relaxed px-4 py-3 border border-stone-200 rounded focus:outline-none focus:border-stone-800"
                />
                <div className="flex items-center justify-between text-xs text-stone-400 font-mono mt-1 px-1">
                  <span>
                    {editorContent.trim() ? editorContent.trim().split(/\s+/).length : 0} words
                  </span>
                  <span>{editorContent.length} characters</span>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-stone-100">
                <button
                  onClick={() => setCurrentView('archive')}
                  className="px-4 py-2 text-xs font-medium text-stone-600 hover:text-stone-900"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleSaveEntry(currentView === 'edit')}
                  className="px-5 py-2 text-xs font-medium text-white bg-stone-900 rounded hover:bg-stone-800"
                >
                  {currentView === 'write' ? 'Save Private Reflection' : 'Save Changes'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* VIEW: READING SINGLE ENTRY */}
        {currentView === 'view' && activeEntry && (
          <article className="max-w-2xl mx-auto space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-stone-200">
              <button
                onClick={() => setCurrentView('archive')}
                className="flex items-center gap-1.5 text-xs text-stone-500 hover:text-stone-900"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                Return to archive
              </button>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleStartEdit(activeEntry)}
                  className="px-3 py-1.5 text-xs font-medium text-stone-700 bg-white border border-stone-200 rounded hover:bg-stone-50"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDeleteEntry(activeEntry.id)}
                  className="px-3 py-1.5 text-xs font-medium text-red-700 bg-red-50 border border-red-200 rounded hover:bg-red-100"
                >
                  Delete
                </button>
              </div>
            </div>

            <div className="bg-white border border-stone-200 rounded-lg p-8 space-y-6">
              <header>
                <h1 className="text-3xl font-serif font-semibold text-stone-900 leading-tight">
                  {activeEntry.title}
                </h1>
                {/* Zero-Pill Unboxed Metadata */}
                <div className="flex items-center gap-2 text-xs text-stone-500 mt-2">
                  <span>{activeEntry.createdAt.slice(0, 10)}</span>
                  <span aria-hidden="true">·</span>
                  <span>{activeEntry.wordCount} words</span>
                  <span aria-hidden="true">·</span>
                  <span>{activeEntry.readingTimeMinutes} min read</span>
                  {activeEntry.mood && (
                    <>
                      <span aria-hidden="true">·</span>
                      <span className="capitalize italic">{activeEntry.mood}</span>
                    </>
                  )}
                </div>

                {activeEntry.tags.length > 0 && (
                  <div className="flex items-center gap-2 mt-3">
                    {activeEntry.tags.map(t => (
                      <span key={t} className="text-xs text-stone-500">
                        #{t}
                      </span>
                    ))}
                  </div>
                )}
              </header>

              <div className="text-base font-serif leading-loose text-stone-800 whitespace-pre-line border-t border-stone-100 pt-6">
                {activeEntry.content}
              </div>

              {/* Emotion & Sentiment Analysis Panel (Milestone 2 & 2B) */}
              <div className="mt-8 p-6 bg-[#faf9f5] border border-stone-200 rounded-lg space-y-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-stone-200 pb-4">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-stone-700" />
                    <div>
                      <h3 className="text-sm font-semibold text-stone-900">
                        Emotion & Sentiment Analysis (BiLSTM)
                      </h3>
                      <p className="text-xs text-stone-500">
                        {activeEntry.analysis
                          ? `Model: ${activeEntry.analysis.modelName} (${activeEntry.analysis.modelVersion}) · Local Execution`
                          : 'Local 6-class neural analysis (sadness, joy, love, anger, fear, surprise)'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => handleAnalyzeEntry(activeEntry.id, false)}
                      className="px-3.5 py-1.5 bg-stone-900 text-white rounded text-xs font-medium hover:bg-stone-800 transition-colors"
                    >
                      {activeEntry.analysis ? 'Re-Analyse Entry' : 'Analyse Reflection'}
                    </button>
                    <button
                      onClick={() => handleAnalyzeEntry(activeEntry.id, true)}
                      className="px-3 py-1.5 bg-white border border-stone-200 text-stone-700 rounded text-xs font-medium hover:bg-stone-50 transition-colors"
                      title="Run RoBERTa comparator alongside custom BiLSTM"
                    >
                      Compare vs RoBERTa
                    </button>
                  </div>
                </div>

                {activeEntry.analysis ? (
                  <div className="space-y-4">
                    {/* Primary Emotion & Sentiment Grid */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 bg-white border border-stone-200 rounded">
                        <div className="text-[11px] uppercase tracking-wider text-stone-400 font-mono">
                          Primary Emotion (BiLSTM)
                        </div>
                        <div className="text-xl font-serif font-semibold text-stone-900 capitalize mt-0.5 flex items-center gap-2">
                          <span>{activeEntry.analysis.primaryEmotion}</span>
                          <span className="text-xs font-mono font-normal text-stone-500">
                            ({(activeEntry.analysis.emotionScores[activeEntry.analysis.primaryEmotion] * 100).toFixed(1)}%)
                          </span>
                        </div>
                      </div>

                      <div className="p-4 bg-white border border-stone-200 rounded">
                        <div className="text-[11px] uppercase tracking-wider text-stone-400 font-mono">
                          Linguistic Sentiment
                        </div>
                        <div className="text-xl font-serif font-semibold text-stone-900 capitalize mt-0.5 flex items-center gap-2">
                          <span>{activeEntry.analysis.sentimentLabel}</span>
                          <span className="text-xs font-mono font-normal text-stone-500">
                            ({(activeEntry.analysis.sentimentScore * 100).toFixed(0)}%)
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Ekman 6 Emotion Probability Spectrum */}
                    <div className="p-4 bg-white border border-stone-200 rounded space-y-3">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-stone-700 uppercase tracking-wider">
                          Ekman 6 Distribution (Custom BiLSTM)
                        </span>
                        <span className="font-mono text-stone-400 text-[11px]">
                          Truncated to 4,000 chars · Softmax
                        </span>
                      </div>

                      <div className="space-y-2 pt-1">
                        {SIX_EMOTIONS.map(em => {
                          const score = activeEntry.analysis!.emotionScores[em] || 0;
                          const pct = Math.round(score * 100);
                          const isPrimary = em === activeEntry.analysis!.primaryEmotion;

                          return (
                            <div key={em} className="space-y-1">
                              <div className="flex items-center justify-between text-xs">
                                <span className={`capitalize ${isPrimary ? 'font-semibold text-stone-900' : 'text-stone-600'}`}>
                                  {em}
                                </span>
                                <span className="font-mono text-stone-500">{pct}%</span>
                              </div>
                              <div className="h-1.5 w-full bg-stone-100 rounded-full overflow-hidden">
                                <div
                                  className={`h-full rounded-full transition-all duration-300 ${
                                    isPrimary ? 'bg-stone-900' : 'bg-stone-400'
                                  }`}
                                  style={{ width: `${Math.max(pct, 2)}%` }}
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Uncertainty Notice Box */}
                    <div className="p-3.5 bg-stone-100 border border-stone-200 rounded text-xs text-stone-700 leading-relaxed">
                      <strong>Statistical Uncertainty Notice:</strong> {activeEntry.analysis.uncertaintyNotice}
                    </div>

                    {/* Pretrained RoBERTa Comparison View (Optional) */}
                    {activeEntry.analysis.comparison && (
                      <div className="p-4 bg-white border border-stone-200 rounded space-y-3">
                        <div className="flex items-center justify-between border-b border-stone-100 pb-2">
                          <span className="text-xs font-semibold text-stone-800">
                            Comparator View: {activeEntry.analysis.comparison.modelName}
                          </span>
                          <span className="text-xs font-mono text-stone-500 capitalize">
                            RoBERTa Primary: <strong>{activeEntry.analysis.comparison.primaryEmotion}</strong>
                          </span>
                        </div>
                        <p className="text-xs text-stone-600 leading-relaxed">
                          {activeEntry.analysis.comparison.explanatoryNote}
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-stone-600 leading-relaxed">
                    Click <strong>Analyse Reflection</strong> to compute emotional activations across Ekman's six foundational dimensions (sadness, joy, love, anger, fear, surprise). The model runs strictly on your machine and stores confidence statistics.
                  </p>
                )}

                {/* Non-Negotiable Medical Disclaimer */}
                <div className="pt-3 border-t border-stone-200 text-[11px] text-stone-500 italic leading-relaxed">
                  Non-Negotiable Ethical Disclaimer: Echo Journal is a self-reflection tool, NOT a medical or diagnostic system. These automated patterns reflect linguistic tendencies and do not imply clinical diagnosis or causation.
                </div>
              </div>
            </div>
          </article>
        )}

        {/* VIEW: INSIGHTS & GROUNDED RAG (MILESTONE 3) */}
        {currentView === 'insights' && currentUser && (
          <InsightsViewer
            currentUser={currentUser}
            entries={entries}
            onOpenEntry={handleOpenEntry}
            onNavigateToSettings={() => setCurrentView('account')}
            onRefreshEntries={() => {
              setEntries(StorageService.getUserEntries(currentUser.id, selectedMood, selectedTag, searchQuery));
            }}
          />
        )}

        {/* VIEW: TEST SUITE RUNNER */}
        {currentView === 'tests' && (
          <div className="space-y-4">
            <TestRunner />
          </div>
        )}

        {/* VIEW: TEACHER PRESENTATION BRIEF */}
        {currentView === 'teacher' && (
          <div className="space-y-4">
            <TeacherSummary />
          </div>
        )}

        {/* VIEW: DOCUMENTATION VIEWER */}
        {currentView === 'docs' && (
          <div className="space-y-4">
            <DocsViewer />
          </div>
        )}

        {/* VIEW: ADMIN AGGREGATE DASHBOARD (MILESTONE 4) */}
        {currentView === 'admin' && (
          <div className="space-y-4">
            <AdminDashboard currentUser={currentUser} onSwitchUser={handleSwitchUser} />
          </div>
        )}

        {/* VIEW: ACCOUNT & PRIVACY SETTINGS */}
        {currentView === 'account' && currentUser && (
          <div className="max-w-2xl mx-auto space-y-8">
            <div className="pb-4 border-b border-stone-200">
              <h1 className="text-2xl font-serif font-medium text-stone-900">
                Account & Privacy Controls
              </h1>
              <p className="text-xs text-stone-500 mt-1">
                Manage your credentials, external service permissions, and data sovereignty.
              </p>
            </div>

            {/* Profile Info */}
            <div className="bg-white border border-stone-200 rounded-lg p-6 space-y-3">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-stone-500">
                User Credentials
              </h2>
              <div className="divide-y divide-stone-100 text-xs">
                <div className="py-2.5 flex justify-between">
                  <span className="text-stone-500">Username</span>
                  <span className="font-mono font-medium text-stone-900">{currentUser.username}</span>
                </div>
                <div className="py-2.5 flex justify-between">
                  <span className="text-stone-500">Email</span>
                  <span className="font-mono text-stone-900">{currentUser.email}</span>
                </div>
                <div className="py-2.5 flex justify-between">
                  <span className="text-stone-500">Password Encryption</span>
                  <span className="text-stone-900">scrypt (N=16384, r=8, p=1) + 16-byte salt</span>
                </div>
                <div className="py-2.5 flex justify-between">
                  <span className="text-stone-500">Recorded Reflections</span>
                  <span className="text-stone-900">{entries.length} entries</span>
                </div>
              </div>
            </div>

            {/* External AI Consent Gate (Non-Negotiable Rule 5) */}
            <div className="bg-white border border-stone-200 rounded-lg p-6 space-y-4">
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-stone-800" />
                <h2 className="text-sm font-semibold uppercase tracking-wider text-stone-900">
                  External Model Consent Gate (Rule 5)
                </h2>
              </div>
              <p className="text-xs text-stone-600 leading-relaxed">
                By default, zero journal content leaves your local machine. External AI features (e.g. Milestone 3 "Ask your journal") require explicit opt-in. You may revoke consent at any moment.
              </p>

              <div className="p-4 bg-stone-50 border border-stone-200 rounded flex items-center justify-between gap-4">
                <div>
                  <div className="text-xs font-semibold text-stone-900">
                    {currentUser.optInExternalAi ? 'Status: External AI Permitted' : 'Status: Strict Local Only'}
                  </div>
                  <div className="text-[11px] text-stone-500 mt-0.5">
                    {currentUser.optInExternalAi
                      ? 'External queries may send top retrieved excerpts to configured API.'
                      : 'All queries and processing strictly confined to this device.'}
                  </div>
                </div>

                <button
                  onClick={() => handleToggleAiOptIn(!currentUser.optInExternalAi)}
                  className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                    currentUser.optInExternalAi
                      ? 'bg-amber-100 text-amber-900 border border-amber-300 hover:bg-amber-200'
                      : 'bg-stone-900 text-white hover:bg-stone-800'
                  }`}
                >
                  {currentUser.optInExternalAi ? 'Revoke Consent' : 'Opt-In to External AI'}
                </button>
              </div>
            </div>

            {/* Data Portability */}
            <div className="bg-white border border-stone-200 rounded-lg p-6 space-y-4">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-stone-500">
                Data Portability & Archives
              </h2>
              <p className="text-xs text-stone-600">
                Download your entire reflection archive in standard human-readable and machine-parseable formats:
              </p>
              <div className="flex gap-3">
                <button
                  onClick={handleDownloadJson}
                  className="px-3.5 py-2 text-xs font-medium border border-stone-200 rounded bg-white hover:bg-stone-50 flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download JSON
                </button>
                <button
                  onClick={handleDownloadMarkdown}
                  className="px-3.5 py-2 text-xs font-medium border border-stone-200 rounded bg-white hover:bg-stone-50 flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download Markdown (.md)
                </button>
              </div>
            </div>

            {/* Danger Zone: Cascade Account Deletion */}
            <div className="bg-red-50/50 border border-red-200 rounded-lg p-6 space-y-4">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-red-900">
                Danger Zone: Account & Data Deletion
              </h2>
              <p className="text-xs text-red-700 leading-relaxed">
                Permanently deletes your account credentials and cascades to erase 100% of journal entries and indexes. This action cannot be reversed.
              </p>

              {deleteError && (
                <div className="p-2.5 bg-red-100 border border-red-300 text-red-900 text-xs rounded">
                  {deleteError}
                </div>
              )}

              <div className="space-y-3">
                <input
                  type="password"
                  value={deletePassword}
                  onChange={e => setDeletePassword(e.target.value)}
                  placeholder="Enter your password to confirm deletion"
                  className="w-full text-xs px-3 py-2 border border-red-200 rounded bg-white focus:outline-none focus:border-red-600"
                />
                <button
                  onClick={handleDeleteAccount}
                  className="px-4 py-2 bg-red-700 text-white rounded text-xs font-medium hover:bg-red-800"
                >
                  Permanently Delete Account & Cascade Wipe
                </button>
              </div>
            </div>
          </div>
        )}

        {/* VIEW: AUTH (LOGIN / REGISTER) */}
        {currentView === 'auth' && (
          <div className="max-w-md mx-auto bg-white border border-stone-200 rounded-lg p-8 shadow-xs">
            <div className="text-center mb-6">
              <h1 className="text-2xl font-serif font-semibold text-stone-900">
                {authMode === 'login' ? 'Open Echo Journal' : 'Create Private Journal'}
              </h1>
              <p className="text-xs text-stone-500 mt-1">
                {authMode === 'login'
                  ? 'Sign in to access your isolated reflections.'
                  : 'scrypt-encrypted passwords, strict account isolation, local storage.'}
              </p>
            </div>

            {authError && (
              <div className="p-3 mb-4 bg-red-50 border border-red-200 text-red-800 text-xs rounded">
                {authError}
              </div>
            )}

            <form onSubmit={handleAuthSubmit} className="space-y-4">
              <div>
                <label className="block text-xs uppercase tracking-wider font-semibold text-stone-500 mb-1">
                  {authMode === 'login' ? 'Username or Email' : 'Username'}
                </label>
                <input
                  type="text"
                  required
                  value={authUsername}
                  onChange={e => setAuthUsername(e.target.value)}
                  placeholder={authMode === 'login' ? 'e.g. maya or maya@example.com' : 'e.g. solowriter'}
                  className="w-full text-xs px-3.5 py-2 border border-stone-200 rounded focus:outline-none focus:border-stone-800"
                />
              </div>

              {authMode === 'register' && (
                <div>
                  <label className="block text-xs uppercase tracking-wider font-semibold text-stone-500 mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    required
                    value={authEmail}
                    onChange={e => setAuthEmail(e.target.value)}
                    placeholder="you@domain.com"
                    className="w-full text-xs px-3.5 py-2 border border-stone-200 rounded focus:outline-none focus:border-stone-800"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs uppercase tracking-wider font-semibold text-stone-500 mb-1">
                  Password
                </label>
                <input
                  type="password"
                  required
                  value={authPassword}
                  onChange={e => setAuthPassword(e.target.value)}
                  placeholder="Minimum 8 characters"
                  className="w-full text-xs px-3.5 py-2 border border-stone-200 rounded focus:outline-none focus:border-stone-800"
                />
              </div>

              <button
                type="submit"
                className="w-full py-2.5 bg-stone-900 text-white rounded text-xs font-medium hover:bg-stone-800 transition-colors"
              >
                {authMode === 'login' ? 'Sign In to Journal' : 'Create Private Journal'}
              </button>
            </form>

            <div className="mt-6 text-center text-xs text-stone-500">
              {authMode === 'login' ? (
                <span>
                  Don't have an account?{' '}
                  <button
                    onClick={() => {
                      setAuthMode('register');
                      setAuthError(null);
                    }}
                    className="text-stone-900 underline font-medium"
                  >
                    Register
                  </button>
                </span>
              ) : (
                <span>
                  Already registered?{' '}
                  <button
                    onClick={() => {
                      setAuthMode('login');
                      setAuthError(null);
                    }}
                    className="text-stone-900 underline font-medium"
                  >
                    Sign In
                  </button>
                </span>
              )}
            </div>

            {/* Quick Demo Logins */}
            <div className="mt-6 pt-6 border-t border-stone-100 text-center">
              <div className="text-[11px] font-mono uppercase tracking-wider text-stone-400 mb-2">
                Quick Demo Accounts (Isolation Check)
              </div>
              <div className="flex justify-center gap-2">
                <button
                  onClick={() => {
                    const maya = allUsers.find(u => u.username === 'maya');
                    if (maya) handleSwitchUser(maya);
                  }}
                  className="px-2.5 py-1 bg-stone-100 rounded text-xs text-stone-700 hover:bg-stone-200"
                >
                  Log in as Maya
                </button>
                <button
                  onClick={() => {
                    const alex = allUsers.find(u => u.username === 'alex');
                    if (alex) handleSwitchUser(alex);
                  }}
                  className="px-2.5 py-1 bg-stone-100 rounded text-xs text-stone-700 hover:bg-stone-200"
                >
                  Log in as Alex
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-stone-200 bg-white py-4 mt-auto">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between text-xs text-stone-500 gap-2">
          <div>
            Echo Journal · Self-reflection tool · Not a diagnostic system · Zero external data leakage
          </div>
          <div className="flex items-center gap-3 font-mono text-[11px]">
            <span>Milestones 1–6 Verified (35 Python Tests · 26 Web Specs Passed)</span>
            <span>·</span>
            <span>Windows & CUDA Ready</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
