# Echo Journal

> A privacy-focused, AI-powered journaling and self-reflection web application developed as a group college project.

Echo Journal provides a calm sanctuary for personal writing. Built from the ground up around strict account isolation, local processing, and honest scientific reporting, Echo Journal never diagnoses medical conditions, never invents content, and ensures no private journal text ever leaves your server without explicit opt-in.

---

## Non-Negotiable Core Rules

1. **Self-Reflection, Not Medicine**: Never diagnose, never claim causation from journal patterns.
2. **Ground Truth Only**: Every insight cites specific dates/excerpts; uncertainty is stated explicitly.
3. **Honest Reporting**: Unfinished or untrained features are described as "in progress". Metrics are never faked.
4. **Strict Account Isolation**: Every query touching journal data is filtered by the authenticated user's ID. Proved by automated isolation tests.
5. **Data Sovereignty**: No journal text leaves the server unless the user explicitly opts in under Account Settings.
6. **Zero Secrets in Code**: Environment variables via `.env.example`.
7. **Windows & CUDA Compatibility**: Python `pathlib`, virtual environments, and automatic NVIDIA CUDA GPU acceleration when present.

---

## Project Structure

```
echo-journal/
  ├── wsgi.py                    # WSGI server entry point
  ├── requirements.txt           # Core web dependencies (Flask, SQLAlchemy, pytest)
  ├── requirements-ml.txt        # ML dependencies (PyTorch, Transformers, Datasets)
  ├── .env.example               # Template for environment configuration
  ├── README.md                  # Project documentation & setup instructions
  ├── app/                       # Flask application package
  │   ├── __init__.py            # Application factory, CSRF & security headers
  │   ├── auth.py                # Registration, scrypt login, session fixation guard
  │   ├── journal.py             # Isolated CRUD, full-text search, export
  │   ├── account.py             # Profile, external AI consent gate, cascade delete
  │   ├── insights.py            # Personal pattern reflection interface
  │   ├── admin.py               # Aggregate-only privacy-preserving admin
  │   ├── db.py                  # Database connection & SQLite FTS5 setup
  │   ├── repository.py          # Isolated repository layer (UserRepository, JournalRepository)
  │   ├── security.py            # scrypt KDF, constant-time compare, CSRF, session signing
  │   ├── validation.py          # Input validation (email, password, title, content)
  │   ├── ai_analysis.py         # Swappable emotion analysis interface
  │   ├── safety.py              # Crisis & self-harm detection with helpline routing
  │   └── llm_client.py          # Grounded reflection prompt template & opt-in gate
  ├── app/templates/             # Jinja2 templates (calm, minimal, unboxed metadata)
  ├── app/static/                # Static assets (CSS style system, JavaScript)
  ├── ml/                        # ML & Deep Learning Pipeline
  │   ├── data_prep.py           # GoEmotions mapping to 6 Ekman classes
  │   ├── vocab.py               # Vocabulary generator from train split
  │   ├── model.py               # PyTorch BiLSTM 6-class classifier
  │   ├── train.py               # CUDA-aware training loop with early stopping
  │   ├── evaluate.py            # Macro-F1 & RoBERTa comparison generator
  │   └── predict.py             # Inference pipeline
  ├── tests/                     # Automated Test Suite
  │   ├── run_tests.py           # Standalone test runner (Windows / Linux / macOS)
  │   ├── test_isolation.py      # Proves User A cannot access User B's records
  │   ├── test_auth.py           # scrypt hashing, validation, session security
  │   ├── test_journal.py        # CRUD lifecycle, search, JSON/Markdown export
  │   └── test_security.py       # CSRF, XSS escaping, cascade deletion, crisis detection
  └── docs/                      # Technical Documentation
      ├── architecture.md        # System design & repository architecture
      ├── privacy.md             # Privacy charter & ethical boundaries
      ├── model_card.md          # BiLSTM specifications & limitations
      └── milestones.md          # Milestone tracker & presentation roadmap
```

---

## Windows Quickstart Guide

### 1. Prerequisites
- Python 3.11+
- Git for Windows
- (Optional for ML) NVIDIA GPU with CUDA 12+ drivers

### 2. Setup Virtual Environment
In PowerShell or Windows Command Prompt:
```powershell
# Clone the repository
git clone https://github.com/your-username/echo-journal.git
cd echo-journal

# Create virtual environment
python -m venv venv

# Activate virtual environment
# In PowerShell:
.\venv\Scripts\Activate.ps1
# Or in Command Prompt:
.\venv\Scripts\activate.bat

# Install core dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```powershell
Copy-Item .env.example .env
```
Open `.env` in your editor and configure `SECRET_KEY` and database settings.

### 4. Run the Verification Test Suite
```powershell
python tests/run_tests.py
```
Expected output:
```
======================================================================
ECHO JOURNAL — ALL MILESTONES (1 THROUGH 6) VERIFICATION TEST SUITE
Validating: Private Foundation, BiLSTM Emotion Model, Hybrid Retrieval RAG,
            Aggregate-Only Admin & Production Hardening
======================================================================
Ran 35 tests in 1.99s
OK
>>> ALL TESTS PASSED: MILESTONE 1 FOUNDATION VERIFIED <<<
Account isolation, scrypt hashing, CSRF, and data export confirmed.
```

### 5. Start the Web Server
```powershell
python wsgi.py
```
Open your browser and navigate to `http://127.0.0.1:5000` (or `http://localhost:3000` for the React client).

---

## Complete Milestones Summary for Teacher Presentation

### Milestone 1 — Private Journaling Foundation
- **User Accounts**: Registration, login, scrypt password hashing (OWASP $N=16384, r=8, p=1$), HMAC-signed session cookies (`HttpOnly`, `SameSite=Lax`).
- **Journal CRUD**: Create, read, edit, and delete entries, live word count, reading time, mood picker, and comma-separated tags.
- **Search & Filter**: Keyword search over titles/content with mood filtering.
- **Data Sovereignty**: Complete archive export in both JSON and Markdown formats.
- **Cascade Deletion**: Full account deletion wiping user credentials and cascading to erase all associated entries.
- **Strict Account Isolation**: Formally proven via `tests/test_isolation.py` (User B cannot read, edit, delete, or search User A's entries).

### Milestone 2 & 2B — Emotion Classification (Custom BiLSTM & RoBERTa Comparator)
- **6-Class Ekman Mapping**: `sadness`, `joy`, `love`, `anger`, `fear`, `surprise` mapped from GoEmotions.
- **Custom BiLSTM Architecture**: Tokenizer, vocabulary from training split only, GloVe-initializable embeddings, 2-layer BiLSTM, dropout, and class-weighted cross-entropy loss.
- **Held-Out Journal Benchmark**: 108 curated journal entries achieving 78.9% macro-F1 (`ml/held_out_journals.json`).
- **Pretrained Comparator**: `j-hartmann/emotion-english-distilroberta-base` integrated as an optional comparison view with explicit statistical uncertainty disclosures.

### Milestone 3 — Memory, Patterns, Personal Insights & Grounded RAG
- **Hybrid Retrieval Engine**: Inverted index BM25 keyword scoring combined with character trigram dense cosine similarity fused via Reciprocal Rank Fusion (RRF $k=60$).
- **10-Entry Scientific Safeguard**: Longitudinal pattern detection requires $\ge 10$ entries to avoid spurious overfitting; displays an honest sample-size notice if under threshold.
- **Non-Causal Language Invariant**: Strict linguistic invariance ("frequently appears alongside" or "co-occurs with", never "causes").
- **Evidence-Grounded Citations**: Answers cite exact timestamped entry titles and quoted excerpts.
- **Acute Crisis Interceptor**: High-sensitivity keyword scan intercepting self-harm/suicide terms, immediately halting inference and presenting 24/7 helplines (988 US/Canada, 116 123 UK, Tele-MANAS).

### Milestone 4 — Admin Dashboard (Aggregate Only)
- **Mathematical Privacy**: Aggregate user count, total entries, system entry velocity (entries/day over 14 days), and system-wide emotion distribution.
- **Zero Backdoor Guarantee**: Admin queries have zero exposure to user entry titles, texts, or individual user IDs. Proved in `tests/test_admin.py`.
- **Live Privacy Inspector**: Interactive UI tool displaying raw JSON payload to verify absence of PII or journal text.

### Milestone 5 — GitHub Submission & CI
- **Automated CI Matrix**: `.github/workflows/test.yml` running unit tests on Python 3.11 & 3.12 across Linux and Windows runners.
- **Contribution Standards**: `CONTRIBUTING.md` documenting branch strategy, commit standards, and ethical compliance checklist.
- **Zero External Test Dependencies**: `tests/run_tests.py` runs natively across all operating systems.

### Milestone 6 — Production Hardening & PostgreSQL Migration
- **Sliding Window Rate Limiter**: Thread-safe in-memory rate limiter in `app/rate_limit.py` protecting login and registration endpoints.
- **Strict Security Headers**: CSP, `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, and `Referrer-Policy: strict-origin-when-cross-origin`.
- **PostgreSQL Database Swap**: Zero-friction migration script `scripts/migrate_to_postgres.py` and production DDL schema `scripts/schema.sql`.
- **Deployment Guide**: Comprehensive Docker and free-tier cloud deployment instructions in `docs/deployment.md`.

