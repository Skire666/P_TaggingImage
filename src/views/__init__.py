#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  Views — Paquetage des vues (interface graphique)
=============================================================================

Expose les composants visuels de l'application :
    - LoadingView  : écran de chargement avec barre de progression.
    - GalleryView  : interface principale (galerie, tags, renommage).

Example:
    >>> from views import LoadingView, GalleryView
"""

from __future__ import annotations

from views.loading_view import LoadingView
from views.gallery_view import GalleryView

__all__ = ["LoadingView", "GalleryView"]
