# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Initial Prompt

### Contexte
J'utilise Google Workspace Pro pour mon entreprise WAKASTELLAR. Dans Google Chat, j'ai créé un espace collaboratif nommé Wakapedia, visible par toute mon équipe. Cet espace est dédié aux échanges sur les nouvelles technologies IA, le développement informatique et l'édition de logiciels SaaS.

### Besoin
Je souhaite concevoir une automatisation qui génère quotidiennement une newsletter appelée "Wakapedia Daily News", envoyée directement dans la conversation tous les matins à 8h (heure de Paris).

### Structure de la newsletter
La newsletter doit comporter trois rubriques :

1. **Daily News** — Une information importante et récente dans notre domaine (IA, développement, SaaS)
2. **Daily Tool** — Une présentation succincte d'un nouvel outil pertinent pour notre activité
3. **Daily Fun Fact** — Un fait insolite, une anecdote méconnue ou un événement historique surprenant du monde de l'informatique (pas de blagues)


## Project Overview

This is a CrewAI-powered multi-agent system that generates a daily tech newsletter called "Wakapedia Daily News". The crew consists of four agents working sequentially to produce an HTML newsletter with tech news, tool discoveries, and fun facts.

## Commands

```bash
# Install dependencies
crewai install

# Run the crew
crewai run

# Train the crew
crewai train <n_iterations> <filename>

# Replay from a specific task
crewai replay <task_id>

# Test the crew
crewai test <n_iterations> <openai_model_name>
```

## Architecture

### Agents (defined in `src/wakapedia_daily_news_generator/config/agents.yaml`)

| Agent | Role | Model | Temperature |
|-------|------|-------|-------------|
| **tech_news_researcher** | Finds daily tech news (AI, dev, SaaS) with anti-duplicate memory | `openai/gpt-4o-mini` | 0.5 |
| **tech_tool_scout** | Discovers new/unknown tech tools | `openai/gpt-4o-mini` | 0.5 |
| **tech_fact_finder** | Finds real tech fun facts (no jokes) | `openai/gpt-4o` | 0.3 |
| **newsletter_editor** | Compiles HTML newsletter in French | `openai/gpt-4o` | 0.3 |

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
- `src/wakapedia_daily_news_generator/main.py`: Entry points for run, train, replay, and test commands
- `src/wakapedia_daily_news_generator/tools/news_memory_tool.py`: Custom tools for URL deduplication (check, save, list)
- `src/wakapedia_daily_news_generator/google_chat_card.py`: Google Chat card formatting
- `memory/used_news_urls.json`: Storage for previously used news URLs (anti-duplicate system)

### Anti-Duplicate System

The `tech_news_researcher` agent uses custom memory tools to avoid republishing the same news:

| Tool | Description |
|------|-------------|
| `check_news_url` | Check if a URL has already been used |
| `save_news_url` | Save a URL after selection |
| `list_used_news_urls` | List recently used URLs |

URLs are stored in `memory/used_news_urls.json` (keeps last 90 entries).

## Environment Setup

Required environment variables in `.env`:
- `OPENAI_API_KEY`: For GPT-4o-mini and GPT-4o models
- `SERPER_API_KEY`: For SerperDevTool web search
- `GOOGLE_CHAT_WEBHOOK_URL`: For sending newsletter to Google Chat

Optional environment variables:
- `NEWSLETTER_LOGO_URL`: Public URL for the logo displayed in the Google Chat card header (must be publicly accessible, e.g., GitHub Raw URL or CDN)

## GitHub Actions

The newsletter is automatically sent every day at **8:00 AM Paris time** via GitHub Actions.

Workflow: `.github/workflows/daily-newsletter.yml`

Required GitHub Secrets:
- `OPENAI_API_KEY`
- `SERPER_API_KEY`
- `GOOGLE_CHAT_WEBHOOK_URL`

Optional GitHub Secrets:
- `NEWSLETTER_LOGO_URL`: Public URL for the newsletter logo in Google Chat card header

## Crew Inputs

The crew accepts these inputs (modify in `main.py`):
- `company_name`: Company name used in agent goals (default: "WAKASTELLAR")
- `email_address`: Target email for the newsletter (default: "wakapedia@wakastellar.com")
