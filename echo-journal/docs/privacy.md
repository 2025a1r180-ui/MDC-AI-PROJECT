# Privacy Policy & Ethical Charter — Echo Journal

## 1. Ethical Boundary & Medical Non-Claim (Non-Negotiable Rule 1)

**Echo Journal is an introspective self-reflection tool, NOT a diagnostic, psychiatric, or healthcare system.**
- The application will **never** diagnose mental health conditions, personality disorders, or affective states.
- The application will **never** claim clinical causation from journal patterns (e.g. "writing late causes sadness"). All pattern observations use observational phrasing ("frequently co-occurs", "appears alongside").

## 2. Server Boundary & External Opt-In (Non-Negotiable Rule 5)

- **Default Stance**: 100% of journal entries, metadata, tags, and reflections reside strictly on the server hosting the application.
- **External AI Gate**: No journal content is ever transmitted to external model providers (e.g., Gemini, Groq, OpenRouter) unless the authenticated user explicitly navigates to Account Settings and activates the "External AI Consent" toggle.
- **Revocability**: Consent can be revoked instantly at any moment, reverting the application to strictly local offline processing.
- **Minimal Context Transmission**: When external queries are issued in "Ask your journal" (Milestone 3), only the top retrieved relevant passages are forwarded—never the entire database.

## 3. Account Isolation & GDPR Right to Erasure

- Every user's reflections are strictly isolated behind foreign key relations validated on every query.
- Users maintain 100% data portability via one-click JSON and Markdown archive downloads.
- Full Account Deletion triggers a hard database cascade, immediately wiping the user credentials, entries, search indexes, and caches without soft-delete retention.

## 4. Crisis & Safety Protocol

If text entered in an entry or reflection query indicates acute self-harm, suicidal ideation, or severe crisis:
- The system **halts automated generative synthesis**.
- The system displays a gentle, supportive notification presenting verified, free, 24/7 crisis helpline contacts (e.g., 988 Lifeline, Samaritans, Tele-MANAS, IASP directory).
