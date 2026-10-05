"""Tests sans Gmail ni Claude réels (faux objets). Lancer : pytest -q"""
import base64
from types import SimpleNamespace

from agent.agent import Agent
from agent.cerveau import Cerveau
from agent.gmail_client import extraire_corps, retirer_citations
from agent.memoire import Memoire
from agent.modeles import Analyse, Courriel


class FauxGmail:
    def __init__(self, courriels):
        self.courriels = {c.id: c for c in courriels}
        self.brouillons, self.envois, self.etiquettes = [], [], {}

    def mon_adresse(self):
        return "moi@entreprise.com"

    def lister(self, requete, maximum):
        return list(self.courriels)[:maximum]

    def lire(self, mid):
        return self.courriels[mid]

    def creer_brouillon(self, c, texte, moi):
        self.brouillons.append((c.id, texte))

    def envoyer(self, c, texte, moi):
        self.envois.append((c.id, texte))

    def etiqueter(self, mid, noms):
        self.etiquettes[mid] = noms


class FauxCerveau:
    def __init__(self, analyse):
        self.analyse, self.appels = analyse, 0

    def analyser(self, c):
        self.appels += 1
        return self.analyse


def cfg(envoi_auto=False):
    return SimpleNamespace(
        envoi_auto=envoi_auto, categories_envoi_auto=["question_frequente"], domaines_bloques=["spam.com"],
        requete_gmail="", max_par_cycle=10, etiquette="Agent-IA",
    )


def courriel(id="1", adresse="client@exemple.com", en_tetes=None):
    return Courriel(id, "t" + id, f"Client <{adresse}>", adresse, "Heures d'ouverture ?", "", "Bonjour, vos heures ?",
                    en_tetes=en_tetes or {})


def analyse(**kw):
    base = dict(categorie="question_frequente", priorite="normale", resume="Demande les heures", doit_repondre=True,
                envoi_auto_ok=True, confiance=0.95, reponse="Bonjour, nous sommes ouverts de 9 h à 17 h.", raison="FAQ")
    base.update(kw)
    return Analyse(**base)


def faire_agent(courriels, a, envoi_auto=False, tmp_path=None):
    g, cer = FauxGmail(courriels), FauxCerveau(a)
    return Agent(g, cer, Memoire(tmp_path / "t.db"), cfg(envoi_auto)), g, cer


def test_brouillon_par_defaut(tmp_path):
    ag, g, _ = faire_agent([courriel()], analyse(), tmp_path=tmp_path)
    assert ag.cycle() == {"brouillon": 1}
    assert len(g.brouillons) == 1 and not g.envois
    assert "Agent-IA/question_frequente" in g.etiquettes["1"]


def test_envoi_auto_si_tout_est_sur(tmp_path):
    ag, g, _ = faire_agent([courriel()], analyse(), envoi_auto=True, tmp_path=tmp_path)
    assert ag.cycle() == {"envoyé": 1}
    assert len(g.envois) == 1


def test_plainte_jamais_envoyee_seule(tmp_path):
    ag, g, _ = faire_agent([courriel()], analyse(categorie="plainte"), envoi_auto=True, tmp_path=tmp_path)
    assert ag.cycle() == {"brouillon": 1} and not g.envois


def test_confiance_faible_donne_brouillon(tmp_path):
    ag, g, _ = faire_agent([courriel()], analyse(confiance=0.5), envoi_auto=True, tmp_path=tmp_path)
    assert ag.cycle() == {"brouillon": 1}


def test_robots_et_infolettres_ignores_sans_appeler_ia(tmp_path):
    cs = [courriel("1", "no-reply@banque.com"), courriel("2", en_tetes={"list-unsubscribe": "<x>"}),
          courriel("3", "a@spam.com"), courriel("4", "moi@entreprise.com")]
    ag, g, cer = faire_agent(cs, analyse(), tmp_path=tmp_path)
    assert ag.cycle() == {"ignoré": 4}
    assert cer.appels == 0


def test_pas_de_double_traitement(tmp_path):
    ag, g, cer = faire_agent([courriel()], analyse(), tmp_path=tmp_path)
    ag.cycle()
    ag.cycle()
    assert cer.appels == 1 and len(g.brouillons) == 1


def test_simulation_ne_touche_pas_gmail(tmp_path):
    ag, g, _ = faire_agent([courriel()], analyse(), tmp_path=tmp_path)
    ag.simulation = True
    ag.cycle()
    assert not g.brouillons and not g.etiquettes


def test_classe_sans_reponse(tmp_path):
    ag, g, _ = faire_agent([courriel()], analyse(doit_repondre=False, reponse=""), tmp_path=tmp_path)
    assert ag.cycle() == {"classé": 1} and not g.brouillons


def test_une_erreur_n_arrete_pas_l_agent(tmp_path):
    class Casse(FauxCerveau):
        def analyser(self, c):
            if c.id == "1":
                raise RuntimeError("panne")
            return super().analyser(c)

    g = FauxGmail([courriel("1"), courriel("2")])
    ag = Agent(g, Casse(analyse()), Memoire(tmp_path / "t.db"), cfg())
    assert ag.cycle() == {"erreur": 1, "brouillon": 1}


def test_cerveau_lit_la_reponse_de_l_outil():
    entree = dict(categorie="demande_rdv", priorite="haute", resume="r", doit_repondre=True, envoi_auto_ok=False,
                  confiance=0.7, reponse="  Bonjour  ", raison="x")
    client = SimpleNamespace(messages=SimpleNamespace(
        create=lambda **kw: SimpleNamespace(content=[SimpleNamespace(type="tool_use", input=entree)])))
    a = Cerveau(client, "m", "s").analyser(courriel())
    assert a.categorie == "demande_rdv" and a.reponse == "Bonjour"


def test_extraction_corps_html_et_citations():
    b64 = lambda s: base64.urlsafe_b64encode(s.encode()).decode()
    payload = {"mimeType": "multipart/alternative", "parts": [
        {"mimeType": "text/html", "body": {"data": b64("<p>Salut&nbsp;!</p><br>Merci")}}]}
    assert "Salut" in extraire_corps(payload) and "<p>" not in extraire_corps(payload)
    assert retirer_citations("Oui merci\n\nLe 3 oct. 2026, Marie a écrit :\n> vieux") == "Oui merci"
