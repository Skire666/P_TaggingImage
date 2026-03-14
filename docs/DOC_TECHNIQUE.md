# Gallery Tagger — Documentation technique

## Vue d'ensemble

**Gallery Tagger** est une application Python 3.8+ avec interface Tkinter, organisée selon le patron **MVC** (Modèle – Vue – Contrôleur). Elle permet de parcourir et renommer des images dans un dossier.

Le drag & drop de dossiers est supporté grâce à `tkinterdnd2`, et la fenêtre utilise `TkinterDnD.Tk()` au lieu de `tk.Tk()`.

---

## Dépendances

| Paquet        | Usage                                      |
|---------------|--------------------------------------------|
| `Pillow`      | Chargement, redimensionnement et affichage d'images (`PIL.Image`, `PIL.ImageTk`) |
| `tkinter`     | Interface graphique (inclus dans la bibliothèque standard Python) |
| `tkinterdnd2` | Drag & drop de dossiers depuis l'Explorateur Windows vers l'application |

---

## Structure du projet

```
tagger3k/
├── Launchme.ps1                # Script PowerShell de lancement (Python 3.10+)
├── config.json                 # Configuration persistante (dernier dossier)
└── src/
    ├── gallery_tagger.py       # Point d'entrée CLI (argparse)
    ├── constants.py            # Configuration centralisée
    ├── utils.py                # Fonctions utilitaires pures
    ├── requirements.txt        # Dépendances pip (Pillow, tkinterdnd2)
    ├── controllers/
    │   ├── __init__.py
    │   ├── main_controller.py      # Contrôleur principal (orchestration)
    │   ├── config_controller.py    # Gestion de la configuration
    │   ├── file_controller.py      # Gestion des fichiers et tags
    │   └── view_controller.py      # Gestion de l'affichage et fenêtre
    ├── models/
    │   ├── __init__.py
    │   ├── image_navigator_model.py # Gestion de la liste de fichiers
    │   ├── config_model.py     # Gestion de la configuration JSON
    │   └── tag_model.py        # Extraction et comptage des tags
    └── views/
        ├── __init__.py
        ├── gallery_view.py     # Interface principale
        └── loading_view.py     # Écran de chargement modal
```

---

## Architecture MVC

### Flux de données

```
Utilisateur  →  Vue (événements)  →  Contrôleur (logique)  →  Modèles (données)
                                           ↓
                                     Vue (mise à jour)
```

### Responsabilités

| Couche         | Rôle                                                                   |
|----------------|------------------------------------------------------------------------|
| **Modèles**    | Données pures : liste de fichiers, index courant, dictionnaire de tags |
| **Vues**       | Construction des widgets Tkinter, aucune logique métier                |
| **Contrôleurs** | Orchestre modèles et vues, gère les événements et le renommage         |

### Pattern de sous-contrôleurs

Depuis la refactorisation, `MainController` délègue à trois sous-contrôleurs spécialisés pour séparer les responsabilités :

```
MainController (orchestration globale)
    ├─ ConfigController (persistance)
    ├─ FileController (modèles fichiers/tags)
    └─ ViewController (affichage / fenêtre Tk)
```

---

## Modules en détail

### `gallery_tagger.py` (point d'entrée)

- Parse les arguments CLI via `argparse` (un argument positionnel optionnel : chemin du dossier).
- Si le dossier est fourni, valide son existence.
- Instancie `MainController(folder)` qui crée et gère tout en interne.
- Le contrôleur crée la fenêtre `TkinterDnD.Tk()` et lance `mainloop()`.

Sans argument, la sélection du dossier est déléguée au contrôleur selon :
1. `last_opened_folder` dans `config.json` (si valide)
2. dossier courant (fallback)

### `constants.py` (configuration)

Contient **toutes** les valeurs paramétrables :

| Catégorie         | Constantes clés                                                                 |
|--------------------|-------------------------------------------------------------------------------------|
| **Extensions**     | `SUPPORTED_EXTENSIONS` (frozenset de 8 formats)                                     |
| **Dimensions**     | `LOADING_WIN_SIZE`, `FOOTER_PX`, `GALLERY_COL_WEIGHTS` |
| **Tailles fenêtre** | `MIN_WIN_WIDTH` (300), `MIN_WIN_HEIGHT` (300)                                       |
| **Limites**        | `max_path_len` et `max_filename_len` via `config.json` (défaults 220/110)            |
| **Séparateurs**    | `MAIN_SEPARATOR` (` - `), `TAG_SEPARATOR` (`, `), `TAG_OPEN` (`[`), `TAG_CLOSE` (`]`) |
| **Couleurs**       | Palette Catppuccin Mocha (voir section Thème visuel)                               |
| **Polices**        | `FONT_SM`, `FONT_SM_BOLD`, `FONT_SM_ITALIC`, `FONT_MD`, `FONT_MD_BOLD`, `FONT_LG_BOLD` (famille `Segoe UI`, taille 11) |
| **Styles boutons** | `BTN_STYLE` (navigation), `BTN_APPLY_STYLE` (renommage, vert succès)               |

### `utils.py` (utilitaires)

Fonctions pures sans dépendance aux modèles/vues :

| Fonction                      | Description                                                         |
|-------------------------------|---------------------------------------------------------------------|
| `get_list_tags(name)`         | Extrait `[tags]` depuis le format à crochets              |
| `_matches_tagged_syntax(stem)` | Vérifie si un stem suit le format `base - [tags] - compteur`        |
| `is_filename_tagged(name)`    | Vérifie si un nom de fichier est conforme au format taggué          |
| `resize_image_to_fit()`       | Redimensionne un `PIL.Image` avec ratio conservé (LANCZOS)           |
| `load_image_safe()`           | Charge un fichier image, retourne `PIL.Image` ou `None`              |
| `open_in_explorer()`          | Ouvre l'Explorateur Windows avec le fichier sélectionné              |
| `is_supported_image()`        | Vérifie l'extension par rapport à `SUPPORTED_EXTENSIONS`             |
| `center_window()`             | Centre une fenêtre Tkinter `Toplevel` sur l'écran                    |

#### Algorithme de `get_list_tags`

```python
# Entrée : "auteur - [tag1, tag2] - 1000.png"
# 1. Sépare extension  →  ("auteur - [tag1, tag2] - 1000", ".png")
# 2. Cherche le délimiteur ouvrant " - ["
# 3. Cherche le délimiteur fermant "] - "
# 4. Extrait le contenu entre crochets, split sur ", "
# 5. Retourne ["tag1", "tag2"]
```

Cas dégradés :
- Pas de crochets → `[]`
- Crochets vides → `[]`

### `models/image_navigator_model.py`

Gère une **liste ordonnée de fichiers** et un **index de navigation** :

| Méthode                | Description                                       |
|------------------------|----------------------------------------------------|
| `load_files()`         | Scanne le dossier, filtre par extensions supportées, trie par nom |
| `has_files()`          | Indique si des fichiers ont été chargés              |
| `current_filename()`   | Retourne le nom du fichier courant                 |
| `current_filepath()`   | Retourne le chemin complet du fichier courant      |
| `filepath_at(index)`   | Chemin d'un fichier par index                       |
| `total()`              | Nombre total de fichiers chargés                    |
| `prev_index()`         | Index de l'image précédente (cyclique)               |
| `next_index()`         | Index de l'image suivante (cyclique)                |
| `go_next()`            | Navigation vers l'image suivante                    |
| `go_previous()`        | Navigation vers l'image précédente                   |
| `rename_current(name)` | Renomme le fichier courant sur le disque           |
| `find_next_untagged()` | Cherche le prochain fichier non conforme au format |
| `file_exists(name)`    | Vérifie l'existence d'un fichier dans le dossier      |

### `models/config_model.py`

Gère la persistance de la configuration dans `config.json` :

| Méthode / Propriété         | Description                                               |
|--------------------------------|-----------------------------------------------------------|
| `last_opened_folder` (prop)    | Get/set le dernier dossier enregistré                    |
| `max_path_len` (prop)          | Get/set la limite de longueur de chemin (défaut 220)     |
| `max_filename_len` (prop)      | Get/set la limite de longueur de nom fichier (défaut 110) |

### `models/tag_model.py`

Construit un `OrderedDict[str, int]` de tags triés :

| Méthode                   | Description                                        |
|---------------------------|----------------------------------------------------|
| `build(files, callback)`  | Parse tous les fichiers, appelle `callback` pour la progression |
| `rebuild(files)`          | Reconstruction sans callback (après renommage)     |
| `_count_tags_in_file()`   | Utilise `get_list_tags` pour extraire les tags     |
| `_sort_dict()`            | Tri par fréquence décroissante puis alphabétique     |

### `views/gallery_view.py`

Construit toute l'interface sans logique métier. Expose des **variables Tkinter** et des **widgets** que le contrôleur connecte :

| Zone        | Composants                                                        |
|-------------|-------------------------------------------------------------------|
| **Galerie** | 3 `LabelFrame` avec `Label` pour images, pondération de la largeur |
| **Info bar** | Nom du fichier, index, boutons navigation (Précédent, Suivant, Prochain à tagguer), bouton explorateur |
| **Tags**    | Widget `tk.Text` (wrap="char") avec `Checkbutton` dynamiques intégrés, défilement vertical via `ttk.Scrollbar` |
| **Rename**  | Entry (nouveau nom), Label (extension), Label (aperçu), Labels (longueurs), label format, bouton renommer |

Variables exposées : `info_var`, `new_name_var`, `ext_label_var`, `path_len_var`, `filename_len_var`, `check_vars` (dict `{tag: BooleanVar}`).

Widgets exposés : `gallery_frame`, `prev_label`, `center_label`, `next_label`.

Le constructeur prend `(root, callbacks)` — le dictionnaire de tags n'est pas passé au constructeur ; les checkboxes sont créées ultérieurement via `build_tag_checkboxes(tag_dict)`.

### `views/loading_view.py`

Fenêtre modale `Toplevel` avec :
- Barre de progression `ttk.Progressbar` (style « clam », couleurs Catppuccin).
- Méthode `update(current, total)` appelée par le contrôleur.
- Méthode `close()` pour libérer le grab et détruire la fenêtre.

---

## Contrôleurs en détail

### `controllers/config_controller.py` — Gestion de la configuration

**Responsabilités** :
- Encapsuler les opérations de lecture/écriture de la configuration persistante.
- Fournir une interface simple au `MainController` sans exposer les détails du `ConfigModel`.

| Méthode                          | Description                                           |
|-----------------------------------|-------------------------------------------------------|
| `__init__(model_config=None)`     | Initialise le sous-contrôleur, crée ou injecte un modèle |
| `get_last_opened_folder()`        | Retourne le dernier dossier ouvert                    |
| `update_last_opened_folder(path)` | Sauvegarde le dossier courant                         |
| `get_max_path_len()`              | Retourne la limite de longueur de chemin              |
| `update_max_path_len(value)`      | Met à jour la limite de longueur de chemin            |
| `get_max_filename_len()`          | Retourne la limite de longueur de nom fichier         |
| `update_max_filename_len(value)`  | Met à jour la limite de longueur de nom fichier       |

**Notes** :
- Ce composant reste volontairement minimal et délègue le stockage au `ConfigModel`.
- Les propriétés `last_opened_folder`, `max_path_len`, et `max_filename_len` du `ConfigModel` sont gérées par getter/setter.

### `controllers/file_controller.py` — Gestion des fichiers et des tags

**Responsabilités** :
- Encapsuler les modèles `ImageNavigatorModel` et `TagModel`.
- Fournir une interface unifié pour accéder à la liste de fichiers, à l'index courant, et aux tags.
- Gérer la résolution du dossier de démarrage (CLI > config > dossier courant).

| Méthode                       | Description                                                  |
|-------------------------------|--------------------------------------------------------------|
| `__init__(folder_path)`       | Initialise les modèles de fichiers et de tags                |
| `resolve_start_folder(path, config_controller)` | Détermine le dossier initial et le persiste          |
| `folder_path` (prop)          | Retourne le chemin absolu du dossier courant                 |
| `current_index` (prop)        | Get/set l'index courant de navigation                        |
| `set_folder(folder_path)`     | Remplace le modèle de fichiers pour un nouveau dossier       |
| `load_files()`                | Charge la liste des images du dossier                        |
| `has_files()`                 | Indique si des images sont disponibles                       |
| `total()`                     | Retourne le nombre total de fichiers                         |
| `current_filename()`          | Retourne le nom du fichier courant                           |
| `current_filepath()`          | Retourne le chemin complet du fichier courant                |
| `filepath_at(index)`          | Retourne le chemin du fichier à un index donné               |
| `prev_index()`                | Index précédent (cyclique)                                   |
| `next_index()`                | Index suivant (cyclique)                                     |
| `go_next()`                   | Navigue vers l'image suivante                                |
| `go_previous()`               | Navigue vers l'image précédente                              |
| `go_next_untagged()`          | Navigue vers le prochain fichier non conforme                |
| `find_available_name(base, ext, ignore)` | Cherche un compteur libre (1000–9999)              |
| `rename_current(name)`        | Renomme le fichier courant sur le disque                    |
| `build_tags(callback)`        | Construit le modèle de tags avec callback de progression     |
| `rebuild_tags()`              | Reconstruit les tags sans callback                           |
| `tag_dict()`                  | Retourne l'OrderedDict des tags comptabilisés                |

**Notes** :
- La méthode statique `resolve_start_folder()` encapsule la logique de priorité : argument CLI > dossier sauvegardé > dossier courant.
- Les tags sont construits via un callback qui met à jour l'interface (barre de progression).

### `controllers/view_controller.py` — Gestion de l'affichage et fenêtre

**Responsabilités** :
- Créer et configurer la fenêtre `TkinterDnD.Tk()`.
- Instancier et mettre à jour la vue principal (`GalleryView`).
- Gérer l'affichage des images, l'info-bar, les tags et les champs de renommage.
- Gérer le redimensionnement dynamique de la galerie avec debounce.
- Gérer le drag-and-drop de dossiers.

| Méthode                                | Description                                                |
|----------------------------------------|--------------------------------------------------------|
| `__init__()`                           | Initialise l'état d'affichage et les références d'images |
| `init_window()`                        | Crée la fenêtre principale `TkinterDnD.Tk()`, la configure |
| `build_view(callbacks)`                | Instancie `GalleryView` avec les callbacks applicatifs    |
| `bind_shortcuts(on_apply_rename)`      | Attache le raccourci `<Return>` pour renommer             |
| `bind_drop(on_drop)`                   | Active le drag-and-drop via `tkinterdnd2`                 |
| `schedule_initial_display(file_controller)` | Planifie le premier rendu via `after_idle`       |
| `refresh_image_displayed(file_controller)` | Charge et affiche les 3 images (prev, center, next) |
| `_show_image(key, index, label, size)` | Charge une image spécifique et l'affiche dans un label    |
| `update_info_and_tags(file_controller)` | Met à jour la barre d'info et les cases à cocher des tags |
| `trace_new_name(file_controller)`       | Attache un observateur sur le champ de nouveau nom        |
| `on_tag_toggled(file_controller)`      | Callback : case cochée/décochée → recompose le nom       |
| `_update_new_name(tag_dict)`           | Reconstruit le nom depuis les tags cochés                 |
| `_trace_new_name()`                    | Observe `new_name_var` pour mettre à jour l'aperçu      |
| `_update_preview()`                    | Génère l'aperçu complet `base - [tags] - 1000.ext`      |
| `_clear_preview_fields()`              | Réinitialise les champs d'aperçu et longueurs            |
| `_bind_gallery_resize(file_controller)` | Attache le handler de redimensionnement avec debounce  |
| `_on_gallery_configure(event)`         | Handler de redimensionnement avec timer de debounce      |
| `_on_gallery_resized(file_controller)` | Recharge les images après stabilisation de la taille     |
| `_get_panel_size(label)`               | Retourne les dimensions disponibles d'un panneau         |

**Mécanismes notables** :

**Debounce du redimensionnement**
Le redimensionnement de la galerie est déclenché par l'événement `<Configure>`. Un timer pour le debounce évite les recalculs excessifs pendant le glissement de la fenêtre. La taille précédente est mémorisée (`_last_gallery_size`) pour ignorer les événements `<Configure>` découlant de l'insertion d'images.

```python
def _on_gallery_configure(self, event):
    new_size = (event.width, event.height)
    if new_size == self._last_gallery_size:
        return
    if self._resize_after_id is not None:
        self.root.after_cancel(self._resize_after_id)
    self._resize_after_id = self.root.after(DEBOUNCE_MS, self._on_gallery_resized)
```

**Gestion des références d'images**
Les images PIL chargées sont stockées dans `_img_refs` pour empêcher le garbage collection. Sans cette référence, les images sont immédiatement libérées et n'apparaissent pas à l'écran.

### `controllers/main_controller.py` — Orchestration globale

**Responsabilités** :
- Initialiser les sous-contrôleurs et la fenêtre.
- Charger les fichiers et construire les tags.
- Instancier la vue et connecter les callbacks.
- Orchestrer la navigation, le renommage, et le rechargement de dossier.
- Gérer les appels à `mainloop()`.

| Méthode                           | Description                                                    |
|-----------------------------------|----------------------------------------------------------------|
| `__init__(folder_path=None)`      | Initialise l'application et lance `mainloop()`                 |
| `_build_view()`                   | Construit la vue en injectant les callbacks applicatifs        |
| `_load_files_or_warn()`           | Charge le dossier et affiche un avertissement si besoin        |
| `_load_current_folder_or_warn(allow_empty)` | Charge le dossier avec gestion d'erreurs |
| `_build_tags_with_progress()`     | Construit les tags avec `LoadingView` comme callback           |
| `apply_rename()`                  | Pipeline complet de renommage                                  |
| `_build_new_filename()`           | Construit le nom final : `base - [tags] - 1000.ext`           |
| `_validate_rename()`              | Vérifie que le nouveau nom diffère de l'actuel                |
| `_resolve_conflict()`             | Incrémente le compteur si le nom existe déjà                  |
| `_check_length()`                 | Vérifie les limites de longueur (chemin et nom)               |
| `_perform_rename()`               | Exécute le renommage et reconstruit les tags                  |
| `go_next()`                       | Navigue vers l'image suivante                                 |
| `go_previous()`                   | Navigue vers l'image précédente                               |
| `go_next_untagged()`              | Navigue vers le prochain fichier non conforme                 |
| `open_explorer()`                 | Ouvre l'Explorateur sur le fichier courant                    |
| `_on_drop(event)`                 | Gère le drop de dossier et déclenche le rechargement           |
| `reload_current_folder()`         | Recharge la liste et les tags du dossier courant              |
| `select_folder()`                 | Affiche un dialog de sélection de dossier                     |

**Flux d'initialisation** :

1. Création des sous-contrôleurs (Config, File, View).
2. Résolution du dossier initial via `FileController.resolve_start_folder()`.
3. Chargement des fichiers via `_load_files_or_warn()`.
4. Construction des tags avec barre de progression via `_build_tags_with_progress()`.
5. Instanciation de la vue avec callbacks via `_build_view()`.
6. Attachement des observateurs et raccourcis.
7. Premier rendu différé via `schedule_initial_display()`.
8. Lancement de `mainloop()`.

**Pipeline de renommage** :

```
apply_rename()
    ├─ _validate_rename() : vérifier le changement
    ├─ _build_new_filename() : composition du nom
    ├─ _check_length() : limites de longueur
    ├─ _resolve_conflict() : gestion conflits
    └─ _perform_rename() : exécution + reconstruction tags
```

---

## Thème visuel

L'application utilise la palette **Catppuccin Mocha** :

| Variable       | Couleur     | Usage                              |
|----------------|-------------|-------------------------------------|
| `BG_COLOR`     | `#1e1e2e`   | Fond principal                      |
| `FG_COLOR`     | `#cdd6f4`   | Texte principal                     |
| `ACCENT_COLOR` | `#89b4fa`   | Accents, liens, titres de sections  |
| `FRAME_BG`     | `#313244`   | Fond des cadres (`LabelFrame`)      |
| `BUTTON_BG`    | `#45475a`   | Fond des boutons et champs de saisie |
| `BUTTON_FG`    | `#cdd6f4`   | Texte des boutons                   |
| `ENTRY_BG`     | `#45475a`   | Fond des champs `Entry`             |
| `ENTRY_FG`     | `#cdd6f4`   | Texte des champs `Entry`            |
| `CHECK_BG`     | `#313244`   | Fond des cases à cocher             |
| `CHECK_FG`     | `#cdd6f4`   | Texte des cases à cocher            |
| `HIGHLIGHT`    | `#f38ba8`   | Surbrillance (rose), texte fallback |
| `SUCCESS_BG`   | `#a6e3a1`   | Fond bouton renommer (vert)         |
| `SUCCESS_FG`   | `#1e1e2e`   | Texte bouton renommer               |

---

## Séquence de démarrage

```
1. gallery_tagger.py : argparse → validation du dossier si argument fourni
2. MainController(folder_path) :
    a. Création de ConfigController
    b. FileController.resolve_start_folder() : CLI > config > dossier courant
    c. Création de FileController et ViewController
    d. ViewController.init_window() → TkinterDnD.Tk()
    e. _load_files_or_warn() → scanne le dossier
    f. _build_tags_with_progress()
      ├─ ViewController.schedule_initial_display()
      ├─ LoadingView.show()
      ├─ FileController.build_tags(loading.update)
      └─ LoadingView.close()
    g. _build_view() → ViewController.build_view(callbacks)
    h. ViewController.trace_new_name(file_controller)
    i. ViewController.bind_shortcuts(apply_rename)
    j. ViewController.bind_drop(on_drop)
    k. ViewController.schedule_initial_display(file_controller)
      ├─ refresh_image_displayed()
      ├─ view.build_tag_checkboxes()
      ├─ update_info_and_tags()
      └─ _bind_gallery_resize()
    l. root.mainloop()
```

---

## Limites connues

- **Windows uniquement** pour l'ouverture dans l'Explorateur (`explorer /select`).
- **Pas de multi-threading** : le chargement des tags bloque l'interface (atténué par `update_idletasks` dans la barre de progression).
- **Plage de compteurs limitée** : 1000 – 9999 (10 000 noms uniques par base), valeurs codées en dur dans le contrôleur.
- **Persistance limitée** : seules les clés `last_opened_folder`, `max_path_len` et `max_filename_len` sont sauvegardées actuellement.
```

---

This updated documentation now reflects:
1. **Project structure tree** — Added the 4 controllers
2. **Architecture section** — Added the sub-controller pattern diagram
3. **Detailed controller explanations** — Complete rewrite with all 4 controllers including their methods, responsibilities, and the orchestration flow