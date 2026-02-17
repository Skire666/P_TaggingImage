#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  TagModel — Modèle de gestion du dictionnaire de tags
=============================================================================

Construit et maintient un dictionnaire { tag: compteur } à partir
d'une liste de noms de fichiers. Les tags sont triés par fréquence
décroissante puis alphabétiquement.

Example:
    >>> model = TagModel()
    >>> model.build(["chat noir.png", "chat blanc.jpg"])
    >>> model.tag_dict
    OrderedDict([('chat', 2), ('blanc', 1), ('noir', 1)])
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Callable

from utils import parse_filename


class TagModel:
    """
    Modèle de données pour les tags extraits des noms de fichiers.

    Attributes:
        tag_dict: Dictionnaire { tag: compteur } trié par fréquence
                  décroissante puis alphabétiquement.

    Example:
        >>> model = TagModel()
        >>> model.tag_dict
        OrderedDict()
    """

    def __init__(self) -> None:
        """
        Initialise le modèle avec un dictionnaire de tags vide.

        Example:
            >>> model = TagModel()
            >>> len(model.tag_dict)
            0
        """
        self.tag_dict: OrderedDict[str, int] = OrderedDict()

    def build(
        self,
        file_list: list[str],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> OrderedDict[str, int]:
        """
        Construit le dictionnaire { tag: compteur } à partir des fichiers.

        Parcourt chaque fichier, extrait les tags via parse_filename(),
        et comptabilise les occurrences (insensible à la casse).

        Args:
            file_list:          Liste des noms de fichiers à analyser.
                                Ex: ["chat noir.png", "chat blanc.jpg"]
            progress_callback:  Fonction optionnelle appelée avec (current, total)
                                à chaque fichier traité. None par défaut.

        Returns:
            OrderedDict[str, int]: Dictionnaire trié mis à jour.

        Example:
            >>> model.build(["chat noir.png", "chat blanc.jpg"])
            OrderedDict([('chat', 2), ('blanc', 1), ('noir', 1)])
        """
        raw_dict: dict[str, int] = {}
        total = len(file_list)

        for idx, filename in enumerate(file_list):
            self._count_tags_in_file(filename, raw_dict)
            if progress_callback:
                progress_callback(idx + 1, total)

        self.tag_dict = self._sort_dict(raw_dict)
        return self.tag_dict

    def rebuild(self, file_list: list[str]) -> OrderedDict[str, int]:
        """
        Reconstruit le dictionnaire sans barre de progression.

        Raccourci vers build() sans callback (utilisé après un renommage).

        Args:
            file_list: Liste des noms de fichiers à analyser.

        Returns:
            OrderedDict[str, int]: Dictionnaire trié mis à jour.

        Example:
            >>> model.rebuild(["paysage montagne.jpg"])
            OrderedDict([('montagne', 1), ('paysage', 1)])
        """
        return self.build(file_list)

    # -----------------------------------------------------------------
    #  Méthodes internes
    # -----------------------------------------------------------------

    @staticmethod
    def _count_tags_in_file(filename: str, accumulator: dict[str, int]) -> None:
        """
        Extrait les tags d'un fichier et incrémente le compteur.

        Args:
            filename:    Nom du fichier à parser. Ex: "chat noir.png"
            accumulator: Dictionnaire mutable { tag: compteur } à enrichir.

        Example:
            >>> acc = {}
            >>> TagModel._count_tags_in_file("chat noir.png", acc)
            >>> acc
            {'chat': 1, 'noir': 1}
        """
        _ext, tags = parse_filename(filename)
        for tag in tags:
            key = tag.lower()
            accumulator[key] = accumulator.get(key, 0) + 1

    @staticmethod
    def _sort_dict(raw_dict: dict[str, int]) -> OrderedDict[str, int]:
        """
        Trie un dictionnaire par compteur décroissant, puis alphabétique.

        Args:
            raw_dict: Dictionnaire brut { tag: compteur }.

        Returns:
            OrderedDict[str, int]: Dictionnaire trié.

        Example:
            >>> TagModel._sort_dict({"noir": 1, "chat": 2, "blanc": 1})
            OrderedDict([('chat', 2), ('blanc', 1), ('noir', 1)])
        """
        sorted_tags = sorted(raw_dict.items(), key=lambda x: (-x[1], x[0]))
        return OrderedDict(sorted_tags)
