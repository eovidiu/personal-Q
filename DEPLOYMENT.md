# Deployment Guide

This guide covers multiple deployment options for the Personal-Q AI Agent Management System.

## Quick Local Deployment

### Prerequisites
- Docker and Docker Compose installed
- Git

### Steps
```bash
git clone https://github.com/eovidiu/personal-Q.git
cd personal-Q
make start
```

Access the application:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/v1/docs

## Cloud Deployment Options

### Option 1: Railway (Recommended for Easy Deployment)

Railway offers free tier and simple deployment from GitHub.

1. **Sign up** at [railway.app](https://railway.app)
2. **Create New Project** → Deploy from GitHub repo
3. **Select your repository**: `eovidiu/personal-Q`
4. **Add Services**:
   - Redis (from Railway marketplace)
   - Backend (from your repo, `backend` directory)
   - Frontend (from your repo, root directory)

**Backend Environment Variables**:
```env
DATABASE_URL=sqlite:///./data/personal_q.db
CHROMA_DB_PATH=./data/chromadb
REDIS_URL=${REDIS_URL}
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
PORT=8000
```

**Frontend Environment Variables**:
```env
VITE_API_BASE_URL=https://your-backend.railway.app
```

### Option 2: Render

1. **Sign up** at [render.com](https://render.com)
2. **Create Web Services**:

**Backend Service**:
- **Build Command**: `cd backend && pip install -r requirements.txt`
- **Start Command**: `cd backend && python app/main.py`
- **Environment Variables**: Same as Railway

**Frontend Service**:
- **Build Command**: `npm install && npm run build`
- **Start Command**: `npm run preview`
- **Environment Variable**: `VITE_API_BASE_URL`

**Redis Service**:
- Add Redis from Render marketplace

### Option 3: Fly.io

1. Install flyctl: `curl -L https://fly.io/install.sh | sh`
2. Login: `flyctl auth login`
3. Deploy:

```bash
# Deploy backend
cd backend
flyctl launch --name personal-q-backend
flyctl deploy

# Deploy frontend
cd ..
flyctl launch --name personal-q-frontend
flyctl deploy
```

### Option 4: Docker Hub + Any VPS

1. **Build and push images**:
```bash
# Build backend
docker build -t yourusername/personal-q-backend:latest ./backend
docker push yourusername/personal-q-backend:latest

# Build frontend
docker build -t yourusername/personal-q-frontend:latest -f Dockerfile.frontend .
docker push yourusername/personal-q-frontend:latest
```

2. **On your VPS** (DigitalOcean, Linode, AWS EC2, etc.):
```bash
# Clone repo
git clone https://github.com/eovidiu/personal-Q.git
cd personal-Q

# Update docker-compose.yml to use your images
# Then start services
docker-compose up -d
```

### Option 5: Local with Ngrok (Development/Testing Only)

Run locally and expose via tunnel:

```bash
# Terminal 1: Start services
make start

# Terminal 2: Install and run ngrok
# Download from https://ngrok.com
ngrok http 5173  # Frontend
# Open another terminal for backend
ngrok http 8000  # Backend
```

## Environment Variables

### Required
- `DATABASE_URL`: SQLite database path
- `REDIS_URL`: Redis connection string
- `CELERY_BROKER_URL`: Celery broker URL (usually same as Redis)

### Optional (for integrations)
- `OPENAI_API_KEY`: For OpenAI models
- `ANTHROPIC_API_KEY`: For Claude models
- `SLACK_BOT_TOKEN`: For Slack integration
- `MICROSOFT_CLIENT_ID`: For Microsoft Graph
- `MICROSOFT_CLIENT_SECRET`: For Microsoft Graph
- `MICROSOFT_TENANT_ID`: For Microsoft Graph

## Configuration

### API Keys
Add your API keys through the web interface:
1. Navigate to Settings
2. Click "API Keys"
3. Add your keys for OpenAI, Anthropic, etc.

### External Integrations
Configure integrations in Settings → Integrations:
- Slack workspace connection
- Microsoft 365 account
- Obsidian vault path

## Monitoring

### Health Checks
- Backend: `GET /health`
- Redis: Check logs with `docker logs personal-q-redis`

### Logs
```bash
# View all logs
make logs

# View specific service
docker logs personal-q-backend
docker logs personal-q-frontend
docker logs personal-q-celery-worker
```

## Troubleshooting

### Build Issues
If Docker build fails with dependency conflicts:
```bash
# Clean rebuild
make clean
docker system prune -a
make start
```

### Database Issues
```bash
# Reset database
docker-compose down -v
rm -rf backend/data
docker-compose up -d
```

### Port Conflicts
If ports 5173 or 8000 are in use, edit `docker-compose.yml`:
```yaml
ports:
  - "3000:5173"  # Change frontend port
  - "9000:8000"  # Change backend port
```

## Production Recommendations

1. **Use PostgreSQL** instead of SQLite for better concurrency
2. **Set up SSL/TLS** with Let's Encrypt
3. **Configure firewall** rules
4. **Set up monitoring** (Sentry, DataDog, etc.)
5. **Regular backups** of database and ChromaDB data
6. **Use secrets management** (AWS Secrets Manager, HashiCorp Vault)
7. **Set up CI/CD** with GitHub Actions

## Support

For issues or questions:
- GitHub Issues: https://github.com/eovidiu/personal-Q/issues
- Documentation: See README.md
