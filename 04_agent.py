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

#1 Fausse base de donnÃ©es (simule l'ERP)
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

TICKETS = []

def create_ticket(
    client_id: str, description: str, urgence: str
) -> dict:
    if client_id not in CLIENTS:
        return {"erreur": f"Client {client_id} inconnu"}
    if urgence not in ("faible", "moyenne", "haute"):
        return {"erreur": f"Urgence invalide : {urgence}"}
    ticket = {
        "numÃ©ro": f"T{len(TICKETS) + 1:03d}",
        "client_id": client_id,
        "description": description,
        "urgence": urgence,
    }
    TICKETS.append(ticket)
    return ticket

OUTILS = {
    "get_client": get_client,
    "search_client": search_client,
    "get_interventions": get_interventions,
    "create_ticket": create_ticket,
}

# Outils qui modifient des donnÃ©es : confirmation humaine requise
OUTILS_ECRITURE = {"create_ticket"}

def confirmer(nom: str, args: dict) -> bool:
    print(f"\nATTENTION : l'agent veut exécuter {nom}")
    for cle, valeur in args.items():
        print(f" {cle} : {valeur}")
    choix = input("Confirmer ? (o/n) ")
    return choix.strip().lower() == "o"

# 3 La description des outils pour le modÃ¨le
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
            "passÃ©es d'un client",
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
            "name": "create_ticket",
            "description": "Crée un ticket "
            "d'intervention pour un client",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Ex : C001",
                    },
                    "description": {
                        "type": "string",
                        "description": "Le problème "
                        "signalé, en une phrase",
                    },
                    "urgence": {
                        "type": "string",
                        "enum": [
                            "faible",
                            "moyenne",
                            "haute",
                        ],
                    },
                },
                "required": [
                    "client_id",
                    "description",
                    "urgence",
                ],
            },
        },
    },
]

#4 La conversation de dÃ©part
messages = [
    {
        "role": "system",
        "content": "Tu es l'assistant du service "
        "client. Utilise les outils pour "
        "répondre. N'invente aucune donnÃ©e.",
    },
    {
        "role": "user",
        "content": "Le Syndicat des eaux du Thor "
        "signale un regard bouché rue de la Gare, "
        "c'est urgent. CrÃ©e un ticket.",
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

    # Pas d'outil demandÃ© : c'est la rÃ©ponse finale
    if not msg.tool_calls:
        print("\nRéponse finale :", msg.content)
        break

    # On garde la demande du modÃ¨le dans l'historique
    messages.append(msg.model_dump(exclude_none=True))

    # On execute chaque outil demandÃ©
    for appel in msg.tool_calls:
        nom = appel.function.name
        args = json.loads(appel.function.arguments)
        print(f"[tour {tour}] outil : {nom}({args})")

        if nom not in OUTILS:
            resultat = {"erreur": f"Outil {nom} inconnu"}
        elif nom in OUTILS_ECRITURE and not confirmer(nom, args):
            resultat = {"erreur": "L'utilisateur a refusé "
                        "cette action. Ne réessaie pas. "
                        "crée et demande s'il veut modifier "
                        "quelque chose."}
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

print("\nTickets en base :", TICKETS)
