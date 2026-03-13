#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  Models — Paquetage des modèles de données
=============================================================================

Expose les modeles metier de l'application :
    - FileModel : gestion de la liste de fichiers, navigation, renommage.
    - TagModel  : construction et gestion du dictionnaire de tags.
  - ConfigModel : gestion de la configuration JSON persistante.

Example:
    >>> from models import FileModel, TagModel, ConfigModel
"""

from __future__ import annotations

from models.file_model import FileModel
from models.tag_model import TagModel
from models.config_model import ConfigModel

__all__ = ["FileModel", "TagModel", "ConfigModel"]
