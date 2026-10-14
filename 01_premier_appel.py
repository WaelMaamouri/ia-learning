import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(base_url=os.environ["BASE_URL"], api_key=os.environ["API_KEY"])

system = "Tu es un assistant qui résume des rapports d'intervention en 3 points courts."
rapport = """Intervention du 14/10 à Avignon, rue des Lices.
Le client signale une baisse de pression. Détection acoustique effectuée :
fuite localisée sur canalisation eau potable fonte DN100, à 1,20 m de profondeur.
Terrassement nécessaire. Urgence moyenne. Prévoir un collier de réparation."""

debut = time.time()
reponse = client.chat.completions.create(
    model=os.environ["MODEL"],
    messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": rapport},
    ],
)
duree = time.time() - debut

print(reponse.choices[0].message.content)
print("---")
print("Tokens :", reponse.usage)
print(f"Durée : {duree:.1f} s")
