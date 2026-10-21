---
name: write-test
description: Écrit des tests pytest pour le firmware GardenIQ PiPico en respectant les conventions du dépôt (GIVEN/WHEN/THEN, classes par objet, fixtures de fichier, mocks MicroPython, mocker), les exécute et rend compte de ce qui est couvert ou non. Utiliser quand l'utilisateur demande "écris les tests de X", "ajoute des tests", "teste ce modèle / ce handler / cette trame / ce parseur", "write-test", "couvre ce changement par des tests" ou "reproduis ce bug par un test".
---

# write-test

Écrit des tests qui ressemblent à ceux du dépôt : même structure, mêmes fixtures, mêmes mocks. Les conventions de base sont dans `.claude/rules/tests.md` et les contraintes du code dans `.claude/rules/src.md` : les **lire** avant d'écrire, ne pas les recopier ici ni les contourner.

Ce skill écrit des tests ; il **ne modifie pas le code testé**. Si un test révèle un bug, le rapporter (voir « Restituer »).

## Procédé

### 0. Cibler ce qu'on teste

Dans l'ordre :
- l'objet ou le comportement nommé par l'utilisateur (« la file », « le parseur de pins », « la réponse au ping ») ;
- sinon le changement de la branche : `git diff $(git merge-base origin/main HEAD)...HEAD -- src`, en ne gardant que le code qui porte du comportement.

Lire le code testé **en entier**, pas seulement les hunks : branches, cas d'erreur, valeurs limites, effets de bord (envoi d'un événement, écriture dans un registre, appel matériel).

### 1. Lire l'existant avant d'écrire

- Les tests voisins de l'objet : `tests/tests_<package>/`. **Ne pas dupliquer** un test qui existe déjà : l'étendre ou le compléter.
- Modèles à suivre :
  - une classe pure, avec cas limites et exceptions : `tests/tests_core/test_queue.py` (classes `TestQueueInit`…, bandeaux, coroutines) ;
  - un objet qui construit du matériel (`Pin`, `PWM`, `ADC`) : `tests/tests_models/test_pin.py` ;
  - un handler ou un workflow avec événements et files : `tests/tests_protocols/tests_usb/test_workflows.py`, `test_callbacks.py` (`mocker.patch`, `AsyncMock`) ;
  - un scénario complet, de la trame brute à la réponse : `tests/tests_protocols/tests_usb/tests_handlers/test_ping_frame.py` et `test_lg_init_frame.py` (fonction d'aide qui calcule le checksum) ;
  - un parseur : `tests/tests_protocols/tests_usb/tests_parsers/` ;
  - une dépendance à `sys.version` ou à l'environnement : `tests/test_versions.py` (`monkeypatch`).
- Les mocks existants : `tests/mocks/machine.py` (`unique_id`, `Pin`, `PWM`, `ADC`), `ubinascii.py`, `sys.py` (stdin et stdout factices). Les réutiliser avant d'en créer. Il n'y a ni factories ni fixtures partagées dans `conftest.py`.

### 2. Choisir quoi couvrir

Un test par comportement observable, pas par ligne de code. Selon la cible :

- **Modèle** (`Pin`, `Order`) : construction, valeurs par défaut, conversions (`fields_cfg`), configuration initiale vidée après l'initialisation, erreurs attendues avec `pytest.raises` (broche inconnue, canal incompatible, valeur hors plage).
- **Store** (`commands_store`, `init_pins_store`) : ajout, lecture, clé absente (`KeyError`), doublon, état remis à zéro entre les tests.
- **Channelsrunner** : un ordre `get` ou `set` par canal (`digit`, `pwm`, `analog`), avec le mock de `machine` ; valeurs limites (0, maximum, hors bornes).
- **Trame et parseur** : trame valide, trame trop courte, délimiteurs absents (`<`, `>`), type inconnu, checksum faux ou absent, UID d'un autre device, `UKW_DEV_UID`, espaces et retour à la ligne. Construire les trames avec une fonction d'aide qui calcule le vrai checksum (`Frame.build_checksum`), pas avec une valeur en dur.
- **Handler et callbacks** : chaque type d'ordre (ping, `LG_INIT`, commande), la réponse `ACK` en état `OK` et en état `ERR` (`CommandError`, `format_error`), le fait qu'une exception ne quitte pas la tâche. Les événements (`order:received`, `order:process`, `response:ready`, `error:occurred`) se vérifient avec un `emit` simulé (`mocker.AsyncMock`).
- **Files et événements** (`Queue`, `EventEmitter`) : file vide, pleine (`QueueFull`, `QueueEmpty`), `maxsize`, `join` et `task_done`, événement inconnu (`UnknownEventError`), désinscription.
- **Protocole = contrat avec le backend** : tout comportement visible du backend (format d'une trame de réponse, code d'erreur, checksum) a un test qui le fige. Si un test fige un comportement douteux (voir `docs/backlog.md`, par exemple le checksum), le dire dans le test et dans le compte rendu, sans le corriger ici.
- **Matériel et USB réels** : jamais. `sys.stdin` et `sys.stdout` sont des mocks ; pour un flux, `mocker.patch` sur le `StreamReader`.
- **Ce qu'un test CPython ne prouve pas** : la compatibilité MicroPython (syntaxe, bibliothèque, mémoire, temps réel). Ne pas écrire de test qui prétend le vérifier ; le noter dans le compte rendu.

Cas limites à chercher dans le code lu à l'étape 0 : valeur absente ou `None`, chaîne vide, liste vide, doublon, borne exacte, entrée mal formée ou malveillante (caractères spéciaux, très longue), file saturée.

### 3. Écrire

Conventions (détail dans `tests.md`) :
- fichier à l'emplacement de l'étape 1, dans un fichier existant s'il y en a un pour l'objet, avec son `__init__.py` dans un nouveau dossier ;
- une docstring d'une ligne, puis **`# GIVEN` / `# WHEN` / `# THEN`** dans chaque test ;
- classes groupées par objet ou comportement, bandeaux `# ----` pour séparer helpers, fixtures et tests dans un fichier long ;
- données par fixtures `@pytest.fixture` du fichier ; `autouse=True` seulement pour remettre à zéro un état global ;
- coroutines : `@pytest.mark.asyncio`, `mocker.AsyncMock()` pour les coroutines simulées ;
- `mocker.patch("src.<chemin>.<nom>")` en visant l'endroit où le nom est **utilisé** ; `monkeypatch` pour un attribut ou l'environnement ; pas d'`unittest.mock` direct ;
- imports en une ligne par nom (`from x import A` / `from x import B`), comme dans tout le dépôt : isort et flake8 tranchent ;
- pas d'ordre d'exécution implicite : un test ne dépend ni d'un autre ni de l'ordre des fichiers ;
- il n'y a ni timeout par test ni marker `slow` : un test lent est un problème à signaler, pas à masquer.

Ne pas modifier `conftest.py` ni `tests/mocks/` sans le dire : l'impact dépasse le test en cours (ajouter une méthode à un mock pour un nouveau module matériel est normal, mais à mentionner). Les tests sont dispensés de typage (voir « Typage » dans `CLAUDE.md`).

### 4. Exécuter

```bash
pytest -- tests/<dossier>/<fichier>.py::<Classe>::<test>
```

Dans `pipenv shell` ou avec `pipenv run`. Pour un dossier : `pytest -- tests/<dossier>`.

- **Nouvelle fonctionnalité** : les tests doivent passer.
- **Reproduction d'un bug** : le test doit **échouer avant le correctif**, pour la bonne raison (l'assertion qui décrit le bug, pas une erreur d'import ou de fixture). Le montrer, puis laisser l'utilisateur valider la cause et le correctif : on ne corrige pas dans ce skill (règle de `CLAUDE.md` : cause racine proposée avant de modifier le code).
- Un test qui passe du premier coup sans avoir vu échouer ce qu'il protège ne prouve rien : pour un comportement critique, vérifier qu'il échoue quand on casse volontairement le code (sur une copie ou en annulant ensuite, jamais en laissant la casse).

Ensuite, le lint comme la CI :

```bash
black --check .
isort --check-only --diff .
flake8 .
```

flake8 signale les imports inutilisés ; `black .` et `isort .` corrigent le reste, sur les fichiers de test écrits seulement.

### 5. Restituer

Dans le chat, en français :
- fichiers de tests créés ou modifiés ;
- **ce qui est couvert** (liste de comportements, pas de pourcentage) et **ce qui ne l'est pas** (et pourquoi : dépend du matériel, de la carte ou du backend, hors périmètre, bug connu du backlog) ;
- résultat réel de l'exécution : commande lancée, nombre de tests passés ou échoués. **Ne jamais affirmer qu'un test passe sans l'avoir lancé**, ni que le code marche sur la carte ;
- bugs ou comportements surprenants découverts en écrivant les tests : les noter dans `docs/backlog.md` plutôt que de les corriger, après avoir cherché un doublon.

Ne pas commiter : les tests se commitent avec le skill `commit`, dans le même changement que le code qu'ils couvrent ou dans un commit distinct (`test` si la branche est de type `test`).

## À éviter

- Modifier le code testé pour faire passer un test.
- Des tests qui répètent l'implémentation (mêmes calculs que le code) au lieu de vérifier le résultat.
- Assertions sur des détails internes (ordre des appels, noms de variables) plutôt que sur le comportement observable.
- Introduire une bibliothèque de factories ou des fixtures partagées sans décision.
- Port USB, broche ou capteur réels, réseau, dépendance à l'heure courante sans la contrôler.
- Tests dépendants les uns des autres, de l'ordre d'exécution ou d'un état global non remis à zéro.
- Valeurs réelles (UID de carte, identifiants) dans les fixtures ou les attendus : `DEVICE_UID` vient du mock de `machine.unique_id`.
- Annoncer « tests OK » sans les avoir exécutés.
