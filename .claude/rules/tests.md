---
paths:
  - "tests/**"
  - "conftest.py"
---

# Tests

- pytest, pytest-asyncio (`asyncio_mode = "auto"` dans `pyproject.toml`), pytest-mock. `pytest-xdist` est installé mais `pytest -n auto` échoue (`AttributeError: module 'tests.mocks.sys' has no attribute 'argv'` : `conftest.py` remplace `sys` avant xdist) ; la suite dure quelques secondes sans parallélisme. Pas de `pytest.ini`, pas de timeout, pas de marker `slow`. Les tests tournent sous CPython 3.13 sur les sources de `src/` ; ils ne prouvent pas que le code fonctionne sur la carte (voir `.claude/rules/src.md`).
- Arborescence : elle reflète `src/` (`tests/tests_core/`, `tests_models/`, `tests_channelsrunner/`, `tests_protocols/tests_usb/` avec `tests_handlers/` et `tests_parsers/`), plus `tests/test_versions.py` à la racine. Un fichier de test porte le nom de l'objet testé (`test_queue.py`) ; chaque dossier a un `__init__.py`.
- Structure d'un test : une docstring d'une ligne, puis les commentaires `# GIVEN`, `# WHEN`, `# THEN`. Classes de test groupées par objet ou par comportement (`TestQueueInit`). Les fichiers longs séparent leurs blocs par des bandeaux `# ----` (« Helpers », « Fixtures », « Tests – <sujet> »), comme `test_queue.py` et `test_ping_frame.py`.
- Un test d'intégration (parser + handler + callbacks, ex. `test_ping_frame.py`, `test_lg_init_frame.py`) le dit dans un commentaire en tête de fichier.
- Les trames de test se construisent avec une fonction d'aide qui calcule le vrai checksum (`Frame.build_checksum`, voir `build_ping_frame_str`) : ne pas écrire de checksum en dur. Si le calcul du checksum change, ces tests le suivent seuls.
- Fixtures : `@pytest.fixture` définies dans le fichier de test (il n'y a pas de fixtures partagées dans `conftest.py`). `autouse=True` seulement pour remettre à zéro un état global (files, registres, singletons) entre les tests.
- Fonctions asynchrones : `@pytest.mark.asyncio` sur le test (déjà utilisé par les tests existants, même si le mode `auto` suffit). Mocker une coroutine avec `mocker.AsyncMock()`.
- Mocks : `pytest-mock` (`mocker.patch("src.<chemin>.<nom>")`, en visant l'endroit où le nom est **utilisé**) et `monkeypatch` pour un attribut ou l'environnement (ex. `monkeypatch.setattr(sys, "version", …)`). `unittest.mock` n'est pas importé directement ; `mocker.MagicMock(spec=Frame)` pour un objet qui doit garder l'interface réelle.
- Modules MicroPython : `conftest.py` installe `tests/mocks/machine.py`, `ubinascii.py` et `sys.py` dans `sys.modules` **avant** la collecte, et patche `asyncio.StreamReader` pour la syntaxe MicroPython. Ne pas importer `machine` ou `ubinascii` autrement. Un nouveau module matériel utilisé dans `src/` demande un mock dans `tests/mocks/` (classes et méthodes strictement nécessaires, avec le même nom et la même signature que l'API réelle) et son enregistrement dans `conftest.py`.
- Jamais de port USB, de broche ou de capteur réels, ni de réseau.
- État global : `event_emitter`, `commands_store`, `init_pins_store`, `frame_handler` et les files `data_received` / `data_to_response` sont des singletons partagés. Un test qui les modifie les remet dans leur état d'origine (fixture avec `yield`, ou patch via `mocker`). Ne pas compter sur un état laissé par un autre test ou un autre fichier.
- Un bug : le reproduire par un test qui échoue avant le correctif. Un comportement sensible pour le protocole (checksum, format de trame, codes d'erreur) a un test qui le fige, puisque le backend en dépend.
- Lancer un fichier ou un test : `pytest -- tests/<dossier>/<fichier>.py::<Classe>::<test>`. Pour aller vite : `-x`.
- Skill : `write-test`.
