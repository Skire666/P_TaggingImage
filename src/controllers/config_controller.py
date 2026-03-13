#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  ConfigController — Sous-controleur de configuration
=============================================================================

Encapsule la gestion de la configuration persistante et expose
des methodes simples de lecture/ecriture.
"""

from __future__ import annotations

from models.config_model import ConfigModel


class ConfigController:
    """Sous-controleur charge de la configuration applicative.

    Notes:
        Ce composant reste volontairement minimal et delegue le stockage
        au `ConfigModel`.
    """

    def __init__(self, model: ConfigModel | None = None) -> None:
        """Initialise le sous-controleur.

        Args:
            model: Instance de modele a injecter (tests). Si `None`,
                une instance par defaut est creee.
        """
        self.model = model or ConfigModel()

    def get_last_opened_folder(self) -> str:
        """Retourne le dernier dossier ouvert enregistre."""
        return self.model.get_last_opened_folder()

    def update_last_opened_folder(self, folder_path: str) -> None:
        """Persiste le dernier dossier ouvert."""
        self.model.set_last_opened_folder(folder_path)

    def get_max_path_len(self) -> int:
        """Retourne la limite de longueur de chemin configuree."""
        return self.model.get_max_path_len()

    def update_max_path_len(self, max_path_len: int) -> None:
        """Met a jour la limite de longueur de chemin."""
        self.model.set_max_path_len(max_path_len)

    def get_max_filename_len(self) -> int:
        """Retourne la limite de longueur de nom de fichier configuree."""
        return self.model.get_max_filename_len()

    def update_max_filename_len(self, max_filename_len: int) -> None:
        """Met a jour la limite de longueur de nom de fichier."""
        self.model.set_max_filename_len(max_filename_len)
