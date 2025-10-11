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
