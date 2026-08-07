from __future__ import annotations

import json
import re

from .config import OPENAI_API_KEY, OPENAI_MODEL

SYSTEME = """Tu es un curateur pour un jeu mobile.

OBJECTIF :
Sélectionner les 5 articles les plus insolites et amusants.


CONDITION OBLIGATOIRE :
Le titre doit obligatoirement contenir un et un seul lieu identifiable (mais pas plusieurs) :
- une ville
OU
- un département


PHASE 1 — FILTRAGE


Exclure les articles si :
- aucun lieu n'est présent dans le titre
- le sujet est grave (meurtre, mort, disparition, catastrophe)
- le titre est banal (travaux, politique, météo)


PHASE 2 — SCORE FUN


+3 insolite ou absurde
+3 situation inattendue
+3 drogue ou alcool
+3 drôle
+3 fait divers surprenant
+3 titre sous forme de question
+3 lié à un délit


-5 tourisme ou descriptif
-5 sujet banal


PHASE 3 — EXTRACTION


Pour chaque article retenu :
1. Extrais la localisation principale (ville OU département)
2. Assure-toi qu'elle apparaît exactement dans le titre
3. Supprime les articles en doublon


PHASE 4 — SORTIE


Retourne uniquement :


[
 {
  "id": 12,
  "titre": "titre exact",
  "lieu": "mot exact présent dans le titre",
  "type": "ville" ou "departement" ou "région"
 }
]


RÈGLES :
- pas 2 fois le même lieu dans 2 articles différents
- localisation doit être un mot exact du titre
- ne pas inventer
- pas d'explication
- JSON uniquement"""


class SelectionIndisponible(Exception):
    pass


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
        for cle in ("articles", "resultats", "selection"):
            if cle in donnees:
                donnees = donnees[cle]
                break
    if not isinstance(donnees, list):
        raise SelectionIndisponible("Réponse OpenAI sans liste JSON")
    return donnees


def appeler_llm(articles: list[dict], date_str: str, exclus: set[int] | None = None) -> list[dict]:
    if not OPENAI_API_KEY:
        raise SelectionIndisponible("OPENAI_API_KEY non définie (voir backend/.env)")

    from openai import OpenAI

    exclus = exclus or set()
    indices = [i for i in range(len(articles)) if i not in exclus]
    fournis = [articles[i] for i in indices]
    if not fournis:
        return []

    lignes = "\n".join(f"{i}. {a['titre']}" for i, a in enumerate(fournis))
    message = (
        f"Voici les articles du {date_str}, numérotés de 0 à {len(fournis) - 1} :\n"
        f"{lignes}\n\n"
        'Réponds avec le tableau JSON demandé, le champ "id" étant le numéro de l\'article ci-dessus.'
    )

    client = OpenAI(api_key=OPENAI_API_KEY)
    reponse = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.4,
        messages=[
            {"role": "system", "content": SYSTEME},
            {"role": "user", "content": message},
        ],
    )
    contenu = reponse.choices[0].message.content or ""
    brut = _extraire_json(contenu)

    resultats = []
    for item in brut:
        if not isinstance(item, dict):
            continue
        try:
            idx = int(item.get("id"))
        except (TypeError, ValueError):
            continue
        if not (0 <= idx < len(fournis)):
            continue
        original = indices[idx]
        resultats.append(
            {
                "id": original,
                "titre": fournis[idx]["titre"],
                "lieu": str(item.get("lieu", "")).strip(),
                "type": str(item.get("type", "")).strip().lower().replace("é", "e"),
            }
        )
    return resultats
