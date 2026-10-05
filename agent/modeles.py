"""Structures de données partagées."""
from __future__ import annotations

from dataclasses import dataclass, field

CATEGORIES = [
    "question_frequente",   # question simple couverte par la base de connaissances
    "question_client",      # question qui demande une vraie réflexion
    "demande_rdv",          # prise de rendez-vous
    "plainte",              # client mécontent -> toujours un humain
    "accuse_reception",     # il suffit de confirmer la réception
    "facture_paiement",     # argent -> toujours un humain
    "notification_auto",    # robots, alertes, no-reply
    "publicite_spam",
    "autre",
]


@dataclass
class Courriel:
    id: str
    thread_id: str
    expediteur: str          # "Marie Tremblay <marie@exemple.com>"
    adresse: str             # "marie@exemple.com"
    sujet: str
    date: str
    corps: str
    message_id: str = ""     # en-tête Message-ID (pour répondre dans le même fil)
    references: str = ""
    en_tetes: dict[str, str] = field(default_factory=dict)


@dataclass
class Analyse:
    categorie: str
    priorite: str            # basse | normale | haute
    resume: str
    doit_repondre: bool
    envoi_auto_ok: bool      # avis du modèle ; le code applique ses propres règles en plus
    confiance: float         # 0 à 1
    reponse: str
    raison: str
