#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  Utils — Fonctions utilitaires (images, parsing, système)
=============================================================================

Regroupe les fonctions pures et les helpers qui ne dépendent ni de
l'état global de l'application, ni du framework Tkinter :
parsing de noms de fichiers, manipulation d'images (PIL), interactions
avec le système d'exploitation.

Example:
    >>> from utils import parse_filename, resize_image_to_fit
    >>> parse_filename("chat noir mignon -- auteur.png")
    (".png", ["chat", "noir", "mignon"])
"""

from __future__ import annotations

import os
import subprocess
import tkinter as tk

try:
    from PIL import Image  # noqa: F401
except ImportError:
    print("ERREUR : La bibliothèque Pillow est requise.")
    print("Installez-la avec : pip install Pillow")
    raise SystemExit(1)

from constants import MAIN_SEPARATOR, TAG_OPEN, TAG_CLOSE, TAG_SEPARATOR, SUPPORTED_EXTENSIONS


# =============================================================================
#  PARSING
# =============================================================================

def parse_filename(filename: str) -> tuple[str, list[str]]:
    """
    Découpe un nom de fichier en (extension, liste_de_tags).

    Format attendu : ``base - [tag1, tag2, tag3] - 0.png``

    Algorithme :
        1. Sépare l'extension du reste du nom.
        2. Cherche les délimiteurs `` - [`` et ``] - `` pour isoler
           la partie entre crochets.
        3. Découpe cette partie par ``, `` → liste de tags.

    Si le nom ne contient pas de crochets, la liste de tags est vide.

    Args:
        filename: Nom du fichier avec extension.
                  Ex: ``"base - [tag1, tag2, tag3] - 1000.png"``

    Returns:
        tuple[str, list[str]]: Tuple (extension, liste_de_tags).

    Example:
        >>> parse_filename("base - [chat, noir, mignon] - 1000.png")
        (".png", ["chat", "noir", "mignon"])
        >>> parse_filename("base - [] - 1000.png")
        (".png", [])
        >>> parse_filename("paysage.jpg")
        (".jpg", [])
    """
    name_without_ext, extension = os.path.splitext(filename)

    open_delim = MAIN_SEPARATOR + TAG_OPEN # ex: " - ["
    close_delim = TAG_CLOSE + MAIN_SEPARATOR # ex: "] - "

    # Trouve l'index du délimiteur ouvrant. S'il n'existe pas, pas de tags → retourne l'extension et une liste vide.
    open_idx = name_without_ext.find(open_delim)
    if open_idx == -1:
        return extension, []

    # L'index de début des tags est juste après le délimiteur ouvrant
    tag_start = open_idx + len(open_delim)
    close_idx = name_without_ext.find(close_delim, tag_start)
    if close_idx == -1: # pas de fermeture après l'ouverture → pas de tags valides
        return extension, []

    tag_content = name_without_ext[tag_start:close_idx].strip()
    if not tag_content: # contenu vide entre les délimiteurs → pas de tags
        return extension, []

    # Découpe par TAG_SEPARATOR et nettoie les tags individuels
    tags = [t.strip() for t in tag_content.split(TAG_SEPARATOR) if t.strip()]
    return extension, tags


def _matches_tagged_syntax(stem: str) -> bool:
    """
    Vérifie si un stem (nom sans extension) suit le format taggué.

    Format attendu : ``base - [tags] - compteur``

    Cherche séquentiellement les délimiteurs `` - [``, ``] - `` puis
    vérifie que la partie finale est un compteur numérique.

    Args:
        stem: Nom de fichier sans extension. Ex: ``"photo - [chat] - 1000"``

    Returns:
        bool: True si le stem est conforme.

    Example:
        >>> _matches_tagged_syntax("photo - [chat, noir] - 1000")
        True
        >>> _matches_tagged_syntax("photo")
        False
    """
    open_delim = MAIN_SEPARATOR + TAG_OPEN       # " - ["
    close_delim = TAG_CLOSE      # "]"

    # 1. Cherche le délimiteur ouvrant (base non-vide avant)
    open_idx = stem.find(open_delim)
    if open_idx <= 0:
        return False

    # 2. Cherche le délimiteur fermant après l'ouverture
    tag_start = open_idx + len(open_delim)
    close_idx = stem.find(close_delim, tag_start)
    if close_idx == -1:
        return False

    return True # ignore la partie après "] - " qui doit être un compteur numérique


def is_filename_tagged(filename: str) -> bool:
    """
    Vérifie si un nom de fichier est conforme à la syntaxe taggée.

    Format attendu : ``base - [tag1, tag2] - 1000.ext``

    Args:
        filename: Nom du fichier avec extension.

    Returns:
        bool: True si le nom est conforme au format attendu.

    Example:
        >>> is_filename_tagged("photo - [chat, noir] - 1000.png")
        True
        >>> is_filename_tagged("photo.png")
        False
        >>> is_filename_tagged("photo - [] - 1000.png")
        True
    """
    stem, ext = os.path.splitext(filename)
    if not ext:
        return False
    return _matches_tagged_syntax(stem)


# =============================================================================
#  IMAGES
# =============================================================================

def resize_image_to_fit(
    image: Image.Image,
    max_width: int,
    max_height: int,
) -> Image.Image:
    """
    Redimensionne une image pour la faire tenir dans un cadre donné.

    Conserve le ratio d'aspect (proportions). Si l'image est déjà
    plus petite que les dimensions maximales, elle est retournée telle
    quelle (pas d'agrandissement).

    Args:
        image:      Objet PIL.Image source à redimensionner.
        max_width:  Largeur maximale autorisée en pixels.
        max_height: Hauteur maximale autorisée en pixels.

    Returns:
        Image.Image: Image redimensionnée, ou l'originale si assez petite.

    Example:
        >>> img = Image.new("RGB", (1920, 1080))
        >>> resized = resize_image_to_fit(img, 700, 550)
        >>> resized.size
        (700, 393)
    """
    orig_w, orig_h = image.size
    if orig_w <= max_width and orig_h <= max_height:
        return image

    ratio = min(max_width / orig_w, max_height / orig_h)
    return image.resize((int(orig_w * ratio), int(orig_h * ratio)), Image.LANCZOS)


def load_image_safe(filepath: str) -> Image.Image | None:
    """
    Charge une image depuis le disque de façon sécurisée.

    Ouvre le fichier, force le chargement complet en mémoire, et
    convertit en RGBA si le mode n'est pas déjà RGB ou RGBA.
    En cas d'erreur (fichier corrompu, introuvable…), affiche un
    avertissement et retourne None au lieu de lever une exception.

    Args:
        filepath: Chemin absolu vers le fichier image.
                  Ex: "C:/images/photo.jpg"

    Returns:
        Image.Image | None: Objet PIL.Image chargé, ou None si échec.

    Example:
        >>> img = load_image_safe("C:/images/photo.jpg")
        >>> img is not None
        True
        >>> load_image_safe("C:/inexistant.jpg") is None
        True
    """
    try:
        img = Image.open(filepath)
        img.load()
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
        return img
    except Exception as exc:
        print(f"  [AVERTISSEMENT] Impossible de charger '{filepath}': {exc}")
        return None


# =============================================================================
#  SYSTÈME
# =============================================================================

def open_in_explorer(filepath: str) -> None:
    """
    Ouvre l'explorateur Windows et sélectionne le fichier donné.

    Utilise la commande ``explorer /select,"<chemin>"`` pour ouvrir
    le dossier parent et pré-sélectionner le fichier dans l'arborescence.

    Args:
        filepath: Chemin absolu vers le fichier à sélectionner.
                  Ex: "C:/images/photo.jpg"

    Example:
        >>> open_in_explorer("C:/images/photo.jpg")
        # Ouvre l'explorateur sur C:/images/ avec photo.jpg sélectionné.
    """
    subprocess.Popen(f'explorer /select,"{filepath}"', shell=True)


def is_supported_image(folder: str, filename: str) -> bool:
    """
    Vérifie qu'un fichier est une image dont l'extension est supportée.

    Contrôle deux conditions : le chemin pointe vers un fichier réel
    (pas un dossier) et son extension (insensible à la casse) figure
    dans SUPPORTED_EXTENSIONS.

    Args:
        folder:   Chemin absolu du dossier contenant le fichier.
        filename: Nom du fichier (avec extension). Ex: "photo.png"

    Returns:
        bool: True si le fichier existe et a une extension supportée.

    Example:
        >>> is_supported_image("C:/images", "photo.png")
        True
        >>> is_supported_image("C:/images", "readme.txt")
        False
    """
    full_path = os.path.join(folder, filename)
    ext = os.path.splitext(filename)[1].lower()
    return os.path.isfile(full_path) and ext in SUPPORTED_EXTENSIONS


def center_window(window: tk.Toplevel, width: int, height: int) -> None:
    """
    Centre une fenêtre Toplevel sur l'écran.

    Calcule la position (x, y) pour que la fenêtre de dimensions
    données apparaisse au milieu de l'écran, puis applique la géométrie.

    Args:
        window: Fenêtre Toplevel Tkinter à positionner.
        width:  Largeur souhaitée de la fenêtre en pixels.
        height: Hauteur souhaitée de la fenêtre en pixels.

    Example:
        >>> top = tk.Toplevel(root)
        >>> center_window(top, 420, 120)
        # La fenêtre est centrée à l'écran avec 420x120 pixels.
    """
    sx = window.winfo_screenwidth()
    sy = window.winfo_screenheight()
    window.geometry(f"{width}x{height}+{(sx - width) // 2}+{(sy - height) // 2}")
