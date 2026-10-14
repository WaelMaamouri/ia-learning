import os
from typing import Literal, Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

load_dotenv()
client =  OpenAI(base_url=os.environ["BASE_URL"], api_key=os.environ["API_KEY"])

Reseau = Literal[
    "eau_potable",
    "assainissement",
    "gaz",
    "telecom",
    "electiricite",
    "autre",
]

# 1. Le schéma : ce qu'on veut extraire
class Intervention(BaseModel):
    date: Optional[str] = Field(description="Date au format JJ/MM, null si absente")
    ville: Optional[str] = Field(description="Ville, null si absente")
    adresse: Optional[str] = Field(description="Rue copiée du rapport")
    type_reseau: Reseau
    anomalie: str = Field(description="Problème technique constaté "
        "(pas le symptôme), en phrase courte "
        "en français normal")
    profondeur_m: Optional[float] = Field(description="Profondeur en mètre, null si absente")
    urgence: Literal["faible", "moyenne", "haute"]
    terrassement: bool
    materiel: list[str] = Field(description="Matériel ) prévoir, liste vide si rien")

system =  """Tu extrais les infos d'un rapport
d'intervention.
Règles :
- Utilise UNIQUEMENT les infos du rapport.
- N'invente rien. Si une info est absente,
  mets null.
- adresse : la rue citée, copiée telle quelle
  (ex : "avenue Jean Jaurès").
- anomalie : le problème technique constaté,
  pas le symptôme, en phrase courte
  (ex : "Rupture de branchement PEHD").
- materiel : en français normal, sans "_".
- Réponds uniquement avec le JSON demandé."""

rapport = """Intervention du 14/10 à Avignon, Rue des Lices.
Le client signale une baisse de pression.
Détection acoustique effectuée : fuite localisée sur la canalisation eau potable fonte DN100.
à 1.20 m de profondeur. Terrassement nécessaire.
Urgence moyenne. Prévoir un collier de réparation."""

schema = Intervention.model_json_schema()

#2 L'appel : on impose le schéma JSON
response = client.chat.completions.create(
    model=os.environ["MODEL"],
    messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": rapport},
    ],
    temperature=0,
    reasoning_effort="none",
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "intervention",
            "schema": schema
        },
    },
)

contenu = response.choices[0].message.content
print("Réponse brute :", contenu)
print("---")

#3 La validation par Pydantic
try:
    inter = Intervention.model_validate_json(contenu)
except ValidationError as e:
    print("JSON invalide :", e)
    raise SystemExit(1)

print(inter.model_dump_json(indent=2))
print("---")

#4 Contrôle anti-hallucination sur l'adresse
adresse = inter.adresse
if adresse is None:
    print("Adresse non trouvée par le modèle.")
elif adresse.lower() in rapport.lower():
    print("Adresse vérifiée.")
else:
    print(f"ALERTE : « {adresse} » inventée !")

u = response.usage
print("Tokens entrée :", u.prompt_tokens)
print("Tokens sortie :", u.completion_tokens)