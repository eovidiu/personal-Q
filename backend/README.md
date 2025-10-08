# Personal-Q Backend

FastAPI backend for the Personal-Q AI Agent Management System.

## Features

- **FastAPI**: Modern, fast web framework
- **SQLite**: Embedded relational database for agent configuration and tasks
- **ChromaDB**: Vector database for agent memory and document embeddings
- **SQLAlchemy**: Async ORM for database operations
- **Alembic**: Database migrations
- **Pydantic**: Data validation and serialization

## Project Structure

```
backend/
├── app/
│   ├── db/               # Database configuration
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── routers/          # API endpoints
│   ├── services/         # Business logic
│   ├── integrations/     # External API clients
│   └── workers/          # Celery tasks
├── config/               # Application configuration
├── migrations/           # Alembic migrations
├── tests/                # Test suite
└── requirements.txt      # Python dependencies
```

## Setup

### Prerequisites

- Python 3.10+
- pip

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Initialize database:
```bash
python app/db/init_db.py
```

## Running

### Development

```bash
cd backend
python app/main.py
```

The API will be available at `http://localhost:8000`.

### API Documentation

- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

## Database

### Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

Run migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

### Initialization

Initialize database with sample data:
```bash
python app/db/init_db.py
```

## Testing

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

Run specific test file:
```bash
pytest tests/unit/test_models.py
```

## Models

- **Agent**: AI agent configuration and metadata
- **Task**: Work items assigned to agents
- **Activity**: System event logs
- **APIKey**: External service credentials
- **Schedule**: Recurring task schedules

## API Endpoints

### Agents
- `GET /api/v1/agents` - List agents
- `POST /api/v1/agents` - Create agent
- `GET /api/v1/agents/{id}` - Get agent details
- `PUT /api/v1/agents/{id}` - Update agent
- `DELETE /api/v1/agents/{id}` - Delete agent
- `PATCH /api/v1/agents/{id}/status` - Update agent status

### Tasks
- `GET /api/v1/tasks` - List tasks
- `POST /api/v1/tasks` - Create task
- `GET /api/v1/tasks/{id}` - Get task details
- `PATCH /api/v1/tasks/{id}` - Update task

### Activities
- `GET /api/v1/activities` - List recent activities

### Settings
- `GET /api/v1/settings` - Get all settings
- `PUT /api/v1/settings` - Update settings

### WebSocket
- `WS /ws` - WebSocket connection for real-time updates

## Development

### Code Style

- Use Black for formatting
- Follow PEP 8 guidelines
- Max line length: 100 characters

### Adding New Models

1. Create model in `app/models/`
2. Import in `app/models/__init__.py`
3. Create Pydantic schema in `app/schemas/`
4. Generate migration: `alembic revision --autogenerate`
5. Run migration: `alembic upgrade head`

### Adding New Endpoints

1. Create router in `app/routers/`
2. Import and include in `app/main.py`
3. Add tests in `tests/`

## License

MIT License - see LICENSE file for details
