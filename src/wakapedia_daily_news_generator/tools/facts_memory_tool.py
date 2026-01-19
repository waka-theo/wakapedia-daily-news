"""
Outil de mémoire pour les fun facts déjà présentés.
Permet d'éviter de présenter les mêmes faits insolites.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# Chemin vers le fichier de mémoire (à la racine du projet)
MEMORY_FILE = Path(__file__).parent.parent.parent.parent / "memory" / "used_facts.json"


def _ensure_memory_file_exists() -> None:
    """Crée le fichier de mémoire s'il n'existe pas."""
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text(json.dumps({"facts": []}, indent=2, ensure_ascii=False))


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


class CheckFactInput(BaseModel):
    """Input schema pour vérifier si un fun fact a déjà été présenté."""
    fact_summary: str = Field(..., description="Un résumé court du fait (quelques mots-clés) pour l'identifier")


class CheckFactTool(BaseTool):
    """Outil pour vérifier si un fun fact a déjà été présenté."""

    name: str = "check_fact"
    description: str = (
        "Vérifie si un fun fact a déjà été présenté dans une newsletter précédente. "
        "Fournissez un résumé court avec les mots-clés principaux (ex: 'premier bug informatique papillon 1947'). "
        "Retourne 'OUI' si le fait existe déjà (à éviter), 'NON' s'il est nouveau (OK à utiliser). "
        "TOUJOURS utiliser cet outil AVANT de sélectionner un fait pour éviter les doublons."
    )
    args_schema: Type[BaseModel] = CheckFactInput

    def _run(self, fact_summary: str) -> str:
        memory = _load_memory()
        used_facts = [entry["summary"].lower().strip() for entry in memory.get("facts", [])]

        # Normaliser le résumé pour la comparaison
        normalized_summary = fact_summary.lower().strip()

        # Vérifier si le résumé existe déjà (comparaison exacte)
        if normalized_summary in used_facts:
            return f"OUI - Ce fait a déjà été présenté. Cherchez un autre fun fact."

        # Vérifier si des mots-clés similaires existent (détection de doublons approximatifs)
        keywords = set(normalized_summary.split())
        for existing_fact in used_facts:
            existing_keywords = set(existing_fact.split())
            # Si plus de 60% des mots sont communs, considérer comme potentiel doublon
            if len(keywords) > 0 and len(existing_keywords) > 0:
                common = keywords.intersection(existing_keywords)
                similarity = len(common) / max(len(keywords), len(existing_keywords))
                if similarity > 0.6:
                    return f"ATTENTION - Ce fait semble similaire à un fait déjà présenté ({existing_fact}). Vérifiez bien ou cherchez un autre fun fact."

        return f"NON - Ce fait est nouveau, vous pouvez le présenter."


class SaveFactInput(BaseModel):
    """Input schema pour sauvegarder un fun fact présenté."""
    fact_summary: str = Field(..., description="Un résumé court du fait pour l'identifier")
    fact_full: str = Field(default="", description="Le fait complet (optionnel)")


class SaveFactTool(BaseTool):
    """Outil pour sauvegarder un fun fact présenté."""

    name: str = "save_fact"
    description: str = (
        "Sauvegarde un fun fact dans la mémoire après l'avoir sélectionné pour la newsletter. "
        "TOUJOURS utiliser cet outil APRÈS avoir finalisé le choix du fait pour éviter "
        "de le réutiliser dans les prochaines éditions."
    )
    args_schema: Type[BaseModel] = SaveFactInput

    def _run(self, fact_summary: str, fact_full: str = "") -> str:
        memory = _load_memory()

        # Vérifier si le fait existe déjà
        used_facts = [entry["summary"].lower().strip() for entry in memory.get("facts", [])]
        if fact_summary.lower().strip() in used_facts:
            return f"Fait déjà enregistré, pas de doublon créé."

        # Ajouter la nouvelle entrée
        new_entry = {
            "summary": fact_summary,
            "full": fact_full,
            "date_used": datetime.now().isoformat()
        }
        memory["facts"].append(new_entry)

        # Garder seulement les 90 dernières entrées
        if len(memory["facts"]) > 90:
            memory["facts"] = memory["facts"][-90:]

        _save_memory(memory)
        return f"Fun fact sauvegardé avec succès. Il ne sera plus proposé dans les prochaines éditions."


class ListUsedFactsInput(BaseModel):
    """Input schema pour lister les fun facts présentés."""
    limit: int = Field(default=10, description="Nombre de faits récents à afficher (défaut: 10)")


class ListUsedFactsTool(BaseTool):
    """Outil pour lister les fun facts récemment présentés."""

    name: str = "list_used_facts"
    description: str = (
        "Liste les fun facts récemment présentés dans les newsletters précédentes. "
        "Utile pour voir rapidement quels faits ont déjà été couverts."
    )
    args_schema: Type[BaseModel] = ListUsedFactsInput

    def _run(self, limit: int = 10) -> str:
        memory = _load_memory()
        facts = memory.get("facts", [])

        if not facts:
            return "Aucun fait en mémoire. C'est la première newsletter !"

        recent = facts[-limit:]
        recent.reverse()  # Plus récent en premier

        result = f"Les {len(recent)} derniers fun facts présentés:\n\n"
        for entry in recent:
            date = entry.get("date_used", "date inconnue")[:10]
            summary = entry.get("summary", "Sans résumé")
            result += f"- [{date}] {summary}\n"

        return result
