#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  Controllers — Paquetage des contrôleurs
=============================================================================

Expose le contrôleur principal de l'application :
    - GalleryController : orchestre modèles et vues.

Example:
    >>> from controllers import GalleryController
"""

from __future__ import annotations

from controllers.gallery_controller import GalleryController

__all__ = ["GalleryController"]
