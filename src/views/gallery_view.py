#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  GalleryView — Vue principale de la galerie d'images
=============================================================================

Construit et expose tous les widgets de l'interface graphique :
galerie triptyque, barre d'information, navigation, renommage et
panneau de tags (cases à cocher).

Ne contient aucune logique métier — la vue se contente de créer
les widgets et d'exposer les StringVar / BooleanVar / Labels
pour être pilotée par le contrôleur.

Layout :
    - Haut  : galerie triptyque (3 cadres -> gauche | centre | droite).
    - Bas   : footer (taille fixe) contenant :
        - Ligne 1 : barre d'info (explorateur | titre | nav)
        - Ligne 2 : tags | renommage

Example:
    >>> view = GalleryView(root, callbacks)
    >>> view.info_var.set("'photo.png'     -     1 / 5")
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections import OrderedDict
from typing import Any, Callable, Mapping

from constants import (
    BG_COLOR, FG_COLOR, ACCENT_COLOR, FRAME_BG,
    ENTRY_BG, ENTRY_FG, CHECK_BG, CHECK_FG,
    HIGHLIGHT, BTN_STYLE, BTN_APPLY_STYLE,
    FOOTER_PX, GALLERY_COL_WEIGHTS, FOOTER_COL_WEIGHTS,
    FONT_FAMILY, FONT_SM, FONT_SM_BOLD, FONT_SM_ITALIC,
    FONT_MD, FONT_MD_BOLD, FONT_LG_BOLD,
)


class GalleryView:
    """
    Vue principale construisant tous les widgets de la galerie.

    Attributes:
        root:             Fenêtre Tk principale.
        info_var:         StringVar du compteur (nom + index).
        new_name_var:     StringVar du champ de renommage.
        ext_label_var:    StringVar de l'extension affichée.
        prev_label:       Label de l'image précédente.
        center_label:     Label de l'image centrale.
        next_label:       Label de l'image suivante.
        check_vars:       { tag: BooleanVar } pour les cases à cocher.

    Example:
        >>> view = GalleryView(root, callbacks)
    """

    def __init__(
        self,
        root: tk.Tk,
        callbacks: Mapping[str, Callable[..., Any]],
    ) -> None:
        """
        Construit l'intégralité de l'interface graphique.

        Args:
            root:      Fenêtre Tk parente.
            callbacks: Dictionnaire de callbacks du contrôleur :
                       - "go_previous" : navigation arrière
                       - "go_next"     : navigation avant
                       - "apply_rename": renommage
                       - "open_explorer": ouvrir l'explorateur
                       - "reload_current_folder": recharger le dossier courant
                       - "on_tag_toggled": tag coché/décoché

        Example:
            >>> view = GalleryView(root, callbacks)
        """
        self.root = root
        self.callbacks = dict(callbacks)
        self.check_vars: dict[str, tk.BooleanVar] = {}

        # --- Footer (packé en premier pour réserver l'espace) ---
        footer = self._build_footer()
        self._build_info_bar(footer)
        self._build_tags_panel(footer)
        self._build_rename_panel(footer)

        # --- Galerie (prend toute la place restante) ---
        self._build_gallery_frame()

    # =================================================================
    #  Galerie triptyque
    # =================================================================

    def _build_gallery_frame(self) -> None:
        """
        Construit la zone galerie triptyque (3 cadres d'images).

        Crée un Frame à 3 colonnes fixes (lié à 'GALLERY_COL_WEIGHTS').
        La hauteur s'adapte à la place restante au-dessus du footer.

        Example:
            >>> self._build_gallery_frame()
            >>> self.center_label.winfo_exists()
            True
        """
        self.gallery_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.gallery_frame.pack(
            side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(10, 5),
        )
        for col, weight in enumerate(GALLERY_COL_WEIGHTS):
            self.gallery_frame.columnconfigure(col, weight=weight, uniform="gallery")
        self.gallery_frame.rowconfigure(0, weight=1)

        self.prev_label = self._create_image_panel(
            self.gallery_frame, " Précédente ", ACCENT_COLOR, col=0, padx=(0, 5),
            on_click=self.callbacks["go_previous"],
        )
        self.center_label = self._create_image_panel(
            self.gallery_frame, " Image courante ", HIGHLIGHT, col=1, padx=5,
            font_size=12,
        )
        self.next_label = self._create_image_panel(
            self.gallery_frame, " Suivante ", ACCENT_COLOR, col=2, padx=(5, 0),
            on_click=self.callbacks["go_next"],
        )

    def _create_image_panel(
        self, parent: tk.Frame, title: str, fg_color: str, *,
        col: int, padx: int | tuple[int, int],
        font_size: int = 12, on_click: Callable | None = None,
    ) -> tk.Label:
        """
        Crée un panneau d'image (LabelFrame + Label) dans la galerie.

        Args:
            parent:    Frame parent (la grille de la galerie).
            title:     Titre affiché sur le bord du LabelFrame.
            fg_color:  Couleur du titre du LabelFrame.
            col:       Index de colonne dans la grille (0, 1 ou 2).
            padx:      Padding horizontal (int ou tuple[gauche, droite]).
            font_size: Taille de police du titre. 9 par défaut.
            on_click:  Callback sans argument déclenché au clic.

        Returns:
            tk.Label: Le label intérieur destiné à recevoir l'image.
        """
        lf = tk.LabelFrame(
            parent, text=title, bg=FRAME_BG, fg=fg_color,
            font=(FONT_FAMILY, font_size, "bold"), labelanchor="n",
        )
        lf.grid(row=0, column=col, sticky="nsew", padx=padx)

        cursor = "hand2" if on_click else ""
        label = tk.Label(lf, bg=FRAME_BG, cursor=cursor)
        label.pack(expand=True, fill=tk.BOTH)
        if on_click:
            label.bind("<Button-1>", lambda _: on_click())
        return label

    # =================================================================
    #  Footer (hauteur fixe)
    # =================================================================

    def _build_footer(self) -> tk.Frame:
        """
        Crée le footer de hauteur fixe en bas de la fenêtre.

        Organisation interne en grille :
            - Ligne 0  : barre d'information (columnspan 2)
            - Ligne 1  : tags | renommage

        Returns:
            tk.Frame: Frame footer prêt à recevoir ses enfants.
        """
        frame = tk.Frame(self.root, bg=BG_COLOR, height=FOOTER_PX)
        frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10))
        frame.pack_propagate(False)
        frame.grid_propagate(False)

        frame.columnconfigure(0, weight=FOOTER_COL_WEIGHTS[0], uniform="footer_split")
        frame.columnconfigure(1, weight=FOOTER_COL_WEIGHTS[1], uniform="footer_split")
        frame.rowconfigure(0, weight=0)
        frame.rowconfigure(1, weight=1)
        return frame

    # =================================================================
    #  Ligne 1 du footer — barre d'information
    # =================================================================

    def _build_info_bar(self, parent: tk.Frame) -> None:
        """
        Construit la barre d'information (ligne 1 du footer).

        Contenu :
            - Gauche  : bouton « Ouvrir l'explorateur »
            - Centre  : titre du fichier + index / compteur
            - Droite  : boutons Précédent et Suivant

        Args:
            parent: Frame footer.
        """
        bar = tk.Frame(parent, bg=BG_COLOR)
        bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        tk.Button(
            bar, text="📁  Ouvrir dans l'explorateur",
            command=self.callbacks["open_explorer"], **BTN_STYLE,
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            bar, text="↻  Recharger",
            command=self.callbacks["reload_current_folder"], **BTN_STYLE,
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.info_var = tk.StringVar(value="")
        tk.Label(
            bar, textvariable=self.info_var,
            bg=BG_COLOR, fg=FG_COLOR,
            font=FONT_LG_BOLD, anchor="center",
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(
            bar, text="Suivant  ▶",
            command=self.callbacks["go_next"], **BTN_STYLE,
        ).pack(side=tk.RIGHT, padx=(5, 0))
        tk.Button(
            bar, text="◀  Précédent",
            command=self.callbacks["go_previous"], **BTN_STYLE,
        ).pack(side=tk.RIGHT, padx=(5, 0))
        tk.Button(
            bar, text="🔍  Prochain à tagguer",
            command=self.callbacks["go_next_untagged"], **BTN_STYLE,
        ).pack(side=tk.RIGHT, padx=(5, 0))

    # =================================================================
    #  Ligne 2 du footer — Tags (gauche)
    # =================================================================

    def _build_tags_panel(self, parent: tk.Frame) -> None:
        """
        Construit le panneau scrollable des tags (cases à cocher).

        Utilise un widget Text en mode wrap="char" pour disposer
        automatiquement les checkboxes avec retour à la ligne natif.

        Args:
            parent: Frame footer.
        """
        outer = tk.LabelFrame(
            parent, text=" Tags détectés ", bg=FRAME_BG, fg=ACCENT_COLOR,
            font=FONT_SM_BOLD, labelanchor="nw",
        )
        outer.grid(row=1, column=0, sticky="nsew", padx=(0, 5))

        scrollbar = ttk.Scrollbar(outer, orient="vertical")

        self._tags_text = tk.Text(
            outer, bg=FRAME_BG, wrap="char", cursor="arrow",
            highlightthickness=0, borderwidth=0,
            yscrollcommand=scrollbar.set,
            state="disabled",
        )
        scrollbar.configure(command=self._tags_text.yview)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._tags_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # =================================================================
    #  Ligne 2 du footer — Renommage (droite)
    # =================================================================

    def _build_rename_panel(self, parent: tk.Frame) -> None:
        """
        Construit le panneau de renommage.

        Placé dans la ligne 2 du footer (colonne 1).

        Args:
            parent: Frame footer.
        """
        outer = tk.LabelFrame(
            parent, text=" Renommage ", bg=FRAME_BG, fg=ACCENT_COLOR,
            font=FONT_SM_BOLD, labelanchor="nw",
        )
        outer.grid(row=1, column=1, sticky="nsew", padx=(5, 0))

        # --- Ligne 1 : Nouveau nom ---
        row1 = tk.Frame(outer, bg=FRAME_BG)
        row1.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(8, 4))

        tk.Label(row1, text="Nouveau nom :", bg=FRAME_BG, fg=FG_COLOR,
                 font=FONT_MD).pack(side=tk.LEFT)

        self.new_name_var = tk.StringVar(value="")
        tk.Entry(
            row1, textvariable=self.new_name_var,
            bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=FG_COLOR,
            font=FONT_MD, relief="flat",
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        self.ext_label_var = tk.StringVar(value="")
        tk.Label(row1, textvariable=self.ext_label_var, bg=FRAME_BG,
                 fg=ACCENT_COLOR, font=FONT_MD_BOLD).pack(side=tk.LEFT)

        # --- Ligne 2 : Résultat final ---
        row2 = tk.Frame(outer, bg=FRAME_BG)
        row2.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(4, 4))

        tk.Label(row2, text="Résultat final :", bg=FRAME_BG, fg=FG_COLOR,
                 font=FONT_SM).pack(side=tk.LEFT)

        self.preview_var = tk.StringVar(value="")
        tk.Label(
            row2, textvariable=self.preview_var,
            bg=FRAME_BG, fg=ACCENT_COLOR,
            font=FONT_SM_ITALIC, anchor="w",
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

        # --- Ligne 3 : Longueurs + Bouton Appliquer ---
        row3 = tk.Frame(outer, bg=FRAME_BG)
        row3.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(0, 0))

        # Longueur totale du chemin
        self.path_len_var = tk.StringVar(value="")
        tk.Label(
            row3, text="Long. Chemin :", bg=FRAME_BG, fg=FG_COLOR,
            font=FONT_SM,
        ).pack(side=tk.LEFT)
        tk.Label(
            row3, textvariable=self.path_len_var, bg=FRAME_BG,
            fg=ACCENT_COLOR, font=FONT_SM_BOLD, width=4, anchor="w",
        ).pack(side=tk.LEFT)

        # Longueur du fichier avec extension
        self.filename_len_var = tk.StringVar(value="")
        tk.Label(
            row3, text="Long. Fichier :", bg=FRAME_BG, fg=FG_COLOR,
            font=FONT_SM,
        ).pack(side=tk.LEFT)
        tk.Label(
            row3, textvariable=self.filename_len_var, bg=FRAME_BG,
            fg=ACCENT_COLOR, font=FONT_SM_BOLD, width=4, anchor="w",
        ).pack(side=tk.LEFT)

        tk.Label(
            row3, text="Forme : 'base - [tags] - count'", bg=FRAME_BG, fg=FG_COLOR,
            font=FONT_SM,
        ).pack(side=tk.LEFT)

        tk.Button(
            row3, text="✔  Renommer fichier",
            command=self.callbacks["apply_rename"], **BTN_APPLY_STYLE,
        ).pack(side=tk.RIGHT)

    # =================================================================
    #  Cases à cocher
    # =================================================================

    def build_tag_checkboxes(self, tag_dict: OrderedDict[str, int]) -> None:
        """
        Crée une case à cocher par tag du dictionnaire.

        Insère chaque checkbox dans le widget Text qui gère
        automatiquement le retour à la ligne.

        Args:
            tag_dict: Dictionnaire { tag: compteur } trié.
        """
        self._tags_text.configure(state="normal")
        self._tags_text.delete("1.0", tk.END)
        self.check_vars.clear()

        for tag, count in tag_dict.items():
            var = tk.BooleanVar(value=False)
            self.check_vars[tag] = var

            cb = tk.Checkbutton(
                self._tags_text, text=f"{tag} ({count})",
                variable=var, command=self.callbacks["on_tag_toggled"],
                bg=CHECK_BG, fg=CHECK_FG, selectcolor=BG_COLOR,
                activebackground=CHECK_BG, activeforeground=ACCENT_COLOR,
                font=FONT_SM, anchor="w", padx=8, pady=2,
            )
            self._tags_text.window_create(tk.END, window=cb)

        self._tags_text.configure(state="disabled")

    # =================================================================
    #  Méthodes d'affichage pour le contrôleur
    # =================================================================

    def set_image(
        self,
        label: tk.Label,
        photo: Any | None,
        fallback_text: str = "",
    ) -> None:
        """
        Affiche une image dans un label, ou un texte de remplacement.

        Args:
            label:         Widget tk.Label cible.
            photo:         PhotoImage à afficher, ou None pour le fallback.
            fallback_text: Texte affiché si photo est None.
        """
        if photo:
            label.config(image=photo, text="")
        else:
            label.config(image="", text=fallback_text, fg=HIGHLIGHT)
