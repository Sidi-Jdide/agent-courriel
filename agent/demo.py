"""Données fictives pour montrer l'interface sans connecter Gmail ni Claude."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

SIGNATURE = "\n\nCordialement,\nL'équipe de Mon Entreprise"

EXEMPLES = [
    (
        "marie.tremblay@exemple.com",
        "Heures d'ouverture ce samedi ?",
        "question_frequente",
        "normale",
        "envoyé",
        "Demande si le magasin est ouvert samedi.",
        "Question couverte par la FAQ, réponse sans risque.",
        "Bonjour Marie,\n\nMerci de votre message. Nous sommes ouverts du lundi au vendredi, de 9 h à 17 h. "
        "Nous sommes malheureusement fermés les fins de semaine." + SIGNATURE,
        0.3,
    ),
    (
        "j.roy@entreprise-abc.ca",
        "Commande #4821 jamais reçue — inacceptable",
        "plainte",
        "haute",
        "brouillon",
        "Client mécontent : commande de 12 jours non livrée.",
        "Plainte : jamais d'envoi automatique, un humain doit valider.",
        "Bonjour M. Roy,\n\nJe suis vraiment désolé pour ce retard. Je transmets immédiatement votre dossier à notre "
        "équipe, qui vérifiera le suivi de la commande #4821 et vous reviendra d'ici 24 h ouvrables." + SIGNATURE,
        1.2,
    ),
    (
        "sophie.n@gmail.com",
        "Rendez-vous pour une consultation",
        "demande_rdv",
        "normale",
        "brouillon",
        "Souhaite prendre rendez-vous la semaine prochaine.",
        "Demande de rendez-vous, le lien de réservation est dans la FAQ.",
        "Bonjour Sophie,\n\nAvec plaisir ! Vous pouvez choisir le moment qui vous convient directement sur "
        "www.exemple.com/rendez-vous." + SIGNATURE,
        2.5,
    ),
    ("no-reply@banque.com", "Votre relevé est disponible", "-", "-", "ignoré", "", "adresse automatique", "", 3.0),
    (
        "comptabilite@fournisseur.ca",
        "Facture 2026-0917 en retard",
        "facture_paiement",
        "haute",
        "brouillon",
        "Fournisseur réclame le paiement d'une facture.",
        "Question d'argent : validation humaine obligatoire.",
        "Bonjour,\n\nMerci pour votre rappel. Je transmets la facture 2026-0917 à notre service de comptabilité, "
        "qui vous confirmera la date de paiement rapidement." + SIGNATURE,
        5.0,
    ),
    (
        "infolettre@magasin.com",
        "-50 % cette fin de semaine !",
        "-",
        "-",
        "ignoré",
        "",
        "infolettre / liste de diffusion",
        "",
        6.0,
    ),
    (
        "alex.b@outlook.com",
        "Politique de retour ?",
        "question_frequente",
        "basse",
        "envoyé",
        "Demande le délai pour retourner un article.",
        "Couvert par la FAQ.",
        "Bonjour Alex,\n\nLes retours sont acceptés dans les 30 jours suivant l'achat, avec la facture." + SIGNATURE,
        20.0,
    ),
    (
        "partenaire@startup.io",
        "Collaboration possible ?",
        "question_client",
        "normale",
        "brouillon",
        "Propose un partenariat commercial.",
        "Sujet stratégique, information absente de la base.",
        "Bonjour,\n\nMerci pour votre intérêt ! Je transmets votre proposition à la direction, qui vous "
        "recontactera prochainement." + SIGNATURE,
        26.0,
    ),
    (
        "alertes@github.com",
        "Nouvelle connexion détectée",
        "notification_auto",
        "basse",
        "classé",
        "Alerte de sécurité automatique.",
        "Notification, aucune réponse nécessaire.",
        "",
        30.0,
    ),
    (
        "luc.gagnon@exemple.com",
        "Merci pour votre aide !",
        "accuse_reception",
        "basse",
        "envoyé",
        "Client qui remercie l'équipe.",
        "Simple remerciement.",
        "Bonjour Luc,\n\nMerci beaucoup pour votre message, ça nous fait plaisir !" + SIGNATURE,
        48.0,
    ),
]


def remplir(memoire) -> None:
    maintenant = datetime.now(UTC)
    for i, (exp, sujet, cat, prio, action, resume, raison, rep, heures) in enumerate(EXEMPLES):
        date = (maintenant - timedelta(hours=heures)).isoformat(timespec="seconds")
        memoire.enregistrer(
            f"demo-{i}",
            exp,
            sujet,
            cat,
            prio,
            action,
            raison,
            resume=resume,
            reponse=rep,
            brouillon_id=f"brouillon-{i}" if action == "brouillon" else None,
            date=date,
        )


class GmailDemo:
    """Fait semblant d'agir sur Gmail (mode démo)."""

    def modifier_brouillon(self, brouillon_id, texte):
        pass

    def envoyer_brouillon(self, brouillon_id):
        return "envoye-" + brouillon_id

    def supprimer_brouillon(self, brouillon_id):
        pass


NOUVEAUX = [
    (
        "emma.c@exemple.com",
        "Livrez-vous à Sherbrooke ?",
        "question_frequente",
        "normale",
        "envoyé",
        "Demande si la livraison couvre Sherbrooke.",
        "Couvert par la FAQ (livraison au Québec).",
        "Bonjour Emma,\n\nOui ! Nous livrons partout au Québec, en 3 à 5 jours ouvrables." + SIGNATURE,
    ),
    (
        "rh@grandeentreprise.ca",
        "Soumission pour 200 unités",
        "question_client",
        "haute",
        "brouillon",
        "Demande de prix pour une grosse commande.",
        "Prix absents de la base : validation humaine.",
        "Bonjour,\n\nMerci pour votre demande ! Je la transmets à notre équipe commerciale, qui vous enverra "
        "une soumission détaillée sous 24 h ouvrables." + SIGNATURE,
    ),
    (
        "newsletter@outils.com",
        "Les nouveautés d'octobre",
        "-",
        "-",
        "ignoré",
        "",
        "infolettre / liste de diffusion",
        "",
    ),
]


def simuler_cycle(memoire) -> dict[str, int]:
    """Mode démo : « reçoit » les courriels de NOUVEAUX qui n'ont pas encore été traités."""
    bilan: dict[str, int] = {}
    for i, (exp, sujet, cat, prio, action, resume, raison, rep) in enumerate(NOUVEAUX):
        mid = f"demo-nouveau-{i}"
        if memoire.deja_traite(mid):
            continue
        memoire.enregistrer(
            mid,
            exp,
            sujet,
            cat,
            prio,
            action,
            raison,
            resume=resume,
            reponse=rep,
            brouillon_id=f"brouillon-nouveau-{i}" if action == "brouillon" else None,
        )
        bilan[action] = bilan.get(action, 0) + 1
    return bilan
