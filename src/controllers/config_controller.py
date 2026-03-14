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

    def __init__(self, model_config: ConfigModel | None = None) -> None:
        """Initialise le sous-controleur.

        Args:
            model: Instance de modele a injecter (tests). Si `None`,
                une instance par defaut est creee.
        """
        self.model_config = model_config or ConfigModel()

    def get_last_opened_folder(self) -> str:
        """Retourne le dernier dossier ouvert enregistre."""
        return self.model_config.last_opened_folder

    def update_last_opened_folder(self, l_folder_path: str) -> None:
        """Persiste le dernier dossier ouvert."""
        self.model_config.last_opened_folder = l_folder_path

    def get_max_path_len(self) -> int:
        """Retourne la limite de longueur de chemin configuree."""
        return self.model_config.max_path_len

    def update_max_path_len(self, l_max_path_len: int) -> None:
        """Met a jour la limite de longueur de chemin."""
        self.model_config.max_path_len = l_max_path_len

    def get_max_filename_len(self) -> int:
        """Retourne la limite de longueur de nom de fichier configuree."""
        return self.model_config.max_filename_len

    def update_max_filename_len(self, l_max_filename_len: int) -> None:
        """Met a jour la limite de longueur de nom de fichier."""
        self.model_config.max_filename_len = l_max_filename_len
