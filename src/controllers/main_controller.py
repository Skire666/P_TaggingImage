#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
    MainController — Controleur global
=============================================================================

Orchestre les sous-controleurs :
- ConfigController : configuration persistante
- FileController   : gestion fichiers/tags
- ViewController   : gestion vue/rendu
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import messagebox

from constants import TAG_CLOSE, TAG_OPEN
from controllers.config_controller import ConfigController
from controllers.file_controller import FileController
from controllers.view_controller import ViewController
from utils import open_in_explorer
from views.loading_view import LoadingView
from tools.tag_tools import TagTools


class MainController:
    """Controleur global qui coordonne les sous-controleurs.

    Responsibilities:
        - Initialiser les sous-controleurs.
        - Connecter les callbacks de la vue.
        - Orchestrer navigation, renommage et rechargement de dossier.
    """

    def __init__(self, folder_path: str | None = None) -> None:
        """Initialise l'application et lance la boucle Tk principale.

        Args:
            folder_path: Dossier optionnel passe en CLI.
        """
        self.config_controller = ConfigController()
        self.max_path_len = self.config_controller.get_max_path_len()
        self.max_filename_len = self.config_controller.get_max_filename_len()
        start_folder = FileController.resolve_start_folder(
            folder_path,
            self.config_controller,
        )

        self.file_controller = FileController(start_folder)
        self.view_controller = ViewController()

        self.view_controller.init_window()
        if not self._load_files_or_warn():
            return

        self._build_tags_with_progress()
        self._build_view()
        self.view_controller.trace_new_name(self.file_controller)
        self.view_controller.bind_shortcuts(self.apply_rename)
        self.view_controller.bind_drop(self._on_drop)
        self.view_controller.schedule_initial_display(self.file_controller)

        if self.view_controller.root is not None:
            self.view_controller.root.mainloop()

    def _build_view(self) -> None:
        """Construit la vue en injectant les callbacks applicatifs."""
        callbacks = {
            "go_previous": self.go_previous,
            "go_next": self.go_next,
            "go_next_untagged": self.go_next_untagged,
            "apply_rename": self.apply_rename,
            "open_explorer": self.open_explorer,
            "reload_current_folder": self.reload_current_folder,
            "on_tag_toggled": lambda: self.view_controller.on_tag_toggled(
                self.file_controller,
            ),
        }
        self.view_controller.build_view(callbacks)

    def _load_files_or_warn(self) -> bool:
        """Charge la liste d'images et affiche un message si besoin.

        Returns:
            `True` si l'initialisation peut continuer, `False` sinon.
        """
        return self._load_current_folder_or_warn(allow_empty=True)

    def _load_current_folder_or_warn(self, *, allow_empty: bool) -> bool:
        """Charge le dossier courant et gere les erreurs/warnings.

        Args:
            allow_empty: Si `True`, un dossier sans image n'interrompt pas
                le flux appelant. Si `False`, le flux est interrompu.

        Returns:
            bool: `True` si le flux appelant peut continuer, sinon `False`.
        """
        try:
            self.file_controller.load_files()
        except OSError as exc:
            messagebox.showerror("Erreur", f"Impossible de lire le dossier :\n{exc}")
            if self.view_controller.root is not None:
                self.view_controller.root.destroy()
            return False

        if self.file_controller.has_files():
            return True

        messagebox.showwarning(
            "Aucune image",
            f"Aucun fichier image trouve dans :\n{self.file_controller.folder_path}",
        )
        return allow_empty

    def _build_tags_with_progress(self) -> None:
        """Construit les tags avec barre de progression modale."""
        if self.view_controller.root is None:
            return
        loading = LoadingView(self.view_controller.root, self.file_controller.total())
        self.file_controller.build_tags(loading.update)
        loading.close()

    def apply_rename(self) -> None:
        """Execute le pipeline complet de renommage du fichier courant."""
        if not self.file_controller.has_files():
            return

        old_filename = self.file_controller.current_filename()
        new_filename = self._build_new_filename(old_filename)

        if not new_filename:
            return
        if not self._validate_rename(old_filename, new_filename):
            return

        new_filename = self._resolve_conflict(new_filename)
        if not new_filename:
            return

        full_path = self.file_controller.full_path_for(new_filename)
        if not self._check_length(
            full_path,
            self.max_path_len,
            "Chemin trop long",
            "Le chemin final",
        ):
            return

        if not self._check_length(
            new_filename,
            self.max_filename_len,
            "Nom de fichier trop long",
            "Le nom du fichier",
        ):
            return

        self._perform_rename(old_filename, new_filename)

    def _build_new_filename(self, old_filename: str) -> str | None:
        """
        Construit un nom initial `base - 1000.ext` depuis le champ de la vue.

        Args:
            old_filename: Le nom actuel du fichier, utilise pour conserver l'extension.

        Returns:
            str | None: Le nouveau nom compose ou None si le champ est vide.
        """
        new_base = self.view_controller.get_new_name().strip()
        if not new_base:
            messagebox.showwarning("Nom vide", "Le nouveau nom ne peut pas etre vide.")
            return None

        return new_base

    def _validate_rename(self, old_filename: str, new_filename: str) -> bool:
        """
        Valide que le renommage modifie effectivement le nom.

        Args:
            old_filename: Le nom de fichier actuel.
            new_filename: Le nouveau nom de fichier propose.

        Returns:
            bool: True si le nom est different et valide, False sinon.
        """
        if old_filename == new_filename:
            messagebox.showinfo("Aucun changement", "Le nom est identique.")
            return False
        return True

    def _resolve_conflict(self, new_filename: str) -> str | None:
        """
        Resout les collisions de nom via incrementation du compteur.

        Args:
            new_filename: Le nom de fichier souhaite.

        Returns:
            str | None: Le nom de fichier avec un compteur unique ou None
                        si aucun nom n'est disponible.
        """
        if not self.file_controller.file_exists(new_filename):
            return new_filename

        base_name = TagTools.get_base_name(new_filename)
        tags_str = TagTools.get_tags_from_filename(new_filename)
        extension = TagTools.get_extension(new_filename)

        resolved = self.file_controller.find_available_name(base_name, tags_str, extension)
        if resolved:
            return resolved

        messagebox.showerror(
            "Conflit",
            "Impossible de trouver un nom disponible :\n"
            f"{base_name}{TAG_OPEN}{tags_str}{TAG_CLOSE}[1000-9999]{extension} sont tous pris.",
        )
        return None

    def _check_length(self, text: str, max_len: int, title: str, label: str) -> bool:
        """
        Verifie une longueur et demande confirmation en cas de depassement.

        Args:
            text: La chaine a verifier (nom de fichier ou chemin).
            max_len: La longueur maximale autorisee.
            title: Le titre de la boite de dialogue d'avertissement.
            label: Le label de l'element verifie a afficher.

        Returns:
            bool: True si la longueur est correcte ou si l'utilisateur confirme, False sinon.
        """
        length = len(text)
        if length > max_len:
            return messagebox.askyesno(
                title,
                f"{label} fait {length} caracteres "
                f"(limite recommandee : {max_len}).\n\n"
                f"{text}\n\n"
                "Continuer malgre tout ?",
            )
        return True

    def _perform_rename(self, old_filename: str, new_filename: str) -> None:
        """
        Applique le renommage sur le disque et rafraichit l'interface.

        Args:
            old_filename: L'ancien nom du fichier.
            new_filename: Le nouveau nom de fichier a appliquer.

        Raises:
            OSError: Intercepte en interne si le renommage echoue, affiche une erreur.
        """
        try:
            self.file_controller.rename_current(new_filename)
        except OSError as exc:
            messagebox.showerror("Erreur", f"Renommage impossible :\n{exc}")
            return

        self.file_controller.build_tags()
        self.view_controller.rebuild_tag_checkboxes(self.file_controller)
        self.view_controller.display_current(self.file_controller)
        messagebox.showinfo("Succes", f"{old_filename}\n->\n{new_filename}")

    def go_next(self) -> None:
        """
        Navigue vers l'image suivante puis rafraichit la vue.
        """
        if not self.file_controller.has_files():
            return
        self.file_controller.go_next()
        self.view_controller.display_current(self.file_controller)

    def go_previous(self) -> None:
        """
        Navigue vers l'image precedente puis rafraichit la vue.
        """
        if not self.file_controller.has_files():
            return
        self.file_controller.go_previous()
        self.view_controller.display_current(self.file_controller)

    def go_next_untagged(self) -> None:
        """Navigue vers le prochain fichier non conforme au format cible."""
        if not self.file_controller.has_files():
            return

        idx = self.file_controller.find_next_untagged()
        if idx is not None:
            self.file_controller.current_index = idx
            self.view_controller.display_current(self.file_controller)
            return

        messagebox.showinfo(
            "Tous taggues",
            "Tous les fichiers sont deja conformes au format\n"
            "'base - [tags] - compteur.ext'.\n\n"
            "Il n'y a plus de fichier a tagguer.",
        )

    def open_explorer(self) -> None:
        """
        Ouvre l'explorateur Windows sur le fichier courant.
        """
        if not self.file_controller.has_files():
            return
        open_in_explorer(self.file_controller.current_filepath())

    def reload_current_folder(self) -> None:
        """Recharge le dossier courant comme apres un drag-and-drop."""
        folder_path = self.file_controller.folder_path
        if not folder_path or not os.path.isdir(folder_path):
            messagebox.showwarning(
                "Dossier invalide",
                "Le dossier courant est introuvable ou invalide.",
            )
            return

        self.config_controller.update_last_opened_folder(folder_path)
        self._reload_folder(folder_path)

    def _on_drop(self, event: tk.Event) -> None:
        """
        Traite le drag-and-drop de dossier depuis l'explorateur.

        Args:
            event: L'evenement Tkinterdnd2 contenant le chemin du dossier depose.
        """
        raw = getattr(event, "data", "")
        if not raw:
            return

        if raw.startswith("{"):
            folder_path = raw.strip("{}").split("}")[0]
        else:
            folder_path = raw.split()[0]

        if not os.path.isdir(folder_path):
            messagebox.showwarning(
                "Pas un dossier",
                f"L'element depose n'est pas un dossier :\n{folder_path}",
            )
            return

        self.config_controller.update_last_opened_folder(folder_path)
        self._reload_folder(folder_path)

    def _reload_folder(self, folder_path: str) -> None:
        """
        Recharge entierement les modeles et la vue pour un nouveau dossier.

        Args:
            folder_path: Le chemin absolu ou relatif du nouveau dossier a charger.
        """
        self.file_controller.set_folder(folder_path)

        if not self._load_current_folder_or_warn(allow_empty=False):
            return

        self._build_tags_with_progress()
        self.view_controller.reset_image_refs()
        self.view_controller.rebuild_tag_checkboxes(self.file_controller)
        self.view_controller.display_current(self.file_controller)

        self.view_controller.set_window_title_for_folder(folder_path)
