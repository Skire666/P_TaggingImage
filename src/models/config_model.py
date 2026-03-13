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


class ConfigModel:
    """Modele d'acces a la configuration persistante.

    Attributes:
        config_path: Chemin absolu du fichier JSON de configuration.

    Notes:
        Le modele garantit l'existence du fichier et applique des
        valeurs par defaut en cas de contenu invalide.
    """

    DEFAULT_PATH_LEN: int = 220
    DEFAULT_FILENAME_LEN: int = 110
    DEFAULT_DATA: dict[str, str | int] = {
        "last_opened_folder": "",
        "max_path_len": DEFAULT_PATH_LEN,
        "max_filename_len": DEFAULT_FILENAME_LEN,
    }

    def __init__(self, config_path: str | None = None) -> None:
        """
        Initialise le modèle et garantit l'existence du fichier JSON.

        Args:
            config_path: Chemin du fichier de config. Si None,
                         utilise la racine du projet.
        """
        if config_path is None:
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            )
            config_path = os.path.join(project_root, "config.json")

        self.config_path = config_path
        self.ensure_exists()

    def ensure_exists(self) -> None:
        """Cree le fichier de configuration s'il n'existe pas."""
        folder = os.path.dirname(self.config_path)
        if folder:
            os.makedirs(folder, exist_ok=True)

        if not os.path.exists(self.config_path):
            self._write(self.DEFAULT_DATA)

    def load(self) -> dict[str, str | int]:
        """
        Charge la configuration depuis le fichier JSON.

        Si le fichier est invalide ou incomplet, le modèle réinitialise
        les valeurs manquantes avec les valeurs par défaut.

        Returns:
            dict[str, str | int]: Configuration normalisee.
        """
        self.ensure_exists()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            data = dict(self.DEFAULT_DATA)
            self._write(data)
            return data

        if not isinstance(data, dict):
            data = dict(self.DEFAULT_DATA)

        merged = dict(self.DEFAULT_DATA)

        folder = data.get("last_opened_folder")
        if isinstance(folder, str):
            merged["last_opened_folder"] = folder

        max_path_len = data.get("max_path_len")
        if isinstance(max_path_len, int) and max_path_len > 0:
            merged["max_path_len"] = max_path_len

        max_filename_len = data.get("max_filename_len")
        if isinstance(max_filename_len, int) and max_filename_len > 0:
            merged["max_filename_len"] = max_filename_len

        if merged != data:
            self._write(merged)

        return merged

    def get_last_opened_folder(self) -> str:
        """Retourne le dernier dossier ouvert.

        Returns:
            str: Chemin absolu du dernier dossier, ou chaine vide.
        """
        data = self.load()
        value = data.get("last_opened_folder", "")
        return value if isinstance(value, str) else ""

    def set_last_opened_folder(self, folder_path: str) -> None:
        """Met a jour et sauvegarde le dernier dossier ouvert.

        Args:
            folder_path: Dossier a persister. Une chaine vide efface la valeur.
        """
        data = self.load()
        data["last_opened_folder"] = os.path.abspath(folder_path) if folder_path else ""
        self._write(data)

    def get_max_path_len(self) -> int:
        """Retourne la limite de longueur de chemin configuree.

        Returns:
            int: Valeur strictement positive. Defaut: 220.
        """
        data = self.load()
        value = data.get("max_path_len", self.DEFAULT_PATH_LEN)
        return value if isinstance(value, int) and value > 0 else self.DEFAULT_PATH_LEN

    def set_max_path_len(self, max_path_len: int) -> None:
        """Met a jour la limite de longueur de chemin.

        Args:
            max_path_len: Limite strictement positive.
        """
        if max_path_len <= 0:
            return

        data = self.load()
        data["max_path_len"] = max_path_len
        self._write(data)

    def get_max_filename_len(self) -> int:
        """Retourne la limite de longueur de nom de fichier configuree.

        Returns:
            int: Valeur strictement positive. Defaut: 110.
        """
        data = self.load()
        value = data.get("max_filename_len", self.DEFAULT_FILENAME_LEN)
        return (
            value
            if isinstance(value, int) and value > 0
            else self.DEFAULT_FILENAME_LEN
        )

    def set_max_filename_len(self, max_filename_len: int) -> None:
        """Met a jour la limite de longueur de nom de fichier.

        Args:
            max_filename_len: Limite strictement positive.
        """
        if max_filename_len <= 0:
            return

        data = self.load()
        data["max_filename_len"] = max_filename_len
        self._write(data)

    def _write(self, data: dict[str, str | int]) -> None:
        """Ecrit la configuration sur disque en JSON lisible.

        Args:
            data: Dictionnaire de configuration a serialiser.
        """
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
