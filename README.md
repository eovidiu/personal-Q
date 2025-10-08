# Personal-Q AI Agent Management System

A comprehensive, locally-run AI agent management platform with CrewAI orchestration, Claude integration, and real-time monitoring.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Node](https://img.shields.io/badge/node-20+-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

## Features

### Core Capabilities
- **Multi-Agent Orchestration**: CrewAI-powered agent collaboration with sequential and hierarchical workflows
- **LLM Integration**: Claude (Anthropic) integration with streaming support
- **Task Management**: Async task queue with Celery + Redis for background processing
- **Memory & Context**: ChromaDB-based vector storage for semantic search and RAG
- **Real-time Updates**: WebSocket communication for live agent status and activity feeds
- **External Integrations**: Slack, Outlook, OneDrive, and Obsidian connectivity

### Agent Features
- Create and configure custom AI agents
- Multiple agent types: Conversational, Analytical, Creative, Automation
- Configurable LLM parameters (temperature, max tokens, system prompts)
- Agent-to-agent communication (A2A)
- Real-time metrics and performance tracking
- Task scheduling with cron expressions

### Management & Monitoring
- Comprehensive dashboard with live statistics
- Agent activity logs and history
- Task execution tracking
- Success rate and uptime metrics
- API key management with connection testing

### Data & Storage
- Embedded SQLite for structured data
- ChromaDB for vector embeddings
- 90-day retention policy
- No internet required for database operations
- Fully portable single-directory deployment

## Quick Start

### With Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/eovidiu/personal-Q.git
cd personal-Q

# Start all services
make start

# Initialize database with sample data
make init-db

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/api/v1/docs
```

### Manual Installation

See [Installation Guide](docs/INSTALLATION.md) for detailed setup instructions.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Frontend (React)                       │
│              Vite + TypeScript + TailwindCSS                 │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API / WebSocket
┌────────────────────────┴────────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Agents     │  │    Tasks     │  │  Activities  │      │
│  │   Service    │  │   Service    │  │   Service    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│  ┌──────┴──────────────────┴──────────────────┴───────┐    │
│  │              CrewAI Orchestration                    │    │
│  │        (Multi-Agent Task Execution)                  │    │
│  └──────────────────────┬───────────────────────────────┘    │
│                         │                                     │
│  ┌──────────────────────┴───────────────────────────────┐   │
│  │           LLM Service (Claude/Anthropic)              │   │
│  └───────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                  Storage & Queue Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   SQLite     │  │   ChromaDB   │  │  Redis +     │      │
│  │  (Agents,    │  │  (Vectors,   │  │  Celery      │      │
│  │   Tasks)     │  │   Memory)    │  │  (Queue)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│              External Integrations                           │
│    Slack  │  Outlook  │  OneDrive  │  Obsidian             │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

**Frontend**
- React 19 + TypeScript
- Vite (build tool)
- TailwindCSS + shadcn/ui
- WebSocket client

**Backend**
- FastAPI (Python 3.11+)
- SQLAlchemy (async ORM)
- Alembic (migrations)
- Celery + Redis (task queue)
- CrewAI (agent orchestration)

**Databases**
- SQLite (structured data)
- ChromaDB (vector embeddings)

**External APIs**
- Anthropic Claude (LLM)
- Slack SDK
- Microsoft Graph API
- Obsidian (local file I/O)

## Project Structure

```
personal-Q/
├── backend/
│   ├── app/
│   │   ├── db/              # Database connections
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── routers/         # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── integrations/    # External APIs
│   │   └── workers/         # Celery tasks
│   ├── config/              # Settings
│   ├── migrations/          # Alembic migrations
│   └── tests/               # Test suite
├── src/                     # Frontend source
├── docs/                    # Documentation
├── docker-compose.yml       # Docker orchestration
└── Makefile                 # Commands
```

## Documentation

- [Installation Guide](docs/INSTALLATION.md) - Complete setup instructions
- [User Guide](docs/USER_GUIDE.md) - Using the application (TODO)
- [Agent Creation Tutorial](docs/AGENT_CREATION.md) - Creating custom agents (TODO)
- [API Documentation](http://localhost:8000/api/v1/docs) - Interactive API docs (when running)
- [Developer Guide](backend/README.md) - Backend development guide

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# With coverage
pytest --cov=app --cov-report=html

# Frontend tests
npm test
```

### Commands

```bash
make start      # Start all services
make stop       # Stop all services
make restart    # Restart all services
make logs       # View logs
make clean      # Remove volumes and data
make test       # Run tests
make init-db    # Initialize database
```

## Configuration

Configure API keys and settings via the Settings page in the UI:

1. **Anthropic Claude**: Required for LLM functionality
2. **Slack**: Optional, for Slack bot capabilities
3. **Microsoft Graph**: Optional, for Outlook/OneDrive access
4. **Obsidian**: Optional, set vault path for note management

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Claude Code](https://claude.com/claude-code)
- Powered by [CrewAI](https://github.com/joaomdmoura/crewAI)
- UI components from [shadcn/ui](https://ui.shadcn.com/)
- LLM by [Anthropic Claude](https://www.anthropic.com/)

## Support

- Issues: [GitHub Issues](https://github.com/eovidiu/personal-Q/issues)
- Documentation: [/docs](docs/)
- API Docs: http://localhost:8000/api/v1/docs (when running)

---

**Personal-Q** - Your Personal AI Agent Orchestration Platform

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
