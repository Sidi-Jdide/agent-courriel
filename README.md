# Agent IA de réponse aux courriels

Un agent qui surveille une boîte Gmail, comprend chaque courriel avec **Claude** (Anthropic), le classe et prépare
une réponse. Par défaut, il crée des **brouillons** : un humain les valide dans une interface web avant l'envoi.

**Stack :** Python 3.13 · FastAPI · Pydantic · SQLite · API Gmail · API Claude · Vue 3 · TypeScript · Vite · Vue Router · Docker

## Démarrage rapide (mode démo, sans Gmail ni clé API)

```bash
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
python -m api --demo
```

Ouvrir **http://127.0.0.1:8000** (interface) et **http://127.0.0.1:8000/docs** (documentation interactive de l'API).

Ou avec Docker : `docker compose up --build demo`

## Fonctionnement

```
Gmail ──► filtres sans IA ──► Claude (analyse structurée) ──► règles de sécurité ──► brouillon / envoi / classement
            (robots,             catégorie, priorité,           (code, pas l'IA)              │
             infolettres)        résumé, réponse                                              ▼
                                                                         SQLite ◄──► API FastAPI ◄──► Interface Vue
                                                                                                    (validation humaine)
```

1. Récupère les courriels non lus.
2. **Filtre sans IA** (gratuit) : no-reply, infolettres, réponses automatiques, ses propres courriels, domaines bloqués.
3. **Claude analyse** via *tool use* : sortie JSON garantie (catégorie, priorité, résumé, réponse, confiance, justification).
4. **Le code décide** : rien à répondre → étiquette ; cas normal → brouillon dans le bon fil ; cas simple et sûr →
   envoi automatique (seulement si `ENVOI_AUTO=true`).
5. **Un humain valide** dans l'interface : il modifie la réponse si besoin, puis l'approuve (envoi Gmail) ou la rejette.

## Architecture

```
agent/                    cœur métier (indépendant du web)
  config.py               réglages (.env)
  gmail_client.py         API Gmail : lecture, brouillons, envoi, étiquettes
  cerveau.py              Claude : prompt système + outil d'analyse structurée
  agent.py                orchestration + règles de sécurité
  memoire.py              SQLite (verrou multi-thread, migration automatique)
  demo.py                 données fictives
api/                      backend FastAPI
  app.py                  routes REST, injection des dépendances, service du frontend
  schemas.py              contrats Pydantic (→ OpenAPI / Swagger)
  __main__.py             démarrage : python -m api [--demo]
frontend/                 application Vue 3 + TypeScript
  src/api.ts              client HTTP typé, gestion d'erreurs
  src/views/              Tableau de bord, Historique, Détail
  src/components/         liste, badges, notifications
main.py                   agent en ligne de commande (--simulation, --boucle, --journal)
tests/                    tests Python (pytest)
Dockerfile                build multi-étapes (Node → Python)
docker-compose.yml        démo, API, vérificateur périodique
```

## API REST

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/api/sante` | mode, envoi auto, modèle |
| GET | `/api/statistiques` | totaux, à valider, répartition par catégorie |
| GET | `/api/courriels?statut=&action=&categorie=&q=&page=&taille=` | liste filtrée et paginée |
| GET | `/api/courriels/{id}` | détail |
| POST | `/api/courriels/{id}/approuver` | envoie le brouillon (texte modifié optionnel) |
| POST | `/api/courriels/{id}/rejeter` | supprime le brouillon |
| POST | `/api/agent/cycle` | lance un passage de l'agent |

Codes d'erreur explicites : `404` introuvable, `409` déjà traité ou passage en cours, `422` paramètre invalide,
`502` erreur Gmail (le statut n'est alors **pas** modifié).

## Sécurité

- **Brouillons par défaut** : l'envoi automatique doit être activé explicitement.
- **Double vérification** : même si Claude dit « OK », le code exige une confiance ≥ 0,85, une catégorie autorisée et
  une priorité non haute. Plaintes et paiements ne partent **jamais** seuls.
- **Injection de prompt** : le contenu du courriel est traité comme une donnée, jamais comme une instruction.
- **Pas d'invention** : l'IA répond seulement avec `connaissances.md`, sinon elle transmet à l'équipe.
- **Pas de double envoi** : un brouillon déjà approuvé ou rejeté renvoie `409`.
- L'API écoute sur `127.0.0.1` par défaut. Secrets exclus de git et de l'image Docker.

## Mise en production avec Gmail

1. Clé Claude : https://console.anthropic.com → dans `.env` (copier `.env.example`).
2. Google Cloud Console : créer un projet, activer **Gmail API**, écran de consentement (utilisateur test),
   créer un **ID client OAuth « Application de bureau »**, télécharger le JSON en `credentials.json`.
3. Première connexion (ouvre le navigateur, crée `token.json`) : `python main.py --simulation`
4. Lancer :
   ```bash
   python -m api                  # interface + API
   python main.py --boucle 300    # vérification automatique toutes les 5 min (autre terminal)
   ```
   ou `docker compose up --build agent verificateur`.

## Développement

```bash
python -m api --demo              # terminal 1 : API sur :8000
cd frontend && npm run dev        # terminal 2 : Vite sur :5173 (rechargement à chaud, proxy vers l'API)
```

## Tests

```bash
pytest -q                         # 20 tests : agent, sécurité, API
cd frontend && npm test           # 8 tests : logique d'affichage, composants
cd frontend && npm run build      # vérification TypeScript stricte + build
```

## Pistes d'amélioration

- Authentification (OAuth Google ou JWT) pour exposer l'interface en ligne
- Notifications Gmail en temps réel (Pub/Sub) au lieu d'une vérification périodique
- Historique du fil complet envoyé à Claude pour les longues conversations
- Support Outlook (Microsoft Graph)
- PostgreSQL et file de tâches (Celery/RQ) pour de gros volumes
