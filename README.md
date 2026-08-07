# ICI ou là ?

Jeu de géolocalisation quotidien basé sur les articles de [ici.fr](https://www.ici.fr) : chaque jour, 5 articles insolites ou amusants sont sélectionnés, le lieu est masqué dans le titre, et le joueur doit le retrouver sur une carte de France.

Le front est un site statique (HTML + JS, Leaflet, Papa Parse). Le backend, en Python, récupère les archives d'ici.fr, fait sélectionner les 5 meilleurs articles par un LLM (OpenAI), géocode les lieux et génère le CSV + la page d'archives.

## Site en ligne

- Accueil : <https://ClementChapalain.github.io/ici-ou-la/>
- Généré automatiquement chaque nuit à 0h35 (heure de Paris) par GitHub Actions.

## Règles du jeu

1. Retrouvez le lieu masqué (`_____`) dans le titre.
2. Placez votre repère sur la carte.
3. Marquez des points selon la proximité de votre réponse (score max 5000, distance max 600 km).

## Structure

```
index.html            Accueil
ici ou là.html        Accueil (nom d'origine, lié par daily/archives)
daily.html            Partie du jour (Leaflet)
archives.html         Les 30 dernières parties (généré)
script_game.js        Logique du jeu
style.css             Styles
articles.csv          Données des parties (généré)
backend/              Générateur Python
.github/workflows/    Workflow GitHub Actions
old/                  Anciennes versions (non publiées)
```

## Backend

### Prérequis

- Python 3.10+
- Une clé API OpenAI (`gpt-4o-mini` par défaut)

### Installation

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # puis renseigner OPENAI_API_KEY
```

### Utilisation

```bash
# Depuis la racine du projet
backend/.venv/bin/python -m backend.run                 # partie de la veille (Europe/Paris)
backend/.venv/bin/python -m backend.run --date 2026-07-29
backend/.venv/bin/python -m backend.run --start 2026-07-30 --end 2026-08-06   # rattrapage
backend/.venv/bin/python -m backend.run --dry-run       # sans écrire le CSV
```

Le script met à jour `articles.csv` (31 parties max) et régénère `archives.html`. Le géocodage (Nominatim) est mis en cache dans `backend/geocode_cache.json`.

### Pipeline

1. `fetch_archive.py` : scrape les archives d'ici.fr (`/archives/{année}/{jour}-{mois}`, paginé).
2. `llm.py` : le modèle reçoit les ~300 titres et renvoie un JSON de 5 articles avec un lieu unique (ville, département ou région) présent tel quel dans le titre ; les doublons et lieux invalides sont retentés jusqu'à 6 fois.
3. `geocode.py` : nettoyage du lieu (gentilés, accents), troncature du titre, géocodage Nominatim (les régions utilisent un tableau de centroïdes) et titre tronqué.
4. `generate.py` : écrit le CSV et `archives.html`.

## Automatisation

Le workflow `.github/workflows/daily.yml` tourne chaque nuit (`cron "35 22 * * *"`, soit ~0h35 à Paris), génère la partie, committe les fichiers produits, puis déploie le site sur GitHub Pages (source : **GitHub Actions**).

Le secret `OPENAI_API_KEY` doit être configuré dans les secrets du dépôt pour que la génération fonctionne en CI.

## Configuration

| Variable | Rôle | Défaut |
| --- | --- | --- |
| `OPENAI_API_KEY` | Clé OpenAI (nécessaire) | — |
| `OPENAI_MODEL` | Modèle de sélection | `gpt-4o-mini` |
