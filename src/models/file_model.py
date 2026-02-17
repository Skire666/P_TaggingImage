#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  FileModel — Modèle de gestion des fichiers images
=============================================================================

Gère la liste des fichiers images d'un dossier :
scanning, navigation cyclique et renommage sur disque.

Example:
    >>> model = FileModel("C:/images")
    >>> model.load_files()
    >>> model.current_filename()
    'chat noir.png'
"""

from __future__ import annotations

import os

from utils import is_supported_image, is_filename_tagged


class FileModel:
    """
    Modèle de données pour la liste de fichiers images.

    Attributes:
        folder_path:   Chemin absolu du dossier scanné.
        file_list:     Liste triée des noms de fichiers images.
        current_index: Index de l'image courante (0 par défaut).

    Example:
        >>> model = FileModel("./images")
        >>> model.load_files()
        >>> len(model.file_list)
        42
    """

    def __init__(self, folder_path: str) -> None:
        """
        Initialise le modèle avec un chemin de dossier.

        Args:
            folder_path: Chemin (relatif ou absolu) vers le dossier
                         contenant les images.

        Example:
            >>> model = FileModel("C:/images")
            >>> model.folder_path
            'C:\\images'
        """
        self.folder_path: str = os.path.abspath(folder_path)
        self.file_list: list[str] = []
        self.current_index: int = 0

    # -----------------------------------------------------------------
    #  Chargement
    # -----------------------------------------------------------------

    def load_files(self) -> list[str]:
        """
        Scanne le dossier et stocke la liste des images triée.

        Parcourt self.folder_path, filtre les fichiers dont l'extension
        est supportée via is_supported_image(), et trie par nom
        (insensible à la casse).

        Returns:
            list[str]: Liste des noms de fichiers trouvés (vide si erreur).

        Raises:
            OSError: Propagée si le dossier est inaccessible.

        Example:
            >>> model.load_files()
            ['chat noir.jpg', 'paysage.png', 'portrait.webp']
        """
        entries = os.listdir(self.folder_path)
        self.file_list = sorted(
            (f for f in entries if is_supported_image(self.folder_path, f)),
            key=str.lower,
        )
        return self.file_list

    def has_files(self) -> bool:
        """
        Indique si des fichiers images ont été chargés.

        Returns:
            bool: True si file_list contient au moins un élément.

        Example:
            >>> model.has_files()
            True
        """
        return len(self.file_list) > 0

    # -----------------------------------------------------------------
    #  Accès aux fichiers
    # -----------------------------------------------------------------

    def current_filename(self) -> str:
        """
        Retourne le nom du fichier actuellement sélectionné.

        Returns:
            str: Nom du fichier à l'index courant.

        Example:
            >>> model.current_filename()
            'chat noir.png'
        """
        return self.file_list[self.current_index]

    def current_filepath(self) -> str:
        """
        Retourne le chemin absolu du fichier actuellement sélectionné.

        Returns:
            str: Chemin complet (folder_path + nom du fichier).

        Example:
            >>> model.current_filepath()
            'C:\\images\\chat noir.png'
        """
        return os.path.join(self.folder_path, self.current_filename())

    def filepath_at(self, index: int) -> str:
        """
        Retourne le chemin absolu du fichier à un index donné.

        Args:
            index: Index dans file_list (0-based).

        Returns:
            str: Chemin complet vers le fichier.

        Example:
            >>> model.filepath_at(2)
            'C:\\images\\portrait.webp'
        """
        return os.path.join(self.folder_path, self.file_list[index])

    def total(self) -> int:
        """
        Retourne le nombre total de fichiers chargés.

        Returns:
            int: Taille de file_list.

        Example:
            >>> model.total()
            42
        """
        return len(self.file_list)

    def prev_index(self) -> int:
        """
        Retourne l'index de l'image précédente (cyclique).

        Returns:
            int: (current_index - 1) % total.

        Example:
            >>> model.current_index = 0
            >>> model.prev_index()
            41  # dernière image (total=42)
        """
        return (self.current_index - 1) % self.total()

    def next_index(self) -> int:
        """
        Retourne l'index de l'image suivante (cyclique).

        Returns:
            int: (current_index + 1) % total.

        Example:
            >>> model.current_index = 41
            >>> model.next_index()
            0  # retour au début
        """
        return (self.current_index + 1) % self.total()

    # -----------------------------------------------------------------
    #  Navigation
    # -----------------------------------------------------------------

    def go_next(self) -> int:
        """
        Avance à l'image suivante (cyclique).

        Returns:
            int: Le nouvel index courant.

        Example:
            >>> model.current_index = 4  # total=5
            >>> model.go_next()
            0
        """
        self.current_index = self.next_index()
        return self.current_index

    def go_previous(self) -> int:
        """
        Recule à l'image précédente (cyclique).

        Returns:
            int: Le nouvel index courant.

        Example:
            >>> model.current_index = 0  # total=5
            >>> model.go_previous()
            4
        """
        self.current_index = self.prev_index()
        return self.current_index

    # -----------------------------------------------------------------
    #  Renommage
    # -----------------------------------------------------------------

    def rename_current(self, new_filename: str) -> None:
        """
        Renomme le fichier courant sur disque et dans file_list.

        Args:
            new_filename: Nouveau nom de fichier (avec extension).
                          Ex: "chat blanc.png"

        Raises:
            OSError: Si le renommage échoue (permissions, etc.).

        Example:
            >>> model.rename_current("chat blanc.png")
            >>> model.current_filename()
            'chat blanc.png'
        """
        old_path = self.current_filepath()
        new_path = os.path.join(self.folder_path, new_filename)
        os.rename(old_path, new_path)
        self.file_list[self.current_index] = new_filename

    def find_next_untagged(self) -> int | None:
        """
        Cherche le prochain fichier dont le nom n'est pas conforme.

        Parcourt la liste à partir de l'index courant + 1 (cyclique)
        et retourne l'index du premier fichier non conforme au format
        ``base - [tags] - compteur.ext``.

        Returns:
            int | None: Index du prochain fichier non conforme,
                        ou None si tous les fichiers sont conformes.

        Example:
            >>> model.find_next_untagged()
            3
        """
        total = self.total()
        for offset in range(total):
            idx = (self.current_index + offset) % total
            if not is_filename_tagged(self.file_list[idx]):
                return idx
        return None

    def file_exists(self, filename: str) -> bool:
        """
        Vérifie si un fichier existe déjà dans le dossier.

        Args:
            filename: Nom du fichier à vérifier. Ex: "chat blanc.png"

        Returns:
            bool: True si le fichier existe.

        Example:
            >>> model.file_exists("chat noir.png")
            True
        """
        return os.path.exists(os.path.join(self.folder_path, filename))
