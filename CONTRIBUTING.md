# Contributing to Wakapedia Daily News

Thank you for your interest in contributing to Wakapedia Daily News!

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [UV](https://github.com/astral-sh/uv) package manager (recommended)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/waka-theo/wakapedia-daily-news.git
cd wakapedia-daily-news
```

2. Create a virtual environment and install dependencies:
```bash
# Using UV (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# Or using pip
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

3. Copy the environment file:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Code Standards

### Style Guide

We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check for issues
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/
```

### Type Checking

We use [mypy](https://mypy.readthedocs.io/) for type checking:

```bash
mypy src/ --ignore-missing-imports
```

### Testing

We use [pytest](https://pytest.org/) for testing:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=wakapedia_daily_news_generator --cov-report=html

# Run specific test file
pytest tests/test_memory_tools.py
```

## Pull Request Process

1. **Fork the repository** and create your branch from `main`

2. **Make your changes** following our code standards

3. **Add tests** for any new functionality

4. **Update documentation** if needed (README, CLAUDE.md, docstrings)

5. **Run the full test suite**:
```bash
ruff check src/ tests/
mypy src/ --ignore-missing-imports
pytest
```

6. **Commit your changes** with a clear message:
```bash
git commit -m "feat: add new feature description"
```

We follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `style:` Formatting, no code change
- `refactor:` Code change that neither fixes a bug nor adds a feature
- `test:` Adding or modifying tests
- `chore:` Maintenance tasks

7. **Push and create a Pull Request**

## Project Structure

```
wakapedia-daily-news/
├── src/wakapedia_daily_news_generator/
│   ├── config/
│   │   ├── agents.yaml      # Agent definitions
│   │   └── tasks.yaml       # Task definitions
│   ├── tools/               # Custom CrewAI tools
│   │   ├── news_memory_tool.py
│   │   ├── tool_memory.py
│   │   └── facts_memory_tool.py
│   ├── crew.py              # Main crew definition
│   ├── main.py              # Entry point
│   └── google_chat_card.py  # Google Chat formatting
├── tests/                   # Unit tests
├── memory/                  # JSON memory files
├── archives/                # Saved newsletters
└── .github/workflows/       # CI/CD workflows
```

## Adding New Features

### Adding a New Agent

1. Define the agent in `config/agents.yaml`:
```yaml
new_agent:
  role: New Agent Role
  llm: openai/gpt-4o-mini
  goal: What this agent should accomplish
  backstory: Background context for the agent
```

2. Add the agent method in `crew.py`:
```python
@agent
def new_agent(self) -> Agent:
    """Description of the agent."""
    config = AGENT_CONFIG["new_agent"]
    return Agent(
        config=self.agents_config["new_agent"],
        tools=[...],
        ...
    )
```

3. Add corresponding task in `tasks.yaml` and `crew.py`

### Adding a New Memory Tool

1. Create a new file in `tools/` following the pattern of existing tools
2. Include error handling, atomic writes, and logging
3. Export from `tools/__init__.py`
4. Add tests in `tests/test_memory_tools.py`

## Getting Help

- Open an [issue](https://github.com/waka-theo/wakapedia-daily-news/issues) for bugs or feature requests
- Check existing issues before creating a new one
- Provide as much context as possible in bug reports

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
