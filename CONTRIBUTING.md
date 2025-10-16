# Contributing to Simple App

Thank you for contributing! This guide covers the essentials.

## Setup

1. Fork and clone the repository
2. Run setup:
   ```bash
   make setup
   ```

## Development Workflow

### 1. Make Your Changes

Create a feature branch and make your changes:
```bash
git checkout -b feature/your-feature-name
# Make your changes...
```

### 2. Run Tests

Ensure all tests pass:
```bash
make test
```

### 3. Run Linters

Format and lint your code:
```bash
make lint
```

This runs:
- **black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting
- **mypy** - Type checking
- **bandit** - Security checks

### 4. Commit Your Changes

Use Commitizen for properly formatted commits:
```bash
make commit
```

This will interactively guide you through creating a [Conventional Commit](https://www.conventionalcommits.org/).

#### Commit Types

- `feat:` - New feature (minor version bump)
- `fix:` - Bug fix (patch version bump)
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Other changes

**Breaking changes:** Add `!` after the type (e.g., `feat!:`) or include `BREAKING CHANGE:` in the commit body for a major version bump.

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then open a Pull Request on GitHub against the `main` branch.

## Quick Reference

```bash
make setup    # Set up development environment
make test     # Run tests
make lint     # Run linters and formatters
make commit   # Create conventional commit
make check    # Run lint + test + imports
```

## Versioning

Version bumps happen **automatically** when your PR is merged to `main`. The version is determined by your commit messages:
- `feat:` → 0.2.0 → 0.3.0
- `fix:` → 0.2.0 → 0.2.1
- `feat!:` → 0.2.0 → 1.0.0

That's it! Happy coding!
