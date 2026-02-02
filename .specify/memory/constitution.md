<!--
CONSTITUTION SYNC IMPACT REPORT
==============================
Version Change: 1.0.0 (Initial Constitution)
Date: 2026-02-02

Core Principles (6 total):
- I. Simplicity & Code Cleanliness
- II. Test-First Development (MANDATORY)
- III. DRY (Don't Repeat Yourself)
- IV. Observability
- V. Documentation  
- VI. Security & Public Exposure

Added Sections:
- Technical Constraints
- Development Workflow
- Governance

Templates Requiring Updates:
✅ plan-template.md - Constitution Check section updated with 6 gates
✅ spec-template.md - Requirements section ensures security/observability/DRY
✅ tasks-template.md - Task categories include tests, logging, docs, security, refactoring

Commit Message: "docs: create Portfolio constitution v1.0.0 (6 core principles + governance)"
-->

# Portfolio Constitution

## Core Principles

### I. Simplicity & Code Cleanliness

Every line of code must earn its place. Remove unused features proactively, apply YAGNI
(You Aren't Gonna Need It) principles rigorously, and use clear naming with minimal 
abstractions. Any complexity must be justified with concrete need - no speculative 
engineering.

**Rationale**: As a solo developer maintaining a public-facing app, code clarity directly 
impacts velocity and reduces the risk of introducing bugs during changes.

### II. Test-First Development (MANDATORY)

TDD cycle is strictly enforced: Write tests → Get user approval → Ensure tests FAIL → 
Implement until GREEN → Refactor. Integration tests required for auth flows, proxy 
services, and cross-service communication. Contract tests required for all API endpoints.

**Rationale**: Public web application with authentication and proxied services demands 
quality assurance. TDD catches regressions early and serves as living documentation.

### III. DRY (Don't Repeat Yourself)

Eliminate code duplication through abstraction. Shared logic MUST be extracted into 
reusable functions, classes, or modules. Common patterns (proxy logic, authentication, 
error handling) require base implementations. Configuration values belong in centralized 
config files, not hardcoded across modules.

**Rationale**: The Portfolio project has multiple proxy services (VS Code, OpenCode), 
shared authentication logic, and common infrastructure patterns (Tailscale, Cloud Run). 
DRY reduces bugs (fix once vs. fix everywhere), accelerates feature development 
(reuse vs. rewrite), and improves maintainability (single source of truth).

### IV. Observability

Structured logging for all critical paths (authentication, proxy operations, errors). 
Health check endpoints for all services. Diagnostic tools maintained for Tailscale, 
proxy connections, and Cloud Run. Text-based I/O wherever possible for debuggability.

**Rationale**: Remote proxy debugging and Cloud Run troubleshooting require visibility. 
Without observability, issues become mysteries.

### V. Documentation

Code comments required for complex logic (proxy implementations, auth flows). API 
documentation required for all routes. Deployment guides maintained. Architecture 
decisions recorded in docs or git history.

**Rationale**: Solo developer needs future-self documentation. Clear docs enable faster 
onboarding if collaborators join or when returning to code after time away.

### VI. Security & Public Exposure

Authentication mandatory for all dev tools. Secrets never committed - use .env files 
and Cloud Run secret manager. 2FA/JWT required for sensitive endpoints. Rate limiting 
on authentication. Regular dependency updates for security patches.

**Rationale**: Public-facing web application with valuable development tools (VS Code, 
OpenCode AI) requires defense in depth. Single security failure exposes entire dev environment.

## Technical Constraints

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Infrastructure**: Google Cloud Run with Tailscale VPN
- **Proxy**: SOCKS5 for secure Mac server access
- **Authentication**: JWT with 2FA (TOTP)

## Development Workflow

- Feature branches follow spec-kit convention: `###-feature-name`
- Git commit required before deployment
- Cloud Run auto-deploys on `main` branch push (per CLAUDE.md)
- Local development uses HTTPS when SSL certs available (fallback to HTTP)
- Session cleanup runs every hour for idle connections

## Governance

**Authority**: This constitution supersedes all ad-hoc development practices.

**Complexity Review**: Any violation of Principle I (Simplicity) must be justified with 
concrete need and simpler alternatives documented as rejected.

**Amendment Process**: Constitution changes require version bump (semantic versioning), 
updated documentation, and migration plan if affecting existing code.

**Compliance**: All changes must verify compliance with the six core principles. Use 
the Constitution Check gates in plan-template.md during feature planning.

**Version**: 1.0.0 | **Ratified**: 2026-02-02 | **Last Amended**: 2026-02-02
