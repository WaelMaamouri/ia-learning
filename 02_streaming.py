import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(base_url=os.environ["BASE_URL"], api_key=os.environ["API_KEY"])

system = "Tu es un assistant qui résume des rapports d'intervention en 3 points courts."
rapport = """Intervention du 14/10 à Avignon, 16 chemin de saint henry.
Le client signale une fuite d'eau. Détection acoustique effectuée :
fuite localisée sur canalisation eau potable fonte DN100, à 1,20 m de profondeur.
Terrassement nécessaire. Urgence moyenne. Prévoir un collier de réparation."""


debut = time.time()
premier_token = None

stream = client.chat.completions.create(
    model=os.environ["MODEL"],
    messages=[
        {"role" : "system", "content": system},
        {"role" : "user", "content": rapport},
    ],
    temperature=0,
    reasoning_effort="none",  # essai : désactiver le raisonnement
    stream=True,
    stream_options={"include_usage": True}
)   

for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        if premier_token is None:
            premier_token = time.time()
        print(chunk.choices[0].delta.content, end="", flush=True)
    if chunk.usage:
        usage = chunk.usage
print("\n---")
print("Tokens sortie :", usage.completion_tokens)
print(f"Prmeier mot après {premier_token:.1f} s")
print(f"Durée totale : {time.time() - debut:.1f} s")