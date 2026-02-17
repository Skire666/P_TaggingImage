#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  LoadingView — Écran de chargement avec barre de progression
=============================================================================

Fenêtre modale affichée pendant le parsing des noms de fichiers.
Informe l'utilisateur de l'avancement via un label de texte et
une barre de progression ttk.

Example:
    >>> loading = LoadingView(root, total=100)
    >>> loading.update(50, 100)
    >>> loading.close()
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from constants import (
    BG_COLOR, FG_COLOR, FRAME_BG, ACCENT_COLOR, LOADING_WIN_SIZE,
    FONT_MD,
)
from utils import center_window


class LoadingView:
    """
    Fenêtre modale affichant une barre de progression.

    Affichée pendant le parsing des noms de fichiers pour informer
    l'utilisateur de l'avancement du traitement.

    Attributes:
        top:          Fenêtre Toplevel modale.
        label:        Label affichant le texte de statut.
        progress_bar: Barre de progression ttk.

    Example:
        >>> loading = LoadingView(root, total=50)
        >>> loading.update(25, 50)   # 50 % terminé
        >>> loading.close()          # Ferme la fenêtre
    """

    def __init__(self, root: tk.Tk, total: int) -> None:
        """
        Initialise et affiche l'écran de chargement.

        Args:
            root:  Fenêtre Tk parente (l'écran sera modal par rapport à elle).
            total: Nombre total d'éléments à traiter (maximum de la barre).

        Example:
            >>> loading = LoadingView(root, total=100)
        """
        self.top = self._create_toplevel(root)
        self.label = self._create_label()
        self.progress_bar = self._create_progressbar(total)

    def _create_toplevel(self, root: tk.Tk) -> tk.Toplevel:
        """
        Crée et configure la fenêtre modale centrée.

        La fenêtre est non-redimensionnable, centrée à l'écran,
        et bloque l'interaction avec la fenêtre parente (grab_set).

        Args:
            root: Fenêtre Tk parente.

        Returns:
            tk.Toplevel: Fenêtre modale configurée.

        Example:
            >>> top = self._create_toplevel(root)
            >>> top.title()
            'Chargement…'
        """
        top = tk.Toplevel(root)
        top.title("Chargement…")
        top.configure(bg=BG_COLOR)
        top.resizable(False, False)
        top.grab_set()
        center_window(top, *LOADING_WIN_SIZE)
        return top

    def _create_label(self) -> tk.Label:
        """
        Crée le label de statut indiquant l'avancement.

        Le texte initial est "Analyse des fichiers en cours…" et sera
        mis à jour via la méthode update().

        Returns:
            tk.Label: Widget label packé dans la fenêtre modale.

        Example:
            >>> label = self._create_label()
            >>> label.cget("text")
            'Analyse des fichiers en cours…'
        """
        label = tk.Label(
            self.top, text="Analyse des fichiers en cours…",
            bg=BG_COLOR, fg=FG_COLOR, font=FONT_MD,
        )
        label.pack(pady=(15, 5))
        return label

    def _create_progressbar(self, total: int) -> ttk.Progressbar:
        """
        Crée et configure la barre de progression ttk.

        Utilise le thème "clam" avec un style personnalisé aux couleurs
        du thème Catppuccin Mocha.

        Args:
            total: Valeur maximale de la barre (nombre total d'éléments).

        Returns:
            ttk.Progressbar: Widget barre de progression packé.

        Example:
            >>> bar = self._create_progressbar(100)
            >>> bar["maximum"]
            100
        """
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Loading.Horizontal.TProgressbar",
            troughcolor=FRAME_BG, background=ACCENT_COLOR, thickness=22,
        )
        bar = ttk.Progressbar(
            self.top, orient="horizontal", length=360,
            mode="determinate", maximum=total,
            style="Loading.Horizontal.TProgressbar",
        )
        bar.pack(pady=(5, 15))
        return bar

    def update(self, current: int, total: int) -> None:
        """
        Met à jour la barre de progression et le texte de statut.

        Force le rafraîchissement visuel via update_idletasks() pour que
        la barre se mette à jour même pendant un traitement bloquant.

        Args:
            current: Nombre d'éléments traités jusqu'ici.
            total:   Nombre total d'éléments à traiter.

        Example:
            >>> loading.update(42, 87)
            # Affiche : "Analyse des fichiers : 42 / 87"
        """
        self.progress_bar["value"] = current
        self.label.config(text=f"Analyse des fichiers : {current} / {total}")
        self.top.update_idletasks()

    def close(self) -> None:
        """
        Ferme l'écran de chargement.

        Libère le grab modal (réactive la fenêtre parente) puis
        détruit la fenêtre Toplevel.

        Example:
            >>> loading.close()
            # La fenêtre disparaît, le focus revient à la fenêtre principale.
        """
        self.top.grab_release()
        self.top.destroy()
