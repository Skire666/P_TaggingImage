#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  ViewController — Sous-controleur de la vue
=============================================================================

Gere la fenetre Tk, la vue GalleryView et le rafraichissement graphique.
"""

from __future__ import annotations

import os
import tkinter as tk
from typing import Callable, Mapping, TYPE_CHECKING

from PIL import ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD

from constants import (
    BG_COLOR,
    GALLERY_RESIZE_DEBOUNCE_MS,
    TAG_CLOSE,
    TAG_OPEN,
    MIN_WIN_HEIGHT,
    MIN_WIN_WIDTH,
    TAG_SEPARATOR,
)

from controllers import file_controller
from utils import load_image_safe, resize_image_to_fit
from views.gallery_view import GalleryView
from tools.tag_tools import TagTools

if TYPE_CHECKING:
    from controllers.file_controller import FileController


class ViewController:
    """Sous-controleur dedie a la gestion de la vue Tkinter."""

    def __init__(self) -> None:
        """Initialise l'etat d'affichage et les references d'images."""
        self.root: TkinterDnD.Tk | None = None
        self.view: GalleryView | None = None
        self._img_refs: dict[str, ImageTk.PhotoImage | None] = {
            "prev": None,
            "center": None,
            "next": None,
        }
        self._resize_after_id: str | None = None
        self._last_gallery_size: tuple[int, int] = (0, 0)

    def init_window(self) -> None:
        """Cree et configure la fenetre principale TkinterDnD."""
        self.root = TkinterDnD.Tk()
        self.root.title("Gallery Tagger")
        self.root.configure(bg=BG_COLOR)
        self.root.minsize(MIN_WIN_WIDTH, MIN_WIN_HEIGHT)
        self.root.state("zoomed")

    def build_view(self, callbacks: Mapping[str, Callable[..., object]]) -> None:
        """Instancie la vue principale avec les callbacks applicatifs."""
        if self.root is None:
            raise RuntimeError("La fenetre doit etre initialisee avant la vue.")
        self.view = GalleryView(self.root, dict(callbacks))

    def bind_shortcuts(self, on_apply_rename: Callable[[], None]) -> None:
        """Attache les raccourcis clavier de la fenetre."""
        if self.root is None:
            return
        
        # touche "Entrée" pour appliquer le renommage
        self.root.bind("<Return>", lambda _: on_apply_rename())

    def bind_drop(self, on_drop: Callable[[tk.Event], None]) -> None:
        """Active le drag-and-drop de dossier sur la fenetre."""
        if self.root is None:
            return
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", on_drop)

    def schedule_initial_display(self, file_controller: FileController) -> None:
        """Planifie le premier rendu apres l'initialisation Tk."""
        if self.root is None:
            return
        self.root.after_idle(lambda: self._initial_display(file_controller))

    def _initial_display(self, file_controller: FileController) -> None:
        """Effectue le premier affichage et prepare le resize dynamique."""
        self.refresh_image_displayed(file_controller)
        if self.view is not None:
            self.view.build_tag_checkboxes(file_controller.tag_dict())
        self.update_info_and_tags(file_controller)
        self._bind_gallery_resize(file_controller)

    def _bind_gallery_resize(self, file_controller: FileController) -> None:
        """Attache le handler de redimensionnement de la galerie."""
        if self.view is None:
            return
        self.view.gallery_frame.bind(
            "<Configure>",
            lambda event: self._on_gallery_configure(event, file_controller),
        )

    def _on_gallery_configure(
        self,
        event: tk.Event,
        file_controller: FileController,
    ) -> None:
        """Gere les evenements `<Configure>` avec debounce."""
        new_size = (event.width, event.height)
        if new_size == self._last_gallery_size:
            return

        if self._resize_after_id is not None and self.root is not None:
            self.root.after_cancel(self._resize_after_id)

        # On utilise `after` pour attendre que le redimensionnement soit stabilise avant de rafraichir les images
        # afin d'eviter des recalculs trop frequents pendant le resize.
        if self.root is not None:
            self._resize_after_id = self.root.after(
                GALLERY_RESIZE_DEBOUNCE_MS,
                lambda: self._on_gallery_resized(file_controller),
            )

    def _on_gallery_resized(self, file_controller: FileController) -> None:
        """Rafraichit les images quand la taille est stabilisee."""
        if self.view is None:
            return
        self._resize_after_id = None
        w = self.view.gallery_frame.winfo_width()
        h = self.view.gallery_frame.winfo_height()
        self._last_gallery_size = (w, h)
        self.refresh_image_displayed(file_controller)

    def refresh_image_displayed(self, file_controller: FileController) -> None:
        """Rafraichit les 3 panneaux d'image"""
        if self.view is None or self.root is None or not file_controller.has_files():
            return

        center_size = self._get_panel_size(self.view.center_label)
        side_size = self._get_panel_size(self.view.prev_label)

        # Si les panneaux n'ont pas encore de taille valide (ex: juste apres creation), on reessaye un peu plus tard
        if center_size[0] <= 1 or center_size[1] <= 1:
            self.root.after(100, lambda: self.refresh_image_displayed(file_controller))
            return

        gf = self.view.gallery_frame
        self._last_gallery_size = (gf.winfo_width(), gf.winfo_height())

        idx = file_controller.current_index
        self._show_image("center", idx, self.view.center_label, center_size, file_controller)
        self._show_image(
            "prev",
            file_controller.prev_index(),
            self.view.prev_label,
            side_size,
            file_controller,
        )
        self._show_image(
            "next",
            file_controller.next_index(),
            self.view.next_label,
            side_size,
            file_controller,
        )

    def _get_panel_size(self, label: tk.Label) -> tuple[int, int]:
        """Retourne une taille minimale valide pour un panneau d'image."""
        w = label.winfo_width()
        h = label.winfo_height()
        return (max(w, 1), max(h, 1))

    def _show_image(
        self,
        key: str,
        index: int,
        label: tk.Label,
        max_size: tuple[int, int],
        file_controller: FileController,
    ) -> None:
        """Charge/redimensionne puis affiche une image dans un panneau."""
        if self.view is None:
            return

        filepath = file_controller.filepath_at(index)
        img = load_image_safe(filepath)

        if img:
            resized = resize_image_to_fit(img, *max_size)
            self._img_refs[key] = ImageTk.PhotoImage(resized)
            self.view.set_image(label, self._img_refs[key])
        else:
            self._img_refs[key] = None
            fallback = "[Image non chargeable]" if key == "center" else "[?]"
            self.view.set_image(label, None, fallback)

    def update_info_and_tags(self, file_controller: FileController) -> None:
        """Met a jour compteur, extension et etat des tags coches."""
        if self.view is None:
            return

        filename = file_controller.current_filename()
        total = file_controller.total()
        idx = file_controller.current_index
        
        counter_text = f" Image courante [ {idx + 1} / {total} ] "
        self.view.center_label.master["text"] = counter_text

        self.view.info_var.set(f"'{filename}'")
        ext = TagTools.get_extension(filename)
        self.view.ext_var.set(ext)

        tags = TagTools.get_list_tags(filename)
        tags_lower = {t.lower() for t in tags}
        for tag, var in self.view.check_vars.items():
            var.set(tag in tags_lower)

        self.update_new_name(file_controller)

    def on_tag_toggled(self, file_controller: FileController) -> None:
        """Callback appele quand un tag est coche/decoché."""
        self.update_new_name(file_controller)

    def update_new_name(self, file_controller: FileController) -> None:
        """Compose le nom cible `base - [tags]` depuis l'etat de la vue."""
        if self.view is None or not file_controller.has_files():
            return

        selected = sorted(
            [tag for tag, var in self.view.check_vars.items() if var.get()],
        )

        filename = file_controller.current_filename()

        base_name = TagTools.get_base_name(filename)
        self.view.base_name_var.set(base_name)

        tag_part = TAG_SEPARATOR.join(selected)
        self.view.tags_var.set(tag_part)

        counter = TagTools.get_counter(filename)
        self.view.counter_var.set(str(counter))

    def trace_new_name(self, file_controller: FileController) -> None:
        """Abonne le recalcul d'aperçu aux modifications du champ nom."""
        if self.view is None:
            return
        self.view.base_name_var.trace_add(
            "write",
            lambda *_: self.update_preview(file_controller),
        )
        self.view.tags_var.trace_add(
            "write",
            lambda *_: self.update_preview(file_controller),
        )

    def clear_preview_fields(self) -> None:
        """Vide les champs d'aperçu et de longueurs."""
        if self.view is None:
            return
        self.view.path_len_var.set("")
        self.view.filename_len_var.set("")

    def update_preview(self, file_controller: FileController) -> None:
        """Met a jour l'aperçu final et les indicateurs de longueurs."""
        if self.view is None:
            return

        if not file_controller.has_files():
            self.clear_preview_fields()
            return

        new_base = self.get_new_name()
        if not new_base:
            self.clear_preview_fields()
            return

        full_path = os.path.join(file_controller.folder_path, new_base)
        self.view.path_len_var.set(str(len(full_path)))
        self.view.filename_len_var.set(str(len(new_base)))

    def get_new_name(self) -> str:
        """Retourne le nom complet généré à partir des différents champs."""
        if self.view is None:
            return ""
            
        base_name = self.view.base_name_var.get()
        tags = self.view.tags_var.get().strip().lower()
        counter = self.view.counter_var.get()
        ext = self.view.ext_var.get()

        if not tags:
            bracket_block = f"{TAG_OPEN}{TAG_CLOSE}"
        else:
            bracket_block = f"{TAG_OPEN}{tags}{TAG_CLOSE}"

        return f"{base_name}{bracket_block}{counter}{ext}";

    def rebuild_tag_checkboxes(self, file_controller: FileController) -> None:
        """Reconstruit la liste des checkboxes a partir des tags agreges."""
        if self.view is None:
            return
        self.view.build_tag_checkboxes(file_controller.tag_dict())

    def reset_image_refs(self) -> None:
        """Reinitialise les references d'images pour liberer la memoire."""
        self._img_refs = {"prev": None, "center": None, "next": None}

    def set_window_title_for_folder(self, folder_path: str) -> None:
        """Met a jour le titre de fenetre avec le dossier actif."""
        if self.root is None:
            return
        self.root.title(f"Gallery Tagger — {os.path.basename(folder_path)}")
