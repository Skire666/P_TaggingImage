#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  ConfigModel — Modèle de configuration JSON
=============================================================================

Gère la lecture/écriture d'un fichier JSON persistant contenant
la configuration applicative.

Clé supportée :
    - last_opened_folder : dernier dossier ouvert par l'application.
    - max_path_len       : seuil d'avertissement pour la longueur de chemin.
    - max_filename_len   : seuil d'avertissement pour la longueur de nom fichier.
"""

from __future__ import annotations

import json
import os
from typing import cast

class ConfigModel:
    """Modele d'acces a la configuration persistante.

    Attributes:
        config_path: Chemin absolu du fichier JSON de configuration.

    Notes:
        Le modele garantit l'existence du fichier et applique des
        valeurs par defaut en cas de contenu invalide.
    """


    # Valeurs par défaut pour la configuration
    DEFAULT_PATH_STR: str = ""
    DEFAULT_PATH_LEN: int = 220
    DEFAULT_FILENAME_LEN: int = 110
    
    # Dictionnaire de configuration par défaut
    DEFAULT_DATA: dict[str, str | int] = {
        "last_opened_folder": DEFAULT_PATH_STR,
        "max_path_len": DEFAULT_PATH_LEN,
        "max_filename_len": DEFAULT_FILENAME_LEN,
    }

    def __init__(self, config_path: str | None = None) -> None:
        """
        Initialise le modèle et garantit l'existence du fichier JSON.

        Args:
            config_path: Chemin du fichier de config. Si None,
                         utilise la racine du projet.

        Notes:
        - Si config_path est None, le modèle cherche config.json à la racine du projet
        - Si le fichier n'existe pas, il est créé avec les valeurs par défaut.
        """

        self._config_path = ""
        self._cached_data: dict[str, str | int] | None = None
        self._last_mtime: float = 0.0

        # Détermine le chemin du fichier de configuration
        if config_path is None:
            # remonte de 3 niveaux pour atteindre la racine du projet
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            )
            config_path = os.path.join(project_root, "config.json")

        self._config_path = config_path

        # garantit que le fichier de configuration existe dès l'initialisation
        self.ensure_exists()

    def ensure_exists(self) -> None:
        """
        Cree le fichier de configuration s'il n'existe pas.

        Notes:
        - Si le dossier parent n'existe pas, il est créé.
        - Si le fichier n'existe pas, il est créé avec les valeurs par défaut.
        """

        # Si le dossier parent n'existe pas, le crée
        folder = os.path.dirname(self._config_path)
        if folder:
            os.makedirs(folder, exist_ok=True)

        # Si le fichier n'existe pas, le crée avec les valeurs par défaut
        if not os.path.exists(self._config_path):
            self._save_json(self.DEFAULT_DATA)

    def load_file_json(self) -> dict[str, str | int]:
        """
        Charge la configuration depuis le fichier JSON.

        Notes:
        - Si le fichier est invalide ou incomplet, le modèle réinitialise avec les valeurs par défaut.

        Returns:
            dict[str, str | int]: Configuration normalisee.
        """
        self.ensure_exists()

        try:
            current_mtime = os.path.getmtime(self._config_path)
        except OSError:
            current_mtime = 0.0

        if self._cached_data is not None and current_mtime <= self._last_mtime:
            return self._cached_data

        try:
            # Lit le contenu du fichier JSON
            with open(self._config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            # En cas d'erreur de lecture ou de parsing, réinitialise avec les valeurs par défaut
            data = dict(self.DEFAULT_DATA)
            self._save_json(data)
            return data

        if not isinstance(data, dict):
            data = dict(self.DEFAULT_DATA)

        merged = cast("dict[str, str | int]", data.copy())
        needs_save = False # indique si une sauvegarde est nécessaire après la validation des clés

        # Valide la présence et le type de chaque clé attendue
        for key, default_val in self.DEFAULT_DATA.items():
            # Si la clé est absente ou de type incorrect, la réinitialise à la valeur par défaut
            if key not in merged or not isinstance(merged[key], type(default_val)):
                merged[key] = default_val
                needs_save = True

        # sauvegarde uniquement si des corrections ont été apportées pour éviter les écritures inutiles
        if needs_save:
            self._save_json(merged)
        
        self._cached_data = merged
        self._last_mtime = current_mtime

        return merged

    def _get_value(self, key: str, default: str | int | None = None) -> str | int | None:
        """Retourne la valeur associée à la clé, ou la valeur par défaut.
        
        Args:
            key: Clé de configuration.
            default: Valeur par défaut.

        Returns:
            La valeur stockée, ou la valeur par défaut si absente.
        """
        data = self.load_file_json()
        if key in data:
            return data[key]
        return default if default is not None else self.DEFAULT_DATA.get(key)

    def _set_value(self, key: str, value: str | int) -> None:
        """Met à jour la valeur associée à la clé et la sauvegarde sur disque.
        
        Args:
            key: Clé de configuration.
            value: Nouvelle valeur.
        """
        data = self.load_file_json()
        data[key] = value
        self._save_json(data)

    def _save_json(self, data: dict[str, str | int]) -> None:
        """Ecrit la configuration sur disque en JSON lisible.

        Args:
            data: Dictionnaire de configuration a serialiser.
        """
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        # Met à jour le cache et la date de modification après sauvegarde
        self._cached_data = cast("dict[str, str | int]", data.copy())
        try:
            self._last_mtime = os.path.getmtime(self._config_path)
        except OSError:
            self._last_mtime = 0.0

    # =============================================================================
    # Propriétés
    # =============================================================================

    # last_opened_folder
    @property
    def last_opened_folder(self) -> str:
        """Retourne le dernier dossier ouvert."""
        val = self._get_value("last_opened_folder", self.DEFAULT_PATH_STR)
        return str(val) if val is not None else self.DEFAULT_PATH_STR

    @last_opened_folder.setter
    def last_opened_folder(self, value: str) -> None:
        """Définit le dernier dossier ouvert."""
        self._set_value("last_opened_folder", value)

    # max_path_len
    @property
    def max_path_len(self) -> int:
        """Retourne la longueur maximale d'un chemin."""
        val = self._get_value("max_path_len", self.DEFAULT_PATH_LEN)
        return int(val) if val is not None else self.DEFAULT_PATH_LEN

    @max_path_len.setter
    def max_path_len(self, value: int) -> None:
        """Définit la longueur maximale d'un chemin."""
        self._set_value("max_path_len", value)

    # max_filename_len
    @property
    def max_filename_len(self) -> int:
        """Retourne la longueur maximale pour un nom de fichier."""
        val = self._get_value("max_filename_len", self.DEFAULT_FILENAME_LEN)
        return int(val) if val is not None else self.DEFAULT_FILENAME_LEN

    @max_filename_len.setter
    def max_filename_len(self, value: int) -> None:
        """Définit la longueur maximale pour un nom de fichier."""
        self._set_value("max_filename_len", value)

# END
