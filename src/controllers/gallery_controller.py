#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  GalleryController — Contrôleur principal de la galerie
=============================================================================

Orchestre les interactions entre les modèles (FileModel, TagModel)
et les vues (LoadingView, GalleryView). Gère la navigation, le
renommage, l'affichage des images et les raccourcis clavier.

Example:
    >>> GalleryController("C:/images")
    # Lance la fenêtre Tk et la boucle événementielle.
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import messagebox

from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import ImageTk

from constants import (
    BG_COLOR, HIGHLIGHT, MAIN_SEPARATOR, TAG_OPEN, TAG_CLOSE, TAG_SEPARATOR,
    MIN_WIN_WIDTH, MIN_WIN_HEIGHT, MAX_PATH_LEN, MAX_FILENAME_LEN,
)
from utils import (
    parse_filename, load_image_safe, resize_image_to_fit, open_in_explorer,
)
from models.file_model import FileModel
from models.tag_model import TagModel
from views.loading_view import LoadingView
from views.gallery_view import GalleryView


class GalleryController:
    """
    Contrôleur principal reliant modèles et vue.

    Attributes:
        file_model: Modèle de gestion des fichiers images.
        tag_model:  Modèle de gestion des tags.
        view:       Vue principale de la galerie.
        root:       Fenêtre Tk racine.

    Example:
        >>> GalleryController("C:/images")
    """

    # -----------------------------------------------------------------
    #  Initialisation
    # -----------------------------------------------------------------

    def __init__(self, folder_path: str) -> None:
        """
        Initialise et lance l'application Gallery Tagger.

        Orchestre séquentiellement : création des modèles, de la fenêtre
        Tk, chargement des fichiers, construction du dictionnaire de
        tags, construction de la vue, affichage initial et lancement
        de la boucle événementielle.

        Args:
            folder_path: Chemin (relatif ou absolu) vers le dossier
                         contenant les images à parcourir.

        Example:
            >>> GalleryController("C:/mes_images")
        """
        self.file_model = FileModel(folder_path)
        self.tag_model = TagModel()
        self._img_refs: dict[str, ImageTk.PhotoImage | None] = {
            "prev": None, "center": None, "next": None,
        }
        self._resize_after_id: str | None = None
        self._last_gallery_size: tuple[int, int] = (0, 0)

        self._init_window()
        if not self._load_files_or_warn():
            return

        self._build_tags_with_progress()
        self._build_view()
        self._trace_new_name()
        self._bind_shortcuts()
        self._bind_drop()
        # Déférer le premier affichage après le rendu initial
        self.root.after_idle(self._initial_display)
        self.root.mainloop()

    def _init_window(self) -> None:
        """
        Crée et configure la fenêtre Tk principale.

        Définit le titre, la couleur de fond, la taille minimale
        (1100x700) et maximise la fenêtre au démarrage.

        Example:
            >>> self._init_window()
            >>> self.root.title()
            'Gallery Tagger'
        """
        self.root = TkinterDnD.Tk()
        self.root.title("Gallery Tagger")
        self.root.configure(bg=BG_COLOR)
        self.root.minsize(MIN_WIN_WIDTH, MIN_WIN_HEIGHT)
        self.root.state("zoomed")

    def _load_files_or_warn(self) -> bool:
        """
        Charge les fichiers images et avertit si le dossier est vide.

        Returns:
            bool: True si des images ont été trouvées, False sinon.

        Example:
            >>> if not self._load_files_or_warn():
            ...     return
        """
        try:
            self.file_model.load_files()
        except OSError as exc:
            messagebox.showerror("Erreur", f"Impossible de lire le dossier :\n{exc}")
            self.root.destroy()
            return False

        if self.file_model.has_files():
            return True

        messagebox.showwarning(
            "Aucune image",
            f"Aucun fichier image trouvé dans :\n{self.file_model.folder_path}",
        )
        return True

    def _build_tags_with_progress(self) -> None:
        """
        Construit le dictionnaire de tags avec barre de progression.

        Crée un LoadingView, lance tag_model.build() en lui passant
        le callback, puis ferme l'écran de chargement.

        Example:
            >>> self._build_tags_with_progress()
        """
        loading = LoadingView(self.root, self.file_model.total())
        self.tag_model.build(self.file_model.file_list, loading.update)
        loading.close()

    def _build_view(self) -> None:
        """
        Instancie la vue principale avec les callbacks du contrôleur.

        Passe le dictionnaire de tags et un dictionnaire de callbacks
        à GalleryView pour que les boutons et checkboxes appellent
        les méthodes du contrôleur.

        Example:
            >>> self._build_view()
            >>> self.view.info_var.get()
            ''
        """
        callbacks = {
            "go_previous": self.go_previous,
            "go_next": self.go_next,
            "go_next_untagged": self.go_next_untagged,
            "apply_rename": self.apply_rename,
            "open_explorer": self.open_explorer,
            "on_tag_toggled": self._on_tag_toggled,
        }
        self.view = GalleryView(self.root, callbacks)

    def _bind_shortcuts(self) -> None:
        """
        Attache les raccourcis clavier à la fenêtre principale.

        Raccourcis :
            - Entrée         → appliquer le renommage

        Example:
            >>> self._bind_shortcuts()
        """
        self.root.bind("<Return>", lambda _: self.apply_rename())

    # -----------------------------------------------------------------
    #  Affichage
    # -----------------------------------------------------------------

    def _initial_display(self) -> None:
        """
        Premier affichage : charge l'image puis alimente les tags.

        Appelé une seule fois après le rendu initial. Affiche l'image
        courante puis construit les checkboxes (le canvas a alors ses
        dimensions réelles), puis active le suivi du redimensionnement.
        """
        self._display_current()
        self.view.build_tag_checkboxes(self.tag_model.tag_dict)
        self._bind_gallery_resize()

    # -----------------------------------------------------------------
    #  Redimensionnement de la galerie
    # -----------------------------------------------------------------

    def _bind_gallery_resize(self) -> None:
        """
        Écoute les changements de taille du cadre galerie.

        Utilise un timer debounce pour éviter de recharger les images
        à chaque pixel de déplacement et compare la taille réelle
        pour ne déclencher qu'en cas de changement effectif.
        """
        self.view.gallery_frame.bind("<Configure>", self._on_gallery_configure)

    def _on_gallery_configure(self, event: tk.Event) -> None:
        """
        Handler <Configure> avec debounce de 150 ms.

        Annule tout timer en attente et en programme un nouveau.
        Ne déclenche le rechargement que si la taille a réellement
        changé (évite la boucle infinie image → configure → image).
        """
        new_size = (event.width, event.height)
        if new_size == self._last_gallery_size:
            return

        if self._resize_after_id is not None:
            self.root.after_cancel(self._resize_after_id)

        self._resize_after_id = self.root.after(150, self._on_gallery_resized)

    def _on_gallery_resized(self) -> None:
        """
        Recharge les images après un redimensionnement stabilisé.

        Met à jour `_last_gallery_size` avant le rechargement afin
        que le <Configure> découlant du changement d'image soit ignoré.
        """
        self._resize_after_id = None
        w = self.view.gallery_frame.winfo_width()
        h = self.view.gallery_frame.winfo_height()
        self._last_gallery_size = (w, h)
        self._display_current()

    def _get_panel_size(self, label: tk.Label) -> tuple[int, int]:
        """
        Retourne la taille disponible d'un panneau d'image.

        Args:
            label: Widget tk.Label dont on mesure le parent.

        Returns:
            tuple[int, int]: (largeur, hauteur) disponibles en pixels.
                             Retourne (1, 1) si le widget n'est pas
                             encore affiché.
        """
        w = label.winfo_width()
        h = label.winfo_height()
        return (max(w, 1), max(h, 1))

    def _display_current(self) -> None:
        """
        Rafraîchit l'affichage complet de la galerie.

        Calcule dynamiquement la taille maximale de chaque image
        à partir des dimensions réelles des panneaux, puis met à jour
        les 3 images, la barre d'info et les cases à cocher.

        Example:
            >>> self._display_current()
        """
        if not self.file_model.has_files():
            return

        center_size = self._get_panel_size(self.view.center_label)
        side_size = self._get_panel_size(self.view.prev_label)

        # Panneaux pas encore rendus — reprogrammer après le cycle idle
        if center_size[0] <= 1 or center_size[1] <= 1:
            self.root.after(50, self._display_current)
            return

        # Mémoriser la taille *avant* d'insérer les images pour
        # que le <Configure> qui en découle soit ignoré.
        gf = self.view.gallery_frame
        self._last_gallery_size = (gf.winfo_width(), gf.winfo_height())

        idx = self.file_model.current_index
        self._show_image("center", idx, self.view.center_label, center_size)
        self._show_image("prev", self.file_model.prev_index(),
                         self.view.prev_label, side_size)
        self._show_image("next", self.file_model.next_index(),
                         self.view.next_label, side_size)
        self._update_info_and_tags()

    def _show_image(
        self, key: str, index: int,
        label: tk.Label, max_size: tuple[int, int],
    ) -> None:
        """
        Charge, redimensionne et affiche une image dans un label.

        Stocke la référence PhotoImage dans self._img_refs[key]
        pour empêcher le garbage collection.

        Args:
            key:      Clé dans _img_refs ("prev", "center" ou "next").
            index:    Index du fichier dans file_list.
            label:    Widget tk.Label cible.
            max_size: Tuple (largeur_max, hauteur_max).

        Example:
            >>> self._show_image("center", 0, self.view.center_label, (700, 550))
        """
        filepath = self.file_model.filepath_at(index)
        img = load_image_safe(filepath)

        if img:
            resized = resize_image_to_fit(img, *max_size)
            self._img_refs[key] = ImageTk.PhotoImage(resized)
            self.view.set_image(label, self._img_refs[key])
        else:
            self._img_refs[key] = None
            fallback = "[Image non chargeable]" if key == "center" else "[?]"
            self.view.set_image(label, None, fallback)

    def _update_info_and_tags(self) -> None:
        """
        Met à jour le compteur, l'extension et les cases à cocher.

        Synchronise la barre d'info, affiche l'extension, pré-coche
        les tags présents dans le nom du fichier et met à jour le
        champ de renommage.

        Example:
            >>> self._update_info_and_tags()
        """
        filename = self.file_model.current_filename()
        total = self.file_model.total()
        idx = self.file_model.current_index

        self.view.info_var.set(f"'{filename}'     -     {idx + 1} / {total}")
        _name, ext = os.path.splitext(filename)
        self.view.ext_label_var.set(ext)

        _ext, tags = parse_filename(filename)
        tags_lower = {t.lower() for t in tags}
        for tag, var in self.view.check_vars.items():
            var.set(tag in tags_lower)

        self._update_new_name()

    # -----------------------------------------------------------------
    #  Tags
    # -----------------------------------------------------------------

    def _on_tag_toggled(self) -> None:
        """
        Callback déclenché quand une case à cocher est cochée/décochée.

        Recompose le futur nom du fichier dans le champ de saisie.

        Example:
            >>> self._on_tag_toggled()
        """
        self._update_new_name()

    def _update_new_name(self) -> None:
        """
        Compose le futur nom de fichier à partir des tags cochés.

        Format produit : ``base - [tag1, tag2, tag3]``.
        Le compteur (``- 100``) est ajouté automatiquement lors de
        l'aperçu et du renommage effectif.

        La partie gauche (base) est conservée depuis le nom actuel.

        Example:
            >>> self._update_new_name()
            >>> self.view.new_name_var.get()
            'base - [chat, noir]'
        """
        selected = sorted(
            [tag for tag, var in self.view.check_vars.items() if var.get()],
        )

        # Extraire la partie « base » (gauche) du nom actuel
        filename = self.file_model.current_filename()
        name_no_ext, _ = os.path.splitext(filename)

        open_delim = MAIN_SEPARATOR + TAG_OPEN
        open_idx = name_no_ext.find(open_delim)

        if open_idx != -1:
            left_part = name_no_ext[:open_idx].strip()
        else:
            # Pas de crochets : tout avant le dernier MAIN_SEPARATOR est la base
            parts = name_no_ext.rsplit(MAIN_SEPARATOR, 1)
            left_part = parts[0].strip()

        tag_part = TAG_SEPARATOR.join(selected)
        bracket_block = TAG_OPEN + tag_part + TAG_CLOSE
        # Recomposer : base - [tags]  (sans compteur)
        if left_part:
            new_name = left_part + MAIN_SEPARATOR + bracket_block
        else:
            new_name = bracket_block

        self.view.new_name_var.set(new_name)

    def _trace_new_name(self) -> None:
        """
        Attache un observateur sur new_name_var pour mettre à jour l'aperçu.

        Garantit que l'aperçu du nom final se rafraîchit aussi lors
        d'une saisie manuelle dans le champ de texte.

        Example:
            >>> self._trace_new_name()
        """
        self.view.new_name_var.trace_add("write", lambda *_: self._update_preview())

    def _clear_preview_fields(self) -> None:
        """Réinitialise les champs d'aperçu et de longueurs."""
        self.view.preview_var.set("")
        self.view.path_len_var.set("")
        self.view.filename_len_var.set("")

    def _find_available_name(
        self, base: str, ext: str, *, ignore: str = "",
    ) -> str | None:
        """
        Cherche un nom disponible ``base - <compteur>.ext``.

        Itère le compteur de 1000 à 9999. Un nom identique à *ignore*
        est considéré comme disponible (utilisé pour l'aperçu quand
        le fichier courant porte déjà ce nom).

        Args:
            base:   Partie du nom avant le compteur.
            ext:    Extension avec le point. Ex: ".png"
            ignore: Nom de fichier à ne pas considérer comme conflit.

        Returns:
            str | None: Premier nom libre, ou None si tous pris.
        """
        for counter in range(1000, 10000):
            candidate = f"{base}{MAIN_SEPARATOR}{counter}{ext}"
            if candidate == ignore or not self.file_model.file_exists(candidate):
                return candidate
        return None

    def _update_preview(self) -> None:
        """
        Met à jour le label d'aperçu avec le nom de fichier final.

        Compose le nom complet ``base - 1000.ext`` et incrémente le
        compteur (1001, 1002…) si le nom est déjà pris.

        Example:
            >>> self._update_preview()
            >>> self.view.preview_var.get()
            'base - [chat, noir] - 1000.png'
        """
        if not self.file_model.has_files():
            self._clear_preview_fields()
            return

        new_base = self.view.new_name_var.get().strip()
        if not new_base:
            self._clear_preview_fields()
            return

        old_filename = self.file_model.current_filename()
        _, ext = os.path.splitext(old_filename)

        resolved = self._find_available_name(new_base, ext, ignore=old_filename)
        self.view.preview_var.set(
            resolved or f"{new_base}{MAIN_SEPARATOR}1000{ext}  [conflit !]"
        )

        # Mise à jour des longueurs
        final_name = self.view.preview_var.get()
        full_path = os.path.join(self.file_model.folder_path, final_name)
        self.view.path_len_var.set(str(len(full_path)))
        self.view.filename_len_var.set(str(len(final_name)))

    # -----------------------------------------------------------------
    #  Renommage
    # -----------------------------------------------------------------

    def apply_rename(self) -> None:
        """
        Orchestre la validation et le renommage du fichier courant.

        Séquence : construction du nom → validation → exécution.

        Example:
            >>> self.view.new_name_var.set("nouveau nom")
            >>> self.apply_rename()
        """
        if not self.file_model.has_files():
            return

        old_filename = self.file_model.current_filename()
        new_filename = self._build_new_filename(old_filename)

        if not new_filename:
            return
        if not self._validate_rename(old_filename, new_filename):
            return

        new_filename = self._resolve_conflict(new_filename, old_filename)
        if not new_filename:
            return

        full_path = os.path.join(self.file_model.folder_path, new_filename)
        if not self._check_length(
            full_path, MAX_PATH_LEN, "Chemin trop long", "Le chemin final",
        ):
            return

        if not self._check_length(
            new_filename, MAX_FILENAME_LEN,
            "Nom de fichier trop long", "Le nom du fichier",
        ):
            return

        self._perform_rename(old_filename, new_filename)

    def _build_new_filename(self, old_filename: str) -> str | None:
        """
        Construit le nouveau nom complet (base - compteur.ext).

        Le compteur commence à 1000 et est incrémenté jusqu'à trouver
        un nom disponible.

        Args:
            old_filename: Nom actuel du fichier. Ex: "base - [chat] - 1000.png"

        Returns:
            str | None: Nouveau nom complet, ou None si vide.

        Example:
            >>> self.view.new_name_var.set("base - [chat, noir]")
            >>> self._build_new_filename("base - [chat] - 1000.png")
            'base - [chat, noir] - 1000.png'
        """
        new_base = self.view.new_name_var.get().strip()
        if not new_base:
            messagebox.showwarning("Nom vide", "Le nouveau nom ne peut pas être vide.")
            return None
        _, ext = os.path.splitext(old_filename)
        return f"{new_base}{MAIN_SEPARATOR}1000{ext}"

    def _validate_rename(self, old_filename: str, new_filename: str) -> bool:
        """
        Vérifie que le renommage est valide.

        Contrôle : le nom proposé doit différer de l'original.

        Args:
            old_filename: Nom actuel. Ex: "chat noir.png"
            new_filename: Nom proposé. Ex: "chat blanc.png"

        Returns:
            bool: True si le renommage est autorisé.

        Example:
            >>> self._validate_rename("a.png", "b.png")
            True
        """
        if old_filename == new_filename:
            messagebox.showinfo("Aucun changement", "Le nom est identique.")
            return False
        return True

    def _resolve_conflict(self, new_filename: str, old_filename: str) -> str | None:
        """
        Résout les conflits de noms en incrémentant le compteur.

        Le nom reçu se termine par ``- 1000.ext``. Si ce nom existe
        déjà, le compteur est incrémenté (1001, 1002…) jusqu'à
        trouver un nom libre.

        Args:
            new_filename: Nom souhaité. Ex: ``"base - [tags] - 1000.png"``
            old_filename: Nom actuel (à ignorer dans le test d'existence).

        Returns:
            str | None: Nom disponible, ou None si épuisé.

        Example:
            >>> self._resolve_conflict("a - [t] - 1000.png", "old.png")
            'a - [t] - 1000.png'    # si libre
            >>> self._resolve_conflict("a - [t] - 1000.png", "old.png")
            'a - [t] - 1001.png'    # si 1000 déjà pris
        """
        if not self.file_model.file_exists(new_filename):
            return new_filename

        # Extraire la base (avant le dernier MAIN_SEPARATOR + compteur)
        base_no_ext, ext = os.path.splitext(new_filename)
        last_sep_idx = base_no_ext.rfind(MAIN_SEPARATOR)
        base_prefix = base_no_ext[:last_sep_idx] if last_sep_idx != -1 else base_no_ext

        resolved = self._find_available_name(base_prefix, ext)
        if resolved:
            return resolved

        messagebox.showerror(
            "Conflit",
            f"Impossible de trouver un nom disponible :\n"
            f"{base_prefix}{MAIN_SEPARATOR}[1000-9999]{ext} sont tous pris.",
        )
        return None

    def _check_length(
        self, text: str, max_len: int, title: str, label: str,
    ) -> bool:
        """
        Vérifie si *text* dépasse *max_len* caractères.

        Si c'est le cas, affiche un avertissement et demande
        confirmation à l'utilisateur via messagebox.

        Args:
            text:    Chaîne dont la longueur est vérifiée.
            max_len: Seuil d'avertissement.
            title:   Titre de la messagebox.
            label:   Libellé décrivant ce qui est mesuré.

        Returns:
            bool: True si on peut continuer, False si l'utilisateur annule.
        """
        length = len(text)
        if length > max_len:
            return messagebox.askyesno(
                title,
                f"{label} fait {length} caractères "
                f"(limite recommandée : {max_len}).\n\n"
                f"{text}\n\n"
                f"Continuer malgré tout ?",
            )
        return True

    def _perform_rename(self, old_filename: str, new_filename: str) -> None:
        """
        Exécute le renommage sur disque et rafraîchit l'interface.

        Appelle file_model.rename_current(), reconstruit le dictionnaire
        de tags, rafraîchit les checkboxes et l'affichage, puis
        affiche une messagebox de succès.

        Args:
            old_filename: Nom actuel. Ex: "chat noir.png"
            new_filename: Nouveau nom. Ex: "chat blanc.png"

        Example:
            >>> self._perform_rename("chat noir.png", "chat blanc.png")
        """
        try:
            self.file_model.rename_current(new_filename)
        except OSError as exc:
            messagebox.showerror("Erreur", f"Renommage impossible :\n{exc}")
            return

        self.tag_model.rebuild(self.file_model.file_list)
        self.view.build_tag_checkboxes(self.tag_model.tag_dict)
        self._display_current()
        messagebox.showinfo("Succès", f"{old_filename}\n→\n{new_filename}")

    # -----------------------------------------------------------------
    #  Navigation
    # -----------------------------------------------------------------

    def go_next(self) -> None:
        """
        Passe à l'image suivante (cyclique) et rafraîchit l'affichage.

        Example:
            >>> self.go_next()
        """
        if not self.file_model.has_files():
            return
        self.file_model.go_next()
        self._display_current()

    def go_previous(self) -> None:
        """
        Passe à l'image précédente (cyclique) et rafraîchit l'affichage.

        Example:
            >>> self.go_previous()
        """
        if not self.file_model.has_files():
            return
        self.file_model.go_previous()
        self._display_current()

    def go_next_untagged(self) -> None:
        """
        Navigue vers le prochain fichier non conforme au format taggué.

        Cherche dans la liste des fichiers le prochain dont le nom
        ne respecte pas ``base - [tags] - compteur.ext``. Si trouvé,
        l'affiche ; sinon, affiche un message informatif.

        Example:
            >>> self.go_next_untagged()
        """
        if not self.file_model.has_files():
            return
        idx = self.file_model.find_next_untagged()
        if idx is not None:
            self.file_model.current_index = idx
            self._display_current()
        else:
            messagebox.showinfo(
                "Tous taggués",
                "Tous les fichiers sont déjà conformes au format\n"
                "'base - [tags] - compteur.ext'.\n\n"
                "Il n'y a plus de fichier à tagguer.",
            )

    # -----------------------------------------------------------------
    #  Explorateur
    # -----------------------------------------------------------------

    def open_explorer(self) -> None:
        """
        Ouvre l'explorateur Windows sur le fichier courant.

        Example:
            >>> self.open_explorer()
        """
        if not self.file_model.has_files():
            return
        open_in_explorer(self.file_model.current_filepath())

    # -----------------------------------------------------------------
    #  Drag-and-drop de dossier
    # -----------------------------------------------------------------

    def _bind_drop(self) -> None:
        """
        Active le drag-and-drop de dossier depuis l'explorateur Windows.

        Utilise tkinterdnd2 pour intercepter les fichiers/dossiers
        déposés sur la fenêtre principale.

        Example:
            >>> self._bind_drop()
        """
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self._on_drop)

    def _on_drop(self, event: tk.Event) -> None:
        """
        Callback déclenché lors d'un drag-and-drop sur la fenêtre.

        Valide que l'élément déposé est un dossier existant, puis
        nettoie l'état courant et charge le nouveau dossier.

        Args:
            event: Événement TkinterDnD contenant event.data
                   (chemins déposés).

        Example:
            >>> # Drop d'un dossier depuis l'explorateur Windows
        """
        raw = event.data
        if not raw:
            return

        # tkinterdnd2 entoure les chemins avec espaces par des accolades
        # Ex: "{C:/mon dossier}" ou "C:/images"
        if raw.startswith("{"):
            folder_path = raw.strip("{}").split("}")[0]
        else:
            folder_path = raw.split()[0]

        if not os.path.isdir(folder_path):
            messagebox.showwarning(
                "Pas un dossier",
                f"L'élément déposé n'est pas un dossier :\n{folder_path}",
            )
            return

        self._reload_folder(folder_path)

    def _reload_folder(self, folder_path: str) -> None:
        """
        Nettoie l'état courant et charge un nouveau dossier.

        Séquence :
        1. Réinitialise le FileModel avec le nouveau chemin.
        2. Charge les fichiers (avertit si vide).
        3. Reconstruit le dictionnaire de tags avec barre de progression.
        4. Réinitialise les références d'images.
        5. Reconstruit les checkboxes et rafraîchit l'affichage.
        6. Met à jour le titre de la fenêtre.

        Args:
            folder_path: Chemin absolu vers le nouveau dossier.

        Example:
            >>> self._reload_folder("C:/nouveau_dossier")
        """
        # 1. Réinitialiser le modèle de fichiers
        self.file_model = FileModel(folder_path)

        # 2. Charger les fichiers
        try:
            self.file_model.load_files()
        except OSError as exc:
            messagebox.showerror(
                "Erreur", f"Impossible de lire le dossier :\n{exc}",
            )
            return

        if not self.file_model.has_files():
            messagebox.showwarning(
                "Aucune image",
                f"Aucun fichier image trouvé dans :\n{self.file_model.folder_path}",
            )
            return

        # 3. Reconstruire les tags avec barre de progression
        self.tag_model = TagModel()
        self._build_tags_with_progress()

        # 4. Nettoyer les références d'images (libérer la mémoire)
        self._img_refs = {"prev": None, "center": None, "next": None}

        # 5. Reconstruire les checkboxes et rafraîchir l'affichage
        self.view.build_tag_checkboxes(self.tag_model.tag_dict)
        self._display_current()

        # 6. Mettre à jour le titre
        self.root.title(f"Gallery Tagger — {os.path.basename(folder_path)}")
