# Wakapedia Daily News

AI-powered daily tech newsletter generator using CrewAI multi-agent system. Automatically delivers tech news, tool discoveries, and fun facts to your Google Chat space every weekday at 8:00 AM Paris time.

## Features

- **Daily News**: Latest tech news from AI, development, and SaaS industries
- **Daily Tool**: Discovery of new and lesser-known developer tools
- **Daily Fun Fact**: Surprising historical facts from the tech world (no jokes!)
- **Anti-duplicate System**: Memory-based deduplication for news, tools, and facts
- **Google Chat Integration**: Beautiful card format delivered via webhook
- **Automated Delivery**: GitHub Actions workflow for daily automation
- **Dry-run Mode**: Preview newsletters before sending
- **Retry Logic**: Automatic retry with exponential backoff

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CrewAI Orchestration                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    News      │  │    Tool      │  │    Fact      │      │
│  │  Researcher  │  │    Scout     │  │   Finder     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           │                                 │
│                           ▼                                 │
│                  ┌──────────────┐                           │
│                  │  Newsletter  │                           │
│                  │    Editor    │                           │
│                  └──────┬───────┘                           │
│                         │                                   │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ▼
                  ┌──────────────┐
                  │ Google Chat  │
                  │   Webhook    │
                  └──────────────┘
```

### Agents

| Agent | Role | Model |
|-------|------|-------|
| **tech_news_researcher** | Finds daily tech news (AI, dev, SaaS) | GPT-4o-mini |
| **tech_tool_scout** | Discovers new/unknown tech tools | GPT-4o-mini |
| **tech_fact_finder** | Finds real tech fun facts | GPT-4o-mini |
| **newsletter_editor** | Compiles HTML newsletter in French | GPT-4o-mini |

## Quick Start

### Prerequisites

- Python 3.10+
- OpenAI API key
- Serper API key
- Google Chat webhook URL

### Installation

```bash
# Clone the repository
git clone https://github.com/waka-theo/wakapedia-daily-news.git
cd wakapedia-daily-news

# Install with UV (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

### Configuration

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `.env` with your API keys:
```env
OPENAI_API_KEY=sk-your-key-here
SERPER_API_KEY=your-serper-key
GOOGLE_CHAT_WEBHOOK_URL=https://chat.googleapis.com/v1/spaces/...
```

### Usage

```bash
# Run the newsletter generator
python -m wakapedia_daily_news_generator.main run

# Dry run (generate without sending)
python -m wakapedia_daily_news_generator.main run --dry-run

# Check system status
python -m wakapedia_daily_news_generator.main status

# Or use CrewAI CLI
crewai run
```

## Commands

| Command | Description |
|---------|-------------|
| `run` | Generate and send the newsletter |
| `run --dry-run` | Generate without sending (saves to `output/preview.html`) |
| `status` | Display system status (memory, env vars, archives) |
| `train <n> <file>` | Train the crew for n iterations |
| `replay <task_id>` | Replay from a specific task |
| `test <n> <model>` | Test with a specific model |

## Project Structure

```
wakapedia-daily-news/
├── src/wakapedia_daily_news_generator/
│   ├── config/
│   │   ├── agents.yaml      # Agent definitions
│   │   └── tasks.yaml       # Task definitions
│   ├── tools/               # Memory tools for deduplication
│   ├── crew.py              # Main crew orchestration
│   ├── main.py              # CLI entry point
│   └── google_chat_card.py  # Google Chat formatting
├── tests/                   # Unit tests
├── memory/                  # Anti-duplicate JSON storage
├── archives/                # Saved newsletters
├── .github/workflows/       # CI/CD automation
├── CLAUDE.md               # AI assistant instructions
├── ROADMAP.md              # Development roadmap
└── CHANGELOG.md            # Version history
```

## Anti-Duplicate System

The system maintains memory files to prevent duplicate content:

| Memory File | Purpose | Retention |
|-------------|---------|-----------|
| `used_news_urls.json` | Track used news article URLs | 90 entries |
| `used_tools.json` | Track presented tools (name + URL) | 90 entries |
| `used_facts.json` | Track fun facts with similarity detection | 90 entries |

## GitHub Actions

The newsletter is automatically sent every weekday at 8:00 AM Paris time.

### Required Secrets

| Secret | Description |
|--------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `SERPER_API_KEY` | Serper API key for web search |
| `GOOGLE_CHAT_WEBHOOK_URL` | Google Chat webhook URL |

### Optional Secrets

| Secret | Description |
|--------|-------------|
| `NEWSLETTER_LOGO_URL` | Public URL for logo in card header |

## Development

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src/ tests/

# Run type checking
mypy src/ --ignore-missing-imports
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features and improvements.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## License

MIT License

## Credits

Built by **TH-SQUAD** at **WAKASTELLAR** using:
- [CrewAI](https://github.com/joaomdmoura/crewai) - Multi-agent orchestration
- [OpenAI GPT-4o-mini](https://openai.com/) - Language model
- [Serper](https://serper.dev/) - Web search API
