"""Orchestrateur : récupère les courriels, les analyse et décide de l'action."""

from __future__ import annotations

import logging
import re

from .modeles import Analyse, Courriel

log = logging.getLogger("agent")

ADRESSES_ROBOTS = re.compile(r"(no-?reply|ne-?pas-?repondre|mailer-daemon|notifications?@|bounce)", re.I)
CATEGORIES_JAMAIS_AUTO = {"plainte", "facture_paiement", "autre"}
SEUIL_CONFIANCE = 0.85


class Agent:
    def __init__(self, gmail, cerveau, memoire, config, simulation: bool = False):
        self.gmail = gmail
        self.cerveau = cerveau
        self.memoire = memoire
        self.cfg = config
        self.simulation = simulation
        self.moi = gmail.mon_adresse()

    # ---------- filtres avant l'IA (gratuits, rapides) ----------
    def raison_ignorer(self, c: Courriel) -> str | None:
        if c.adresse == self.moi:
            return "envoyé par moi-même"
        if ADRESSES_ROBOTS.search(c.adresse):
            return "adresse automatique"
        if "list-unsubscribe" in c.en_tetes or c.en_tetes.get("precedence", "").lower() in {"bulk", "list"}:
            return "infolettre / liste de diffusion"
        if c.en_tetes.get("auto-submitted", "no").lower() != "no":
            return "réponse automatique"
        domaine = c.adresse.split("@")[-1]
        if domaine in self.cfg.domaines_bloques:
            return f"domaine bloqué ({domaine})"
        return None

    # ---------- règles de sécurité après l'IA ----------
    def peut_envoyer_seul(self, a: Analyse) -> bool:
        return (
            self.cfg.envoi_auto
            and a.envoi_auto_ok
            and a.doit_repondre
            and a.confiance >= SEUIL_CONFIANCE
            and a.categorie in self.cfg.categories_envoi_auto
            and a.categorie not in CATEGORIES_JAMAIS_AUTO
            and a.priorite != "haute"
        )

    def traiter(self, c: Courriel) -> str:
        if (raison := self.raison_ignorer(c)) is not None:
            self.memoire.enregistrer(c.id, c.adresse, c.sujet, "-", "-", "ignoré", raison)
            return "ignoré"

        a = self.cerveau.analyser(c)
        etiquettes = [self.cfg.etiquette, f"{self.cfg.etiquette}/{a.categorie}"]
        if a.priorite == "haute":
            etiquettes.append(f"{self.cfg.etiquette}/urgent")

        brouillon_id = None
        if not a.doit_repondre or not a.reponse:
            action = "classé"
        elif self.peut_envoyer_seul(a):
            action = "envoyé"
            if not self.simulation:
                self.gmail.envoyer(c, a.reponse, self.moi)
        else:
            action = "brouillon"
            if not self.simulation:
                brouillon_id = self.gmail.creer_brouillon(c, a.reponse, self.moi)

        if not self.simulation:
            self.gmail.etiqueter(c.id, etiquettes)
        self.memoire.enregistrer(
            c.id,
            c.adresse,
            c.sujet,
            a.categorie,
            a.priorite,
            action,
            a.raison,
            resume=a.resume,
            reponse=a.reponse,
            brouillon_id=brouillon_id,
        )
        log.info("[%s] %s | %s | %s", action.upper(), c.adresse, c.sujet, a.resume)
        if self.simulation and a.reponse:
            log.info("--- Réponse proposée ---\n%s\n-----------------------", a.reponse)
        return action

    def cycle(self) -> dict[str, int]:
        bilan: dict[str, int] = {}
        for mid in self.gmail.lister(self.cfg.requete_gmail, self.cfg.max_par_cycle):
            if self.memoire.deja_traite(mid):
                continue
            try:
                action = self.traiter(self.gmail.lire(mid))
            except Exception:  # un courriel problématique ne doit pas arrêter l'agent
                log.exception("Erreur sur le courriel %s", mid)
                action = "erreur"
            bilan[action] = bilan.get(action, 0) + 1
        return bilan
