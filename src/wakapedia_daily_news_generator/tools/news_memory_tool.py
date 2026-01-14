"""
Outil de mémoire pour les URLs de news déjà utilisées.
Permet d'éviter de republier les mêmes actualités.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# Chemin vers le fichier de mémoire (à la racine du projet)
MEMORY_FILE = Path(__file__).parent.parent.parent.parent / "memory" / "used_news_urls.json"


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


class CheckNewsUrlInput(BaseModel):
    """Input schema pour vérifier si une URL a déjà été utilisée."""
    url: str = Field(..., description="L'URL de l'article à vérifier")


class CheckNewsUrlTool(BaseTool):
    """Outil pour vérifier si une URL de news a déjà été utilisée."""
    
    name: str = "check_news_url"
    description: str = (
        "Vérifie si une URL d'article a déjà été utilisée dans une newsletter précédente. "
        "Retourne 'OUI' si l'URL existe déjà (à éviter), 'NON' si elle est nouvelle (OK à utiliser). "
        "TOUJOURS utiliser cet outil AVANT de sélectionner un article pour éviter les doublons."
    )
    args_schema: Type[BaseModel] = CheckNewsUrlInput

    def _run(self, url: str) -> str:
        memory = _load_memory()
        used_urls = [entry["url"] for entry in memory.get("urls", [])]
        
        # Normaliser l'URL pour la comparaison (enlever trailing slash, etc.)
        normalized_url = url.rstrip("/").lower()
        normalized_used = [u.rstrip("/").lower() for u in used_urls]
        
        if normalized_url in normalized_used:
            return f"OUI - Cette URL a déjà été utilisée. Cherchez un autre article."
        return f"NON - Cette URL est nouvelle, vous pouvez l'utiliser."


class SaveNewsUrlInput(BaseModel):
    """Input schema pour sauvegarder une URL utilisée."""
    url: str = Field(..., description="L'URL de l'article à sauvegarder")
    title: str = Field(..., description="Le titre de l'article")


class SaveNewsUrlTool(BaseTool):
    """Outil pour sauvegarder une URL de news utilisée."""
    
    name: str = "save_news_url"
    description: str = (
        "Sauvegarde une URL d'article dans la mémoire après l'avoir sélectionnée pour la newsletter. "
        "TOUJOURS utiliser cet outil APRÈS avoir finalisé le choix de l'article pour éviter "
        "de le réutiliser dans les prochaines éditions."
    )
    args_schema: Type[BaseModel] = SaveNewsUrlInput

    def _run(self, url: str, title: str) -> str:
        memory = _load_memory()
        
        # Vérifier si l'URL existe déjà
        used_urls = [entry["url"].rstrip("/").lower() for entry in memory.get("urls", [])]
        if url.rstrip("/").lower() in used_urls:
            return f"URL déjà enregistrée, pas de doublon créé."
        
        # Ajouter la nouvelle entrée
        new_entry = {
            "url": url,
            "title": title,
            "date_used": datetime.now().isoformat()
        }
        memory["urls"].append(new_entry)
        
        # Garder seulement les 90 derniers jours (environ 90 entrées)
        # pour éviter que le fichier ne grossisse indéfiniment
        if len(memory["urls"]) > 90:
            memory["urls"] = memory["urls"][-90:]
        
        _save_memory(memory)
        return f"URL sauvegardée avec succès. Elle ne sera plus proposée dans les prochaines éditions."


class ListUsedNewsUrlsInput(BaseModel):
    """Input schema pour lister les URLs utilisées."""
    limit: int = Field(default=10, description="Nombre d'URLs récentes à afficher (défaut: 10)")


class ListUsedNewsUrlsTool(BaseTool):
    """Outil pour lister les URLs de news récemment utilisées."""
    
    name: str = "list_used_news_urls"
    description: str = (
        "Liste les URLs d'articles récemment utilisées dans les newsletters précédentes. "
        "Utile pour voir rapidement quels sujets ont déjà été couverts."
    )
    args_schema: Type[BaseModel] = ListUsedNewsUrlsInput

    def _run(self, limit: int = 10) -> str:
        memory = _load_memory()
        urls = memory.get("urls", [])
        
        if not urls:
            return "Aucune URL en mémoire. C'est la première newsletter !"
        
        recent = urls[-limit:]
        recent.reverse()  # Plus récent en premier
        
        result = f"Les {len(recent)} dernières URLs utilisées:\n\n"
        for entry in recent:
            date = entry.get("date_used", "date inconnue")[:10]
            title = entry.get("title", "Sans titre")
            result += f"- [{date}] {title}\n"
        
        return result
