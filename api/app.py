"""Application FastAPI : routes REST + service de l'application Vue compilée."""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from agent.memoire import Memoire

from .schemas import Approbation, BilanCycle, Courriel, PageCourriels, Sante, Statistiques

log = logging.getLogger("api")
DOSSIER_FRONTEND = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@dataclass
class Services:
    """Dépendances injectées : permet de brancher Gmail réel, le mode démo ou des faux objets en test."""
    memoire: Memoire
    fournir_gmail: Callable[[], object]
    lancer_cycle: Callable[[], dict[str, int]]
    mode: str
    envoi_auto: bool = False
    modele: str = ""


def creer_app(services: Services, servir_frontend: bool = True) -> FastAPI:
    app = FastAPI(
        title="Agent courriel IA",
        description="Tri et réponses aux courriels avec Claude, validation humaine des brouillons.",
        version="1.0.0",
    )
    # Pour le développement : le serveur Vite (port 5173) appelle l'API.
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                       allow_methods=["*"], allow_headers=["*"])

    api = APIRouter(prefix="/api")
    m = services.memoire
    verrou_cycle = threading.Lock()

    def courriel_ou_404(mid: str) -> dict:
        c = m.obtenir(mid)
        if c is None:
            raise HTTPException(404, "Courriel introuvable.")
        return c

    @api.get("/sante", response_model=Sante, tags=["système"])
    def sante():
        return Sante(mode=services.mode, envoi_auto=services.envoi_auto, modele=services.modele)

    @api.get("/statistiques", response_model=Statistiques, tags=["tableau de bord"])
    def statistiques():
        return m.statistiques()

    @api.get("/courriels", response_model=PageCourriels, tags=["courriels"])
    def lister_courriels(
        action: str | None = None,
        categorie: str | None = None,
        statut: str | None = None,
        q: str | None = Query(None, max_length=200, description="Recherche : expéditeur, sujet, résumé"),
        page: int = Query(1, ge=1),
        taille: int = Query(20, ge=1, le=100),
    ):
        filtres = dict(action=action, categorie=categorie, statut=statut, recherche=q)
        return PageCourriels(
            elements=m.lister(**filtres, limite=taille, decalage=(page - 1) * taille),
            total=m.compter(**filtres), page=page, taille=taille,
        )

    @api.get("/courriels/{mid}", response_model=Courriel, tags=["courriels"])
    def obtenir_courriel(mid: str):
        return courriel_ou_404(mid)

    @api.post("/courriels/{mid}/approuver", response_model=Courriel, tags=["validation"])
    def approuver(mid: str, corps: Approbation):
        c = courriel_ou_404(mid)
        if c["statut"] != "en_attente" or not c["brouillon_id"]:
            raise HTTPException(409, "Ce brouillon n'est plus en attente de validation.")
        texte = (corps.texte or "").replace("\r\n", "\n").strip()
        try:
            gmail = services.fournir_gmail()
            if texte and texte != (c["reponse"] or "").strip():
                gmail.modifier_brouillon(c["brouillon_id"], texte)
            gmail.envoyer_brouillon(c["brouillon_id"])
        except Exception as e:  # brouillon supprimé dans Gmail, réseau, jeton expiré...
            log.exception("Échec de l'envoi du brouillon %s", c["brouillon_id"])
            raise HTTPException(502, f"Gmail a refusé l'envoi : {e}") from e
        m.mettre_a_jour(mid, statut="approuvé", reponse=texte or c["reponse"])
        return m.obtenir(mid)

    @api.post("/courriels/{mid}/rejeter", response_model=Courriel, tags=["validation"])
    def rejeter(mid: str):
        c = courriel_ou_404(mid)
        if c["statut"] != "en_attente":
            raise HTTPException(409, "Ce brouillon n'est plus en attente de validation.")
        if c["brouillon_id"]:
            try:
                services.fournir_gmail().supprimer_brouillon(c["brouillon_id"])
            except Exception:  # déjà supprimé à la main dans Gmail : on marque quand même
                log.warning("Brouillon %s introuvable dans Gmail", c["brouillon_id"])
        m.mettre_a_jour(mid, statut="rejeté")
        return m.obtenir(mid)

    @api.post("/agent/cycle", response_model=BilanCycle, tags=["agent"])
    def lancer_cycle():
        if not verrou_cycle.acquire(blocking=False):
            raise HTTPException(409, "Un passage est déjà en cours.")
        try:
            return BilanCycle(bilan=services.lancer_cycle())
        except Exception as e:
            log.exception("Échec du passage")
            raise HTTPException(502, f"Le passage a échoué : {e}") from e
        finally:
            verrou_cycle.release()

    app.include_router(api)

    # ---------- application Vue compilée (npm run build) ----------
    if servir_frontend and (DOSSIER_FRONTEND / "index.html").exists():
        app.mount("/assets", StaticFiles(directory=DOSSIER_FRONTEND / "assets"), name="assets")

        @app.get("/{chemin:path}", include_in_schema=False)
        def application_vue(chemin: str):
            if chemin.startswith("api/"):
                raise HTTPException(404, "Route d'API inconnue.")
            fichier = (DOSSIER_FRONTEND / chemin).resolve()
            if chemin and fichier.is_file() and DOSSIER_FRONTEND in fichier.parents:
                return FileResponse(fichier)
            return FileResponse(DOSSIER_FRONTEND / "index.html")  # routes gérées par Vue Router

    return app
