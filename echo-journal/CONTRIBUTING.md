# Contributing to Echo Journal

Welcome to the **Echo Journal** group project! This document outlines the engineering guidelines, privacy invariants, and testing standards required for all contributors.

---

## 1. Non-Negotiable Rules (Read First)

Every pull request must adhere to our seven architectural invariants:

1. **Self-Reflection, Not Medicine**: Never diagnose, never claim causation from journal patterns. Always use correlation language ("co-occurs with", "appears together").
2. **Ground Truth Only**: Every insight cites specific dates/excerpts; uncertainty is explicitly stated.
3. **Honest Reporting**: Unfinished or untrained features must be marked "in progress". Metrics are never faked.
4. **Strict Account Isolation**: Every database query touching journal data must be parameterized with `user_id`. Direct lookups by `entry_id` alone are strictly forbidden.
5. **Data Sovereignty**: Zero journal text leaves the server unless the user explicitly opts in via Account Settings.
6. **Zero Secrets in Code**: Secrets belong in `.env`. Never commit API keys or credentials.
7. **Windows & CUDA Compatibility**: Use Python `pathlib`, virtual environments, and automatic NVIDIA CUDA GPU acceleration when present, with CPU fallback.

---

## 2. Branching & Git Workflow

- `main`: Production-ready, fully verified milestone code.
- `develop`: Integration branch where group members merge milestone deliverables.
- Feature branches: Named by milestone, e.g.:
  - `feature/m1-scrypt-auth`
  - `feature/m2-bilstm-classifier`
  - `feature/m3-hybrid-retrieval`
  - `feature/m4-admin-dashboard`
  - `feature/m5-ci-hygiene`
  - `feature/m6-postgres-hardening`

### Commit Message Format
Use Conventional Commits:
```
feat(m4): add aggregate-only admin metrics calculation
test(isolation): add cross-user deletion invariant checks
docs(model-card): document held-out journal macro-F1 evaluation
```

---

## 3. Local Development Setup (Windows / Linux / macOS)

### Virtual Environment Setup
```bash
# Clone the repository
git clone https://github.com/your-username/echo-journal.git
cd echo-journal

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows Command Prompt:
.\venv\Scripts\activate.bat
# Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-ml.txt
```

---

## 4. Running the Verification Suite

Before submitting any Pull Request, you must execute the full automated test suite:

```bash
python tests/run_tests.py
```

All 35+ test specs must pass with 0 failures and 0 errors:
- `tests/test_isolation.py`: Account isolation & ownership proofs
- `tests/test_auth.py`: scrypt hashing, validation, session security
- `tests/test_journal.py`: CRUD lifecycle, search, JSON/Markdown export
- `tests/test_ml.py`: BiLSTM 6-class output, RoBERTa comparator, truncation
- `tests/test_insights.py`: Hybrid retrieval, non-causal language, 10-entry threshold
- `tests/test_admin.py`: Aggregate metrics & zero-exposure privacy guarantees
- `tests/test_security.py`: CSRF, XSS defense, cascade deletion, rate limiter, crisis safety

---

## 5. Privacy & Security Review Checklist

Before opening a PR, ensure:
- [ ] No route exposes another user's entry or user ID.
- [ ] Admin endpoints return aggregate statistics only; zero entry titles or text.
- [ ] Any new reflection text uses correlational, not causal, phrasing.
- [ ] All forms include CSRF tokens.
- [ ] Python code passes without syntax errors or unhandled exceptions.
