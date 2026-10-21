# GardenIQ PiPico

Firmware MicroPython du Raspberry Pi Pico pour GardenIQ. Le Pico est piloté par le backend Django (dépôt `gardenIQ-back`) via un protocole de trames sur USB : il reçoit des ordres, les exécute sur ses broches (numérique, PWM, analogique) et répond par un ACK.

Le code de `src/` est du Python typé, compilé en `.mpy` puis téléversé sur la carte, où il tourne sous MicroPython. Les tests tournent sous CPython 3.13.5 sur les sources, avec des mocks des modules MicroPython. Aucune dépendance runtime : le `Pipfile` ne contient que des `dev-packages`.

## Commandes

Tout passe par l'environnement pipenv : soit dans `pipenv shell`, soit en préfixant chaque commande par `pipenv run` (les deux sont acceptés ; les commandes ci-dessous sont écrites sans préfixe).

| Besoin | Commande |
|---|---|
| Lint (écrit les corrections) | `black .` `isort .` `flake8 .` |
| Lint comme la CI (sans écrire) | `black --check .` `isort --check-only --diff .` `flake8 .` |
| Tous les hooks pre-commit | `pre-commit run --all-files` |
| Tests | `pytest` |
| Tests plus rapides | `-x` (stoppe au premier échec), `-n auto` (pytest-xdist) |
| Un test précis | `pytest -- tests/<dossier>/<fichier>.py::<Classe>::<test>` |
| Couverture (comme la CI) | `pytest --cov=. --cov-report=term-missing` |
| Mettre à jour les dépendances | `pipenv run update_dep` (régénère `Pipfile.lock` et `requirements_dev.txt`, utilisé par la CI) |
| Envoyer sur la carte | extension VS Code MicroPico (`.micropico`, réglages dans `.vscode/settings.json`) |

Il n'y a pas de commande pour lancer le firmware hors carte : `main.py` est un point d'entrée de test manuel (`usb.setup()` puis `usb.process()`) à exécuter sur le Pico.

## Architecture

Structure de `src/` et sens des imports (chaque couche n'importe que les précédentes) :

`core` ← `datasheet` ← `models` ← `stores` ← `channelsrunner` ← `protocols`

- `core` : briques sans dépendance (`Queue`, `EventEmitter`, `PseudoEnum`, `DEVICE_UID`, utilitaires). N'importe rien d'autre de `src`.
- `datasheet` : broches et canaux du Pico (n'importe que `core`).
- `models` : `Pin`, `Order`, `ModelType` (importent `core` et `datasheet`).
- `stores` : registres en mémoire des commandes (`commands_store`) et des broches (`init_pins_store`).
- `channelsrunner` : exécute un `Order` sur une broche selon son canal (`digit`, `pwm`, `analog`) via `channel_handler`.
- `protocols/usb` : trames (`frame.py`), parseurs, `FrameHandler` (`handler.py`), callbacks, workflow asyncio. Point d'entrée : `usb.setup()` et `usb.process()`.

Règles :

- Jamais de cycle d'import ni d'import « vers le haut » (ex. `models` n'importe pas `stores`). Exception : les tests.
- Un module n'importe pas son module parent (`ban-relative-imports = parents`), seulement ses frères (`from .frame import Frame`) ; tout le reste en absolu `src.<package>...`. Un import par ligne (isort `force_single_line`).
- Les singletons se créent en fin de module (`frame_handler`, `commands_store`, `channel_handler`, `event_emitter`) et s'importent tels quels.
- Les erreurs du protocole utilisent `CommandError` (`protocols/errors.py`) et `format_error` (`core/utils.py`) : le Pico répond par une trame `ACK` en état `ERR`, il ne plante pas.
- Style : black, isort, flake8 à 120 colonnes (`pyproject.toml`, `setup.cfg`).

## Contraintes MicroPython

Le détail (bibliothèques, mémoire, performance, canal USB, sécurité, robustesse, matériel) est dans `.claude/rules/src.md`, chargée en travaillant sur `src/`. L'essentiel :

- Le code de `src/` est écrit **typé et avec `typing`** : en développement cela sert les linters, les hooks et la lecture du code. `typing` n'existe pas sur MicroPython : le code est nettoyé (imports `typing`, annotations…), minifié puis compilé en `.mpy` avant d'être téléversé, donc `src/` n'est pas exécutable tel quel sur le Pico. Ce traitement ne se fait pas dans ce dépôt.
  - Écrire normalement du code typé ; ne pas retirer le typage ni les imports `typing` « pour MicroPython ».
  - En cas de construction de typage inhabituelle (génériques, `TypeVar`, `Protocol`, `TYPE_CHECKING`…), la signaler à l'utilisateur.
  - Ne pas annoncer « fonctionne sur la carte » sans l'avoir testé sur la carte.
- Pas de bibliothèque standard complète (`enum`, `dataclasses`, `match/case`…) : d'où `PseudoEnum`, `FrozenDataclass` et le retrait de `match/case` (TK-68). Ne pas introduire de module CPython-only sans vérifier qu'il existe sur la carte.
- Pas de `print()` dans `src/` : `sys.stdout` est le canal du protocole USB.
- Les modules matériels (`machine`, `ubinascii`, `sys`) sont absents de CPython : les tests utilisent `tests/mocks/` (installés par `conftest.py`) ; tout nouveau module matériel demande son mock.
- Le protocole de trames (format `< TYPE device_uid command_id … > checksum`, checksum Fletcher8 ; page Notion « USB ») est un contrat avec le backend : toute modification de `protocols/usb/frame.py` ou des parseurs doit rester compatible avec `gardenIQ-back`. Le dire à l'utilisateur au lieu de décider seul.
- `src/__version__.py` porte la version du firmware, renvoyée au backend dans la réponse au ping.

## Typage

Typer au maximum, pour la lisibilité et l'aide de l'éditeur :

- Toute fonction ou méthode écrite ou modifiée a ses paramètres et son retour typés, y compris `-> None`. Typer aussi les attributs de classe et les variables dont le type n'est pas évident.
- Syntaxe moderne (Python 3.13) : `list[str]`, `dict[str, int]`, `X | None`. Les annotations de signature ne sont pas évaluées par MicroPython. Ne pas ajouter de `typing.Dict`, `List`, `Optional`, `Union` ; ceux déjà présents ne sont pas migrés sans demande (diff minimal).
- `typing` reste permis (`Callable`, `Generic`, `TypeVar`…) quand le type natif ne suffit pas : il est retiré avant compilation (voir « Contraintes MicroPython »).
- `Any` en dernier recours. Pour une exception au vérificateur, `# pyright: ignore[<règle>]` avec la règle précise, jamais un `ignore` nu.
- Pas de vérificateur de types en CI ni dans les hooks : seul Pylance (VS Code, mode `basic`, stubs MicroPython `~/.micropico-stubs`) signale les erreurs. Ne pas annoncer « typage vérifié » sans l'avoir contrôlé.
- Tests exclus. Pas de campagne de typage sur du code non touché, sauf demande.

## Tests

pytest, pytest-asyncio (`asyncio_mode = "auto"`), pytest-mock, pytest-xdist. Pas de `pytest.ini`, pas de timeout, pas de marker `slow`.

- Les tests reflètent `src/` : `tests/tests_<package>/test_<objet>.py` (`tests_core`, `tests_models`, `tests_channelsrunner`, `tests_protocols/tests_usb/...`), plus `tests/test_versions.py`. Un fichier de test porte le nom de l'objet testé.
- Structure : une docstring d'une ligne, puis les commentaires `# GIVEN`, `# WHEN`, `# THEN` ; tests groupés en classes par objet (`TestQueueInit`).
- Mocks : `pytest-mock` (`mocker.patch`) et `monkeypatch`. Jamais de port USB ni de broche réels.
- Skill : `write-test`.

## Git et GitHub

- Flux : GitHub Flow, branches courtes depuis `main`, une PR par branche (dépôt `riderflo85/gardenIQ-PiPico`).
- Branche : `(TK-<id>)(<type>)-<slug>` (ex. `(TK-61)(feat)-Optimise-remove-and-add-models`). `TK` = « Ticket » : `<id>` est le numéro de la carte du kanban Notion.
- Commit : `(TK-<id>)(<type>) - <module>: <Description>`, **en anglais**, un commit par changement logique.
  - Exemple : `(TK-41)(feat) - protocols: Add frame protocol unit tests`.
  - Le hook local `.git/hooks/prepare-commit-msg` (non versionné) ajoute tout seul le préfixe `(TK-<id>)(<type>) - ` à partir du nom de la branche : n'écrire que `<module>: <Description>`. Pour un commit d'un autre type que la branche, écrire `(<type>) - <module>: <Description>` : le hook garde ce type et met le ticket de la branche.
  - Types : `feat`, `fix`, `enh`, `refactor`, `test`, `docs`, `chore`. L'historique contient d'anciennes variantes (`feature`, `bugfix`, `tk 60`) : ne pas les reprendre. Le type `docs` sert aux commits de documentation (`README.md`, `CLAUDE.md`, règles et skills) dans une branche `feat`, `fix` ou `enh`.
  - Modules : le package concerné (`core`, `datasheet`, `models`, `stores`, `channelsrunner`, `protocols`) ou `tests`, `ci`, `deps`, `hooks`, `claude`, `settings` hors `src/`. Si un nouveau package est ajouté dans `src/`, l'ajouter à cette liste.
- Squash au merge de la PR : le titre de la PR devient le message sur `main`, avec le suffixe ` (#<n>)` ajouté par GitHub. Rebaser sur `main` avant de pousser.

Hooks : `.git/hooks/pre-commit` est le framework `pre-commit` (`pre-commit install`) : il lance black, flake8, isort, check-json, end-of-file-fixer et trailing-whitespace sur les fichiers indexés. Ne jamais contourner avec `--no-verify`.
CI (GitHub Actions, à chaque push et pull request) : `black --check .`, `isort --check-only --diff .`, `flake8 .`, `pytest --cov`.

## Garde-fous

- Confirmation avant **chaque** commit (une approbation = un seul commit) et avant tout merge de PR.
- Aucune mention de Claude ni d'une IA dans les commits (pas de `Co-Authored-By`), les descriptions de PR et tout texte publié sur GitHub ou Notion.
- Lire un fichier avant de le modifier ; diff minimal, sans refactor non demandé.
- Pour un bug : proposer la cause racine et le correctif **avant** de modifier le code.

## Notion (kanban des tickets)

Les tickets vivent dans le kanban Notion, accessible par le serveur MCP `notion` (espace « GardenerIQ », compte « Garden » : toute écriture apparaît sous ce compte). Le kanban est commun à tous les dépôts GardenIQ. Les outils `mcp__notion__*` sont chargés à la demande : `ToolSearch` avec `select:<nom>` avant le premier appel. Skills : `ticket` (lire et traiter un ticket, tenir son statut à jour) et `ticket-create` (créer des tickets à partir de `docs/backlog.md`).

- **Base** : « Tableau kanban », `collection://28f54287-aae0-81ff-b3d7-000b26a0535c`. Propriétés : `Nom`, `Id carte` (`TK-<n>`, automatique, lecture seule), `Statut`, `Priorité`, `Tags`, `Équipe`, `Assigné à`, `Nom de la branche GitHub`, `Pull Requests GitHub`.
- **Statuts** et lien avec Git : `À faire` → `En développement` (branche créée) → `Code review & test` (PR ouverte) → `À merge` (PR relue) → `Fait` (PR fusionnée sur `main`). L'intégration GitHub de Notion relie la PR au ticket et le passe à `Code review & test` toute seule après l'ouverture de la PR : relire le ticket avant d'écrire un statut, n'écrire que si l'intégration ne l'a pas fait.
- **Tags** : type `feature`, `bug`, `enhancement` (soit `feat`, `fix`, `enh` pour la branche) et périmètre `back`, `front`, `software`. Ce dépôt est `software` (le logiciel compilé puis téléversé sur le hardware, le Raspberry Pi Pico). Pas de tag pour `refactor`, `test`, `docs`, `chore` : demander.
- **Contenu d'un ticket** : le modèle « Template User Story » (carte `TK-39`) : user story, critères d'acceptation en cases à cocher, conditions techniques, dépendances, tâches, tests.
- **Lecture** : `notion-query-data-sources` en mode `rows` (le SQL a un quota sur ce plan), `notion-search` pour chercher par mots-clés (la recherche IA n'est pas disponible). La base des pull requests liées est synchronisée depuis GitHub et le MCP ne peut pas la lire directement.
- **Écriture** : le kanban est partagé avec l'équipe, donc **confirmation avant toute création ou modification** (une demande explicite de l'utilisateur dans le message vaut confirmation). Jamais d'écriture dans `Id carte` ni dans la relation `Pull Requests GitHub`. Pas de suppression de page ni de changement de schéma (refusés dans `.claude/settings.json`) : ajouter un tag ou un statut se fait dans Notion.
- **Ticket de la branche** : le `<id>` de `(TK-<id>)…` est l'`Id carte` du ticket. Pour lire un ticket par son numéro, voir le skill `ticket`.

## Backlog

Tout bug, problème d'architecture ou remarque repéré en passant et **hors du périmètre demandé** se note dans `docs/backlog.md` au lieu d'être corrigé. Ce fichier sert à créer les tickets dans le kanban Notion (skill `ticket-create`). Il est local : ignoré par git (`.gitignore`), donc absent d'un clone neuf.

- Une entrée par sujet, au format du fichier : titre, type (`bug`, `architecture`, `remarque`), user story (« En tant que … je veux … afin de … »), description, critères d'acceptation, fichiers.
- Vérifier le constat avant de l'écrire (lire le code, lancer un test) et dire ce qui n'a pas été reproduit.
- Chercher d'abord si le sujet existe déjà ; ne pas créer de doublon.
- Ne pas corriger sans demande : l'ajout au backlog ne remplace pas la décision de l'utilisateur.
- **Relire régulièrement** `docs/backlog.md` (au moins avant de créer une PR, au début d'un travail sur un sujet proche, et quand l'utilisateur le demande) et vérifier chaque entrée dont le statut n'est pas `Traité` : relire les fichiers cités, rejouer la vérification décrite, regarder si une PR ou un commit récent l'a réglée. Si le problème est résolu, passer le statut à `Traité` avec la date et la PR ou le commit ; si le constat a changé, mettre l'entrée à jour ; si elle est devenue sans objet, le dire à l'utilisateur. Ne jamais supprimer une entrée. Pour une entrée qui a un ticket, le statut se lit dans Notion (skill `ticket-create sync`) : un ticket `Fait` ne suffit pas à clore l'entrée, la vérification dans le code reste obligatoire. Le numéro `TK-<id>` s'écrit dans l'entrée à la création du ticket (statut `Ticket créé`) ; ne jamais le deviner.

## Documentation

La documentation de référence (features, protocole USB, runbooks) vivra dans `docs/features/` et `docs/runbooks/` (Markdown, diagrammes Mermaid) ; ces dossiers n'existent pas encore. Skill : `write-doc`.

## Faire évoluer ce fichier

Chaque piège rencontré devient une ligne ici, courte et précise. Préférences personnelles : `CLAUDE.local.md` (non versionné).
