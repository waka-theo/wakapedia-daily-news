# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Initial Prompt

### Contexte
J'utilise Google Workspace Pro pour mon entreprise WAKASTELLAR. Dans Google Chat, j'ai cree un espace collaboratif nomme Wakapedia, visible par toute mon equipe. Cet espace est dedie aux echanges sur les nouvelles technologies IA, le developpement informatique et l'edition de logiciels SaaS.

### Besoin
Je souhaite concevoir une automatisation qui genere quotidiennement une newsletter appelee "Wakapedia Daily News", envoyee directement dans la conversation tous les matins a 8h (heure de Paris).

### Structure de la newsletter
La newsletter doit comporter trois rubriques :

1. **Daily News** - Une information importante et recente dans notre domaine (IA, developpement, SaaS)
2. **Daily Tool** - Une presentation succincte d'un nouvel outil pertinent pour notre activite
3. **Daily Fun Fact** - Un fait insolite, une anecdote meconnue ou un evenement historique surprenant du monde de l'informatique (pas de blagues)


## Project Overview

This is a CrewAI-powered multi-agent system that generates a daily tech newsletter called "Wakapedia Daily News". The crew consists of four agents working sequentially to produce an HTML newsletter with tech news, tool discoveries, and fun facts.

## Commands

```bash
# Install dependencies
uv pip install -e .

# Run the newsletter generator
python -m wakapedia_daily_news_generator.main run

# Dry run (generate without sending)
python -m wakapedia_daily_news_generator.main run --dry-run

# Check system status
python -m wakapedia_daily_news_generator.main status

# Train the crew
python -m wakapedia_daily_news_generator.main train <n_iterations> <filename>

# Replay from a specific task
python -m wakapedia_daily_news_generator.main replay <task_id>

# Test the crew
python -m wakapedia_daily_news_generator.main test <n_iterations> <eval_llm>

# Or use CrewAI CLI
crewai run
```

## Architecture

### Agents (defined in `src/wakapedia_daily_news_generator/config/agents.yaml`)

| Agent | Role | Model | Temperature |
|-------|------|-------|-------------|
| **tech_news_researcher** | Finds daily tech news (AI, dev, SaaS) with anti-duplicate memory | `gpt-4o-mini` | 0.2 |
| **tech_tool_scout** | Discovers new/unknown tech tools | `gpt-4o-mini` | 0.3 |
| **tech_fact_finder** | Finds real tech fun facts (no jokes) | `gpt-4o-mini` | 0.3 |
| **newsletter_editor** | Compiles HTML newsletter in French | `gpt-4o-mini` | 0.2 |

### Tasks (defined in `src/wakapedia_daily_news_generator/config/tasks.yaml`)

| Task | Agent | Description |
|------|-------|-------------|
| `recherche_actualite_tech_du_jour` | tech_news_researcher | Find today's most important tech news (with URL deduplication) |
| `decouverte_outil_du_jour` | tech_tool_scout | Discover a new/unknown tech tool |
| `recherche_fait_insolite_du_jour` | tech_fact_finder | Find a surprising tech fun fact (real, no jokes) |
| `compilation_newsletter_wakapedia_daily_news` | newsletter_editor | Compile HTML newsletter from all sections |

Tasks run sequentially with the final task receiving context from the three previous tasks.

### Key Files
- `src/wakapedia_daily_news_generator/crew.py`: Main crew definition with `@CrewBase` decorator, agent and task methods
- `src/wakapedia_daily_news_generator/main.py`: Entry points with CLI argument parsing (run, status, train, replay, test)
- `src/wakapedia_daily_news_generator/tools/news_memory_tool.py`: News URL deduplication tools
- `src/wakapedia_daily_news_generator/tools/tool_memory.py`: Tool deduplication tools (by name and URL)
- `src/wakapedia_daily_news_generator/tools/facts_memory_tool.py`: Facts deduplication tools with similarity detection
- `src/wakapedia_daily_news_generator/google_chat_card.py`: Google Chat card formatting

### Anti-Duplicate System

All agents use custom memory tools to avoid republishing the same content:

| Memory File | Tools | Description |
|-------------|-------|-------------|
| `memory/used_news_urls.json` | `check_news_url`, `save_news_url`, `list_used_news_urls` | News URL tracking |
| `memory/used_tools.json` | `check_tool_url`, `save_tool_url`, `list_used_tools_urls` | Tool tracking (name + URL) |
| `memory/used_facts.json` | `check_fact`, `save_fact`, `list_used_facts` | Facts tracking with similarity detection |

All memory files keep last 90 entries and use atomic writes with backup on corruption.

## Environment Setup

Required environment variables in `.env`:
- `OPENAI_API_KEY`: For GPT-4o-mini model
- `SERPER_API_KEY`: For SerperDevTool web search
- `GOOGLE_CHAT_WEBHOOK_URL`: For sending newsletter to Google Chat

Optional environment variables:
- `NEWSLETTER_LOGO_URL`: Public URL for the logo displayed in the Google Chat card header
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

Copy `.env.example` to `.env` and fill in your values.

## GitHub Actions

The newsletter is automatically sent every weekday at **8:00 AM Paris time** via GitHub Actions.

Workflow: `.github/workflows/daily-newsletter.yml`
- Dual cron schedules for winter/summer time (DST)
- Automatic retry on failure
- Dry-run support via workflow dispatch

Testing workflow: `.github/workflows/tests.yml`
- Runs on push/PR to main
- Linting with ruff
- Type checking with mypy
- Unit tests with pytest

Required GitHub Secrets:
- `OPENAI_API_KEY`
- `SERPER_API_KEY`
- `GOOGLE_CHAT_WEBHOOK_URL`

Optional GitHub Secrets:
- `NEWSLETTER_LOGO_URL`: Public URL for the newsletter logo in Google Chat card header

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

## Crew Inputs

The crew accepts these inputs (defined in `main.py`):
- `company_name`: Company name used in agent goals (default: "WAKASTELLAR")
- `email_address`: Target email for the newsletter (default: "wakapedia@wakastellar.com")

## Additional Documentation

- `README.md`: Project overview and quick start
- `ROADMAP.md`: Development roadmap with planned features
- `CHANGELOG.md`: Version history
- `CONTRIBUTING.md`: Contribution guidelines
