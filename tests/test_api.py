"""Tests de l'API FastAPI (TestClient, aucune connexion réseau)."""
import pytest
from fastapi.testclient import TestClient

from agent.demo import remplir, simuler_cycle
from agent.memoire import Memoire
from api.app import Services, creer_app


class GmailEspion:
    def __init__(self, panne=False):
        self.panne = panne
        self.modifies, self.envoyes, self.supprimes = [], [], []

    def modifier_brouillon(self, bid, texte):
        self.modifies.append((bid, texte))

    def envoyer_brouillon(self, bid):
        if self.panne:
            raise RuntimeError("jeton expiré")
        self.envoyes.append(bid)

    def supprimer_brouillon(self, bid):
        self.supprimes.append(bid)


def construire(panne=False):
    m = Memoire(":memory:")
    remplir(m)
    g = GmailEspion(panne)
    app = creer_app(Services(m, lambda: g, lambda: simuler_cycle(m), mode="demo"), servir_frontend=False)
    return TestClient(app), m, g


@pytest.fixture
def env():
    return construire()


def test_sante_et_statistiques(env):
    client, _, _ = env
    assert client.get("/api/sante").json()["mode"] == "demo"
    stats = client.get("/api/statistiques").json()
    assert stats["total"] == 10 and stats["en_attente"] == 4
    assert stats["par_categorie"]["question_frequente"] == 2


def test_liste_filtres_et_pagination(env):
    client, _, _ = env
    page = client.get("/api/courriels", params={"taille": 3}).json()
    assert page["total"] == 10 and len(page["elements"]) == 3
    page2 = client.get("/api/courriels", params={"taille": 3, "page": 2}).json()
    assert {e["id"] for e in page["elements"]}.isdisjoint(e["id"] for e in page2["elements"])
    attente = client.get("/api/courriels", params={"statut": "en_attente"}).json()
    assert attente["total"] == 4 and all(e["statut"] == "en_attente" for e in attente["elements"])
    assert client.get("/api/courriels", params={"q": "sophie"}).json()["total"] == 1
    assert client.get("/api/courriels", params={"taille": 500}).status_code == 422


def test_detail_et_404(env):
    client, _, _ = env
    assert client.get("/api/courriels/demo-1").json()["categorie"] == "plainte"
    assert client.get("/api/courriels/inconnu").status_code == 404


def test_approuver_avec_modification(env):
    client, m, g = env
    r = client.post("/api/courriels/demo-1/approuver", json={"texte": "Texte corrigé"})
    assert r.status_code == 200 and r.json()["statut"] == "approuvé" and r.json()["reponse"] == "Texte corrigé"
    assert g.modifies == [("brouillon-1", "Texte corrigé")]
    assert g.envoyes == ["brouillon-1"]
    assert client.post("/api/courriels/demo-1/approuver", json={}).status_code == 409  # pas deux fois


def test_approuver_sans_modification(env):
    client, _, g = env
    assert client.post("/api/courriels/demo-2/approuver", json={}).status_code == 200
    assert g.modifies == [] and g.envoyes == ["brouillon-2"]


def test_erreur_gmail_ne_change_pas_le_statut():
    client, m, _ = construire(panne=True)
    r = client.post("/api/courriels/demo-1/approuver", json={})
    assert r.status_code == 502 and "jeton expiré" in r.json()["detail"]
    assert m.obtenir("demo-1")["statut"] == "en_attente"


def test_rejeter(env):
    client, _, g = env
    assert client.post("/api/courriels/demo-4/rejeter").json()["statut"] == "rejeté"
    assert g.supprimes == ["brouillon-4"]
    assert client.post("/api/courriels/demo-4/rejeter").status_code == 409


def test_lancer_un_passage(env):
    client, _, _ = env
    assert client.post("/api/agent/cycle").json()["bilan"] == {"envoyé": 1, "brouillon": 1, "ignoré": 1}
    assert client.post("/api/agent/cycle").json()["bilan"] == {}
    assert client.get("/api/statistiques").json()["total"] == 13


def test_documentation_openapi(env):
    client, _, _ = env
    chemins = client.get("/openapi.json").json()["paths"]
    assert "/api/courriels/{mid}/approuver" in chemins
