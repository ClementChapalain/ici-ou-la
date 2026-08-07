from __future__ import annotations

import json
import re

from .config import OPENAI_API_KEY, OPENAI_MODEL

SYSTEME_SCORE = """Tu es un curateur pour un jeu mobile de géolocalisation.

Je vais te donner les titres d'articles du jour, numérotés. Pour chaque article, attribue un score de 0 à 10.

Score = à quel point on a ENVIE DE LIRE cet article, ET à quel point il fait un bon sujet pour le jeu géo.

Un bon sujet pour le jeu géo :
- le titre contient le nom d'une ville ou d'un village (ex. "Guingamp", "Bastia", "Aubenas") que le jeu masquera
- le titre contient en plus un indice qui permet de deviner cette ville : un stade célèbre (Roudourou, St Symphorien), un festival connu (Porto Latino, Fête des Fifres), un monument, un musée, une usine connue (Haribo), un site naturel (le Gros Bessillon), un club (SM Caen, FC Metz)
- à défaut d'indice, le sujet doit rendre la ville devinable par son originalité

Exemples d'excellents sujets (8+) :
- "À Guingamp, Roudourou s'offre une nouvelle toiture" : on masque Guingamp, l'indice Roudourou (stade de Guingamp) fait deviner
- "Un affaissement entraîne l'évacuation du festival Porto Latino à Bastia" : on masque Bastia, l'indice Porto Latino (festival de Bastia) fait deviner
- "Sixième semaine de grève chez Haribo à Marseille" : on masque Marseille, l'indice Haribo (usine à Marseille) fait deviner

Attribue 0 à tout article qui correspond à un de ces cas :
- aucun nom de ville ou de village dans le titre (impossible à masquer)
- sordide : meurtre, violences sexuelles, accident mortel, scandale intime, fait divers gratuit et glauque
- sans intérêt : brève, communiqué, conseils, pub déguisée, programme TV, résultats sportifs bruts, météo du jour, portrait sans angle
- guide ou reportage-balade : "Nos conseils pour visiter", "que faire à", "une journée à", carnet de route, balade découverte, visite touristique, spectacle, agenda culturel, sortie du week-end
- titre trop vague : pas d'angle, pas d'enjeu, pas d'indice

Augmente le score si :
+2 sujet qu'on a vraiment envie de lire (enjeu, surprise, contexte fort)
+2 l'indice du titre est reconnaissable et fait vraiment deviner la ville
+2 l'article concerne un lieu emblématique ou une histoire marquante
+2 tous les thèmes sont les bienvenus : sport, économie, faits divers, culture, société, insolite, nature

Vise un mélange de difficultés : des lieux faciles à deviner pour tout le monde ET des lieux pointus pour les connaisseurs.
Sois exigeant : les 8, 9 et 10 sont rares et réservés aux articles vraiment excellents.

Réponds uniquement avec un tableau JSON, un objet par article, dans l'ordre, sans explication :
[{"id": 0, "score": 5}, {"id": 1, "score": 0}, ...]"""

SYSTEME_EXTRACTION = """Tu es un assistant qui extrait le nom de la ville et le sujet depuis un titre d'article.

Pour chaque article numéroté fourni, extrais :
- "lieu" : le nom de la ville ou du village à masquer, composé de mots présents exactement dans le titre
- "type" : toujours "ville" (jamais un département ou une région)
- "sujet" : le thème principal de l'article, court et normalisé (minuscules, sans accents), ex. "tour de france", "incendie", "handball", "festival", "musee"

Règles :
- le "lieu" doit être la VILLE ou le VILLAGE principal de l'article, celui qu'on placera sur la carte
- PRÉFÈRE la ville citée (même dans un nom de club : "SM Caen" → "Caen", "FC Metz" → "Metz"), pas le stade, le festival ou le monument qui n'est qu'un indice
- exemple : "FC Metz : les ultras ... à St Symphorien" → lieu "Metz", pas "St Symphorien" (le stade)
- utilise le nom le plus complet présent dans le titre (ex. "Vaison-la-Romaine" plutôt que "Vaison")
- le lieu doit être composé de mots présents exactement dans le titre
- si plusieurs villes, prends la plus centrale
- si aucune ville dans le titre, renvoie "lieu" vide (jamais un département ou une région)
- ne pas inventer, ne pas donner de synonyme

Réponds uniquement avec un tableau JSON, un objet par article, sans explication :
[{"id": 12, "lieu": "Guingamp", "type": "ville", "sujet": "football"}, ...]"""


class SelectionIndisponible(Exception):
    pass


def _client():
    if not OPENAI_API_KEY:
        raise SelectionIndisponible("OPENAI_API_KEY non définie (voir backend/.env)")
    from openai import OpenAI

    return OpenAI(api_key=OPENAI_API_KEY)


def _complete(messages: list[dict]) -> str:
    reponse = _client().chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.2,
        messages=messages,
    )
    return reponse.choices[0].message.content or ""


def _extraire_json(texte: str) -> list:
    texte = texte.strip()
    if texte.startswith("```"):
        texte = re.sub(r"^```[a-z]*\s*", "", texte)
        texte = re.sub(r"\s*```$", "", texte)
    try:
        donnees = json.loads(texte)
    except json.JSONDecodeError:
        debut = texte.find("[")
        fin = texte.rfind("]")
        if debut == -1 or fin == -1 or fin < debut:
            raise SelectionIndisponible(f"JSON illisible : {texte[:200]}")
        donnees = json.loads(texte[debut : fin + 1])
    if isinstance(donnees, dict):
        for cle in ("articles", "resultats", "selection", "scores"):
            if cle in donnees:
                donnees = donnees[cle]
                break
    if not isinstance(donnees, list):
        raise SelectionIndisponible("Réponse OpenAI sans liste JSON")
    return donnees


def _lister(articles: list[dict]) -> str:
    return "\n".join(f"{i}. {a['titre']}" for i, a in enumerate(articles))


def noter_articles(articles: list[dict], date_str: str) -> dict[int, int]:
    """Retourne {id: score_fun} pour tous les articles."""
    message = (
        f"Voici les articles du {date_str}, numérotés de 0 à {len(articles) - 1} :\n"
        f"{_lister(articles)}\n\n"
        "Rends le tableau JSON des scores, un objet par article."
    )
    brut = _extraire_json(_complete(
        [
            {"role": "system", "content": SYSTEME_SCORE},
            {"role": "user", "content": message},
        ]
    ))
    scores: dict[int, int] = {}
    for item in brut:
        if not isinstance(item, dict):
            continue
        try:
            idx = int(item.get("id"))
            score = int(item.get("score"))
        except (TypeError, ValueError):
            continue
        if 0 <= idx < len(articles):
            scores[idx] = score
    return scores


def extraire_lieux(articles: list[dict], date_str: str, indices: list[int]) -> dict[int, dict]:
    """Retourne {id: {lieu, type}} pour les articles dont l'id est dans indices."""
    message = (
        f"Articles du {date_str} (numéros d'origine entre parenthèses) :\n"
        + "\n".join(
            f"{n}. ({i}) {a['titre']}" for n, (i, a) in enumerate(
                ((i, articles[i]) for i in indices)
            )
        )
        + "\n\nRends le tableau JSON, un objet par article, dans l'ordre."
    )
    brut = _extraire_json(_complete(
        [
            {"role": "system", "content": SYSTEME_EXTRACTION},
            {"role": "user", "content": message},
        ]
    ))
    resultats: dict[int, dict] = {}
    for n, item in enumerate(brut):
        if not isinstance(item, dict):
            continue
        if n >= len(indices):
            continue
        idx = indices[n]
        lieu = str(item.get("lieu", "")).strip()
        type_lieu = str(item.get("type", "")).strip().lower().replace("é", "e")
        if lieu:
            resultats[idx] = {"lieu": lieu, "type": type_lieu}
    return resultats
