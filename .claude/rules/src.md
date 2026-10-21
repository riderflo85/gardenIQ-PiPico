---
paths:
  - "src/**"
  - "main.py"
---

# Code du firmware (`src/`) : contraintes MicroPython

Le code de `src/` finit sur un Raspberry Pi Pico (RP2040, 264 Ko de RAM, 2 Mo de flash) sous MicroPython. Ce qui marche sous CPython (les tests) peut échouer sur la carte : en cas de doute, vérifier sur la carte et le dire, au lieu d'affirmer. Les points marqués « à vérifier » n'ont pas été contrôlés sur la carte.

## Bibliothèques et langage

- Seule une partie de la bibliothèque standard existe, parfois réduite. Absents ou à éviter : `enum`, `dataclasses`, `abc`, `logging`, `pathlib`, `threading`, `unittest`, `match/case`. Équivalents du projet : `PseudoEnum` (`core/enum.py`), `FrozenDataclass` (`core/dataclass.py`), `core/queue.py` (file asyncio maison), `EventEmitter`.
- Les modules qui existent sont des sous-ensembles : `re` (syntaxe limitée, à vérifier avant d'écrire un motif complexe ; `protocols/settings.py` utilise `\d{1,2}`), `json`, `asyncio` (version MicroPython, pas celle de CPython), `time` (`ticks_ms`/`ticks_diff` plutôt que `time.time()` pour mesurer une durée), `struct`, `collections` (`deque`, `OrderedDict` partiels).
- Fonctions de `str`, `list` ou `dict` récentes, syntaxe récente (f-strings imbriquées avec les mêmes guillemets, comme dans `core/utils.py:format_error`, `removesuffix`) : à vérifier avant de s'y fier, la compilation `.mpy` ou l'exécution peut échouer alors que les tests passent.
- Pas de nouvelle dépendance PyPI : le firmware n'a aucune dépendance runtime. Une bibliothèque MicroPython externe (`micropython-lib`) se discute avec l'utilisateur (taille, licence, compatibilité).
- Les modules matériels (`machine`, `rp2`, `utime`, `ubinascii`…) n'existent pas sous CPython : chaque nouvel usage demande un mock dans `tests/mocks/` (voir `.claude/rules/tests.md`).
- Le typage reste écrit comme d'habitude (voir `CLAUDE.md`) : il est retiré avant l'exécution. Ne pas écrire de code qui **dépend** des annotations à l'exécution (`typing.get_type_hints`, `__annotations__`, `isinstance` sur un type générique, `Protocol` à l'exécution, `TypeVar` utilisé comme valeur).

## Mémoire

- RAM limitée et fragmentée : éviter les grosses chaînes, listes et dictionnaires, les concaténations de `str` dans une boucle (`"".join(...)`), les copies (`bytes(buf)`, tranches de `bytes`/`list`). Préférer `bytearray` + `memoryview` et les tampons réutilisés.
- Classes instanciées en nombre : `__slots__` (déjà le cas de `Frame`, `FrozenDataclass`).
- Libérer ce qui ne sert plus (exemple : `Pin._set_done_init` vide `initial_configuration`). Les registres (`commands_store`, `init_pins_store`) ne doivent pas grandir sans borne : fixer ou documenter une taille maximale.
- `Queue(maxsize=…)` : toujours borné. Une file non bornée alimentée par l'USB peut saturer la RAM.
- `gc.collect()` : seulement à des endroits choisis (après l'initialisation, avant une allocation importante), jamais dans une boucle chaude. `gc.mem_free()` / `gc.mem_alloc()` servent à mesurer, pas à rester dans le code.
- `micropython.const()` pour les constantes entières de bas niveau (broches, masques, tailles) : elles ne coûtent pas de RAM.
- Importer à la demande ce qui est rare et lourd ; les imports de tête restent dans le module qui les utilise (voir règles d'architecture de `CLAUDE.md`).
- Une exception avec un long message, un `repr` ou un traceback formaté coûte de la RAM : garder les messages courts (ils sont aussi renvoyés au backend, voir `format_error`).

## Performance

- Rien de bloquant dans les tâches `asyncio` : pas de `time.sleep()`, pas de boucle d'attente active, pas de calcul long sans rendre la main (`await asyncio.sleep(0)` ou `sleep_ms`). Une tâche qui bloque fige la lecture de l'USB.
- Boucle chaude (parsing de trame, checksum, exécution d'un ordre) : variables locales plutôt qu'attributs/globaux répétés, pas d'allocation inutile, pas de `re` si un `split`/`startswith` suffit.
- Matériel : un `Pin`/`PWM`/`ADC` se crée **une fois** (au `LG_INIT`) et se réutilise ; ne pas le ré-instancier à chaque ordre. Les accès (`value()`, `duty_u16()`, `read_u16()`) sont rapides, mais une lecture analogique doit respecter le temps de stabilisation du capteur.
- Délais courts et précis : `time.sleep_us`/`sleep_ms`, `ticks_ms`/`ticks_diff` (gèrent le débordement). Ne pas comparer deux `ticks` directement.
- Les `print()` sont lents et, ici, dangereux (voir Sécurité).

## Canal USB et protocole

- `sys.stdin` / `sys.stdout` **sont** le canal du protocole : tout `print()` ou affichage de debug dans `src/` s'ajoute au flux de trames et corrompt les réponses vues par le backend. Pas de `print()` ni de trace sur stdout ; pour déboguer, utiliser un REPL manuel ou la LED, et retirer avant de commiter.
- Une trame = une ligne terminée par `\n` ; les espaces séparent les blocs (voir `format_error` qui les remplace par `_`). Toute donnée ajoutée à une trame ne doit contenir ni espace, ni `<`, ni `>`, ni retour à la ligne.
- Le protocole est partagé avec le backend (`gardenIQ-back`) : changer un format, un type de trame, un code d'erreur ou le checksum se décide avec l'utilisateur, jamais seul.

## Sécurité

- Tout ce qui arrive par l'USB est non fiable : valider le format, la longueur, les types et les bornes (numéro de broche présent dans `datasheet`, canal compatible avec la broche, valeur PWM dans la plage) **avant** de toucher au matériel. Une trame invalide donne une réponse `ERR`, pas une exception non gérée.
- Ordre de vérification d'une trame : longueur et format, UID du device, checksum, puis exécution (voir `FrameHandler.handle_master_command`). Ne pas exécuter avant d'avoir vérifié.
- Le checksum Fletcher8 détecte les erreurs de transmission, il **n'authentifie pas** l'émetteur : ne pas le présenter comme une protection contre un acteur malveillant.
- `UKW_DEV_UID` est accepté à la place de l'UID du device pour la première prise de contact (ping, `LG_INIT`) : c'est voulu, ne pas étendre ce passe-droit à d'autres usages.
- Pas de `eval`, `exec`, `__import__` ni d'import dynamique construit à partir de données reçues. Pas de désérialisation d'objets arbitraires : `json.loads` sur des données validées en aval seulement, avec un `try`.
- Pas de secret, de clé ni d'identifiant en dur dans `src/` : le firmware est lisible sur la carte.
- Les actionneurs (vannes, pompes) ont un état sûr : à la mise sous tension et sur erreur, sorties à l'arrêt. Une commande ne doit pas pouvoir laisser une vanne ouverte indéfiniment sans mécanisme de sécurité (délai maximal, arrêt à la perte de communication) : le signaler à l'utilisateur quand on ajoute une sortie.
- Les messages d'erreur renvoyés au backend ne contiennent pas d'informations internes inutiles (chemins, valeurs de configuration).

## Robustesse

- Les tâches `asyncio` (`protocols/usb/workflow.py`) ne doivent jamais se terminer sur une exception : un `try/except Exception` à l'intérieur de la boucle, avec une réponse `ERR`, sinon la tâche s'arrête en silence et le Pico ne répond plus. Garder une référence aux tâches créées.
- Toute attente d'entrée/sortie externe (lecture capteur, bus I2C/SPI/UART) a un délai maximal ; ne jamais attendre sans fin.
- Un firmware qui boucle ou bloque doit pouvoir se relancer seul : prévoir un `machine.WDT` (watchdog) sur la boucle principale et le nourrir à un endroit qui prouve que le système vit (pas dans un `try/finally` qui masque un blocage). Non présent aujourd'hui ; à décider avec l'utilisateur avant de l'ajouter.
- Les erreurs attendues (clé absente, valeur invalide, broche inconnue) sont gérées explicitement et deviennent une trame `ERR` (`CommandError`, `format_error`). `Exception` nue seulement en dernier rempart, dans les tâches.
- `assert` : ne pas s'en servir pour valider une entrée (retiré à la compilation en mode optimisé, et `AssertionError` n'est pas une réponse de protocole).
- Un état global modifiable (registres, singletons) est accédé depuis plusieurs tâches : pas d'`await` entre une lecture et l'écriture qui en dépend si l'état doit rester cohérent.

## Matériel (RP2040)

- Numéros de broches = GPIO, pas les numéros physiques de la carte. La source de vérité des broches et de leurs capacités est `src/datasheet.py`.
- Le ADC lit 12 bits mais MicroPython renvoie 16 bits (`read_u16`) ; le PWM se règle en fréquence et `duty_u16`. Garder les unités explicites dans les noms.
- Tension : GPIO en 3,3 V, ne jamais supposer un capteur 5 V compatible. L'ADC mesure 0 à 3,3 V.
- Plusieurs fonctions sur la même broche (PWM, I2C, UART) : refuser la double affectation, ne pas la laisser à la chance.
- Le démarrage fixe l'état initial des broches avant toute commande du backend.

## Écriture de code

- Courts : fonctions petites, peu d'indirections, pas de couches « au cas où ». Chaque couche coûte de la RAM et du temps.
- Pas de dépendance cachée au contexte CPython (`sys.modules`, `__file__`, `os.environ`, `threading`, `locale`, `datetime` complet).
- Les commentaires et docstrings sont retirés ou minifiés avant la compilation : ne rien y faire dépendre du comportement.
- Le code évolue en même temps que sa carte cible : avant d'utiliser une API MicroPython, vérifier qu'elle existe dans la version visée (`src/__version__.py` lit la version de MicroPython au démarrage ; stubs d'éditeur dans `~/.micropico-stubs`).
