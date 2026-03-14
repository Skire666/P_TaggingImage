#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  Constants — Constantes, thème de couleurs et styles réutilisables
=============================================================================

Centralise toutes les valeurs de configuration de l'application :
extensions supportées, dimensions, séparateurs, couleurs du thème
Catppuccin Mocha et styles de boutons Tkinter.

Example:
    >>> from constants import SUPPORTED_EXTENSIONS, BG_COLOR, BTN_STYLE
    >>> ".png" in SUPPORTED_EXTENSIONS
    True
"""

from __future__ import annotations


# =============================================================================
#  EXTENSIONS D'IMAGES
# =============================================================================

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".bmp",
    ".tiff", ".tif", ".webp",
})
"""Extensions de fichiers image reconnues par l'application (minuscules)."""


# =============================================================================
#  DIMENSIONS
# =============================================================================

LOADING_WIN_SIZE: tuple[int, int] = (450, 350)
"""Dimensions (largeur, hauteur) de la fenêtre de chargement en pixels."""

FOOTER_PX: int = 200
"""Hauteur fixe du footer en pixels."""

GALLERY_COL_WEIGHTS: list[int] = [20, 60, 20]
"""Poids des colonnes de la galerie triptyque (gauche, centre, droite)."""

FOOTER_COL_WEIGHTS: tuple[int, int] = (54, 46)
"""Poids des colonnes du footer (tags, renommage) pour une répartition 54/46."""

MIN_WIN_WIDTH: int = 300
"""Largeur minimale de la fenêtre principale en pixels."""

MIN_WIN_HEIGHT: int = 300
"""Hauteur minimale de la fenêtre principale en pixels (0 = pas de minimum)."""

GALLERY_RESIZE_DEBOUNCE_MS: int = 120
"""Délai de debounce (ms) avant rafraîchissement des images au resize."""

# =============================================================================
#  SÉPARATEURS (ex: 'base - [tags] - 1000')
# =============================================================================

TAG_OPEN: str = " - ["
"""Délimiteur ouvrant de la liste de tags."""

TAG_CLOSE: str = "] - "
"""Délimiteur fermant de la liste de tags."""

TAG_CLOSE_FLEX: str = "]."
"""Délimiteur plus souple (sans compteur) fermant de la liste de tags."""

TAG_SEPARATOR: str = ", "
"""Séparateur entre les tags individuels dans les crochets."""


# =============================================================================
#  THÈME DE COULEURS — Catppuccin Mocha
# =============================================================================

BG_COLOR: str = "#1e1e2e"
"""Fond principal (sombre)."""

FG_COLOR: str = "#cdd6f4"
"""Texte principal (clair)."""

ACCENT_COLOR: str = "#89b4fa"
"""Couleur d'accentuation (bleu)."""

FRAME_BG: str = "#313244"
"""Fond des cadres (LabelFrame, etc.)."""

BUTTON_BG: str = "#45475a"
"""Fond des boutons."""

BUTTON_FG: str = "#cdd6f4"
"""Texte des boutons."""

ENTRY_BG: str = "#45475a"
"""Fond des champs de saisie."""

ENTRY_FG: str = "#c9d1ea"
"""Texte des champs de saisie."""

CHECK_BG: str = "#313244"
"""Fond des cases à cocher."""

CHECK_FG: str = "#cdd6f4"
"""Texte des cases à cocher."""

HIGHLIGHT: str = "#f38ba8"
"""Couleur de surbrillance (rose)."""

SUCCESS_BG: str = "#a6e3a1"
"""Fond bouton succès (vert)."""

SUCCESS_FG: str = "#1e1e2e"
"""Texte bouton succès."""


# =============================================================================
#  POLICES
# =============================================================================

FONT_FAMILY: str = "Segoe UI"
"""Famille de police utilisée dans toute l'application."""

FONT_SM: tuple[str, int] = (FONT_FAMILY, 11)
"""Police standard petite (taille 11)."""

FONT_SM_BOLD: tuple[str, int, str] = (FONT_FAMILY, 11, "bold")
"""Police petite grasse (taille 11, bold)."""

FONT_SM_ITALIC: tuple[str, int, str] = (FONT_FAMILY, 11, "italic")
"""Police petite italique (taille 11, italic)."""

FONT_MD: tuple[str, int] = (FONT_FAMILY, 11)
"""Police standard moyenne (taille 11)."""

FONT_MD_BOLD: tuple[str, int, str] = (FONT_FAMILY, 11, "bold")
"""Police moyenne grasse (taille 11, bold)."""

FONT_LG_BOLD: tuple[str, int, str] = (FONT_FAMILY, 11, "bold")
"""Police grande grasse (taille 11, bold)."""

# =============================================================================
#  STYLES DE BOUTONS
# =============================================================================

# Style de base pour les boutons de navigation (suivant, précédent, etc.)
# padx pour espacer horizontalement, pady pour espacer verticalement

BTN_STYLE: dict = {
    "bg": BUTTON_BG, "fg": BUTTON_FG,
    "activebackground": ACCENT_COLOR, "activeforeground": "#000",
    "font": FONT_MD_BOLD,
    "relief": "flat", "cursor": "hand2",
    "padx": 8, "pady": 4,
}
"""Style par défaut des boutons de navigation."""

BTN_APPLY_STYLE: dict = {
    "bg": SUCCESS_BG, "fg": SUCCESS_FG,
    "activebackground": "#40a02b", "activeforeground": "#fff",
    "font": FONT_MD_BOLD,
    "relief": "flat", "cursor": "hand2",
    "padx": 8, "pady": 4,
}
"""Style du bouton « Appliquer le renommage » (vert succès)."""
