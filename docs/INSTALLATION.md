# Installation Guide

Complete installation guide for Personal-Q AI Agent Management System.

## Prerequisites

- Docker & Docker Compose (recommended)
- OR Python 3.11+ and Node.js 20+ (for local development)

## Quick Start with Docker (Recommended)

1. **Clone the repository**:
```bash
git clone https://github.com/eovidiu/personal-Q.git
cd personal-Q
```

2. **Start all services**:
```bash
make start
```

3. **Initialize database with sample data**:
```bash
make init-db
```

4. **Access the application**:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/api/v1/docs

## Manual Installation (Local Development)

### Backend Setup

1. **Navigate to backend directory**:
```bash
cd backend
```

2. **Create virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**:
```bash
python app/db/init_db.py
```

6. **Start Redis** (required for Celery):
```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# OR install Redis locally
# macOS: brew install redis && brew services start redis
# Ubuntu: sudo apt install redis-server && sudo systemctl start redis
```

7. **Start backend server**:
```bash
python app/main.py
```

8. **Start Celery worker** (in new terminal):
```bash
celery -A app.workers.celery_app worker --loglevel=info
```

9. **Start Celery beat** (in new terminal):
```bash
celery -A app.workers.celery_app beat --loglevel=info
```

### Frontend Setup

1. **Navigate to project root**:
```bash
cd ..
```

2. **Install dependencies**:
```bash
npm install
```

3. **Start development server**:
```bash
npm run dev
```

4. **Access frontend**: http://localhost:5173

## Configuration

### API Keys

Configure external service API keys via the Settings page in the UI:

1. Navigate to Settings
2. Add API keys for:
   - **Anthropic Claude**: Required for LLM functionality
   - **Slack**: Optional, for Slack integration
   - **Microsoft Graph**: Optional, for Outlook/OneDrive integration
   - **Obsidian**: Optional, configure vault path

### Environment Variables

Backend `.env` file:
```env
# Application
APP_NAME=Personal-Q AI Agent Manager
ENV=development

# Database
DATABASE_URL=sqlite:///./data/personal_q.db
CHROMA_DB_PATH=./data/chromadb

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Memory
MEMORY_RETENTION_DAYS=90
```

## Verification

1. **Check backend health**:
```bash
curl http://localhost:8000/health
```

2. **Check API docs**:
Open http://localhost:8000/api/v1/docs in browser

3. **Check frontend**:
Open http://localhost:5173 in browser

4. **Check Redis**:
```bash
redis-cli ping
# Should return: PONG
```

5. **Check Celery**:
```bash
celery -A app.workers.celery_app inspect active
```

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (should be 3.11+)
- Check Redis is running: `redis-cli ping`
- Check database file permissions in `backend/data/`

### Frontend won't start
- Check Node version: `node --version` (should be 20+)
- Clear node_modules: `rm -rf node_modules && npm install`
- Check port 5173 is available

### Celery tasks not executing
- Ensure Redis is running
- Check Celery worker logs
- Verify `CELERY_BROKER_URL` in .env

### Database errors
- Remove and reinitialize: `rm backend/data/personal_q.db && python app/db/init_db.py`
- Check write permissions on `backend/data/` directory

## Next Steps

After installation:

1. Read the [User Guide](USER_GUIDE.md)
2. Learn [Agent Creation](AGENT_CREATION.md)
3. Explore [API Documentation](http://localhost:8000/api/v1/docs)
4. Check [Developer Guide](DEVELOPER_GUIDE.md) for customization

## Updating

### With Docker
```bash
git pull
docker-compose down
docker-compose build
make start
```

### Manual
```bash
git pull
cd backend && pip install -r requirements.txt
cd .. && npm install
# Restart all services
```
