id: rules.lang.python
version: 1.0.0
description: Python-specific programming guidelines for AI assistants
globs: ["**/*.py", "**/pyproject.toml", "**/requirements.txt", "**/Pipfile", "**/setup.py"]
tags: ["language", "python"]
---

# Python-Specific Guidelines

## Language-Specific Naming Conventions

### Semantic Naming Matrix
| Type | Pattern | Example |
|------|---------|---------|
| Classes | PascalCase | `DataProcessor`, `AuthenticationService` |
| Functions | snake_case | `validate_input()`, `process_request()` |
| Variables | snake_case | `user_count`, `is_authenticated` |
| Constants | SCREAMING_SNAKE | `MAX_RETRY_ATTEMPTS`, `DEFAULT_TIMEOUT` |
| Private methods | Leading underscore | `_internal_helper()` |
| Protected attributes | Single underscore | `_protected_var` |
| Module-private | Double underscore | `__private_var` |

## Code Examples

### Design Patterns

**Simplicity First (YAGNI)**:
```python
# BAD - Over-engineered
class AbstractToolFactory:
    def create_tool(self, config: ToolConfig) -> Tool:
        return self.get_builder(config).build()

# GOOD - Simple and sufficient
def create_tool(tool_type: str) -> Tool:
    return Tool(tool_type)
```

**Dependency Injection**:
```python
# GOOD - Testable and flexible
class EmailService:
    def __init__(self, smtp_client: SMTPClient):
        self._client = smtp_client
    
    def send(self, message: Message) -> None:
        self._client.send(message)

# BAD - Hard to test
class EmailService:
    def __init__(self):
        self._client = SMTPClient()  # Direct instantiation
```

## File Documentation Template

```python
"""
ABOUTME: Primary responsibility of this module
ABOUTME: Key patterns: [e.g., singleton, observer]
DEPENDENCIES: External libraries used
SECURITY: Any security considerations
PERFORMANCE: Known bottlenecks or optimizations

Example:
    >>> from module import function
    >>> result = function(param)
    >>> print(result)
"""

from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)
```

## Type Hints and Annotations

Always use type hints for function signatures:

```python
from typing import Optional, List, Dict, Union, Tuple, Any
from dataclasses import dataclass

@dataclass
class UserData:
    """User information container."""
    user_id: int
    username: str
    email: Optional[str] = None
    roles: List[str] = field(default_factory=list)

def process_users(
    users: List[UserData],
    filter_inactive: bool = True
) -> Dict[int, UserData]:
    """
    Process user data with optional filtering.
    
    Args:
        users: List of user data objects
        filter_inactive: Whether to filter inactive users
        
    Returns:
        Dictionary mapping user IDs to UserData objects
        
    Raises:
        ValueError: If users list is empty
    """
    if not users:
        raise ValueError("Users list cannot be empty")
    
    return {user.user_id: user for user in users}
```

## Error Handling

### Error Response Pattern
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import traceback

@dataclass
class ErrorResponse:
    """Standardized error response structure."""
    error_code: str  # e.g., "VALIDATION_ERROR"
    message: str      # User-friendly message
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp,
            'request_id': self.request_id
        }

# Usage example
try:
    result = risky_operation()
except ValidationError as e:
    error = ErrorResponse(
        error_code="VALIDATION_ERROR",
        message="Invalid input provided",
        details={'field': e.field, 'value': e.value}
    )
    logger.error(f"Validation failed: {error.to_dict()}")
    return error.to_dict(), 400
```

### Context Managers for Resource Management
```python
from contextlib import contextmanager
import time

@contextmanager
def timed_operation(operation_name: str):
    """Context manager for timing operations."""
    start = time.time()
    try:
        logger.info(f"Starting {operation_name}")
        yield
    except Exception as e:
        logger.error(f"{operation_name} failed: {str(e)}")
        raise
    finally:
        duration = time.time() - start
        logger.info(f"{operation_name} took {duration:.2f} seconds")

# Usage
with timed_operation("database_query"):
    results = db.execute(query)
```

## Testing Patterns

### Test Structure Template
```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

class TestUserService:
    """Test suite for UserService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        repo = Mock()
        repo.find_by_id.return_value = {"id": 1, "name": "Test User"}
        return repo
    
    @pytest.fixture
    def service(self, mock_repository):
        """Create service instance with mocked dependencies."""
        return UserService(repository=mock_repository)
    
    def test_get_user_not_found_raises_exception(self, service, mock_repository):
        """Test that getting non-existent user raises NotFoundError."""
        # Arrange
        mock_repository.find_by_id.return_value = None
        user_id = 999
        
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            service.get_user(user_id)
        
        assert str(exc_info.value) == f"User {user_id} not found"
        mock_repository.find_by_id.assert_called_once_with(user_id)
    
    def test_get_user_success(self, service, mock_repository):
        """Test successful user retrieval."""
        # Arrange
        expected_user = {"id": 1, "name": "Test User"}
        user_id = 1
        
        # Act
        result = service.get_user(user_id)
        
        # Assert
        assert result == expected_user
        mock_repository.find_by_id.assert_called_once_with(user_id)
    
    @pytest.mark.parametrize("input_value,expected", [
        ("", False),
        ("invalid", False),
        ("user@example.com", True),
        ("user+tag@example.co.uk", True),
    ])
    def test_email_validation(self, service, input_value, expected):
        """Test email validation with various inputs."""
        assert service.is_valid_email(input_value) == expected
```

## Logging Standards

```python
import logging
import sys
from logging.handlers import RotatingFileHandler

# Configure logging
def setup_logging(app_name: str = "app") -> None:
    """Configure application logging."""
    log_format = (
        '%(asctime)s - %(name)s - %(levelname)s - '
        '%(filename)s:%(lineno)d - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        f'{app_name}.log',
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        handlers=[console_handler, file_handler]
    )

# Usage in modules
logger = logging.getLogger(__name__)

# Log levels and when to use them
logger.debug("Detailed diagnostic info")
logger.info("General informational messages") 
logger.warning("Something unexpected but handled")
logger.error("Error that should be investigated")
logger.critical("System-breaking error")

# Structured logging
logger.info(
    "User action completed",
    extra={
        'user_id': user.id,
        'action': 'login',
        'ip_address': request.remote_addr,
        'duration_ms': duration
    }
)
```

## Code Generation Patterns

When generating Python code, always:
1. Start with imports (standard library, third-party, local)
2. Include type hints for all function parameters and returns
3. Add comprehensive docstrings
4. Include error handling with specific exceptions
5. Provide usage examples in docstrings or as separate functions
6. Write corresponding test cases

### Import Organization
```python
# Standard library imports
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict

# Third-party imports
import requests
import pandas as pd
from sqlalchemy import create_engine

# Local application imports
from app.models import User
from app.utils import validate_email
from app.constants import DEFAULT_TIMEOUT
```

## Async/Await Patterns

```python
import asyncio
from typing import List, Optional
import aiohttp

async def fetch_data(session: aiohttp.ClientSession, url: str) -> dict:
    """Fetch data from URL asynchronously."""
    try:
        async with session.get(url, timeout=30) as response:
            response.raise_for_status()
            return await response.json()
    except aiohttp.ClientError as e:
        logger.error(f"Failed to fetch {url}: {e}")
        raise

async def fetch_multiple(urls: List[str]) -> List[Optional[dict]]:
    """Fetch multiple URLs concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_data(session, url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)

# Usage
if __name__ == "__main__":
    urls = ["http://api1.com", "http://api2.com"]
    results = asyncio.run(fetch_multiple(urls))
```

## Performance Optimization Patterns

### Use Generators for Memory Efficiency
```python
def process_large_file(filepath: str):
    """Process large file line by line using generator."""
    with open(filepath, 'r') as file:
        for line in file:  # Generator - doesn't load entire file
            yield process_line(line)

# Instead of
def process_large_file_bad(filepath: str):
    with open(filepath, 'r') as file:
        lines = file.readlines()  # Loads entire file into memory
        return [process_line(line) for line in lines]
```

### Caching with functools
```python
from functools import lru_cache, cache

@lru_cache(maxsize=128)
def expensive_computation(n: int) -> int:
    """Cache results of expensive computation."""
    # Complex calculation here
    return result

@cache  # Python 3.9+ unlimited cache
def fibonacci(n: int) -> int:
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

## Security Best Practices

### SQL Injection Prevention
```python
# BAD - SQL Injection vulnerable
query = f"SELECT * FROM users WHERE name = '{user_input}'"

# GOOD - Parameterized query
query = "SELECT * FROM users WHERE name = %s"
cursor.execute(query, (user_input,))

# GOOD - Using SQLAlchemy
from sqlalchemy import text
query = text("SELECT * FROM users WHERE name = :name")
result = connection.execute(query, {"name": user_input})
```

### Secure Password Handling
```python
import bcrypt
import secrets

def hash_password(password: str) -> bytes:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def verify_password(password: str, hashed: bytes) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure token."""
    return secrets.token_urlsafe(length)
```
