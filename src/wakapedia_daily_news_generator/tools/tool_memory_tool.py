"""
Outil de mémoire pour les URLs d'outils tech déjà présentés.
Permet d'éviter de présenter les mêmes outils.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# Chemin vers le fichier de mémoire (à la racine du projet)
MEMORY_FILE = Path(__file__).parent.parent.parent.parent / "memory" / "used_tools_urls.json"


def _ensure_memory_file_exists() -> None:
    """Crée le fichier de mémoire s'il n'existe pas."""
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text(json.dumps({"urls": []}, indent=2, ensure_ascii=False))


def _load_memory() -> dict:
    """Charge la mémoire depuis le fichier JSON."""
    _ensure_memory_file_exists()
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_memory(data: dict) -> None:
    """Sauvegarde la mémoire dans le fichier JSON."""
    _ensure_memory_file_exists()
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


class CheckToolUrlInput(BaseModel):
    """Input schema pour vérifier si un outil a déjà été présenté."""
    url: str = Field(..., description="L'URL de l'outil à vérifier")


class CheckToolUrlTool(BaseTool):
    """Outil pour vérifier si un outil tech a déjà été présenté."""

    name: str = "check_tool_url"
    description: str = (
        "Vérifie si un outil a déjà été présenté dans une newsletter précédente. "
        "Retourne 'OUI' si l'outil existe déjà (à éviter), 'NON' s'il est nouveau (OK à utiliser). "
        "TOUJOURS utiliser cet outil AVANT de sélectionner un outil pour éviter les doublons."
    )
    args_schema: Type[BaseModel] = CheckToolUrlInput

    def _run(self, url: str) -> str:
        memory = _load_memory()
        used_urls = [entry["url"] for entry in memory.get("urls", [])]

        # Normaliser l'URL pour la comparaison (enlever trailing slash, etc.)
        normalized_url = url.rstrip("/").lower()
        normalized_used = [u.rstrip("/").lower() for u in used_urls]

        if normalized_url in normalized_used:
            return f"OUI - Cet outil a déjà été présenté. Cherchez un autre outil."
        return f"NON - Cet outil est nouveau, vous pouvez le présenter."


class SaveToolUrlInput(BaseModel):
    """Input schema pour sauvegarder un outil présenté."""
    url: str = Field(..., description="L'URL de l'outil à sauvegarder")
    name: str = Field(..., description="Le nom de l'outil")


class SaveToolUrlTool(BaseTool):
    """Outil pour sauvegarder un outil tech présenté."""

    name: str = "save_tool_url"
    description: str = (
        "Sauvegarde un outil dans la mémoire après l'avoir sélectionné pour la newsletter. "
        "TOUJOURS utiliser cet outil APRÈS avoir finalisé le choix de l'outil pour éviter "
        "de le réutiliser dans les prochaines éditions."
    )
    args_schema: Type[BaseModel] = SaveToolUrlInput

    def _run(self, url: str, name: str) -> str:
        memory = _load_memory()

        # Vérifier si l'URL existe déjà
        used_urls = [entry["url"].rstrip("/").lower() for entry in memory.get("urls", [])]
        if url.rstrip("/").lower() in used_urls:
            return f"Outil déjà enregistré, pas de doublon créé."

        # Ajouter la nouvelle entrée
        new_entry = {
            "url": url,
            "name": name,
            "date_used": datetime.now().isoformat()
        }
        memory["urls"].append(new_entry)

        # Garder seulement les 90 dernières entrées
        # pour éviter que le fichier ne grossisse indéfiniment
        if len(memory["urls"]) > 90:
            memory["urls"] = memory["urls"][-90:]

        _save_memory(memory)
        return f"Outil sauvegardé avec succès. Il ne sera plus proposé dans les prochaines éditions."


class ListUsedToolsUrlsInput(BaseModel):
    """Input schema pour lister les outils présentés."""
    limit: int = Field(default=10, description="Nombre d'outils récents à afficher (défaut: 10)")


class ListUsedToolsUrlsTool(BaseTool):
    """Outil pour lister les outils tech récemment présentés."""

    name: str = "list_used_tools_urls"
    description: str = (
        "Liste les outils récemment présentés dans les newsletters précédentes. "
        "Utile pour voir rapidement quels outils ont déjà été couverts."
    )
    args_schema: Type[BaseModel] = ListUsedToolsUrlsInput

    def _run(self, limit: int = 10) -> str:
        memory = _load_memory()
        urls = memory.get("urls", [])

        if not urls:
            return "Aucun outil en mémoire. C'est la première newsletter !"

        recent = urls[-limit:]
        recent.reverse()  # Plus récent en premier

        result = f"Les {len(recent)} derniers outils présentés:\n\n"
        for entry in recent:
            date = entry.get("date_used", "date inconnue")[:10]
            name = entry.get("name", "Sans nom")
            result += f"- [{date}] {name}\n"

        return result
