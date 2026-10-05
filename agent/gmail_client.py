"""Accès à Gmail : lire, étiqueter, créer des brouillons et envoyer."""

from __future__ import annotations

import base64
import html
import re
from email import message_from_bytes, policy
from email.message import EmailMessage
from email.utils import parseaddr

from .modeles import Courriel

# gmail.modify permet de lire, étiqueter, créer des brouillons et envoyer.
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def connecter(credentials_path, token_path):
    """Ouvre une session Gmail (OAuth). La première fois, un navigateur s'ouvre."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _decoder(data: str) -> str:
    return base64.urlsafe_b64decode(data.encode()).decode("utf-8", errors="replace")


def _html_en_texte(texte: str) -> str:
    texte = re.sub(r"(?is)<(script|style).*?</\1>", "", texte)
    texte = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", texte)
    texte = re.sub(r"<[^>]+>", "", texte)
    return re.sub(r"\n{3,}", "\n\n", html.unescape(texte)).strip()


def extraire_corps(payload: dict) -> str:
    """Retourne le texte du courriel (text/plain de préférence, sinon HTML nettoyé)."""
    texte, html_brut = [], []

    def parcourir(partie):
        mime = partie.get("mimeType", "")
        data = partie.get("body", {}).get("data")
        if data and mime == "text/plain":
            texte.append(_decoder(data))
        elif data and mime == "text/html":
            html_brut.append(_decoder(data))
        for sous in partie.get("parts", []) or []:
            parcourir(sous)

    parcourir(payload)
    if texte:
        return "\n".join(texte).strip()
    if html_brut:
        return _html_en_texte("\n".join(html_brut))
    return ""


def retirer_citations(corps: str) -> str:
    """Enlève l'historique cité (« Le ... a écrit : », lignes en >) pour garder le nouveau message."""
    motifs = [r"^Le .+ a écrit\s*:", r"^On .+ wrote:", r"^-{2,}\s*Original Message", r"^De\s*:.*$"]
    lignes = []
    for ligne in corps.splitlines():
        if any(re.match(m, ligne.strip(), re.I) for m in motifs):
            break
        if not ligne.lstrip().startswith(">"):
            lignes.append(ligne)
    return "\n".join(lignes).strip() or corps


class Gmail:
    def __init__(self, service):
        self.s = service
        self._etiquettes: dict[str, str] = {}

    def mon_adresse(self) -> str:
        return self.s.users().getProfile(userId="me").execute()["emailAddress"].lower()

    def lister(self, requete: str, maximum: int) -> list[str]:
        res = self.s.users().messages().list(userId="me", q=requete, maxResults=maximum).execute()
        return [m["id"] for m in res.get("messages", [])]

    def lire(self, message_id: str) -> Courriel:
        m = self.s.users().messages().get(userId="me", id=message_id, format="full").execute()
        en_tetes = {h["name"].lower(): h["value"] for h in m["payload"].get("headers", [])}
        expediteur = en_tetes.get("reply-to") or en_tetes.get("from", "")
        return Courriel(
            id=m["id"],
            thread_id=m["threadId"],
            expediteur=en_tetes.get("from", ""),
            adresse=parseaddr(expediteur)[1].lower(),
            sujet=en_tetes.get("subject", "(sans sujet)"),
            date=en_tetes.get("date", ""),
            corps=retirer_citations(extraire_corps(m["payload"]))[:15000],
            message_id=en_tetes.get("message-id", ""),
            references=en_tetes.get("references", ""),
            en_tetes=en_tetes,
        )

    def _construire_reponse(self, c: Courriel, texte: str, moi: str) -> dict:
        msg = EmailMessage()
        msg["To"] = c.adresse
        msg["From"] = moi
        msg["Subject"] = c.sujet if c.sujet.lower().startswith("re:") else f"Re: {c.sujet}"
        if c.message_id:
            msg["In-Reply-To"] = c.message_id
            msg["References"] = f"{c.references} {c.message_id}".strip()
        msg.set_content(texte)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        return {"raw": raw, "threadId": c.thread_id}

    def creer_brouillon(self, c: Courriel, texte: str, moi: str) -> str:
        corps = {"message": self._construire_reponse(c, texte, moi)}
        return self.s.users().drafts().create(userId="me", body=corps).execute()["id"]

    def envoyer(self, c: Courriel, texte: str, moi: str) -> str:
        corps = self._construire_reponse(c, texte, moi)
        return self.s.users().messages().send(userId="me", body=corps).execute()["id"]

    # ---------- gestion des brouillons depuis l'interface ----------
    def modifier_brouillon(self, brouillon_id: str, texte: str) -> None:
        """Remplace le texte d'un brouillon en gardant destinataire, sujet et fil de discussion."""
        d = self.s.users().drafts().get(userId="me", id=brouillon_id, format="raw").execute()
        msg = message_from_bytes(base64.urlsafe_b64decode(d["message"]["raw"]), policy=policy.default)
        msg.set_content(texte)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        corps = {"id": brouillon_id, "message": {"raw": raw, "threadId": d["message"]["threadId"]}}
        self.s.users().drafts().update(userId="me", id=brouillon_id, body=corps).execute()

    def envoyer_brouillon(self, brouillon_id: str) -> str:
        return self.s.users().drafts().send(userId="me", body={"id": brouillon_id}).execute()["id"]

    def supprimer_brouillon(self, brouillon_id: str) -> None:
        self.s.users().drafts().delete(userId="me", id=brouillon_id).execute()

    def _id_etiquette(self, nom: str) -> str:
        if nom in self._etiquettes:
            return self._etiquettes[nom]
        existantes = self.s.users().labels().list(userId="me").execute().get("labels", [])
        for e in existantes:
            if e["name"] == nom:
                self._etiquettes[nom] = e["id"]
                return e["id"]
        nouvelle = (
            self.s.users()
            .labels()
            .create(
                userId="me", body={"name": nom, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
            )
            .execute()
        )
        self._etiquettes[nom] = nouvelle["id"]
        return nouvelle["id"]

    def etiqueter(self, message_id: str, noms: list[str]) -> None:
        ids = [self._id_etiquette(n) for n in noms]
        self.s.users().messages().modify(userId="me", id=message_id, body={"addLabelIds": ids}).execute()
