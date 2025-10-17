## [Init] Lesson: Centralize assistant state
**Situation**: Multiple state file names and locations caused confusion
**Learning**: A single `.ai_state` at repo root avoids ambiguity
**Application**: Read/write `.ai_state` only; deprecate tool-specific variants

## 2025-10-05 Lesson: Indexing rules improves adoption

Situation
- Previous rules were harder to discover and scope.

Learning
- A small `registry.yaml` with front‑matter makes selection and validation straightforward.

Application
- Use the registry pattern in future repos needing AI-assistant rules.

## 2025-10-11 Lesson: Pre-Release Security Audits are Critical

### Situation
- Conducted comprehensive security audit before first production release
- Found 1 CRITICAL, 5 HIGH, 7 MEDIUM, and 3 LOW severity vulnerabilities
- Most issues were preventable with security-first design thinking

### Key Security Findings

1. **LLM Prompt Injection (HIGH SEVERITY)**
   - No sanitization of user inputs sent to Claude API
   - Attackers could override system prompts, exfiltrate data, manipulate agents
   - Solution: Implemented PromptSanitizer with pattern-based detection

2. **CVE-2025-30208 in Vite 6.2.0 (CRITICAL)**
   - Development server allowed unauthorized file system access
   - Solution: Upgraded to Vite 6.2.3

3. **Overly Permissive CORS (HIGH)**
   - `allow_methods=["*"]` and `allow_headers=["*"]` increased attack surface
   - Solution: Restricted to specific whitelisted methods/headers

4. **Debug Mode Default (MEDIUM)**
   - `debug=True` exposed stack traces and system internals
   - Solution: Changed default to `False`, added production validation

5. **Missing Encryption Key Validation (HIGH)**
   - System generated temporary keys leading to data loss
   - Solution: Fail hard in production if ENCRYPTION_KEY not set

### Lessons Learned

1. **Security Must Be Proactive, Not Reactive**
   - Waiting until after deployment to think about security is too late
   - Security review should happen at design phase and pre-release

2. **LLM Systems Have Unique Attack Surfaces**
   - Prompt injection is as serious as SQL injection
   - User inputs to LLMs must be sanitized and validated
   - Pattern-based detection catches common injection attempts

3. **Dependency Vulnerabilities Emerge Quickly**
   - Even recent packages (Vite 6.2.0) can have critical CVEs
   - Monthly automated scanning is essential
   - Manual CVE research supplements automated tools

4. **Fail-Safe Defaults Prevent Mistakes**
   - `debug=False`, not `debug=True`
   - Explicit CORS whitelists, not wildcards
   - Fail hard on missing secrets in production

5. **Rate Limiting for Cost Control**
   - LLM API calls are expensive
   - Rate limits protect both security AND budget
   - Cost-based limits as important as request-based limits

6. **Defense in Depth Works**
   - Multiple security layers compensate for individual failures
   - Auth + Rate Limiting + Input Validation + Encryption
   - No single point of failure

### Application Going Forward

- ✅ Implemented prompt sanitization service
- ✅ Fixed all CRITICAL and HIGH vulnerabilities
- ✅ Upgraded dependencies with known CVEs
- ✅ Documented security best practices
- 🔄 Establishing monthly security scan cadence
- 🔄 Adding security tests to CI/CD pipeline
- 📋 Backlog: ChromaDB auth, HTTPS enforcement, WebSocket validation

### Security Resources

- OWASP LLM Top 10: https://owasp.org/www-project-top-10-for-large-language-model-applications/
- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
- Anthropic Safety: https://docs.anthropic.com/claude/docs/security-best-practices

---

## 2025-10-15 Lesson: Follow-Up Security Audit Reveals Strong Posture

### Situation
- Conducted comprehensive follow-up security audit before production release
- **Severity Distribution**: CRITICAL: 0, HIGH: 3, MEDIUM: 5, LOW: 4
- **Overall Risk Level**: MEDIUM (significantly improved from previous audit)
- Previous security fixes from October 2025 audit have been effective

### Key Findings

**Positive Improvements ✅**:
1. **API Key Encryption Working** - Fernet encryption properly implemented
2. **Prompt Injection Sanitization Active** - Pattern-based detection catching injection attempts
3. **Rate Limiting Implemented** - Write operations protected
4. **Docker Hardening Complete** - Non-root containers for frontend and backend
5. **CORS Properly Configured** - Specific methods and headers whitelisted
6. **Debug Default Fixed** - `debug=False` is now the default

**High-Priority Issues Found ⚠️**:

1. **HIGH-001: Authentication Bypass in Debug Mode**
   - Condition: If `DEBUG=True` AND `ENV != production` AND no credentials
   - Result: All API endpoints accessible without authentication
   - Risk: Accidental production exposure if ENV not set correctly
   - **File**: backend/app/dependencies/auth.py:37-39

2. **HIGH-002: Ephemeral Encryption Keys**
   - If `ENCRYPTION_KEY` not set, system generates random session key
   - On restart, new key generated → all stored API keys permanently lost
   - Risk: User must re-enter all credentials after every restart
   - **File**: backend/app/services/encryption_service.py:26-38

3. **HIGH-003: CORS Production Validation Missing**
   - Default CORS origins include localhost:5173 and localhost:3000
   - If not overridden in production, localhost origins still allowed
   - Risk: Developer configs leaking into production
   - **File**: backend/config/settings.py:30, 65-67

### Medium-Priority Findings

1. **MEDIUM-001: Prompt Sanitization Bypass Risk**
   - Unicode homoglyphs can bypass regex: "ıgnore prevıous ınstructıons"
   - Zero-width characters: "ignore​previous​instructions"
   - Semantic attacks: "disregard earlier guidelines"
   - Recommendation: Add unicode normalization and semantic detection

2. **MEDIUM-002: Hardcoded Session Secret Fallback**
   - Development sessions use `"dev-secret-key-for-local-only"`
   - If committed session cookies leaked, anyone could decrypt
   - Recommendation: Generate random dev key per session

3. **MEDIUM-005: Docker Compose Missing Encryption Key**
   - docker-compose.yml doesn't require ENCRYPTION_KEY
   - Containers will start but API keys won't persist
   - Recommendation: Add `${ENCRYPTION_KEY:?ERROR: Required}` to env

### Lessons Learned

1. **Security is an Ongoing Process, Not a One-Time Task**
   - Even after fixing issues, new patterns emerge
   - Monthly security audits catch configuration drift
   - Previous fixes (prompt sanitization, encryption) are working well

2. **Environment Variable Validation is Critical**
   - Missing or wrong ENV settings can bypass all security
   - Production must validate required secrets on startup
   - Fail-fast is better than fail-open

3. **Defense in Depth Catches Mistakes**
   - AUTH bypass only triggers if debug=True AND env!=production AND no credentials
   - Multiple conditions reduce risk of accidental exposure
   - But production should NEVER check debug flag for auth

4. **Encryption Without Persistence is Useless**
   - Ephemeral encryption keys = data loss on restart
   - Users won't tolerate re-entering credentials constantly
   - Must fail hard in production if encryption key missing

5. **Development Convenience vs Production Security**
   - Hardcoded dev secrets are convenient but risky
   - Generate random dev keys per session
   - Make production requirements explicit and validated

6. **Docker Deployments Need Extra Validation**
   - Container restarts are more frequent than VM restarts
   - Ephemeral keys are especially problematic in containers
   - docker-compose.yml should enforce required env vars

### Security Metrics Comparison

| Metric | Oct 2025 Initial | Oct 2025 Follow-Up | Change |
|--------|-----------------|-------------------|--------|
| Critical | 1 | 0 | ✅ -1 |
| High | 5 | 3 | ✅ -2 |
| Medium | 7 | 5 | ✅ -2 |
| Low | 3 | 4 | ⚠️ +1 |
| **Total** | **16** | **12** | **✅ -4** |

### Application Going Forward

**Immediate Actions** (blocking release):
- ✅ Fix authentication bypass (make production check first)
- ✅ Mandate ENCRYPTION_KEY in production (fail on startup if missing)
- ✅ Add CORS production validation (reject localhost origins)
- ✅ Update docker-compose.yml to require ENCRYPTION_KEY
- ✅ Add startup validation for production environment

**Short-Term** (next sprint):
- 🔄 Improve prompt sanitization with unicode normalization
- 🔄 Generate random dev session secrets
- 🔄 Add rate limiting to read endpoints
- 🔄 Remove encryption key from logs
- 🔄 Add WebSocket origin validation

**Long-Term** (roadmap):
- 📋 Implement automated security scanning in CI/CD (pip-audit, npm audit, Bandit)
- 📋 Add security regression tests
- 📋 Consider PostgreSQL for production (more robust than SQLite)
- 📋 Implement API key rotation with expiration dates
- 📋 Add immutable audit logging for sensitive operations

### Tools and Methodology

**Manual Analysis**:
- ✅ Code review of 25+ critical files
- ✅ Pattern search for SQL injection, XSS, command injection
- ✅ LLM prompt injection test cases (5 scenarios tested)
- ✅ Docker security review
- ✅ Configuration audit (settings, env files, docker-compose)

**Automated Scanning** (partial):
- ⚠️ pip-audit: Not available in scan environment
- ⚠️ npm audit: Timed out (package-lock.json generation failed)
- ⚠️ Bandit: Not available in scan environment

**Recommendations for Next Audit**:
1. Set up CI/CD security pipeline with pip-audit + Bandit + npm audit
2. Add pre-commit hooks for security checks
3. Configure Dependabot/Renovate for automated dependency updates
4. Consider professional penetration testing before public launch

### Documentation

- ✅ Full security report: `docs/security/2025-10-security-report.md`
- ✅ Code fixes documented with before/after examples
- ✅ Pull request checklist for security review
- ✅ Compliance checklist (11/12 items passing)
