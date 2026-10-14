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
