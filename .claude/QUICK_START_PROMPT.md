# Quick Start Prompt for Claude Code

Copy and paste this into chat when starting a new session:

---

**System Context:** This is a production Django 5.0 application for German construction document analysis, currently in Phase 3 testing with 169+ tests and OCR as core functionality. **Critical Rule:** NEVER disable or make features optional to bypass issues - always fix root causes properly, considering this will deploy to Google Cloud Run (headless environment). Before making any changes that could affect functionality, ask me first and explain trade-offs clearly. Research thoroughly using available documentation (DOCKER_OPENCV_FIX_RESEARCH.md, .claude/CLAUDE.md, PHASE3_INTEGRATION_SUMMARY.md) before proposing solutions. Proceed with deep research and implementation following these integrity guidelines.

---

**Usage:** Paste this at the start of any chat where Claude needs context about system constraints.
