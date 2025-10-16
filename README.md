# Simple API

A simple Flask API with health endpoint and best practices.

## Prerequisites

- Python 3.12.9
- Poetry
- pyenv (optional, for Python version management)

## Installation

Install Poetry if you haven't already:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Clone the repository and set up dependencies:

```bash
git clone <repository-url>
cd simple_api
make setup
```

## Usage

### Development Server

Run the API server in development mode:

```bash
make start
```

The API will be available at `http://0.0.0.0:3000` by default.

You can customize the server using environment variables:

```bash
# Run with custom host and port
SERVER_HOST=127.0.0.1 SERVER_PORT=5000 make start

# Run with debug logging
LOG_LEVEL=DEBUG make start

# Enable auto-reload on file changes
AUTO_SAVE=true make start
```

### Production Server

Run the API with Gunicorn for production:

```bash
make start-server
```

Customize the production server:

```bash
# Custom host and port
SERVER_HOST=0.0.0.0 SERVER_PORT=8080 make start-server

# Custom log level
LOG_LEVEL=WARNING make start-server
```

### Debugging

Run the server with debugpy for remote debugging:

```bash
make debug
```

This starts the server with a debugger listening on port 5678. You can attach your IDE's debugger to this port.

### Endpoints

- `GET /` - Index endpoint
  - Returns: `{"service": "simple_api", "version": "0.2.1"}`
  - Status code: 200

- `GET /health` - Health check endpoint
  - Returns: `{"status": "healthy", "service": "simple_api"}`
  - Status code: 200

Example:
```bash
curl http://0.0.0.0:3000/
curl http://0.0.0.0:3000/health
```

## Development

Run tests:

```bash
make test
```

Run linters (includes formatting, type checking, and security checks):

```bash
make lint
```

Check for unused dependencies:

```bash
make imports
```

Run all checks (lint + test + imports):

```bash
make check
```

Clean build artifacts:

```bash
make clean
```

Check version information:

```bash
make version
```

## Project Structure

```
simple_api/
├── src/
│   └── simple_api/          # Source code
│       ├── __init__.py      # Package initialization
│       ├── flask.py         # Flask application factory
│       └── utils/           # Utility modules
│           ├── logger.py    # Logging configuration
│           └── metadata.py  # Project metadata
├── tests/                   # Test files
│   ├── __init__.py
│   └── test_main.py
├── main.py                  # Application entry point
├── Makefile                 # Make commands
├── pyproject.toml           # Poetry configuration
├── poetry.toml              # Poetry settings
├── CONTRIBUTING.md          # Contributing guidelines
├── CHANGELOG.md             # Version changelog
└── README.md                # This file
```

## Available Make Commands

| Command | Description |
|---------|-------------|
| `make version` | Display project version and Python version |
| `make setup` | Set up local Python environment with pyenv and install dependencies |
| `make start` | Run the development server (uses environment variables) |
| `make start-server` | Run production server with Gunicorn |
| `make debug` | Run server with debugpy for remote debugging |
| `make test` | Run tests with pytest |
| `make lint` | Run all linters (black, isort, flake8, mypy, bandit) |
| `make imports` | Check for unused dependencies with deptry |
| `make check` | Run lint, test, and imports checks |
| `make commit` | Create a conventional commit using commitizen |
| `make bump` | Bump version and update changelog using commitizen |

## Environment Variables

The application supports the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_HOST` | `0.0.0.0` | Server host address |
| `SERVER_PORT` | `3000` | Server port number |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `AUTO_SAVE` | `false` | Enable auto-reload on file changes (development only) |

## Configuration

### Poetry Settings

The project uses Poetry for dependency management. Configuration is in [pyproject.toml](pyproject.toml):

```toml
[tool.poetry]
name = "simple_api"
version = "0.2.1"
python = "3.12.9"
```

### Development Tools

- **Black**: Code formatting (88 char line length)
- **isort**: Import sorting
- **flake8**: Python linting
- **MyPy**: Static type checking
- **bandit**: Security issue detection
- **deptry**: Dependency usage analysis
- **pytest**: Testing framework
- **debugpy**: Python debugger
- **commitizen**: Conventional commits and versioning
- **gunicorn**: Production WSGI server

## Testing

Run the test suite:

```bash
make test
```

Tests are located in the `tests/` directory and use pytest.

## Code Quality

Run all quality checks before committing:

```bash
make check
```

This runs:
- Linting (black, isort, flake8, mypy, bandit)
- Tests (pytest)
- Dependency analysis (deptry)

To run the debugger in VSCode, you must create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Remote Attach",
            "type": "debugpy",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5678
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "."
                }
            ]
        },
        {
            "name": "Python: Current File",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal"
        }
    ]
}
```
