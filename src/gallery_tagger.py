#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  Gallery Tagger — Point d'entrée principal
=============================================================================

Description :
    Application graphique (Tkinter) permettant de :
      1. Parcourir un dossier d'images passé en argument.
      2. Parser les noms de fichiers pour en extraire des tags (mots).
      3. Afficher une galerie triptyque (image précédente / courante / suivante).
      4. Proposer un système de cases à cocher basées sur les tags détectés,
         pour composer un nouveau nom de fichier.
      5. Renommer le fichier courant avec le nom composé.
      6. Ouvrir l'explorateur Windows sur le fichier courant.

Architecture MVC :
    - constants.py                    → Constantes, thème, styles
    - utils.py                        → Fonctions utilitaires (parsing, images, système)
    - models/file_model.py            → Modèle de gestion des fichiers
    - models/tag_model.py             → Modèle de gestion des tags
    - views/loading_view.py           → Écran de chargement
    - views/gallery_view.py           → Vue principale (galerie, tags, renommage)
    - controllers/gallery_controller.py → Contrôleur principal

Usage :
    python gallery_tagger.py <chemin_vers_dossier>

Dépendances :
    - Python 3.8+
    - Pillow (pip install Pillow)

Auteur  : Assistant IA
Date    : 2026-02-13
Licence : MIT
=============================================================================
"""

from __future__ import annotations

import os
import sys
import argparse

from controllers.gallery_controller import GalleryController


# =============================================================================
#  POINT D'ENTRÉE
# =============================================================================

def parse_arguments() -> argparse.Namespace:
    """
    Parse les arguments de la ligne de commande.

    Définit un argument positionnel obligatoire "dossier" (chemin vers
    un dossier d'images). Affiche l'aide et des exemples d'utilisation.

    Returns:
        argparse.Namespace: Objet contenant l'attribut 'dossier' (str).

    Example:
        >>> # Appel: python gallery_tagger.py ./images
        >>> args = parse_arguments()
        >>> args.dossier
        './images'
    """
    parser = argparse.ArgumentParser(
        description="Gallery Tagger — Visualiseur d'images avec tags et renommage.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemples :\n"
            '  python gallery_tagger.py "C:\\Users\\moi\\Images\\dossier"\n'
            "  python gallery_tagger.py ./images\n"
        ),
    )
    parser.add_argument(
        "dossier", type=str,
        help="Chemin vers le dossier contenant les images.",
    )
    return parser.parse_args()


def main() -> None:
    """
    Point d'entrée principal du programme.

    Séquence :
    1. Parse les arguments CLI via parse_arguments().
    2. Vérifie que le chemin pointe vers un dossier existant.
    3. Affiche le dossier cible en console.
    4. Lance GalleryController (boucle Tkinter).

    Quitte avec code 1 si le dossier est invalide.

    Example:
        >>> # python gallery_tagger.py "C:/mes_images"
        >>> main()
        Dossier cible : C:/mes_images
        Lancement de l'interface graphique…
    """
    args = parse_arguments()
    folder = args.dossier

    if not os.path.isdir(folder):
        print(f"ERREUR : '{folder}' n'est pas un dossier valide.")
        sys.exit(1)

    print(f"Dossier cible : {os.path.abspath(folder)}")
    print("Lancement de l'interface graphique…")
    GalleryController(folder)


if __name__ == "__main__":
    main()
