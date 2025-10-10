#!/bin/bash
# Development environment setup script
# Sets up pre-commit hooks and development dependencies

set -e

echo "🔧 Setting up development environment..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2 | cut -d '.' -f 1,2)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python version OK: $PYTHON_VERSION"

# Install pre-commit
echo "📦 Installing pre-commit..."
pip3 install pre-commit

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
pre-commit install

echo "✅ Pre-commit hooks installed!"

# Install backend development dependencies
echo "📦 Installing backend development dependencies..."
cd backend
pip3 install -e ".[dev]"
cd ..

echo "✅ Backend dependencies installed!"

# Run pre-commit on all files (optional, can be commented out)
echo "🔍 Running pre-commit checks on all files..."
echo "   (This may take a while on first run...)"
pre-commit run --all-files || true

echo ""
echo "✨ Development environment setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Make sure Redis is running: docker run -d -p 6379:6379 redis:7-alpine"
echo "   2. Copy .env.example to .env and configure your settings"
echo "   3. Run tests: cd backend && pytest"
echo "   4. Start development: docker-compose up"
echo ""
echo "💡 Pre-commit hooks will now run automatically on git commit"
echo "   To run manually: pre-commit run --all-files"
echo ""

