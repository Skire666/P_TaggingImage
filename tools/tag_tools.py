#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  Tag Tools — Boite a outils de manipulation des noms tagges
=============================================================================

Ce module centralise des helpers simples pour travailler avec un format
de nommage de fichiers image base sur des tags.
"""

from __future__ import annotations

import os
import re

from constants import TAG_CLOSE_FLEX, TAG_OPEN, TAG_CLOSE, TAG_SEPARATOR


class TagTools:
    @staticmethod
    def _get_substring(text: str, left_sep: str, right_sep: str) -> str:
        """
        Extrait la sous-chaîne située entre deux séparateurs.
        """
        try:
            if not left_sep or not right_sep:
                return ""

            left_idx = text.find(left_sep)
            if left_idx == -1:
                return ""

            start_idx = left_idx + len(left_sep)
            right_idx = text.find(right_sep, start_idx)
            if right_idx == -1:
                return ""

            return text[start_idx:right_idx]
        except Exception:
            return ""

    @staticmethod
    def get_base_name(filename: str) -> str:
        """
        Recupere la base du nom de fichier.
        """
        name_without_ext, _ = os.path.splitext(filename)
        idx = name_without_ext.find(TAG_OPEN)
        
        if idx == -1:
            return name_without_ext.strip()
                
        return name_without_ext[:idx].strip()

    @staticmethod
    def get_extension(filename: str) -> str:
        """
        Extrait l'extension d'un nom de fichier (incluant le point).
        """
        _, ext = os.path.splitext(filename)
        return ext.lower()

    @staticmethod
    def get_string_tags(filename: str) -> str:
        """
        Decoupe un nom de fichier pour extraire ses tags (sous forme de chaîne).
        """
        tag_content = TagTools._get_substring(filename, TAG_OPEN, TAG_CLOSE).strip()
        if not tag_content:
            tag_content = TagTools._get_substring(filename, TAG_OPEN, TAG_CLOSE_FLEX).strip()
            if not tag_content:
                return ""
        return tag_content

    @staticmethod
    def get_tags_from_filename(filename: str) -> str:
        """Alias pour appels dans autres modules"""
        return TagTools.get_string_tags(filename)

    @staticmethod
    def get_list_tags(filename: str) -> list[str]:
        """
        Decoupe un nom de fichier pour extraire sa liste de tags.
        """
        tag_content = TagTools._get_substring(filename, TAG_OPEN, TAG_CLOSE).strip()
        if not tag_content:
            tag_content = TagTools._get_substring(filename, TAG_OPEN, TAG_CLOSE_FLEX).strip()
            if not tag_content:
                return []

        return [tag.strip() for tag in tag_content.split(TAG_SEPARATOR) if tag.strip()]

    @staticmethod
    def get_counter(filename: str) -> int:
        """
        Extrait le compteur situé à la fin du nom de fichier, avant l'extension.
        S'il n'existe pas ou s'il est inférieur à 1000, retourne 1000.
        """
        name_without_ext, _ = os.path.splitext(filename)
        name_without_ext = name_without_ext.strip()
        
        # Cherche les chiffres situés à la fin de la chaîne
        match = re.search(r'(\d+)$', name_without_ext)
        if match:
            counter = int(match.group(1))
            return max(counter, 1000)
            
        return 1000

