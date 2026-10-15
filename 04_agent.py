import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    base_url=os.environ["BASE_URL"],
    api_key=os.environ["API_KEY"],
)
MODEL = os.environ["MODEL"]

#1 Fausse base de données (simule l'ERP)
CLIENTS = {
    "C001": {
        "nom": "Mairie d'Avignon",
        "ville": "Avignon",
    },
    "C002": {
        "nom": "Syndicat des eaux du Thor",
        "ville": "Le Thor",
    }
}

INTERVENTIONS = [
    {"client": "C001", "date": "02/09",
     "type": "fuite eau potable"},
    {"client": "C001", "date": "14/10",
     "type": "fuite eau potable"},
    {"client": "C002", "date": "20/09",
     "type": "inspection assainissement"},
]

#2 Les outils: de vraies fonctions Python
def get_client(client_id: str) -> dict:
    infos = CLIENTS.get(client_id)
    if infos is None:
        return {"erreur": f"Client {client_id} inconnu"}
    return infos

def search_client(nom: str) -> list:
    nom = nom.lower()
    return [
        {"id": client_id, **infos}
        for client_id, infos in CLIENTS.items()
        if nom in infos["nom"].lower()
    ]

def get_interventions(client_id: str) -> list:
    return [
        i for i in INTERVENTIONS
        if i["client"] == client_id
    ]

OUTILS = {
    "get_client": get_client,
    "search_client": search_client,
    "get_interventions": get_interventions,
}

# 3 La description des outils pour le modèle
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_client",
            "description": "Renvoie le nom et la "
            "ville d'un client à partir de son id",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Ex : C001",
                    },
                },
                "required": ["client_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_client",
            "description": "Cherche des clients par "
            "nom (recherche partielle) et renvoie "
            "leur id, nom et ville",
            "parameters": {
                "type": "object",
                "properties": {
                    "nom": {
                        "type": "string",
                        "description": "Ex : Avignon",
                    },
                },
                "required": ["nom"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_interventions",
            "description": "Liste les interventions "
            "passées d'un client",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Ex : C001",
                    },
                },
                "required": ["client_id"],
            },
        },
    },
]

#4 La conversation de départ
messages = [
    {
        "role": "system",
        "content": "Tu es l'assistant du service "
        "client. Utilise les outils pour "
        "répondre. N'invente aucune donnée.",
    },
    {
        "role": "user",
        "content": "Combien d'interventions pour "
        "le Syndicat des eaux du Thor?",
    },
]

#5 La boucle d'agent
for tour in range(5):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        temperature=0,
        reasoning_effort="none",
    )
    msg = response.choices[0].message
    
    # Pas d'outil demandé : c'est la réponse finale
    if not msg.tool_calls:
        print("\nRéponse finale :", msg.content)
        break
    
    # On garde la demande du modèle dans l'historique
    messages.append(msg.model_dump(exclude_none=True))
    
    # On execute chaque outil demandé
    for appel in msg.tool_calls:
        nom = appel.function.name
        args = json.loads(appel.function.arguments)
        print(f"[tour {tour}] outil : {nom}({args})")
        
        if nom not in OUTILS:
            resultat = {"erreur": f"Outil {nom} inconnu"}
        else:
            resultat = OUTILS[nom](**args)
        
        print(f"        résultat : {resultat}")
        
        messages.append({
            "role": "tool",
            "tool_call_id": appel.id,
            "content": json.dumps(
                resultat, ensure_ascii=False
            ),
        })
else:
    print("Arrêt : trop de tours")