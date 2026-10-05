"""Schémas Pydantic : contrat de l'API (visible dans /docs)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Action = Literal["brouillon", "envoyé", "classé", "ignoré"]
Statut = Literal["en_attente", "approuvé", "rejeté", "envoyé", "-"]


class Courriel(BaseModel):
    id: str
    date: str
    expediteur: str
    sujet: str
    categorie: str
    priorite: str
    action: Action
    statut: Statut | None = None
    resume: str | None = None
    raison: str | None = None
    reponse: str | None = None
    brouillon_id: str | None = None


class PageCourriels(BaseModel):
    elements: list[Courriel]
    total: int
    page: int
    taille: int


class Statistiques(BaseModel):
    total: int
    en_attente: int
    par_action: dict[str, int]
    par_categorie: dict[str, int]


class Approbation(BaseModel):
    texte: str | None = Field(
        default=None, max_length=20_000, description="Texte modifié. Absent : le brouillon est envoyé tel quel."
    )


class BilanCycle(BaseModel):
    bilan: dict[str, int]


class Sante(BaseModel):
    statut: Literal["ok"] = "ok"
    mode: Literal["demo", "gmail"]
    envoi_auto: bool
    modele: str
