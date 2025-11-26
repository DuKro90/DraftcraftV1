# Documentation Archive - November 2025

Archived files from the documentation reorganization performed on November 26, 2025.

## Summary
Aggressive documentation cleanup to improve maintainability and eliminate confusion from duplicate/outdated files. All content preserved in git history.

## Archived Files

### Duplicate Documentation (Superseded)

- **CLAUDE_NEW.md** → Content consolidated into [.claude/CLAUDE.md](../../.claude/CLAUDE.md)
  - Duplicate Claude Code development guide
  - Merged content into authoritative version

- **CHANGELOG_GERMAN.md** (formerly `.claude/CHANGELOG.md`) → Merged into [CHANGELOG.md](../../CHANGELOG.md)
  - German Handwerk-focused changelog
  - Content reviewed and consolidated into main changelog
  - Different project framing, consolidated into unified project history

- **LOCAL_SETUP_GUIDE.md** → Content now in [DEVELOPER_GUIDE.md](../../DEVELOPER_GUIDE.md)
  - Duplicate local development setup guide
  - Content merged into comprehensive development guide
  - Reduces setup documentation redundancy

### Reason for Archival

These files created confusion by:
- Duplicating content across multiple authoritative sources
- Using conflicting project names and descriptions
- Having different status information scattered across docs
- Making it unclear which file was current

## Archive Policy

Files are kept in this dated folder for:
- **Historical reference** - Understanding evolution of documentation
- **Content recovery** - If any unique information is found in archived versions
- **Git history** - All changes preserved via `git mv` (not deleted)

## Notes

**Date of Archive:** November 26, 2025
**Reason:** Documentation reorganization per user request
**Impact:** None on functionality - purely organizational change
**Git History:** All moves preserved via `git mv` for full traceability

## Structure

Files in this directory are **read-only historical archives**. For current documentation:
- See [README.md](../../README.md) - Main project overview
- See [DEVELOPER_GUIDE.md](../../DEVELOPER_GUIDE.md) - Development setup
- See [DEPLOYMENT_GUIDE.md](../../DEPLOYMENT_GUIDE.md) - Production deployment
- See [.claude/CLAUDE.md](../../.claude/CLAUDE.md) - Claude Code guidance
