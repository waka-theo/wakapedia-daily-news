# ROADMAP - Wakapedia Daily News

> Dernière mise à jour : Janvier 2026

Ce document liste toutes les améliorations, corrections et nouvelles fonctionnalités identifiées pour le projet.

---

## Table des matières

1. [Bugs Critiques](#1-bugs-critiques-)
2. [Corrections Prioritaires](#2-corrections-prioritaires-)
3. [Améliorations de Code](#3-améliorations-de-code-)
4. [Nouvelles Fonctionnalités](#4-nouvelles-fonctionnalités-)
5. [Tests & Qualité](#5-tests--qualité-)
6. [Performance](#6-performance-)
7. [Sécurité](#7-sécurité-)
8. [Documentation](#8-documentation-)
9. [Infrastructure & DevOps](#9-infrastructure--devops-)
10. [UX & Interface](#10-ux--interface-)

---

## 1. Bugs Critiques 🔴

### 1.1 Confusion des outils de mémoire pour les tools
**Fichier:** `src/wakapedia_daily_news_generator/crew.py`

**Problème:** Le crew utilise `tools_memory_tool.py` (CheckToolTool basé sur les noms) mais `agents.yaml` et `tasks.yaml` référencent `check_tool_url` (basé sur les URLs depuis `tool_memory_tool.py`). Les agents reçoivent les mauvais outils.

**Solution:**
- [ ] Unifier les fichiers `tools_memory_tool.py` et `tool_memory_tool.py`
- [ ] Mettre à jour les imports dans `crew.py`
- [ ] Aligner les instructions dans `tasks.yaml`

---

### 1.2 Fallback avec une blague au lieu d'un fait réel
**Fichier:** `src/wakapedia_daily_news_generator/main.py` (ligne ~181)

**Problème:** Le fallback utilise une blague de développeur alors que la newsletter exige des faits réels, pas de blagues.

```python
# Actuel (incorrect)
fun_content = "Pourquoi les développeurs préfèrent le mode sombre ? Parce que la lumière attire les bugs !"

# À corriger
fun_content = "Le premier bug informatique documenté était un vrai insecte : un papillon de nuit trouvé dans le Harvard Mark II en 1947."
```

**Solution:**
- [ ] Remplacer la blague par un vrai fait tech
- [ ] Ajouter plusieurs fallbacks en rotation

---

### 1.3 Absence de gestion d'erreurs lors de l'exécution du Crew
**Fichier:** `src/wakapedia_daily_news_generator/main.py`

**Problème:** La fonction `run()` n'a pas de try-except autour de `crew().kickoff()`. Une exception non gérée fait crasher silencieusement le workflow.

**Solution:**
- [ ] Ajouter try-except avec logging approprié
- [ ] Envoyer une notification en cas d'échec (Discord/Slack/Email)
- [ ] Implémenter une logique de retry (3 tentatives avec backoff exponentiel)

---

### 1.4 Corruption JSON possible dans les memory tools
**Fichiers:** Tous les fichiers dans `tools/`

**Problème:** `json.load()` peut lever `JSONDecodeError` si le fichier est corrompu. Aucune gestion d'erreur n'existe.

**Solution:**
- [ ] Ajouter try-except autour de `json.load()`
- [ ] Créer une backup avant chaque écriture
- [ ] Implémenter une validation du schéma JSON

---

## 2. Corrections Prioritaires 🟠

### 2.1 Bug du changement d'heure (DST)
**Fichier:** `.github/workflows/daily-newsletter.yml`

**Problème:** Le cron `0 7 * * 1-5` (7h UTC) ne couvre que l'heure d'hiver CET. En été (CEST, UTC+2), la newsletter part à 9h au lieu de 8h.

**Solutions proposées:**
- [ ] Option A: Utiliser deux schedules cron (hiver: 7h UTC, été: 6h UTC)
- [ ] Option B: Utiliser un service externe comme EasyCron avec timezone
- [ ] Option C: Créer une action qui calcule dynamiquement l'offset

---

### 2.2 Fragilité de l'extraction par regex
**Fichier:** `src/wakapedia_daily_news_generator/main.py` (60+ lignes de regex)

**Problème:** L'extraction HTML via regex est fragile et casse si les agents changent le format de sortie.

**Solution:**
- [ ] Modifier les agents pour retourner du JSON structuré
- [ ] Utiliser un parseur HTML (BeautifulSoup) au lieu de regex
- [ ] Ajouter des tests de validation du format de sortie

---

### 2.3 Incohérence des modèles et températures
**Fichiers:** `config/agents.yaml` et `crew.py`

**Problème:** `agents.yaml` ne spécifie pas les températures, mais `crew.py` les override. Documentation trompeuse.

**Solution:**
- [ ] Documenter les vraies valeurs dans `agents.yaml` (en commentaires)
- [ ] Centraliser la configuration des modèles
- [ ] Créer un fichier `config/models.yaml` dédié

---

### 2.4 Validation des arguments CLI manquante
**Fichier:** `src/wakapedia_daily_news_generator/main.py`

**Problème:** `train()`, `replay()`, `test()` accèdent à `sys.argv[1]`, `sys.argv[2]` sans validation.

**Solution:**
- [ ] Utiliser `argparse` ou `click` pour la gestion des arguments
- [ ] Ajouter des messages d'usage clairs
- [ ] Valider les types (int pour n_iterations, etc.)

---

### 2.5 Opérations d'écriture non atomiques
**Fichiers:** Tous les memory tools

**Problème:** Les écritures JSON peuvent corrompre le fichier en cas d'accès concurrent ou de crash.

**Solution:**
- [ ] Écrire dans un fichier temporaire puis renommer (atomique)
- [ ] Ajouter un file lock (`fcntl.flock`)
- [ ] Implémenter un système de versioning des données

```python
# Pattern recommandé
import tempfile
import os

def _save_memory(memory: dict) -> None:
    temp_fd, temp_path = tempfile.mkstemp(dir=MEMORY_DIR)
    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, MEMORY_FILE)  # Atomique
    except:
        os.unlink(temp_path)
        raise
```

---

## 3. Améliorations de Code 🟡

### 3.1 Ajouter du logging structuré
**Impact:** Tout le projet

**État actuel:** Aucun logging, débogage difficile.

**Solution:**
- [ ] Configurer `logging` avec différents niveaux (DEBUG, INFO, WARNING, ERROR)
- [ ] Logger les étapes clés (début/fin crew, extraction, envoi webhook)
- [ ] Ajouter des timestamps et contexte

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('wakapedia')
```

---

### 3.2 Ajouter des type hints
**Fichiers:** `main.py`, `crew.py`, tous les tools

**État actuel:** Aucun type hint, difficile à maintenir.

**Solution:**
- [ ] Ajouter des annotations de type à toutes les fonctions
- [ ] Utiliser `mypy` pour la vérification statique
- [ ] Ajouter un script de vérification dans CI

---

### 3.3 Supprimer les fichiers dupliqués
**Fichiers:** `tools_memory_tool.py` vs `tool_memory_tool.py`

**Solution:**
- [ ] Fusionner en un seul fichier `tool_memory.py`
- [ ] Exposer les deux types d'outils (par nom ET par URL)
- [ ] Mettre à jour tous les imports

---

### 3.4 Supprimer `custom_tool.py` (template inutilisé)
**Fichier:** `src/wakapedia_daily_news_generator/tools/custom_tool.py`

**Solution:**
- [ ] Supprimer ce fichier template
- [ ] Ou le renommer en `_template_tool.py` avec underscore

---

### 3.5 Améliorer la détection de similarité
**Fichier:** `tools/facts_memory_tool.py`

**État actuel:** Détection basée uniquement sur 60% de mots-clés communs.

**Solution:**
- [ ] Implémenter la distance de Levenshtein pour le fuzzy matching
- [ ] Ajouter la détection de similarité aux tools news et tools (pas seulement facts)
- [ ] Rendre le seuil configurable via variable d'environnement

---

### 3.6 Centraliser la configuration
**État actuel:** Configuration éparpillée entre `.env`, YAML, et code.

**Solution:**
- [ ] Créer un fichier `config/settings.py` avec Pydantic Settings
- [ ] Valider toutes les variables d'environnement au démarrage
- [ ] Fournir des valeurs par défaut documentées

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    serper_api_key: str
    google_chat_webhook_url: str | None = None
    newsletter_logo_url: str | None = None
    memory_retention_days: int = 90
    max_agent_iterations: int = 10

    class Config:
        env_file = ".env"
```

---

## 4. Nouvelles Fonctionnalités 🟢

### 4.1 Mode dry-run / preview
**Priorité:** Haute

**Description:** Permettre de générer la newsletter sans l'envoyer, pour vérification.

**Implémentation:**
- [ ] Ajouter un flag `--dry-run` à la CLI
- [ ] Générer un fichier HTML local pour preview
- [ ] Ouvrir automatiquement dans le navigateur

```bash
crewai run --dry-run  # Génère output/preview.html
```

---

### 4.2 Support multi-canaux
**Priorité:** Moyenne

**Description:** Envoyer la newsletter sur plusieurs plateformes.

**Canaux à supporter:**
- [ ] Google Chat (existant)
- [ ] Slack
- [ ] Discord
- [ ] Microsoft Teams
- [ ] Email (SMTP)

**Implémentation:**
- [ ] Créer une interface `NewsletterChannel`
- [ ] Implémenter un adaptateur par canal
- [ ] Configuration via `NEWSLETTER_CHANNELS=gchat,slack,discord`

---

### 4.3 Dashboard de monitoring
**Priorité:** Basse

**Description:** Interface web pour suivre l'historique des newsletters.

**Fonctionnalités:**
- [ ] Historique des envois (date, statut, contenu)
- [ ] Statistiques (taux de succès, temps d'exécution, coûts API)
- [ ] Visualisation de la mémoire anti-doublon
- [ ] Bouton "Renvoyer" pour les échecs

**Stack suggérée:** Streamlit ou Gradio pour simplicité

---

### 4.4 Support multilingue
**Priorité:** Basse

**Description:** Générer la newsletter en plusieurs langues.

**Implémentation:**
- [ ] Paramètre `NEWSLETTER_LANGUAGE=fr|en|es`
- [ ] Templates de prompts par langue
- [ ] Localisation des dates dans `google_chat_card.py`

---

### 4.5 Système de retry intelligent
**Priorité:** Haute

**Description:** Retry automatique en cas d'échec avec backoff exponentiel.

**Implémentation:**
- [ ] Utiliser `tenacity` pour les retries
- [ ] Configurer: 3 tentatives, backoff 2^n secondes
- [ ] Logger chaque tentative

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
def run_crew():
    return crew.kickoff(inputs=inputs)
```

---

### 4.6 Notifications d'échec
**Priorité:** Haute

**Description:** Alerter en cas d'échec de génération.

**Canaux:**
- [ ] Email via SMTP
- [ ] Webhook personnalisé
- [ ] GitHub Issue automatique

---

### 4.7 Mode interactif de sélection
**Priorité:** Basse

**Description:** Permettre à un humain de valider/modifier le contenu avant envoi.

**Workflow:**
1. Crew génère les propositions
2. CLI affiche les options
3. Utilisateur sélectionne ou édite
4. Envoi après validation

---

### 4.8 Archives et historique
**Priorité:** Moyenne

**Description:** Conserver un historique des newsletters envoyées.

**Implémentation:**
- [ ] Sauvegarder chaque newsletter en JSON/HTML dans `archives/YYYY-MM-DD.json`
- [ ] Ajouter une commande `crewai history` pour lister
- [ ] Permettre le renvoi d'une archive

---

### 4.9 Métriques de coût API
**Priorité:** Moyenne

**Description:** Tracker les coûts OpenAI et Serper.

**Implémentation:**
- [ ] Logger les tokens utilisés par requête
- [ ] Calculer le coût estimé (tokens × prix)
- [ ] Rapport hebdomadaire/mensuel

---

### 4.10 Thèmes personnalisables
**Priorité:** Basse

**Description:** Permettre de personnaliser l'apparence de la card Google Chat.

**Options:**
- [ ] Couleurs personnalisables
- [ ] Emojis configurables
- [ ] Format de date configurable

---

### 4.11 Rubriques additionnelles
**Priorité:** Basse

**Description:** Ajouter des rubriques optionnelles à la newsletter.

**Idées:**
- [ ] **Weekly Recap** (résumé hebdomadaire le vendredi)
- [ ] **Quote of the Day** (citation tech inspirante)
- [ ] **Job Alert** (offres d'emploi tech)
- [ ] **Learning Resource** (tutoriel/cours du jour)
- [ ] **GitHub Trending** (repo populaire du jour)

---

### 4.12 Feedback utilisateur
**Priorité:** Moyenne

**Description:** Permettre aux lecteurs de noter le contenu.

**Implémentation:**
- [ ] Boutons emoji dans la card (👍 👎)
- [ ] Collecter les réactions
- [ ] Utiliser le feedback pour améliorer les prompts

---

### 4.13 Sources configurables
**Priorité:** Moyenne

**Description:** Permettre de configurer les sources de news préférées.

**Implémentation:**
- [ ] Fichier `config/sources.yaml` avec liste de domaines
- [ ] Poids par source (fiabilité)
- [ ] Blacklist de domaines

---

### 4.14 Génération de résumé hebdomadaire
**Priorité:** Basse

**Description:** Compilation automatique des 5 meilleures news de la semaine.

**Trigger:** Vendredi à 17h ou samedi matin

---

### 4.15 Mode "breaking news"
**Priorité:** Basse

**Description:** Envoi immédiat pour les actualités majeures.

**Critères:**
- Score d'importance > seuil
- Keywords critiques (ex: "GPT-5", "acquisition majeure")

---

## 5. Tests & Qualité 🔵

### 5.1 Tests unitaires pour les memory tools
**Priorité:** Haute

**Fichiers à tester:**
- [ ] `news_memory_tool.py`
- [ ] `tools_memory_tool.py`
- [ ] `facts_memory_tool.py`

**Cas de test:**
- Création de fichier si inexistant
- Lecture/écriture JSON
- Limite des 90 entrées
- Détection de doublons
- Détection de similarité

---

### 5.2 Tests unitaires pour l'extraction HTML
**Priorité:** Haute

**Fichier:** `main.py`

**Cas de test:**
- Extraction titre/contenu news
- Extraction titre/contenu tool
- Extraction fun fact
- Extraction des liens
- Gestion des cas limites (contenu vide, format inattendu)

---

### 5.3 Tests unitaires pour Google Chat card
**Priorité:** Moyenne

**Fichier:** `google_chat_card.py`

**Cas de test:**
- Formatage date français
- Structure JSON valide
- Gestion des valeurs None
- Liens optionnels

---

### 5.4 Tests d'intégration
**Priorité:** Moyenne

**Scénarios:**
- [ ] Exécution complète du crew avec mock API
- [ ] Envoi webhook avec mock endpoint
- [ ] Cycle complet dry-run

---

### 5.5 Tests de bout en bout (E2E)
**Priorité:** Basse

**Scénarios:**
- [ ] Génération réelle avec vraies API (quota limité)
- [ ] Vérification format Google Chat

---

### 5.6 Configuration CI/CD pour les tests
**Priorité:** Haute

**Fichier:** `.github/workflows/tests.yml`

**Contenu:**
- [ ] Lancer pytest sur chaque PR
- [ ] Vérification mypy
- [ ] Vérification ruff (linting)
- [ ] Coverage minimum 80%

---

### 5.7 Fixtures de test
**Priorité:** Moyenne

**Créer:**
- [ ] `tests/fixtures/sample_crew_output.html`
- [ ] `tests/fixtures/sample_memory.json`
- [ ] `tests/conftest.py` avec fixtures pytest

---

## 6. Performance 🟣

### 6.1 Cache des dépendances GitHub Actions
**Fichier:** `.github/workflows/daily-newsletter.yml`

**Gain estimé:** 60-90 secondes par run

**Implémentation:**
```yaml
- name: Cache UV dependencies
  uses: actions/cache@v4
  with:
    path: ~/.cache/uv
    key: ${{ runner.os }}-uv-${{ hashFiles('pyproject.toml') }}
```

---

### 6.2 Réduire max_iter des agents
**Fichier:** `crew.py`

**État actuel:** `max_iter=10` pour tous les agents

**Recommandation:**
- [ ] `tech_news_researcher`: max_iter=5 (recherche simple)
- [ ] `tech_tool_scout`: max_iter=5
- [ ] `tech_fact_finder`: max_iter=5
- [ ] `newsletter_editor`: max_iter=3 (compilation uniquement)

---

### 6.3 Ajouter des timeouts
**Fichier:** `crew.py`

**Implémentation:**
```python
@agent
def tech_news_researcher(self) -> Agent:
    return Agent(
        ...
        max_execution_time=300,  # 5 minutes max
        max_rpm=10,  # Limite de requêtes par minute
    )
```

---

### 6.4 Optimiser les regex d'extraction
**Fichier:** `main.py`

**Problème:** Regex complexes compilés à chaque exécution.

**Solution:**
- [ ] Pré-compiler les regex au niveau module
- [ ] Utiliser `re.compile()` une seule fois

```python
NEWS_PATTERN = re.compile(r'<h2[^>]*>.*?Daily News.*?</h2>\s*<p[^>]*>(.*?)</p>', re.DOTALL | re.IGNORECASE)
```

---

### 6.5 Paralléliser les agents indépendants
**État actuel:** Les 3 premiers agents s'exécutent séquentiellement.

**Optimisation possible:**
- [ ] Exécuter `tech_news_researcher`, `tech_tool_scout`, et `tech_fact_finder` en parallèle
- [ ] Attendre les 3 résultats avant `newsletter_editor`

**Note:** Nécessite modification de l'architecture CrewAI (Process.parallel)

---

### 6.6 Connection pooling pour les requêtes HTTP
**Fichier:** `main.py`

**Solution:**
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('https://', adapter)
```

---

## 7. Sécurité 🔒

### 7.1 Ne pas afficher le contenu en console si webhook échoue
**Fichier:** `main.py` (ligne ~188)

**Problème:** Le contenu complet est imprimé en console, potentiellement visible dans les logs publics.

**Solution:**
- [ ] Écrire dans un fichier local au lieu de stdout
- [ ] Logger uniquement un résumé (titre, date)

---

### 7.2 Valider le format de l'URL webhook
**Fichier:** `main.py`

**Solution:**
```python
from urllib.parse import urlparse

def validate_webhook_url(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.scheme == 'https' and
        'chat.googleapis.com' in parsed.netloc
    )
```

---

### 7.3 Sanitiser le contenu avant envoi
**Problème:** Le contenu généré par LLM est envoyé directement.

**Risques:** Injection de scripts, liens malveillants

**Solution:**
- [ ] Valider les URLs extraites (domaines autorisés)
- [ ] Échapper les caractères HTML spéciaux
- [ ] Limiter la longueur du contenu

---

### 7.4 Rotation des clés API
**Recommandation:**
- [ ] Documenter la procédure de rotation
- [ ] Ajouter des alertes si clé proche expiration
- [ ] Utiliser un gestionnaire de secrets (Vault, AWS Secrets Manager)

---

### 7.5 Permissions minimales GitHub Actions
**Fichier:** `.github/workflows/daily-newsletter.yml`

**Ajouter:**
```yaml
permissions:
  contents: read
```

---

### 7.6 Audit des dépendances
**Solution:**
- [ ] Ajouter `pip-audit` ou `safety` dans CI
- [ ] Activer Dependabot pour les mises à jour de sécurité

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
```

---

## 8. Documentation 📚

### 8.1 Mettre à jour le README.md
**État actuel:** Template générique CrewAI

**À ajouter:**
- [ ] Description détaillée du projet
- [ ] Architecture et flux de données
- [ ] Guide de configuration .env complet
- [ ] Exemples de sortie
- [ ] Troubleshooting courant

---

### 8.2 Documenter les variables d'environnement
**Créer:** `.env.example`

```env
# Required
OPENAI_API_KEY=sk-...
SERPER_API_KEY=...
GOOGLE_CHAT_WEBHOOK_URL=https://chat.googleapis.com/v1/spaces/...

# Optional
NEWSLETTER_LOGO_URL=https://...
NEWSLETTER_LANGUAGE=fr
LOG_LEVEL=INFO
```

---

### 8.3 Ajouter des docstrings
**Fichiers concernés:**
- [ ] `crew.py` - Toutes les méthodes
- [ ] `main.py` - Toutes les fonctions
- [ ] Memory tools - Classes et méthodes

---

### 8.4 Créer un CONTRIBUTING.md
**Contenu:**
- [ ] Comment configurer l'environnement de dev
- [ ] Standards de code (formatage, types)
- [ ] Process de PR
- [ ] Tests requis

---

### 8.5 Créer un CHANGELOG.md
**Format:** Keep a Changelog

```markdown
# Changelog

## [Unreleased]
### Added
- ...

## [1.1.0] - 2026-XX-XX
### Added
- Anti-duplicate memory system
```

---

### 8.6 Documenter l'architecture
**Créer:** `docs/ARCHITECTURE.md`

**Contenu:**
- [ ] Diagramme de flux des agents
- [ ] Schéma des données
- [ ] Description de chaque composant

---

## 9. Infrastructure & DevOps ⚙️

### 9.1 Améliorer le workflow GitHub Actions

**Améliorations:**
- [ ] Ajouter `set -e` pour fail-fast
- [ ] Capturer et archiver les logs
- [ ] Envoyer notification sur échec

```yaml
- name: Run newsletter
  id: newsletter
  run: |
    set -e
    python -c "from wakapedia_daily_news_generator.main import run; run()" 2>&1 | tee output.log

- name: Upload logs on failure
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    name: logs
    path: output.log
```

---

### 9.2 Ajouter un workflow de test sur PR
**Créer:** `.github/workflows/test.yml`

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -e ".[dev]"
      - run: pytest --cov
```

---

### 9.3 Gestion DST automatique
**Option:** Utiliser deux schedules cron

```yaml
on:
  schedule:
    # Heure d'hiver (novembre-mars): 7:00 UTC = 8:00 CET
    - cron: '0 7 * 11,12,1,2,3 1-5'
    # Heure d'été (avril-octobre): 6:00 UTC = 8:00 CEST
    - cron: '0 6 * 4,5,6,7,8,9,10 1-5'
```

---

### 9.4 Healthcheck endpoint
**Description:** Endpoint pour vérifier que le système fonctionne.

**Implémentation:**
- [ ] Créer un simple endpoint HTTP (Flask/FastAPI minimal)
- [ ] Vérifier la validité des clés API
- [ ] Retourner statut des fichiers mémoire

---

### 9.5 Containerisation Docker
**Créer:** `Dockerfile`

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["python", "-c", "from wakapedia_daily_news_generator.main import run; run()"]
```

**Avantages:**
- Environnement reproductible
- Déploiement sur cloud facilité
- Tests locaux identiques à la production

---

### 9.6 Backup automatique de la mémoire
**Description:** Sauvegarder régulièrement les fichiers JSON de mémoire.

**Options:**
- [ ] Commit automatique dans le repo (branche `data`)
- [ ] Upload vers S3/GCS
- [ ] GitHub Actions artifact

---

## 10. UX & Interface 🎨

### 10.1 Améliorer le format Google Chat card
**Fichier:** `google_chat_card.py`

**Améliorations:**
- [ ] Utiliser Card V2 API (plus de fonctionnalités)
- [ ] Ajouter des images/thumbnails
- [ ] Boutons d'action (partager, sauvegarder)

---

### 10.2 CLI améliorée avec Rich
**Description:** Utiliser Rich pour une meilleure expérience CLI.

```python
from rich.console import Console
from rich.progress import Progress

console = Console()

with Progress() as progress:
    task = progress.add_task("[cyan]Generating newsletter...", total=4)
    # ... update progress
```

---

### 10.3 Indicateur de progression
**Description:** Afficher la progression pendant l'exécution.

**Étapes à afficher:**
1. Recherche actualité tech...
2. Découverte outil du jour...
3. Recherche fait insolite...
4. Compilation newsletter...
5. Envoi Google Chat...

---

### 10.4 Mode verbeux configurable
**Implémentation:**

```bash
crewai run --verbose    # Logs détaillés
crewai run --quiet      # Silencieux
crewai run              # Normal
```

---

### 10.5 Commande de statut
**Description:** Afficher l'état du système.

```bash
crewai status

# Output:
# Memory: 45/90 news URLs, 32/90 tools, 28/90 facts
# Last run: 2026-01-19 08:00:00
# Next scheduled: 2026-01-20 08:00:00
# API keys: ✓ OpenAI, ✓ Serper, ✓ Webhook
```

---

## Priorités de développement

### Phase 1 - Stabilité (Immédiat)
1. Corriger les bugs critiques (1.1 - 1.4)
2. Ajouter gestion d'erreurs basique
3. Corriger le bug DST

### Phase 2 - Qualité (Court terme)
1. Ajouter tests unitaires essentiels
2. Implémenter le logging
3. Mettre à jour la documentation

### Phase 3 - Fonctionnalités (Moyen terme)
1. Mode dry-run
2. Système de retry
3. Notifications d'échec
4. Archives

### Phase 4 - Évolution (Long terme)
1. Support multi-canaux
2. Dashboard monitoring
3. Support multilingue
4. Feedback utilisateur

---

## Métriques de succès

| Métrique | Objectif |
|----------|----------|
| Taux de succès des envois | > 99% |
| Temps d'exécution moyen | < 3 minutes |
| Couverture de tests | > 80% |
| Doublons détectés | 0% |
| Satisfaction utilisateur | > 4/5 |

---

*Ce document est vivant et sera mis à jour au fur et à mesure de l'avancement du projet.*
