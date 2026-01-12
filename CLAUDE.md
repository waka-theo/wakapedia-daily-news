# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Initial Prompt

### Contexte
J'utilise Google Workspace Pro pour mon entreprise WAKASTELLAR. Dans Google Chat, j'ai créé un espace collaboratif nommé Wakapedia, visible par toute mon équipe. Cet espace est dédié aux échanges sur les nouvelles technologies IA, le développement informatique et l'édition de logiciels SaaS.
Besoin
Je souhaite concevoir une automatisation qui génère quotidiennement une newsletter appelée "Wakapedia Daily News", envoyée directement dans la conversation tous les matins à 9h. 

### Structure de la newsletter
La newsletter doit comporter trois rubriques :

L'actualité du jour — Une information importante et récente dans notre domaine (IA, développement, SaaS)
L'outil du jour — Une présentation succincte d'un nouvel outil pertinent pour notre activité
La blague du jour — Une histoire drôle, une blague de développeur ou une info insolite et amusante liée au monde de l'informatique


## Project Overview

This is a CrewAI-powered multi-agent system that generates a daily tech newsletter called "Wakapedia Daily News". The crew consists of four agents working sequentially to produce an HTML newsletter with tech news, tool discoveries, and humor.

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
| **tech_news_researcher** | Finds daily tech news (AI, dev, SaaS) | `openai/gpt-4o-mini` | 0.5 |
| **tech_tool_scout** | Discovers new tech tools | `openai/gpt-4o-mini` | 0.5 |
| **tech_humorist** | Creates tech jokes/fun facts | `openai/gpt-4o` | 0.9 |
| **newsletter_editor** | Compiles HTML newsletter | `openai/gpt-4o` | 0.3 |

### Tasks (defined in `src/wakapedia_daily_news_generator/config/tasks.yaml`)
Tasks run sequentially with the final `compilation_newsletter_wakapedia_daily_news` task receiving context from the three previous tasks.

### Key Files
- `src/wakapedia_daily_news_generator/crew.py`: Main crew definition with `@CrewBase` decorator, agent and task methods
- `src/wakapedia_daily_news_generator/main.py`: Entry points for run, train, replay, and test commands
- `src/wakapedia_daily_news_generator/tools/custom_tool.py`: Template for creating custom CrewAI tools

## Environment Setup

Required environment variables in `.env`:
- `OPENAI_API_KEY`: For GPT-4o-mini and GPT-4o models
- `SERPER_API_KEY`: For SerperDevTool web search (researcher, scout, and humorist agents)

Optional (if using Anthropic models):
- `ANTHROPIC_API_KEY`: For Claude models (e.g., `claude-haiku-3-5-20241022`, `claude-sonnet-4-20250514`)

## Crew Inputs

The crew accepts these inputs (modify in `main.py`):
- `company_name`: Company name used in agent goals
- `email_address`: Target email for the newsletter
