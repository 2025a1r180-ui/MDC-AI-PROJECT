# Architecture Documentation — Echo Journal

## 1. System Overview

Echo Journal is engineered as a secure, privacy-first personal reflection platform built with a clear separation of concerns between client interface, application logic, persistence, and machine learning pipelines.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ECHO JOURNAL SYSTEM ARCHITECTURE                 │
├───────────────────────────────────┬────────────────────────────────────┤
│           Client Layer            │         Application Layer          │
│   (HTML5, Vanilla JS, CSS)        │         (Python 3.11+ Flask)       │
│                                   │                                    │
│   • Serene Archival Theme         │   • App Factory (create_app)       │
│   • Client-side Metrics           │   • Auth Blueprint (scrypt, CSRF)  │
│   • Form CSRF Token Transmission  │   • Journal Blueprint (CRUD)       │
│   • Export Download Triggers      │   • Account Blueprint (GDPR purge) │
│                                   │   • Safety Layer (Crisis routing)  │
└─────────────────┬─────────────────┴──────────────────┬─────────────────┘
                  │                                    │
                  ▼                                    ▼
┌───────────────────────────────────┐┌───────────────────────────────────┐
│        Persistence Layer          ││       Machine Learning Layer      │
│  (Repository Pattern Abstraction) ││       (Local PyTorch Pipeline)    │
│                                   ││                                   │
│   • UserRepository                ││   • Custom 6-Class BiLSTM         │
│   • JournalRepository             ││   • Vocab Builder (Train Split)   │
│   • Strict User ID Filtering      ││   • GPU CUDA / CPU Auto-detect    │
│   • Dev: SQLite (WAL + FTS5)      ││   • Pretrained RoBERTa Comparator │
│   • Prod: PostgreSQL (SQLAlchemy) ││   • Strict Truncation (4,000 char)│
└───────────────────────────────────┘└───────────────────────────────────┘
```

## 2. Strict Account Isolation (Non-Negotiable Rule 4)

Multi-tenant privacy is enforced at the repository layer. The database interface prohibits raw queries by record ID alone:

- **Every Query Parameterized**: All retrieval, mutation, and deletion SQL queries take `(entry_id, user_id)` or `WHERE user_id = ?`.
- **Zero Cross-User Enumeration**: An attempt by User B to access an entry created by User A yields an immediate `None` / `404 Not Found`.
- **Audit Verification**: Verified by automated test suite (`tests/test_isolation.py`), proving zero cross-user search leakage and zero cross-user export contamination.

## 3. Storage Layer & Zero-Friction Engine Swap

Echo Journal utilizes the Repository Pattern to decouple business logic from the underlying SQL dialect:
- **Development**: SQLite with `PRAGMA foreign_keys = ON` and `PRAGMA journal_mode = WAL`.
- **Full-Text Retrieval**: SQLite FTS5 virtual table synchronized via atomic insert/update/delete triggers.
- **Production**: Configurable via `DATABASE_URL=postgresql://...`. Changing storage requires updating one environment variable.

## 4. Cryptographic Security Standards

1. **Password Hashing**: `scrypt` with OWASP-recommended parameters:
   - $N = 16384$ (CPU/memory cost)
   - $r = 8$ (block size)
   - $p = 1$ (parallelization)
   - 16-byte cryptographically secure random salt (`os.urandom(16)`)
   - Constant-time verification using `hmac.compare_digest`.
2. **CSRF Protection**: High-entropy 32-byte cryptographic tokens (`secrets.token_hex(32)`), bound to signed sessions and checked on every mutating HTTP verb (`POST`, `PUT`, `DELETE`).
3. **Session Cookies**: Signed with HMAC-SHA256, flagged with `HttpOnly`, `SameSite=Lax`, and `Secure` (in production).
