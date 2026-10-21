---
name: pre-push
description: Déroule la checklist avant de pousser une branche GardenIQ PiPico (rebase sur la cible, contraintes MicroPython et protocole, documentation, backlog, lint et typage, tests, hygiène des commits) et rend un bilan point par point, sans pousser. Utiliser quand l'utilisateur demande "pre-push", "je peux pousser ?", "checklist avant push", "prépare le push", "vérifie avant de pousser" ou avant `pr-create`.
---

# pre-push

Déroule la checklist « avant de pousser » et en fait un bilan honnête. C'est une **porte de contrôle** : elle diagnostique, propose des corrections, mais **ne pousse jamais** (le push et la PR se font à la demande, via `pr-create`).

Règle générale : tout ce qui réécrit l'historique (rebase) ou modifie du code est **proposé puis confirmé**, jamais fait en silence. Un point non vérifié est marqué « non vérifié », jamais « OK ».

## Procédé

### 0. Contexte

```bash
git branch --show-current
git fetch origin
git status --short
```

- Arrêter sur `main` ou sur une branche qui ne suit pas `(TK-<id>)(<type>)-<slug>`.
- Arbre de travail non propre : le signaler (les vérifications portent sur les commits, mais tests et lint s'exécutent sur l'arbre).
- **Branche cible** : celle de la PR si elle existe (`gh pr view --json baseRefName -q .baseRefName`), sinon `main`. Pour une PR **empilée** (cible différente de `main`), toutes les comparaisons ci-dessous se font contre cette branche. Dans la suite : `<cible>`.
- Commits concernés : `git log origin/<cible>..HEAD --oneline`. Aucun commit : rien à pousser, le dire.

### 1. Rebase sur la cible

```bash
git rev-list --count HEAD..origin/<cible>
```

0 : à jour. Sinon `<cible>` a avancé : proposer `git rebase origin/<cible>`.
- **Branche jamais poussée** : le rebase est sans conséquence, le faire après confirmation.
- **Branche déjà poussée** : un rebase obligerait à forcer le push (`git push --force` est refusé par `settings.json`). Ne pas rebaser seul : expliquer et laisser l'utilisateur décider.

Faire cette étape **en premier** : elle change ce que les suivantes vérifient.

### 2. Contraintes MicroPython et protocole

Lire le code **ajouté ou modifié** dans `src/` (`git diff origin/<cible>...HEAD -- src main.py`) avec `.claude/rules/src.md`. Signaler, avec fichier et ligne :

- un `print()` ou une trace sur stdout : `sys.stdout` est le canal du protocole USB, une trace corrompt les trames (❌) ;
- un import de module absent ou partiel sous MicroPython (`enum`, `dataclasses`, `logging`, `threading`, `abc`…), un `match/case`, une syntaxe récente à vérifier (⚠️) ;
- un nouveau module matériel (`machine`, `rp2`, `utime`…) sans mock dans `tests/mocks/` ni enregistrement dans `conftest.py` (❌) ;
- une structure qui grandit sans borne (file sans `maxsize`, registre sans limite), une boucle sans `await` ni délai, une attente sans délai maximal (⚠️) ;
- une entrée USB utilisée avant validation (format, bornes, broche, canal) ou avant le contrôle du checksum (❌) ;
- une tâche `asyncio` dont une exception peut sortir de la boucle (⚠️) ;
- un actionneur ajouté sans état sûr à l'initialisation ni à l'erreur (⚠️) ;
- une dépendance ajoutée au `Pipfile` : le firmware n'a aucune dépendance runtime, un ajout est à discuter (⚠️).

**Protocole** : si `protocols/usb/frame.py`, `protocols/usb/parsers/`, `protocols/errors.py` ou `core/utils.py` (`format_error`) changent, le format, les types de trame, les codes d'erreur ou le checksum sont un contrat avec `gardenIQ-back` : marquer ⚠️ « changement de contrat » et demander à l'utilisateur si le backend a la même modification, dans quelle PR, et si `src/__version__.py` doit changer. Un test qui fige le comportement doit exister.

Aucun changement dans `src/` : « non concerné ».

### 3. Documentation

Si le **comportement** change (nouvelle feature, nouvelle commande ou trame, procédure d'exploitation), la fiche de référence `docs/features/` ou `docs/runbooks/` doit être créée ou mise à jour : proposer le skill `write-doc` (ces dossiers n'existent pas encore : le dire). Si la branche change une règle ou une commande décrite dans `CLAUDE.md` ou `.claude/rules/`, vérifier que ces fichiers restent justes. Pur refactor ou changement sans effet visible : « non concerné ».

### 4. Backlog

`docs/backlog.md` est local (absent d'un clone neuf). Le lire et vérifier chaque entrée dont le statut n'est pas `Traité` (règle de `CLAUDE.md`, section « Backlog ») : la branche en règle-t-elle une ? Si oui, proposer de la passer à `Traité` (date, PR ou commit) ; ne pas modifier sans accord. Les problèmes repérés dans la branche hors de son périmètre s'y notent, sans doublon. Fichier absent : « non vérifié ».

### 5. Lint et typage

```bash
black --check .
isort --check-only --diff .
flake8 .
```

(les mêmes contrôles que la CI). Corriger ce qui relève de la branche, avec `black .` ou `isort .` si besoin, sans reformater de fichier sans rapport. `pre-commit run --all-files` rejoue en plus les contrôles de fin de fichier et d'espaces. Les commandes se lancent dans `pipenv shell` ou avec `pipenv run`.

**Typage** : aucun outil ne le vérifie (voir « Typage » dans `CLAUDE.md`). Lire le code ajouté ou modifié dans `src/` : une fonction ou méthode sans paramètres ou retour typés, un nouveau `typing.Dict/List/Optional/Union`, un `# pyright: ignore` sans règle précise, un usage inhabituel de `typing` (génériques, `Protocol`, `TYPE_CHECKING`…) sont à signaler (⚠️, non bloquant). Les tests sont exclus.

### 6. Tests

Faire cette étape **en dernier** pour tester l'état final (après rebase).

```bash
pytest
```

Suite complète en local. Pour un périmètre réduit : `pytest -- tests/<dossier>` ; l'écrire dans le bilan. Échec : donner le test et l'erreur, ne pas conclure sans les avoir lus (un test instable se relance, un échec reproductible est à traiter). Les tests tournent sous CPython avec les mocks MicroPython : un test vert ne prouve pas que le code fonctionne sur la carte, et le bilan ne le dit jamais.

### 7. Hygiène des commits

```bash
git log origin/<cible>..HEAD --format='%h %s'
git diff --name-only origin/<cible>...HEAD
```

- Chaque titre suit `(TK-<id>)(<type>) - <module>: <Description>`, en anglais, avec le ticket de la branche ajouté par le hook local. Le type est celui de la branche, ou un type explicite valide (par exemple `docs` pour de la documentation). Un préfixe absent, doublé ou avec un autre ticket indique un hook inactif ou ancien : le signaler.
- Pas de commit `fixup`, `WIP`, ni de fichier personnel ou sensible dans le diff : `.env`, `docs/backlog.md`, `CLAUDE.local.md`, `.claude/settings.local.json`, secret.
- Les commits sont conservés sur la branche et **squashés au merge de la PR** : le titre de la PR devient le message sur `main`. Ne pas les squasher avant.

### 8. Bilan

Un tableau, dans le chat, en français :

| Point | Statut | Détail |
|---|---|---|
| Rebase sur `<cible>` | ✅ / ⚠️ / ❌ / ➖ non concerné / ⏭️ non vérifié | … |
| MicroPython et protocole | | |
| Documentation | | |
| Backlog | | |
| Lint | | |
| Typage | | |
| Tests | | commande, nombre de tests, périmètre |
| Commits | | |

Terminer par un verdict : **prêt à pousser**, **à corriger avant** (liste des ❌) ou **non vérifié** pour ce qui n'a pas pu être contrôlé. Les fichiers produits par les étapes (doc) se commitent avec le skill `commit`, un commit par changement logique. Puis, à la demande de l'utilisateur seulement : push et `pr-create`.

## À éviter

- Pousser, ou forcer un push, depuis ce skill.
- Rebaser une branche déjà poussée sans l'accord explicite de l'utilisateur.
- Annoncer « tests OK » sans les avoir lancés, ou sur un périmètre réduit sans le dire, ou « fonctionne sur la carte » à partir des tests.
- Annoncer « typage vérifié » : il n'y a pas de vérificateur automatique.
- Décider seul d'un changement de protocole ou de version du firmware.
- Embarquer dans la branche des changements sans rapport avec elle.
- Contourner les hooks (`--no-verify`).
