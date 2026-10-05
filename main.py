"""Point d'entrée.

Exemples :
    python main.py --simulation        # analyse sans rien toucher dans Gmail
    python main.py                     # un seul passage
    python main.py --boucle 300        # vérifie la boîte toutes les 5 minutes
    python main.py --journal           # affiche les derniers courriels traités
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

from agent.config import Config


def main() -> int:
    p = argparse.ArgumentParser(description="Agent IA de réponse aux courriels (Gmail + Claude)")
    p.add_argument("--simulation", action="store_true", help="n'écrit rien dans Gmail, affiche les réponses")
    p.add_argument("--boucle", type=int, metavar="SECONDES", help="tourner en continu avec cet intervalle")
    p.add_argument("--journal", action="store_true", help="afficher l'historique et quitter")
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    cfg = Config()

    from agent.memoire import Memoire

    memoire = Memoire(cfg.base_donnees)
    if args.journal:
        for ligne in memoire.journal():
            print(" | ".join(str(x) for x in ligne))
        return 0

    if not cfg.anthropic_api_key:
        print("Erreur : ANTHROPIC_API_KEY manquant dans le fichier .env")
        return 1

    import anthropic

    from agent.agent import Agent
    from agent.cerveau import Cerveau, prompt_systeme
    from agent.gmail_client import Gmail, connecter

    gmail = Gmail(connecter(cfg.credentials_path, cfg.token_path))
    cerveau = Cerveau(
        anthropic.Anthropic(api_key=cfg.anthropic_api_key),
        cfg.modele,
        prompt_systeme(cfg.nom_entreprise, cfg.signature, cfg.connaissances()),
    )
    agent = Agent(gmail, cerveau, memoire, cfg, simulation=args.simulation)
    logging.info(
        "Agent démarré pour %s (envoi auto : %s)", agent.moi, "OUI" if cfg.envoi_auto else "non, brouillons seulement"
    )

    while True:
        bilan = agent.cycle()
        logging.info("Bilan du passage : %s", bilan or "aucun nouveau courriel")
        if not args.boucle:
            return 0
        time.sleep(args.boucle)


if __name__ == "__main__":
    sys.exit(main())
