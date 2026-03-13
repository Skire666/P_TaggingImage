#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  FileController — Sous-controleur de fichiers/tags
=============================================================================

Encapsule la gestion du modele de fichiers et du modele de tags.
"""

from __future__ import annotations

import os
from collections import OrderedDict
from typing import Callable, TYPE_CHECKING

from constants import TAG_OPEN, TAG_CLOSE
from models.image_navigator_model import ImageNavigatorModel
from models.tag_model import TagModel

if TYPE_CHECKING:
    from controllers.config_controller import ConfigController


class FileController:
    """Sous-controleur dedie a la gestion des fichiers et des tags."""

    def __init__(self, folder_path: str) -> None:
        """Initialise les modeles de fichiers et de tags."""
        self.image_navigator_model = ImageNavigatorModel(folder_path)
        self.tag_model = TagModel()

    @staticmethod
    def resolve_start_folder(
        folder_path: str | None,
        config_controller: ConfigController,
    ) -> str:
        """
        Determine le dossier de demarrage (CLI > config > dossier courant).

        Le dossier retenu est persiste dans la configuration.
        """
        if folder_path and os.path.isdir(folder_path):
            selected = os.path.abspath(folder_path)
        else:
            configured = config_controller.get_last_opened_folder().strip()
            if configured and os.path.isdir(configured):
                selected = os.path.abspath(configured)
            else:
                selected = os.path.abspath(os.getcwd()) # par défaut, est le dossier copurant de l'executable

        config_controller.update_last_opened_folder(selected)
        return selected

    @property
    def folder_path(self) -> str:
        """Retourne le dossier courant (chemin absolu)."""
        return self.image_navigator_model.folder_path

    @property
    def current_index(self) -> int:
        """Retourne l'index courant de navigation."""
        return self.image_navigator_model.current_index

    @current_index.setter
    def current_index(self, value: int) -> None:
        """Met a jour l'index courant de navigation."""
        self.image_navigator_model.current_index = value

    def set_folder(self, folder_path: str) -> None:
        """Remplace le modele de fichiers pour un nouveau dossier."""
        self.image_navigator_model = ImageNavigatorModel(folder_path)

    def load_files(self) -> list[str]:
        """Charge et retourne la liste des images du dossier courant."""
        return self.image_navigator_model.load_files()

    def has_files(self) -> bool:
        """Indique si des images sont disponibles."""
        return self.image_navigator_model.has_files()

    def total(self) -> int:
        """Retourne le nombre total de fichiers charges."""
        return self.image_navigator_model.total()

    def current_filename(self) -> str:
        """Retourne le nom du fichier courant."""
        return self.image_navigator_model.current_filename()

    def current_filepath(self) -> str:
        """Retourne le chemin complet du fichier courant."""
        return self.image_navigator_model.current_filepath()

    def filepath_at(self, index: int) -> str:
        """Retourne le chemin complet du fichier a `index`."""
        return self.image_navigator_model.filepath_at(index)

    def prev_index(self) -> int:
        """Retourne l'index precedent (cyclique)."""
        return self.image_navigator_model.prev_index()

    def next_index(self) -> int:
        """Retourne l'index suivant (cyclique)."""
        return self.image_navigator_model.next_index()

    def go_next(self) -> int:
        """Avance a l'image suivante et retourne le nouvel index."""
        return self.image_navigator_model.go_next()

    def go_previous(self) -> int:
        """Recule a l'image precedente et retourne le nouvel index."""
        return self.image_navigator_model.go_previous()

    def find_next_untagged(self) -> int | None:
        """Retourne l'index du prochain fichier non conforme, sinon `None`."""
        return self.image_navigator_model.find_next_untagged()

    def rename_current(self, new_filename: str) -> None:
        """Renomme le fichier courant."""
        self.image_navigator_model.rename_current(new_filename)

    def file_exists(self, filename: str) -> bool:
        """Indique si `filename` existe deja dans le dossier courant."""
        return self.image_navigator_model.file_exists(filename)

    def build_tags(
        self,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> None:
        """Construit/reconstruit le dictionnaire de tags.

        Args:
            progress_callback: Callback optionnel recevant `(current, total)`.
        """
        if progress_callback is None:
            self.tag_model.rebuild(self.image_navigator_model.file_list)
        else:
            self.tag_model.build(self.image_navigator_model.file_list, progress_callback)

    def tag_dict(self) -> OrderedDict[str, int]:
        """Retourne le dictionnaire des tags agreges."""
        return self.tag_model.tag_dict

    def find_available_name(self, base_name: str, tags_str: str,  ext: str, *, ignore: str = "") -> str | None:
        """
        Trouve le premier nom de fichier final disponible en y ajoutant le compteur.
        Format final : `base_with_tags - compteur.ext`
        """
        for counter in range(1000, 10000):
            candidate = f"{base_name}{TAG_OPEN}{tags_str}{TAG_CLOSE}{counter}{ext}"
            # Si le nom proposé est celui à ignorer ou s'il existe déjà, continue la recherche
            if candidate == ignore or not self.file_exists(candidate):
                return candidate
        return None

    def full_path_for(self, filename: str) -> str:
        """Construit le chemin absolu de `filename` dans le dossier courant."""
        return os.path.join(self.folder_path, filename)
