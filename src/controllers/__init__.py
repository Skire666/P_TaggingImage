#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  Controllers — Paquetage des contrôleurs
=============================================================================

Expose le controleur principal et les sous-controleurs :
    - MainController    : controleur global.
    - ConfigController  : gestion de la configuration.
    - FileController    : gestion des fichiers et tags.
    - ViewController    : gestion de la vue.

Example:
    >>> from controllers import MainController
"""

from __future__ import annotations

from controllers.main_controller import MainController
from controllers.config_controller import ConfigController
from controllers.file_controller import FileController
from controllers.view_controller import ViewController

__all__ = [
    "MainController",
    "ConfigController",
    "FileController",
    "ViewController",
]
