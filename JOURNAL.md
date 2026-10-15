@'

# Journal d'apprentissage IA

## Jour 1 : premiers appels à un LLM par API

### Ce que j'ai fait

- Mis en place le projet : dépôt Git local, environnement virtuel Python, `openai` et `python-dotenv`, `.env` exclu du dépôt via `.gitignore`.
- Lancé Ollama en local (`ollama serve`) avec le modèle `qwen3.5:4b`.
- Premier appel avec le SDK OpenAI branché sur Ollama (API compatible OpenAI) : résumé d'un rapport d'intervention en 3 points.

### Ce que j'ai appris

- Un appel = une liste de `messages` : `system` (consignes) et `user` (demande).
- Le SDK OpenAI marche avec d'autres fournisseurs : on change seulement `base_url`, `api_key` et `model`. Le code reste le même, ce qui facilite le passage du local au cloud.
- `usage` indique les tokens en entrée et en sortie, c'est la base du calcul du coût.
- **Point clé** : 113 tokens en entrée, mais 1 539 en sortie pour un résumé d'environ 60 tokens. Les ~1 480 tokens restants sont le raisonnement caché du modèle (modèle « thinking »). Durée : 139 s.
  - En production, il faut choisir le modèle et le niveau de raisonnement selon la tâche. Une tâche simple (résumé, extraction) n'a pas besoin de raisonnement, qui coûte du temps et de l'argent.

### Problèmes rencontrés et solutions

- `ollama list` : « timed out waiting for server to start » → démarrer le serveur à la main avec `ollama serve` dans un terminal dédié.
- Fichier `.py` vide (taille 0) → créé directement depuis PowerShell avec un here-string `@' ... '@ | Set-Content`.
- Sous Windows PowerShell, `echo > fichier` écrit en UTF-16 → utiliser `Set-Content -Encoding utf8`.

### À retenir pour l'entretien

- « Je sais brancher une application sur plusieurs fournisseurs de LLM (local avec Ollama, cloud avec OpenAI ou Anthropic) et je surveille les tokens, le coût et la latence. »

'@ | Add-Content JOURNAL.md -Encoding utf8

## Jour 1 (suite) : streaming, raisonnement et hallucinations

### Ce que j'ai fait

- Script `02_streaming.py` : affichage de la réponse au fur et à mesure (`stream=True`).
- Désactivation du raisonnement du modèle avec `reasoning_effort="none"`.
- `temperature=0` pour des réponses plus stables.

### Résultats

|                  | Raisonnement activé | Raisonnement désactivé |
| ---------------- | ------------------- | ---------------------- |
| Tokens en sortie | 1 539               | 105                    |
| Durée totale     | 139 s               | 19,7 s                 |

### Ce que j'ai appris

- Le streaming n'accélère pas la génération, mais l'utilisateur voit le texte arriver tout de suite. C'est indispensable pour l'expérience utilisateur.
- Avec le streaming, l'objet `usage` n'arrive que dans le dernier chunk, et seulement si on le demande (`stream_options={"include_usage": True}`).
- Désactiver le raisonnement sur une tâche simple divise ici les tokens par 15 et le temps par 7, sans perte de qualité visible.
- **Hallucination** : le modèle a inventé une adresse (« 16 chemin de Saint-Henry » au lieu de « rue des Lices »), même avec `temperature=0`. Une température basse rend le modèle plus stable, pas plus exact.
  - En entreprise, il ne faut jamais envoyer directement une sortie d'IA dans un système (ERP, base, e-mail client) sans la contrôler.
  - Parades : prompt strict (« n'invente rien »), sorties structurées en JSON validées, contrôle des champs critiques par le code, et validation humaine si l'enjeu est important.

### Bug corrigé

- J'affichais `time.time()` (un timestamp, nombre de secondes depuis 1970) au lieu de `time.time() - debut` (une durée).

### À retenir pour l'entretien

- « Je mesure la latence et les tokens, j'adapte le niveau de raisonnement à la tâche, et je ne fais jamais confiance aveuglément à la sortie d'un LLM : je la valide avant toute action. »

## Jour 1 (suite) : sorties structurées

### Ce que j'ai fait

- Script `03_extraction.py` : extraction d'un
  rapport d'intervention en JSON, imposé par un
  schéma (`response_format` + `json_schema`).
- Schéma décrit avec Pydantic (`BaseModel`,
  `Literal`, `Optional`), puis validation de la
  réponse avec `model_validate_json`.
- Contrôle par le code : l'adresse extraite
  doit apparaître dans le rapport.

### Ce que j'ai appris

- Le schéma impose la FORME (champs, types,
  valeurs autorisées), pas le FOND (exactitude).
- Avec Ollama, les descriptions des champs ne
  sont pas envoyées au modèle : les tokens en
  entrée restaient à 155. Les consignes doivent
  aller dans le prompt système.
- Si une consigne ne change rien, vérifier
  d'abord qu'elle arrive bien au modèle
  (les tokens en entrée sont un bon indicateur).
- `default=None` rend un champ facultatif : le
  modèle peut l'omettre et Pydantic le remplit
  en silence. Sans valeur par défaut, la clé
  est obligatoire (valeur ou null) : le modèle
  doit prendre position.
  -> En PHP : `?string $a` contre `?string $a = null`.
- Un contrôle doit traiter 3 cas : absent,
  vérifié, inventé.
- Des exemples dans le prompt aident les petits
  modèles. Il faut les choisir différents des
  données testées pour ne pas souffler la réponse.

### Évolution du résultat

| Version           | adresse       | anomalie                           |
| ----------------- | ------------- | ---------------------------------- |
| Initiale          | absente       | baisse_de_pression                 |
| Champ obligatoire | Rue des Lices | baisse_de_pression                 |
| + prompt précis   | Rue des Lices | Fuite sur canalisation fonte DN100 |

### Problèmes rencontrés

- `List` non défini : utiliser `list[str]`
  (minuscule, intégré à Python).
- Résultat identique malgré mes modifications :
  le fichier n'était pas enregistré.
  Vérifier avec `Get-Content` / `Select-String`.

### À retenir pour l'entretien

- « Pour intégrer un LLM dans un ERP, j'impose
  un schéma JSON, je valide avec Pydantic, je
  rends les champs obligatoires et je contrôle
  les champs critiques par le code avant toute
  écriture en base. »

## Jour 2 : tool calling, mon premier agent

### Ce que j'ai fait

- Script `04_agent.py` : un agent qui répond à
  des questions sur des clients en appelant mes
  fonctions Python (fausse base type ERP).
- 3 outils : `get_client`, `get_interventions`,
  `search_client`.
- Boucle d'agent écrite à la main, sans
  framework, avec une limite de 5 tours.

### Comment marche un agent

1. J'envoie au modèle la question + la liste
   des outils (nom, description, paramètres).
2. Le modèle n'exécute rien : il renvoie des
   `tool_calls` (« appelle telle fonction avec
   tels arguments »).
3. MON code exécute la fonction, puis renvoie
   le résultat avec `role: "tool"` et le
   `tool_call_id` correspondant.
4. On recommence jusqu'à ce que le modèle
   réponde sans demander d'outil.

### Ce que j'ai observé

- Appels parallèles : pour « qui est C001 et
  combien d'interventions ? », il appelle les
  2 outils dans le même tour.
- Appels enchaînés : avec un nom de client, il
  appelle `search_client`, récupère l'id, puis
  appelle `get_interventions`.
- Client inconnu : il lit l'erreur renvoyée par
  l'outil et n'invente rien.
- Sans outil de recherche par nom, il demande
  l'id au lieu de le deviner. C'est fiable, mais
  peu pratique : la solution est d'ajouter un
  outil, pas de demander à l'utilisateur.
- Question hors sujet : il répond quand même.
  Pour un assistant métier, il faut limiter le
  périmètre dans le prompt système.

### Bonnes pratiques retenues

- La `description` d'un outil est un prompt :
  c'est elle qui fait choisir le bon outil.
- Toujours limiter le nombre de tours.
- Ne jamais exécuter un outil inconnu : le
  modèle peut demander n'importe quoi.
- Garder des noms cohérents entre les outils
  (`client_id` partout).
- Les outils d'écriture (ticket, e-mail) sont
  plus risqués : l'ordre des appels et la
  validation deviennent critiques.

### À retenir pour l'entretien

- « J'ai codé une boucle d'agent sans framework :
  je sais ce que font LangChain ou le SDK
  Agents, parce que je l'ai écrit moi-même.
  Le modèle propose, mon code exécute et
  contrôle. »
