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
    MAIN_SEPARATOR,
    TAG_CLOSE,
    TAG_OPEN,
    TAG_SEPARATOR,
    MIN_WIN_HEIGHT,
    MIN_WIN_WIDTH,
)
from utils import load_image_safe, parse_filename, resize_image_to_fit
from views.gallery_view import GalleryView

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
        self.display_current(file_controller)
        if self.view is not None:
            self.view.build_tag_checkboxes(file_controller.tag_dict())
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

        if self.root is not None:
            self._resize_after_id = self.root.after(
                150,
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
        self.display_current(file_controller)

    def display_current(self, file_controller: FileController) -> None:
        """Rafraichit les 3 panneaux d'image et les infos associees."""
        if self.view is None or self.root is None or not file_controller.has_files():
            return

        center_size = self._get_panel_size(self.view.center_label)
        side_size = self._get_panel_size(self.view.prev_label)

        if center_size[0] <= 1 or center_size[1] <= 1:
            self.root.after(50, lambda: self.display_current(file_controller))
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
        self.update_info_and_tags(file_controller)

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

        self.view.info_var.set(f"'{filename}'     -     {idx + 1} / {total}")
        _name, ext = os.path.splitext(filename)
        self.view.ext_label_var.set(ext)

        _ext, tags = parse_filename(filename)
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
        name_no_ext, _ = os.path.splitext(filename)

        open_delim = MAIN_SEPARATOR + TAG_OPEN
        open_idx = name_no_ext.find(open_delim)

        if open_idx != -1:
            left_part = name_no_ext[:open_idx].strip()
        else:
            parts = name_no_ext.rsplit(MAIN_SEPARATOR, 1)
            left_part = parts[0].strip()

        tag_part = TAG_SEPARATOR.join(selected)
        bracket_block = TAG_OPEN + tag_part + TAG_CLOSE

        if left_part:
            new_name = left_part + MAIN_SEPARATOR + bracket_block
        else:
            new_name = bracket_block

        self.view.new_name_var.set(new_name)

    def trace_new_name(self, file_controller: FileController) -> None:
        """Abonne le recalcul d'aperçu aux modifications du champ nom."""
        if self.view is None:
            return
        self.view.new_name_var.trace_add(
            "write",
            lambda *_: self.update_preview(file_controller),
        )

    def clear_preview_fields(self) -> None:
        """Vide les champs d'aperçu et de longueurs."""
        if self.view is None:
            return
        self.view.preview_var.set("")
        self.view.path_len_var.set("")
        self.view.filename_len_var.set("")

    def update_preview(self, file_controller: FileController) -> None:
        """Met a jour l'aperçu final et les indicateurs de longueurs."""
        if self.view is None:
            return

        if not file_controller.has_files():
            self.clear_preview_fields()
            return

        new_base = self.view.new_name_var.get().strip()
        if not new_base:
            self.clear_preview_fields()
            return

        old_filename = file_controller.current_filename()
        _, ext = os.path.splitext(old_filename)

        resolved = file_controller.find_available_name(new_base, ext, ignore=old_filename)
        self.view.preview_var.set(
            resolved or f"{new_base}{MAIN_SEPARATOR}1000{ext}  [conflit !]",
        )

        final_name = self.view.preview_var.get()
        full_path = os.path.join(file_controller.folder_path, final_name)
        self.view.path_len_var.set(str(len(full_path)))
        self.view.filename_len_var.set(str(len(final_name)))

    def get_new_name(self) -> str:
        """Retourne le contenu du champ `Nouveau nom`."""
        if self.view is None:
            return ""
        return self.view.new_name_var.get()

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
