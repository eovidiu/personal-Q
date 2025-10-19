# CI/CD Setup Guide

Comprehensive guide for setting up Continuous Integration and Continuous Deployment for the Personal-Q AI Agent Manager application.

## Table of Contents

- [Overview](#overview)
- [GitHub Actions Workflows](#github-actions-workflows)
- [Environment Setup](#environment-setup)
- [Deployment Strategies](#deployment-strategies)
- [Security Best Practices](#security-best-practices)
- [Monitoring and Notifications](#monitoring-and-notifications)
- [Troubleshooting](#troubleshooting)

---

## Overview

This project uses **GitHub Actions** for CI/CD, with separate workflows for:

1. **Testing** - Run on every push and PR
2. **Security Scanning** - Run nightly and on security-sensitive changes
3. **Deployment** - Deploy to staging/production on merge to main

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Developer pushes to feature branch                     │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│  GitHub Actions: Test Workflow                          │
│  - Backend unit tests (pytest)                          │
│  - Frontend E2E tests (Playwright)                      │
│  - Linting and type checking                            │
│  - Security scanning                                    │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓ (if tests pass)
┌─────────────────────────────────────────────────────────┐
│  Create Pull Request                                    │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓ (after review and approval)
┌─────────────────────────────────────────────────────────┐
│  Merge to main branch                                   │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│  GitHub Actions: Deploy Workflow                        │
│  - Deploy to staging                                    │
│  - Run smoke tests                                      │
│  - Deploy to production (manual approval)               │
└─────────────────────────────────────────────────────────┘
```

---

## GitHub Actions Workflows

### 1. Test Workflow

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  workflow_dispatch:

jobs:
  backend-tests:
    name: Backend Tests
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: personal_q_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend
          pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run linting
        run: |
          cd backend
          ruff check app/

      - name: Run type checking
        run: |
          cd backend
          mypy app/

      - name: Run tests with coverage
        env:
          ENV: test
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/personal_q_test
          REDIS_URL: redis://localhost:6379/0
          JWT_SECRET_KEY: test_secret_key_at_least_32_characters_long
          ALLOWED_EMAIL: test@example.com
        run: |
          cd backend
          pytest --cov=app --cov-report=xml --cov-report=term

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./backend/coverage.xml
          flags: backend
          name: backend-coverage

  frontend-tests:
    name: Frontend Tests
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: personal_q_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run linting
        run: npm run lint

      - name: Run type checking
        run: npx tsc --noEmit

      - name: Set up Python 3.11 (for backend)
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install backend dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Start backend server
        env:
          ENV: development
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/personal_q_test
          REDIS_URL: redis://localhost:6379/0
          JWT_SECRET_KEY: test_secret_key_at_least_32_characters_long
          ALLOWED_EMAIL: test@example.com
        run: |
          cd backend
          alembic upgrade head
          uvicorn app.main:app --host 0.0.0.0 --port 8000 &
          sleep 5

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Build frontend
        env:
          VITE_API_BASE_URL: http://localhost:8000
        run: npm run build

      - name: Run Playwright tests
        env:
          VITE_API_BASE_URL: http://localhost:8000
          ALLOWED_EMAIL: test@example.com
        run: npx playwright test

      - name: Upload Playwright report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30

  security-scan:
    name: Security Scanning
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Run Bandit security linter
        run: |
          pip install bandit
          bandit -r backend/app/ -f json -o bandit-report.json || true

      - name: Run npm audit
        run: |
          npm audit --audit-level=moderate || true

      - name: Check for secrets
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          head: HEAD
```

### 2. Security Scanning Workflow

Create `.github/workflows/security.yml`:

```yaml
name: Security Scan

on:
  schedule:
    # Run nightly at 2 AM UTC
    - cron: '0 2 * * *'
  workflow_dispatch:

jobs:
  dependency-scan:
    name: Dependency Security Scan
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Check Python dependencies
        run: |
          pip install safety
          cd backend
          safety check --json

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Check npm dependencies
        run: |
          npm audit --audit-level=moderate

  code-scan:
    name: Code Security Scan
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: python, javascript

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3

  container-scan:
    name: Container Security Scan
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Build Docker images
        run: docker-compose build

      - name: Run Trivy on backend image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'personal-q-backend:latest'
          format: 'sarif'
          output: 'trivy-backend.sarif'

      - name: Run Trivy on frontend image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'personal-q-frontend:latest'
          format: 'sarif'
          output: 'trivy-frontend.sarif'

      - name: Upload results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: '.'
```

### 3. Deployment Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [ main ]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        type: choice
        options:
          - staging
          - production

jobs:
  build:
    name: Build and Push Images
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=ref,event=branch
            type=sha,prefix={{branch}}-
            type=semver,pattern={{version}}

      - name: Build and push backend
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: ghcr.io/${{ github.repository }}/backend:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build and push frontend
        uses: docker/build-push-action@v5
        with:
          context: .
          file: Dockerfile
          push: true
          tags: ghcr.io/${{ github.repository }}/frontend:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    environment:
      name: staging
      url: https://staging.your-domain.com

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy to staging
        run: |
          # Replace with your deployment method
          # Examples: AWS ECS, Kubernetes, Docker Swarm, etc.

          # Example for SSH deployment:
          echo "${{ secrets.STAGING_SSH_KEY }}" > deploy_key
          chmod 600 deploy_key
          ssh -i deploy_key -o StrictHostKeyChecking=no ${{ secrets.STAGING_USER }}@${{ secrets.STAGING_HOST }} << 'EOF'
            cd /app/personal-q
            docker-compose pull
            docker-compose up -d
            docker-compose exec -T backend alembic upgrade head
          EOF

      - name: Run smoke tests
        run: |
          sleep 10  # Wait for services to start
          curl -f https://staging.your-domain.com/health || exit 1

      - name: Notify deployment
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Staging deployment ${{ job.status }}'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: deploy-staging
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://your-domain.com

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Create backup
        run: |
          # Backup database before deployment
          echo "${{ secrets.PROD_SSH_KEY }}" > deploy_key
          chmod 600 deploy_key
          ssh -i deploy_key ${{ secrets.PROD_USER }}@${{ secrets.PROD_HOST }} << 'EOF'
            docker-compose exec -T backend pg_dump -U postgres personal_q > backup_$(date +%Y%m%d_%H%M%S).sql
          EOF

      - name: Deploy to production
        run: |
          echo "${{ secrets.PROD_SSH_KEY }}" > deploy_key
          chmod 600 deploy_key
          ssh -i deploy_key ${{ secrets.PROD_USER }}@${{ secrets.PROD_HOST }} << 'EOF'
            cd /app/personal-q
            docker-compose pull
            docker-compose up -d
            docker-compose exec -T backend alembic upgrade head
          EOF

      - name: Verify deployment
        run: |
          sleep 10
          curl -f https://your-domain.com/health || exit 1

      - name: Run production smoke tests
        run: |
          # Add your smoke tests here
          curl -f https://your-domain.com/api/v1/auth/validate || exit 1

      - name: Verify test auth disabled
        run: |
          # CRITICAL: Ensure test auth endpoint returns 404
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://your-domain.com/api/v1/auth/test-login)
          if [ "$STATUS" != "404" ]; then
            echo "ERROR: Test auth endpoint is accessible in production!"
            exit 1
          fi

      - name: Notify deployment
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Production deployment ${{ job.status }}'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## Environment Setup

### GitHub Secrets

Configure these secrets in **Settings → Secrets and variables → Actions**:

#### General Secrets

```
CODECOV_TOKEN               # For code coverage reporting
SLACK_WEBHOOK              # For deployment notifications
```

#### Staging Environment Secrets

```
STAGING_SSH_KEY            # SSH private key for staging server
STAGING_USER               # SSH username for staging
STAGING_HOST               # Staging server hostname/IP
STAGING_ENV_FILE           # Complete .env file for staging (base64 encoded)
```

#### Production Environment Secrets

```
PROD_SSH_KEY               # SSH private key for production server
PROD_USER                  # SSH username for production
PROD_HOST                  # Production server hostname/IP
PROD_ENV_FILE              # Complete .env file for production (base64 encoded)

# Application secrets
PROD_JWT_SECRET_KEY        # JWT secret (32+ characters)
PROD_GOOGLE_CLIENT_ID      # Google OAuth client ID
PROD_GOOGLE_CLIENT_SECRET  # Google OAuth client secret
PROD_ALLOWED_EMAIL         # Admin email address
PROD_DATABASE_URL          # PostgreSQL connection string
PROD_REDIS_URL             # Redis connection string
```

### Environment Configuration

#### Staging Environment Variables

Create base64-encoded .env file:

```bash
# Create staging.env
cat > staging.env << 'EOF'
ENV=development
DEBUG=true
JWT_SECRET_KEY=staging_secret_key_at_least_32_characters
GOOGLE_CLIENT_ID=your-staging-client-id
GOOGLE_CLIENT_SECRET=your-staging-client-secret
ALLOWED_EMAIL=your-email@example.com
DATABASE_URL=postgresql://user:pass@staging-db:5432/personal_q
REDIS_URL=redis://staging-redis:6379/0
CORS_ORIGINS=["https://staging.your-domain.com"]
EOF

# Encode to base64
base64 staging.env > staging.env.b64

# Add to GitHub secrets as STAGING_ENV_FILE
```

#### Production Environment Variables

Create base64-encoded .env file:

```bash
# Create production.env
cat > production.env << 'EOF'
ENV=production
DEBUG=false
JWT_SECRET_KEY=<strong-random-secret-32+-characters>
GOOGLE_CLIENT_ID=<production-oauth-client-id>
GOOGLE_CLIENT_SECRET=<production-oauth-client-secret>
ALLOWED_EMAIL=admin@your-domain.com
DATABASE_URL=postgresql://user:pass@prod-db:5432/personal_q
REDIS_URL=redis://prod-redis:6379/0
CORS_ORIGINS=["https://your-domain.com"]
EOF

# Encode to base64
base64 production.env > production.env.b64

# Add to GitHub secrets as PROD_ENV_FILE
```

### GitHub Environments

Create environments in **Settings → Environments**:

#### Staging Environment

- **Name**: `staging`
- **Protection rules**: None (auto-deploy)
- **Secrets**: STAGING_SSH_KEY, STAGING_USER, STAGING_HOST, STAGING_ENV_FILE
- **Variables**:
  - `URL`: https://staging.your-domain.com
  - `API_URL`: https://api-staging.your-domain.com

#### Production Environment

- **Name**: `production`
- **Protection rules**:
  - ✅ Required reviewers: [Select reviewers]
  - ✅ Wait timer: 5 minutes
  - ✅ Deployment branches: `main` only
- **Secrets**: PROD_SSH_KEY, PROD_USER, PROD_HOST, PROD_ENV_FILE, etc.
- **Variables**:
  - `URL`: https://your-domain.com
  - `API_URL`: https://api.your-domain.com

---

## Deployment Strategies

### Blue-Green Deployment

Recommended for zero-downtime deployments:

```yaml
# .github/workflows/blue-green-deploy.yml
- name: Deploy with blue-green strategy
  run: |
    ssh ${{ secrets.PROD_USER }}@${{ secrets.PROD_HOST }} << 'EOF'
      cd /app/personal-q

      # Start green environment
      docker-compose -f docker-compose.green.yml up -d

      # Wait for health check
      sleep 10
      curl -f http://localhost:8001/health || exit 1

      # Switch traffic to green
      # (Update load balancer or nginx config)

      # Stop blue environment
      docker-compose -f docker-compose.blue.yml down

      # Rename: green becomes blue
      mv docker-compose.green.yml docker-compose.blue.yml
    EOF
```

### Canary Deployment

Gradual rollout to subset of users:

```yaml
- name: Canary deployment (10%)
  run: |
    # Deploy to 10% of servers
    # Monitor error rates
    # If stable, proceed to 50%, then 100%
```

### Rolling Deployment

For Kubernetes:

```yaml
- name: Rolling deployment
  run: |
    kubectl set image deployment/personal-q-backend \
      backend=ghcr.io/${{ github.repository }}/backend:${{ github.sha }}

    kubectl rollout status deployment/personal-q-backend
```

---

## Security Best Practices

### Secret Management

1. **Never commit secrets** to git
2. **Rotate secrets** regularly
3. **Use environment-specific secrets** (staging ≠ production)
4. **Encrypt sensitive data** in GitHub secrets
5. **Limit secret access** to required workflows only

### Deployment Security

1. **Use SSH keys** instead of passwords
2. **Verify checksums** of deployed artifacts
3. **Sign commits** with GPG
4. **Enable branch protection** on main
5. **Require status checks** before merging

### Container Security

1. **Scan images** for vulnerabilities (Trivy)
2. **Use specific tags** (not `latest`)
3. **Run as non-root** user
4. **Minimize image size** (multi-stage builds)
5. **Keep base images updated**

### Access Control

1. **Use OIDC** for AWS/GCP authentication
2. **Limit workflow permissions** to minimum required
3. **Enable audit logging**
4. **Review access** regularly
5. **Use environment protection rules**

---

## Monitoring and Notifications

### Slack Notifications

```yaml
- name: Notify Slack on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: |
      Deployment failed!
      Repository: ${{ github.repository }}
      Branch: ${{ github.ref }}
      Commit: ${{ github.sha }}
      Author: ${{ github.actor }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Email Notifications

Configure in **Settings → Notifications** for:
- Failed workflow runs
- Successful deployments to production
- Security alerts

### Status Badges

Add to README.md:

```markdown
![Tests](https://github.com/yourusername/personal-Q/workflows/Tests/badge.svg)
![Security](https://github.com/yourusername/personal-Q/workflows/Security%20Scan/badge.svg)
![Deploy](https://github.com/yourusername/personal-Q/workflows/Deploy/badge.svg)
```

---

## Troubleshooting

### Common Issues

#### 1. Tests Failing in CI but Passing Locally

**Cause**: Environment differences, timing issues, port conflicts

**Fix**:
```yaml
# Add debug output
- name: Debug environment
  run: |
    echo "Node version: $(node --version)"
    echo "Python version: $(python --version)"
    echo "Working directory: $(pwd)"
    ls -la

# Increase timeouts for E2E tests
- name: Run Playwright tests
  run: npx playwright test --timeout=60000
```

#### 2. Deployment Fails with "Connection Refused"

**Cause**: SSH key not configured or firewall blocking

**Fix**:
```yaml
# Test SSH connection first
- name: Test SSH connection
  run: |
    echo "${{ secrets.PROD_SSH_KEY }}" > key
    chmod 600 key
    ssh -i key -o StrictHostKeyChecking=no \
      ${{ secrets.PROD_USER }}@${{ secrets.PROD_HOST }} \
      "echo 'SSH connection successful'"
```

#### 3. Docker Build Fails with "No Space Left"

**Cause**: GitHub runner out of disk space

**Fix**:
```yaml
# Clean up before build
- name: Free disk space
  run: |
    sudo rm -rf /usr/share/dotnet
    sudo rm -rf /opt/ghc
    sudo rm -rf "/usr/local/share/boost"
    df -h
```

#### 4. Database Migration Fails

**Cause**: Migration conflict or database locked

**Fix**:
```yaml
# Run migrations with retry
- name: Run migrations with retry
  run: |
    for i in {1..3}; do
      docker-compose exec -T backend alembic upgrade head && break
      echo "Migration failed, retrying in 5s..."
      sleep 5
    done
```

#### 5. Environment Variables Not Set

**Cause**: Secrets not configured or wrong environment

**Fix**:
```yaml
# Verify secrets are set
- name: Verify environment
  run: |
    if [ -z "${{ secrets.PROD_JWT_SECRET_KEY }}" ]; then
      echo "ERROR: PROD_JWT_SECRET_KEY not set"
      exit 1
    fi
    echo "All secrets configured ✓"
```

### Debug Mode

Enable debug logging:

```yaml
- name: Enable debug logging
  run: |
    echo "ACTIONS_RUNNER_DEBUG=true" >> $GITHUB_ENV
    echo "ACTIONS_STEP_DEBUG=true" >> $GITHUB_ENV
```

### Manual Workflow Dispatch

Trigger workflows manually with custom parameters:

```yaml
on:
  workflow_dispatch:
    inputs:
      log_level:
        description: 'Log level'
        required: true
        default: 'info'
        type: choice
        options:
          - debug
          - info
          - warning
          - error
```

---

## Best Practices

### Workflow Organization

1. **Separate concerns**: Testing, security, deployment in different workflows
2. **Reusable workflows**: Extract common steps
3. **Conditional execution**: Only run necessary jobs
4. **Parallelization**: Run independent jobs concurrently
5. **Caching**: Cache dependencies to speed up builds

### Testing in CI

1. **Run fast tests first**: Unit tests before E2E tests
2. **Fail fast**: Use `-x` flag for pytest
3. **Parallel execution**: Run tests concurrently when possible
4. **Retry flaky tests**: Use `--retries` for Playwright
5. **Upload artifacts**: Save test reports and screenshots

### Deployment Safety

1. **Staging first**: Always deploy to staging before production
2. **Smoke tests**: Run basic health checks after deployment
3. **Rollback plan**: Have automated rollback ready
4. **Gradual rollout**: Use canary or blue-green deployments
5. **Monitor metrics**: Track error rates and performance

### Documentation

1. **Document workflows**: Add comments explaining complex steps
2. **Runbook**: Create troubleshooting guide
3. **Change log**: Track what was deployed when
4. **Rollback procedure**: Document how to rollback
5. **Contact info**: List who to contact for issues

---

## Example: Complete Deployment Flow

```mermaid
graph TB
    A[Push to main] --> B[Build Images]
    B --> C[Run Tests]
    C -->|Pass| D[Deploy to Staging]
    C -->|Fail| Z[Notify Team]
    D --> E[Run Smoke Tests]
    E -->|Pass| F[Await Approval]
    E -->|Fail| Y[Rollback Staging]
    F -->|Approved| G[Backup Production DB]
    G --> H[Deploy to Production]
    H --> I[Run Production Tests]
    I -->|Pass| J[Verify Test Auth Disabled]
    J -->|Pass| K[Monitor Metrics]
    J -->|Fail| X[Emergency Rollback]
    I -->|Fail| X
    K --> L[Deployment Complete]
    X --> W[Notify Team]
```

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes Deployment Strategies](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Testing Guide](./testing-guide.md)
- [Validation Checklist](./validation-checklist.md)
- [Production Deployment Guide](./spec/phase-5-deployment-production-guide.md)
