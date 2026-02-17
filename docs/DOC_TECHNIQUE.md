# Gallery Tagger — Documentation technique

## Vue d’ensemble

**Gallery Tagger** est une application Python 3.8+ avec interface Tkinter, organisée selon le patron **MVC** (Modèle – Vue – Contrôleur). Elle permet de parcourir et renommer des images dans un dossier.

Le drag & drop de dossiers est supporté grâce à `tkinterdnd2`, et la fenêtre utilise `TkinterDnD.Tk()` au lieu de `tk.Tk()`.

---

## Dépendances

| Paquet        | Usage                                      |
|---------------|--------------------------------------------|
| `Pillow`      | Chargement, redimensionnement et affichage d’images (`PIL.Image`, `PIL.ImageTk`) |
| `tkinter`     | Interface graphique (inclus dans la bibliothèque standard Python) |
| `tkinterdnd2` | Drag & drop de dossiers depuis l’Explorateur Windows vers l’application |

---

## Structure du projet

```
tagger3k/
├── Launchme.ps1                # Script PowerShell de lancement (Python 3.10+)
└── src/
    ├── gallery_tagger.py       # Point d’entrée CLI (argparse)
    ├── constants.py            # Configuration centralisée
    ├── utils.py                # Fonctions utilitaires pures
    ├── requirements.txt        # Dépendances pip (Pillow, tkinterdnd2)
    ├── controllers/
    │   ├── __init__.py
    │   └── gallery_controller.py   # Contrôleur principal
    ├── models/
    │   ├── __init__.py
    │   ├── file_model.py       # Gestion de la liste de fichiers
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
| **Contrôleur** | Orchestre modèles et vues, gère les événements et le renommage         |

---

## Modules en détail

### `gallery_tagger.py` (point d’entrée)

- Parse les arguments CLI via `argparse` (un argument positionnel : chemin du dossier).
- Valide l’existence du dossier.
- Instancie `GalleryController(folder)` qui crée et gère tout en interne.
- Le contrôleur crée la fenêtre `TkinterDnD.Tk()` et lance `mainloop()`.

### `constants.py` (configuration)

Contient **toutes** les valeurs paramétrables :

| Catégorie         | Constantes clés                                                                 |
|--------------------|-------------------------------------------------------------------------------------|
| **Extensions**     | `SUPPORTED_EXTENSIONS` (frozenset de 8 formats)                                     |
| **Dimensions**     | `LOADING_WIN_SIZE` (420×120), `FOOTER_PX` (190 px), `GALLERY_COL_WEIGHTS` (`[2, 6, 2]`) |
| **Tailles fenêtre** | `MIN_WIN_WIDTH` (300), `MIN_WIN_HEIGHT` (300)                                       |
| **Limites**        | `MAX_PATH_LEN` (235), `MAX_FILENAME_LEN` (120)                                     |
| **Séparateurs**    | `MAIN_SEPARATOR` (` - `), `TAG_SEPARATOR` (`, `), `TAG_OPEN` (`[`), `TAG_CLOSE` (`]`) |
| **Couleurs**       | Palette Catppuccin Mocha (voir section Thème visuel)                               |
| **Polices**        | `FONT_SM`, `FONT_SM_BOLD`, `FONT_SM_ITALIC`, `FONT_MD`, `FONT_MD_BOLD`, `FONT_LG_BOLD` (famille `Segoe UI`, taille 11) |
| **Styles boutons** | `BTN_STYLE` (navigation), `BTN_APPLY_STYLE` (renommage, vert succès)               |

### `utils.py` (utilitaires)

Fonctions pures sans dépendance aux modèles/vues :

| Fonction                     | Description                                                         |
|------------------------------|---------------------------------------------------------------------|
| `parse_filename(name)`       | Extrait `(extension, [tags])` depuis le format à crochets              |
| `_matches_tagged_syntax(stem)` | Vérifie si un stem suit le format `base - [tags] - compteur`        |
| `is_filename_tagged(name)`   | Vérifie si un nom de fichier est conforme au format taggué          |
| `resize_image_to_fit()`      | Redimensionne un `PIL.Image` avec ratio conservé (LANCZOS)           |
| `load_image_safe()`          | Charge un fichier image, retourne `PIL.Image` ou `None`              |
| `open_in_explorer()`         | Ouvre l’Explorateur Windows avec le fichier sélectionné              |
| `is_supported_image()`       | Vérifie l’extension par rapport à `SUPPORTED_EXTENSIONS`             |
| `center_window()`            | Centre une fenêtre Tkinter `Toplevel` sur l’écran                    |

#### Algorithme de `parse_filename`

```python
# Entrée : "auteur - [tag1, tag2] - 1000.png"
# 1. Sépare extension  →  ("auteur - [tag1, tag2] - 1000", ".png")
# 2. Cherche le délimiteur ouvrant " - ["
# 3. Cherche le délimiteur fermant "] - "
# 4. Extrait le contenu entre crochets, split sur ", "
# 5. Retourne (".png", ["tag1", "tag2"])
```

Cas dégradés :
- Pas de crochets → `(ext, [])`
- Crochets vides → `(ext, [])`

### `models/file_model.py`

Gère une **liste ordonnée de fichiers** et un **index de navigation** :

| Méthode                | Description                                       |
|------------------------|----------------------------------------------------|
| `load_files()`         | Scanne le dossier, filtre par extensions supportées, trie par nom |
| `has_files()`          | Indique si des fichiers ont été chargés              |
| `current_filename()`   | Retourne le nom du fichier courant                 |
| `current_filepath()`   | Retourne le chemin complet du fichier courant      |
| `filepath_at(index)`   | Chemin d’un fichier par index                       |
| `total()`              | Nombre total de fichiers chargés                    |
| `prev_index()`         | Index de l’image précédente (cyclique)               |
| `next_index()`         | Index de l’image suivante (cyclique)                |
| `go_next()`            | Navigation vers l’image suivante                    |
| `go_previous()`        | Navigation vers l’image précédente                   |
| `rename_current(name)` | Renomme le fichier courant sur le disque           |
| `find_next_untagged()` | Cherche le prochain fichier non conforme au format |
| `file_exists(name)`    | Vérifie l’existence d’un fichier dans le dossier      |

### `models/tag_model.py`

Construit un `OrderedDict[str, int]` de tags triés :

| Méthode                   | Description                                        |
|---------------------------|----------------------------------------------------|
| `build(files, callback)`  | Parse tous les fichiers, appelle `callback` pour la progression |
| `rebuild(files)`          | Reconstruction sans callback (après renommage)     |
| `_count_tags_in_file()`   | Utilise `parse_filename` pour extraire les tags     |
| `_sort_dict()`            | Tri par fréquence décroissante puis alphabétique     |

### `views/gallery_view.py`

Construit toute l’interface sans logique métier. Expose des **variables Tkinter** et des **widgets** que le contrôleur connecte :

| Zone        | Composants                                                        |
|-------------|-------------------------------------------------------------------|
| **Galerie** | 3 `LabelFrame` avec `Label` pour images, pondération `[2, 6, 2]` |
| **Info bar** | Nom du fichier, index, boutons navigation (Précédent, Suivant, Prochain non-taggué), bouton explorateur |
| **Tags**    | Widget `tk.Text` (wrap="char") avec `Checkbutton` dynamiques intégrés, défilement vertical via `ttk.Scrollbar` |
| **Rename**  | Entry (nouveau nom), Label (extension), Label (aperçu), Labels (longueurs), label format, bouton renommer |

Variables exposées : `info_var`, `new_name_var`, `ext_label_var`, `preview_var`, `path_len_var`, `filename_len_var`, `check_vars` (dict `{tag: BooleanVar}`).

Widgets exposés : `gallery_frame`, `prev_label`, `center_label`, `next_label`.

Le constructeur prend `(root, callbacks)` — le dictionnaire de tags n’est pas passé au constructeur ; les checkboxes sont créées ultérieurement via `build_tag_checkboxes(tag_dict)`.

### `views/loading_view.py`

Fenêtre modale `Toplevel` avec :
- Barre de progression `ttk.Progressbar` (style « clam », couleurs Catppuccin).
- Méthode `update(current, total)` appelée par le contrôleur.
- Méthode `close()` pour libérer le grab et détruire la fenêtre.

### `controllers/gallery_controller.py`

Orchestre l’ensemble de l’application (~845 lignes) :

#### Initialisation et démarrage

| Méthode                      | Rôle                                                            |
|--------------------------------|-----------------------------------------------------------------|
| `__init__(folder_path)`        | Crée les modèles, la fenêtre, charge les fichiers/tags, construit la vue, lance `mainloop()` |
| `_init_window()`               | Crée `TkinterDnD.Tk()`, configure titre/fond/taille, maximise  |
| `_load_files_or_warn()`        | Charge les fichiers, avertit si dossier vide/inaccessible       |
| `_build_tags_with_progress()`  | Construit les tags avec `LoadingView` comme callback            |
| `_build_view()`                | Instancie `GalleryView` avec les callbacks                      |
| `_bind_shortcuts()`            | Attache `<Return>` → `apply_rename()`                          |
| `_bind_drop()`                 | Active le drag & drop via `tkinterdnd2`                         |
| `_initial_display()`           | Premier affichage déféré via `after_idle`                       |

#### Affichage et redimensionnement

| Méthode                               | Rôle                                                   |
|-----------------------------------------|------------------------------------------------------|
| `_display_current()`                    | Rafraîchit les 3 images + info + tags                 |
| `_show_image(key, index, label, size)`  | Charge et affiche une image dans un label            |
| `_update_info_and_tags()`               | Met à jour barre d’info et coche les tags adéquats     |
| `_bind_gallery_resize()`               | Écoute `<Configure>` sur le cadre galerie             |
| `_on_gallery_configure(event)`          | Handler debounce (150 ms) pour le redimensionnement  |
| `_on_gallery_resized()`                 | Recharge les images après stabilisation de la taille |
| `_get_panel_size(label)`                | Retourne les dimensions disponibles d’un panneau      |

#### Tags et composition du nom

| Méthode                    | Rôle                                                            |
|------------------------------|------------------------------------------------------------------|
| `_on_tag_toggled()`          | Callback d’une case à cocher → recompose le nom                    |
| `_update_new_name()`         | Reconstruit `base - [tags]` depuis les tags cochés               |
| `_trace_new_name()`          | Observe `new_name_var` pour mettre à jour l’aperçu en temps réel |
| `_update_preview()`          | Génère l’aperçu complet `base - [tags] - 1000.ext`               |
| `_clear_preview_fields()`   | Réinitialise les champs d’aperçu et de longueur                   |
| `_find_available_name()`     | Cherche un compteur libre entre 1000 et 9999                      |

#### Renommage

| Méthode                   | Rôle                                                            |
|----------------------------|-----------------------------------------------------------------|
| `apply_rename()`           | Pipeline complet de renommage                                   |
| `_build_new_filename()`    | Construit le nom final : `base - [tags] - 1000.ext`            |
| `_validate_rename()`       | Vérifie que le nouveau nom diffère de l’actuel                    |
| `_resolve_conflict()`      | Incrémente le compteur si le nom existe déjà                      |
| `_check_length()`          | Vérifie les limites de longueur (chemin et nom de fichier)      |
| `_perform_rename()`        | Exécute le renommage via FileModel et reconstruit les tags      |

#### Navigation

| Méthode              | Rôle                                              |
|----------------------|---------------------------------------------------|
| `go_next()`          | Image suivante (cyclique)                         |
| `go_previous()`      | Image précédente (cyclique)                       |
| `go_next_untagged()` | Navigue vers le prochain fichier non conforme     |
| `open_explorer()`    | Ouvre l’Explorateur Windows sur le fichier courant |

#### Drag & drop

| Méthode                       | Rôle                                                       |
|---------------------------------|--------------------------------------------------------------|
| `_bind_drop()`                  | Enregistre la fenêtre comme cible de drop via `tkinterdnd2` |
| `_on_drop(event)`               | Valide le dossier déposé et déclenche `_reload_folder()`     |
| `_reload_folder(folder_path)`   | Réinitialise complètement l’application sur un nouveau dossier |

#### Mécanismes notables

**Debounce du redimensionnement**

Le redimensionnement de la galerie est déclenché par l’événement `<Configure>`. Un timer de **150 ms** évite les recalculs excessifs pendant le glissement de la fenêtre. La taille précédente est mémorisée (`_last_gallery_size`) pour ignorer les événements `<Configure>` découlant de l’insertion d’images.

```python
def _on_gallery_configure(self, event):
    new_size = (event.width, event.height)
    if new_size == self._last_gallery_size:
        return
    if self._resize_after_id is not None:
        self.root.after_cancel(self._resize_after_id)
    self._resize_after_id = self.root.after(150, self._on_gallery_resized)
```

**Résolution de conflit de noms**

```python
def _find_available_name(self, base, ext, *, ignore=""):
    for counter in range(1000, 10000):
        candidate = f"{base}{MAIN_SEPARATOR}{counter}{ext}"
        if candidate == ignore or not self.file_model.file_exists(candidate):
            return candidate
    return None  # Tous les compteurs épuisés
```

**Rechargement de dossier (drag & drop)**

La méthode `_reload_folder()` réinitialise complètement l’état :
1. Crée un nouveau `FileModel` avec le nouveau chemin.
2. Charge les fichiers (avertit si vide).
3. Crée un nouveau `TagModel` et construit les tags avec barre de progression.
4. Libère les références d’images (`_img_refs`).
5. Reconstruit les checkboxes et rafraîchit l’affichage.
6. Met à jour le titre de la fenêtre.

---

## Thème visuel

L’application utilise la palette **Catppuccin Mocha** :

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
1. gallery_tagger.py : argparse → validation du dossier
2. GalleryController(folder_path) :
   a. Création de FileModel, TagModel
   b. _init_window() → TkinterDnD.Tk(), titre, taille, maximize
   c. _load_files_or_warn() → scanne le dossier
   d. _build_tags_with_progress()
      ├─ LoadingView.show()
      ├─ TagModel.build(files, loading.update)
      └─ LoadingView.close()
   e. _build_view() → GalleryView(root, callbacks)
   f. _trace_new_name() → observe new_name_var
   g. _bind_shortcuts() → <Return>
   h. _bind_drop() → tkinterdnd2 DND_FILES
   i. root.after_idle(_initial_display)
      ├─ _display_current()
      ├─ view.build_tag_checkboxes()
      └─ _bind_gallery_resize()
   j. root.mainloop()
```

---

## Limites connues

- **Windows uniquement** pour l’ouverture dans l’Explorateur (`explorer /select`).
- **Pas de multi-threading** : le chargement des tags bloque l’interface (atténué par `update_idletasks` dans la barre de progression).
- **Plage de compteurs limitée** : 1000 – 9999 (10 000 noms uniques par base), valeurs codées en dur dans le contrôleur.
- **Pas de persistance** : les réglages et l’historique ne sont pas sauvegardés entre les sessions.
