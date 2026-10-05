"""Configuration lue depuis les variables d'environnement (fichier .env)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _bool(nom: str, defaut: bool = False) -> bool:
    return os.getenv(nom, str(defaut)).strip().lower() in {"1", "true", "oui", "yes"}


def _liste(nom: str, defaut: str = "") -> list[str]:
    return [x.strip() for x in os.getenv(nom, defaut).split(",") if x.strip()]


@dataclass
class Config:
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    modele: str = field(default_factory=lambda: os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5"))

    nom_entreprise: str = field(default_factory=lambda: os.getenv("NOM_ENTREPRISE", "Mon Entreprise"))
    signature: str = field(default_factory=lambda: os.getenv("SIGNATURE", "L'équipe"))
    fichier_connaissances: Path = field(
        default_factory=lambda: Path(os.getenv("FICHIER_CONNAISSANCES", "connaissances.md"))
    )

    credentials_path: Path = field(default_factory=lambda: Path(os.getenv("GMAIL_CREDENTIALS", "credentials.json")))
    token_path: Path = field(default_factory=lambda: Path(os.getenv("GMAIL_TOKEN", "token.json")))
    requete_gmail: str = field(default_factory=lambda: os.getenv("REQUETE_GMAIL", "is:unread in:inbox newer_than:2d"))
    max_par_cycle: int = field(default_factory=lambda: int(os.getenv("MAX_PAR_CYCLE", "20")))

    # Sécurité : par défaut l'agent crée seulement des BROUILLONS.
    envoi_auto: bool = field(default_factory=lambda: _bool("ENVOI_AUTO", False))
    categories_envoi_auto: list[str] = field(
        default_factory=lambda: _liste("CATEGORIES_ENVOI_AUTO", "accuse_reception,question_frequente")
    )
    domaines_bloques: list[str] = field(default_factory=lambda: _liste("DOMAINES_BLOQUES"))

    base_donnees: Path = field(default_factory=lambda: Path(os.getenv("BASE_DONNEES", "agent.db")))
    etiquette: str = field(default_factory=lambda: os.getenv("ETIQUETTE", "Agent-IA"))

    def connaissances(self) -> str:
        if self.fichier_connaissances.exists():
            return self.fichier_connaissances.read_text(encoding="utf-8")
        return "(Aucune base de connaissances fournie.)"
