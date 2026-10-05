"""Mémoire SQLite : évite de traiter deux fois le même courriel et garde l'historique complet."""
from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone

SCHEMA = """CREATE TABLE IF NOT EXISTS traites (
    id TEXT PRIMARY KEY, date TEXT, expediteur TEXT, sujet TEXT,
    categorie TEXT, priorite TEXT, action TEXT, raison TEXT
)"""
# Colonnes ajoutées plus tard : ajoutées automatiquement aux anciennes bases (migration simple).
COLONNES_AJOUTEES = {"resume": "TEXT", "reponse": "TEXT", "brouillon_id": "TEXT", "statut": "TEXT"}
CHAMPS_MODIFIABLES = {"statut", "reponse"}
STATUT_INITIAL = {"brouillon": "en_attente", "envoyé": "envoyé"}


class Memoire:
    def __init__(self, chemin):
        # L'API sert plusieurs requêtes en parallèle : un verrou protège la connexion partagée.
        self._verrou = threading.RLock()
        self.db = sqlite3.connect(str(chemin), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        with self._verrou:
            self.db.execute(SCHEMA)
            existantes = {r["name"] for r in self.db.execute("PRAGMA table_info(traites)")}
            for nom, type_ in COLONNES_AJOUTEES.items():
                if nom not in existantes:
                    self.db.execute(f"ALTER TABLE traites ADD COLUMN {nom} {type_}")
            self.db.execute("CREATE INDEX IF NOT EXISTS idx_date ON traites(date)")
            self.db.commit()

    def deja_traite(self, message_id: str) -> bool:
        with self._verrou:
            return self.db.execute("SELECT 1 FROM traites WHERE id = ?", (message_id,)).fetchone() is not None

    def enregistrer(self, message_id, expediteur, sujet, categorie, priorite, action, raison,
                    resume="", reponse="", brouillon_id=None, date=None):
        with self._verrou:
            self.db.execute(
                """INSERT OR REPLACE INTO traites
                   (id, date, expediteur, sujet, categorie, priorite, action, raison, resume, reponse, brouillon_id, statut)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (message_id, date or datetime.now(timezone.utc).isoformat(timespec="seconds"), expediteur, sujet,
                 categorie, priorite, action, raison, resume, reponse, brouillon_id, STATUT_INITIAL.get(action, "-")),
            )
            self.db.commit()

    # ---------- lecture ----------
    @staticmethod
    def _filtres(action, categorie, statut, recherche):
        sql, params = " WHERE 1=1", []
        for col, val in (("action", action), ("categorie", categorie), ("statut", statut)):
            if val:
                sql += f" AND {col} = ?"
                params.append(val)
        if recherche:
            sql += " AND (expediteur LIKE ? OR sujet LIKE ? OR resume LIKE ?)"
            params += [f"%{recherche}%"] * 3
        return sql, params

    def lister(self, action=None, categorie=None, statut=None, recherche=None, limite=50, decalage=0) -> list[dict]:
        where, params = self._filtres(action, categorie, statut, recherche)
        with self._verrou:
            rows = self.db.execute(f"SELECT * FROM traites{where} ORDER BY date DESC LIMIT ? OFFSET ?",
                                   (*params, limite, decalage))
            return [dict(r) for r in rows]

    def compter(self, action=None, categorie=None, statut=None, recherche=None) -> int:
        where, params = self._filtres(action, categorie, statut, recherche)
        with self._verrou:
            return self.db.execute(f"SELECT COUNT(*) FROM traites{where}", params).fetchone()[0]

    def obtenir(self, message_id: str) -> dict | None:
        with self._verrou:
            r = self.db.execute("SELECT * FROM traites WHERE id = ?", (message_id,)).fetchone()
        return dict(r) if r else None

    def statistiques(self) -> dict:
        with self._verrou:
            par_action = {r[0]: r[1] for r in self.db.execute("SELECT action, COUNT(*) FROM traites GROUP BY action")}
            par_cat = {r[0]: r[1] for r in self.db.execute(
                "SELECT categorie, COUNT(*) FROM traites WHERE categorie != '-' GROUP BY categorie ORDER BY 2 DESC")}
            en_attente = self.db.execute("SELECT COUNT(*) FROM traites WHERE statut = 'en_attente'").fetchone()[0]
        return {"total": sum(par_action.values()), "en_attente": en_attente,
                "par_action": par_action, "par_categorie": par_cat}

    def mettre_a_jour(self, message_id: str, **champs) -> None:
        inconnus = set(champs) - CHAMPS_MODIFIABLES
        if inconnus:
            raise ValueError(f"Champs non modifiables : {inconnus}")
        cles = ", ".join(f"{k} = ?" for k in champs)
        with self._verrou:
            self.db.execute(f"UPDATE traites SET {cles} WHERE id = ?", (*champs.values(), message_id))
            self.db.commit()

    def journal(self, limite: int = 20):
        return [(r["date"], r["expediteur"], r["sujet"], r["categorie"], r["action"]) for r in self.lister(limite=limite)]
