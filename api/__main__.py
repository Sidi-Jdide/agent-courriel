"""Démarre le serveur.

    python -m api --demo     # données fictives : ni Gmail ni clé API
    python -m api            # vraie base + Gmail + Claude
"""
from __future__ import annotations

import argparse
import logging

import uvicorn

from agent.config import Config
from agent.memoire import Memoire

from .app import Services, creer_app


def services_demo() -> Services:
    from agent.demo import GmailDemo, remplir, simuler_cycle

    memoire = Memoire(":memory:")
    remplir(memoire)
    gmail = GmailDemo()
    return Services(memoire, lambda: gmail, lambda: simuler_cycle(memoire), mode="demo", modele="démo")


def services_reels(cfg: Config) -> Services:
    memoire = Memoire(cfg.base_donnees)
    cache: dict = {}

    def gmail():
        if "gmail" not in cache:
            from agent.gmail_client import Gmail, connecter
            cache["gmail"] = Gmail(connecter(cfg.credentials_path, cfg.token_path))
        return cache["gmail"]

    def agent():
        if "agent" not in cache:
            import anthropic

            from agent.agent import Agent
            from agent.cerveau import Cerveau, prompt_systeme
            cerveau = Cerveau(anthropic.Anthropic(api_key=cfg.anthropic_api_key), cfg.modele,
                              prompt_systeme(cfg.nom_entreprise, cfg.signature, cfg.connaissances()))
            cache["agent"] = Agent(gmail(), cerveau, memoire, cfg)
        return cache["agent"]

    return Services(memoire, gmail, lambda: agent().cycle(), mode="gmail",
                    envoi_auto=cfg.envoi_auto, modele=cfg.modele)


def main():
    p = argparse.ArgumentParser(description="Serveur API + interface de l'agent courriel")
    p.add_argument("--demo", action="store_true", help="données fictives, sans Gmail ni Claude")
    p.add_argument("--hote", default="127.0.0.1", help="0.0.0.0 pour Docker")
    p.add_argument("--port", type=int, default=8000)
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    services = services_demo() if args.demo else services_reels(Config())
    print(f"Interface : http://127.0.0.1:{args.port}   Documentation API : http://127.0.0.1:{args.port}/docs")
    uvicorn.run(creer_app(services), host=args.hote, port=args.port)


if __name__ == "__main__":
    main()
