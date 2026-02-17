#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  Models — Paquetage des modèles de données
=============================================================================

Expose les modèles métier de l'application :
    - FileModel : gestion de la liste de fichiers, navigation, renommage.
    - TagModel  : construction et gestion du dictionnaire de tags.

Example:
    >>> from models import FileModel, TagModel
"""

from __future__ import annotations

from models.file_model import FileModel
from models.tag_model import TagModel

__all__ = ["FileModel", "TagModel"]
