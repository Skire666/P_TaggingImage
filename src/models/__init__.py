#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  Models — Paquetage des modèles de données
=============================================================================

Expose les modeles metier de l'application :
  - ImageNavigatorModel : gestion de la liste de fichiers, navigation, renommage.
    - TagModel  : construction et gestion du dictionnaire de tags.
  - ConfigModel : gestion de la configuration JSON persistante.

Example:
  >>> from models import ImageNavigatorModel, TagModel, ConfigModel
"""

from __future__ import annotations

from models.image_navigator_model import ImageNavigatorModel
from models.tag_model import TagModel
from models.config_model import ConfigModel

__all__ = ["ImageNavigatorModel", "TagModel", "ConfigModel"]
