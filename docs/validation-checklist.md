# Production Validation Checklist

Comprehensive checklist for validating the Personal-Q AI Agent Manager application before and after deployment to production.

## Table of Contents

- [Pre-Deployment Validation](#pre-deployment-validation)
- [Security Validation](#security-validation)
- [Performance Validation](#performance-validation)
- [Database Validation](#database-validation)
- [Environment Validation](#environment-validation)
- [Post-Deployment Validation](#post-deployment-validation)
- [Monitoring Setup](#monitoring-setup)
- [Rollback Plan](#rollback-plan)

---

## Pre-Deployment Validation

### Code Quality

- [ ] All tests passing locally
  ```bash
  cd backend && pytest --cov=app
  npx playwright test
  ```
- [ ] Code coverage ≥ 90%
- [ ] No critical security vulnerabilities
  ```bash
  pip audit
  npm audit
  ```
- [ ] All linting checks pass
  ```bash
  cd backend && mypy app/
  npm run lint
  ```
- [ ] Type checking passes
  ```bash
  cd backend && mypy app/
  npx tsc --noEmit
  ```

### Dependencies

- [ ] All dependencies up to date
- [ ] No known security vulnerabilities in dependencies
- [ ] Production dependencies separated from dev dependencies
- [ ] requirements.txt and package.json locked to specific versions

### Documentation

- [ ] README.md up to date
- [ ] API documentation current
- [ ] Environment variables documented
- [ ] Deployment guide available
- [ ] Testing documentation complete

### Git Repository

- [ ] All changes committed
- [ ] No sensitive data in git history
- [ ] .gitignore properly configured
- [ ] All features merged to main branch
- [ ] Version tagged (e.g., v1.0.0)

---

## Security Validation

### Authentication & Authorization

- [ ] **CRITICAL**: Test auth endpoint disabled in production
  ```bash
  # Verify ENV=production in .env
  grep "^ENV=production" .env

  # Test endpoint should return 404
  curl -X POST https://your-domain.com/api/v1/auth/test-login \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com"}'
  # Expected: 404 Not Found
  ```

- [ ] Google OAuth configured correctly
  ```bash
  # Verify OAuth credentials set
  grep "^GOOGLE_CLIENT_ID=" .env
  grep "^GOOGLE_CLIENT_SECRET=" .env
  ```

- [ ] ALLOWED_EMAIL properly configured
  ```bash
  grep "^ALLOWED_EMAIL=" .env
  ```

- [ ] JWT_SECRET_KEY is strong (≥32 characters, random)
  ```bash
  # Should be at least 32 characters
  python -c "import os; key=os.getenv('JWT_SECRET_KEY'); print(f'Length: {len(key)}')"
  ```

- [ ] CORS origins restricted to production domains
  ```python
  # backend/app/main.py should have:
  # origins = ["https://your-production-domain.com"]
  ```

### API Security

- [ ] Rate limiting enabled on all auth endpoints
  ```bash
  # Test rate limiting
  for i in {1..15}; do
    curl -X POST http://localhost:8000/api/v1/auth/test-login \
      -H "Content-Type: application/json" \
      -d '{"email": "test@example.com"}'
  done
  # Should see 429 (Too Many Requests) after 10 requests
  ```

- [ ] All sensitive endpoints require authentication
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (proper escaping)

### Secrets Management

- [ ] No secrets in code or git history
- [ ] .env file in .gitignore
- [ ] Environment variables properly set in production
- [ ] API keys rotated from development values
- [ ] Database credentials strong and unique

### Network Security

- [ ] HTTPS/TLS enabled (production only)
- [ ] Security headers configured
  ```python
  # Should include:
  # - X-Content-Type-Options: nosniff
  # - X-Frame-Options: DENY
  # - X-XSS-Protection: 1; mode=block
  # - Strict-Transport-Security: max-age=31536000
  ```

---

## Performance Validation

### Backend Performance

- [ ] Database queries optimized (no N+1 queries)
- [ ] Indexes created on frequently queried columns
  ```sql
  -- Verify indexes
  SELECT * FROM sqlite_master WHERE type='index';
  ```

- [ ] Redis caching working
  ```bash
  docker exec personal-q-redis redis-cli ping
  # Expected: PONG

  # Check cache keys
  docker exec personal-q-redis redis-cli KEYS "*"
  ```

- [ ] Cache hit rate acceptable (≥50%)
- [ ] API response times < 500ms for 95th percentile
  ```bash
  # Test with ab (Apache Bench)
  ab -n 1000 -c 10 -H "Authorization: Bearer YOUR_TOKEN" \
    http://localhost:8000/api/v1/agents?skip=0&limit=10
  ```

### Frontend Performance

- [ ] Build size optimized
  ```bash
  npm run build
  ls -lh dist/assets/
  # Main bundle should be < 500KB
  ```

- [ ] Code splitting implemented
- [ ] Lazy loading for routes
- [ ] Images optimized
- [ ] First Contentful Paint < 2s
- [ ] Time to Interactive < 3s

### WebSocket Performance

- [ ] WebSocket connections stable
- [ ] Message latency < 100ms
- [ ] Reconnection logic working
- [ ] No memory leaks on long-lived connections
  ```bash
  # Monitor with browser DevTools Network tab
  # Keep connection open for 10+ minutes
  # Check memory usage stays stable
  ```

### Load Testing

- [ ] Application handles expected concurrent users
- [ ] Database connection pool sized appropriately
- [ ] Redis connection pool configured
- [ ] Memory usage stable under load
- [ ] No resource leaks

---

## Database Validation

### Schema Validation

- [ ] All migrations applied
  ```bash
  docker-compose exec backend alembic current
  docker-compose exec backend alembic heads
  # Should match
  ```

- [ ] Foreign key constraints working
- [ ] Indexes present on foreign keys
- [ ] Unique constraints validated
- [ ] Default values set correctly

### Data Integrity

- [ ] No orphaned records
  ```sql
  -- Check for activities without agents (should be minimal)
  SELECT COUNT(*) FROM activity WHERE agent_id IS NOT NULL
    AND agent_id NOT IN (SELECT id FROM agent);
  ```

- [ ] Timestamps use UTC
- [ ] Enum values consistent
- [ ] JSON fields valid

### Backup & Recovery

- [ ] Backup strategy defined
- [ ] Backup tested and working
  ```bash
  # For PostgreSQL
  docker-compose exec backend pg_dump -U postgres personal_q > backup.sql

  # For SQLite (development)
  cp backend/data/personal_q.db backend/data/personal_q_backup.db
  ```

- [ ] Recovery procedure documented
- [ ] Backup retention policy defined
- [ ] Point-in-time recovery tested

### Performance

- [ ] Query execution plans reviewed
  ```sql
  EXPLAIN QUERY PLAN SELECT * FROM agent WHERE status = 'active';
  ```

- [ ] Slow query log enabled and monitored
- [ ] Database statistics up to date
- [ ] Connection pooling configured

---

## Environment Validation

### Environment Variables

Required variables for production:

**Backend (.env):**
```bash
# Core
ENV=production
DEBUG=false

# Security
JWT_SECRET_KEY=<strong-random-32+-char-string>
GOOGLE_CLIENT_ID=<your-google-oauth-client-id>
GOOGLE_CLIENT_SECRET=<your-google-oauth-secret>
ALLOWED_EMAIL=<your-email@domain.com>

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://host:6379/0

# CORS (adjust to your domain)
CORS_ORIGINS=["https://your-domain.com"]
```

**Frontend (.env):**
```bash
VITE_API_BASE_URL=https://api.your-domain.com
VITE_GOOGLE_CLIENT_ID=<same-as-backend>
```

### Validation Commands

```bash
# Check all required variables are set
cd backend
python -c "
from app.config.settings import settings
print('ENV:', settings.env)
print('Debug:', settings.debug)
print('JWT Secret Length:', len(settings.jwt_secret_key))
print('Google Client ID set:', bool(settings.google_client_id))
print('Allowed Email:', settings.allowed_email)
print('Database URL:', settings.database_url.replace(settings.database_url.password, '***'))
print('Redis URL:', settings.redis_url)
"
```

### Checklist

- [ ] ENV=production
- [ ] DEBUG=false
- [ ] JWT_SECRET_KEY is strong and unique
- [ ] GOOGLE_CLIENT_ID matches OAuth app
- [ ] GOOGLE_CLIENT_SECRET set correctly
- [ ] ALLOWED_EMAIL set to admin email
- [ ] DATABASE_URL points to production database
- [ ] REDIS_URL points to production Redis
- [ ] CORS_ORIGINS restricted to production domain
- [ ] No test/development values in production

---

## Post-Deployment Validation

### Smoke Tests

Run immediately after deployment:

#### 1. Health Check
```bash
curl https://your-domain.com/health
# Expected: {"status": "healthy"}
```

#### 2. API Accessibility
```bash
curl https://api.your-domain.com/api/v1/auth/validate
# Should return validation response
```

#### 3. Authentication Flow
- [ ] Navigate to https://your-domain.com
- [ ] Click "Sign in with Google"
- [ ] Complete OAuth flow
- [ ] Verify redirected to /agents
- [ ] Verify email matches ALLOWED_EMAIL

#### 4. Core Functionality
- [ ] Create new agent
- [ ] Update agent settings
- [ ] View agent details
- [ ] Delete agent
- [ ] Check activity feed updates

#### 5. WebSocket Connection
- [ ] Open browser DevTools → Network → WS
- [ ] Verify WebSocket connection established
- [ ] Create/update agent
- [ ] Verify real-time update received

#### 6. Database Persistence
- [ ] Create agent
- [ ] Restart backend
  ```bash
  docker-compose restart backend
  ```
- [ ] Verify agent still exists
- [ ] Verify activity logged

#### 7. Cache Working
- [ ] Access agent detail page (should hit database)
- [ ] Refresh page (should hit cache - check logs)
- [ ] Update agent (should invalidate cache)
- [ ] Access agent detail again (should hit database)

### Production Test Endpoint Validation

**CRITICAL SECURITY CHECK**:

```bash
# Test auth endpoint should be DISABLED
curl -X POST https://your-domain.com/api/v1/auth/test-login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Expected: 404 Not Found
# If you get 200 OK, STOP and fix immediately - security breach!
```

```bash
# Validate endpoint should also be disabled
curl https://your-domain.com/api/v1/auth/test-validate

# Expected: 404 Not Found
```

### Monitoring Checks

- [ ] Application logs flowing to monitoring system
- [ ] Error tracking configured (Sentry, etc.)
- [ ] Performance metrics being collected
- [ ] Alerts configured for critical errors
- [ ] Database metrics monitored
- [ ] Redis metrics monitored

### Performance Verification

```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s https://api.your-domain.com/api/v1/agents

# curl-format.txt:
# time_namelookup: %{time_namelookup}\n
# time_connect: %{time_connect}\n
# time_starttransfer: %{time_starttransfer}\n
# time_total: %{time_total}\n
```

- [ ] API response time < 500ms
- [ ] Frontend load time < 3s
- [ ] WebSocket latency < 100ms
- [ ] Database query time < 100ms

---

## Monitoring Setup

### Application Monitoring

- [ ] Error tracking configured (Sentry, Rollbar, etc.)
- [ ] Log aggregation setup (CloudWatch, ELK, etc.)
- [ ] Uptime monitoring (UptimeRobot, Pingdom, etc.)
- [ ] Performance monitoring (New Relic, Datadog, etc.)

### Alerts Configuration

Configure alerts for:

- [ ] Application errors (500 errors)
- [ ] High response times (>1s)
- [ ] Database connection failures
- [ ] Redis connection failures
- [ ] Disk space < 20%
- [ ] Memory usage > 80%
- [ ] CPU usage > 80%
- [ ] Failed authentication attempts (>10/min)

### Metrics to Track

**Backend:**
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (errors/second)
- Database query count
- Cache hit rate
- Active WebSocket connections

**Frontend:**
- Page load time
- First Contentful Paint
- Time to Interactive
- JavaScript errors
- API call failures

**Infrastructure:**
- CPU utilization
- Memory utilization
- Disk I/O
- Network I/O
- Database connections
- Redis connections

---

## Rollback Plan

### Preparation

- [ ] Previous version tagged in git
- [ ] Database backup taken immediately before deployment
- [ ] Rollback procedure documented
- [ ] Rollback tested in staging

### Rollback Triggers

Rollback if:
- Error rate > 5% for 5 minutes
- Response time > 2x baseline for 10 minutes
- Critical functionality broken
- Security vulnerability discovered
- Data corruption detected

### Rollback Procedure

#### 1. Stop new deployment
```bash
# If using Docker
docker-compose down

# If using Kubernetes
kubectl rollout undo deployment/personal-q
```

#### 2. Restore previous version
```bash
# Git
git checkout <previous-version-tag>

# Docker
docker-compose up -d

# Or pull previous image
docker pull your-registry/personal-q:previous-version
```

#### 3. Database rollback (if needed)
```bash
# Restore from backup
psql -U postgres personal_q < backup.sql

# Or run down migration
docker-compose exec backend alembic downgrade -1
```

#### 4. Verify rollback successful
- [ ] Health check passing
- [ ] Authentication working
- [ ] Core functionality working
- [ ] No errors in logs

#### 5. Incident report
- [ ] Document what went wrong
- [ ] Root cause analysis
- [ ] Prevention measures
- [ ] Update deployment checklist

---

## Final Sign-Off

Before marking deployment complete:

- [ ] All pre-deployment checks passed
- [ ] All security validations passed
- [ ] All performance checks passed
- [ ] All smoke tests passed
- [ ] Monitoring and alerts configured
- [ ] Rollback plan tested and ready
- [ ] Team notified of deployment
- [ ] Documentation updated with production details

**Deployment approved by**: ___________________
**Date**: ___________________
**Version**: ___________________

---

## Quick Reference

### Essential Commands

```bash
# Health check
curl https://your-domain.com/health

# Check backend logs
docker-compose logs -f backend --tail 100

# Check frontend logs
docker-compose logs -f frontend --tail 100

# Check database
docker-compose exec backend alembic current

# Check Redis
docker exec personal-q-redis redis-cli ping

# Restart services
docker-compose restart backend
docker-compose restart frontend

# View active connections
docker-compose exec backend python -c "
from app.database import engine
print('Active connections:', engine.pool.size())
"
```

### Emergency Contacts

- **DevOps Lead**: [Contact info]
- **Backend Lead**: [Contact info]
- **Frontend Lead**: [Contact info]
- **Database Admin**: [Contact info]
- **Security Team**: [Contact info]

---

## Additional Resources

- [Testing Guide](./testing-guide.md)
- [Deployment Guide](../docs/spec/phase-5-deployment-production-guide.md)
- [API Documentation](./api-documentation.md)
- [CI/CD Setup](./ci-cd-setup.md)
