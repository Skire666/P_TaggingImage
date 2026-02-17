# Gallery Tagger — Documentation fonctionnelle

## Présentation

**Gallery Tagger** est une application de bureau Windows permettant de parcourir un dossier d’images, de visualiser chaque image dans une galerie triptyque, et de renommer les fichiers selon un système de tags structuré.

L’objectif est de normaliser les noms de fichiers images au format :

```
base - [tag1, tag2, tag3] - 1000.png
```

---

## Lancement

```bash
python gallery_tagger.py <chemin_vers_dossier>
```

L’application scanne le dossier fourni, charge toutes les images reconnues, puis ouvre la fenêtre graphique maximisée.

Un script PowerShell `Launchme.ps1` est également fourni pour automatiser la vérification de Python, l’installation des dépendances et le lancement :

```powershell
.\Launchme.ps1 "C:\chemin\vers\dossier"
```

---

## Fonctionnalités

### 1. Galerie triptyque

L’écran principal affiche trois images côte à côte :

| Panneau       | Poids (proportion) | Rôle                         |
|---------------|---------------------|------------------------------|
| **Gauche**    | 2 (20 %)            | Image précédente (cliquable) |
| **Centre**    | 6 (60 %)            | Image courante               |
| **Droite**    | 2 (20 %)            | Image suivante (cliquable)   |

- Les images sont redimensionnées dynamiquement pour s’adapter à la taille de la fenêtre tout en conservant leur ratio d’aspect.
- Cliquer sur l’image de gauche ou de droite navigue directement vers cette image.
- Le redimensionnement est géré avec un debounce de 150 ms pour éviter les recalculs excessifs.

### 2. Navigation

- **Boutons « Précédent » / « Suivant »** dans la barre d’information.
- **Bouton « Prochain non-taggué »** : saute au prochain fichier dont le nom ne respecte pas le format `base - [tags] - compteur.ext`. Si tous les fichiers sont conformes, un message informatif est affiché.
- **Clic sur les panneaux latéraux** de la galerie.
- La navigation est **cyclique** : après la dernière image, on revient à la première.

### 3. Barre d’information

Affiche en permanence :
- Le **nom du fichier courant** entre guillemets.
- L’**index** du fichier dans la liste (ex : `3 / 42`).

### 4. Panneau de tags (cases à cocher)

- Situé en bas à gauche (50 % de la largeur du footer).
- Affiche **tous les tags** détectés dans l’ensemble du dossier, avec leur nombre d’occurrences entre parenthèses (ex : `chat (5)`).
- Les tags sont triés par **fréquence décroissante**, puis alphabétiquement.
- Les tags présents dans le nom du fichier courant sont **pré-cochés automatiquement**.
- Cocher/décocher un tag met à jour instantanément le champ de renommage.
- Les cases à cocher sont disposées dans un widget Text avec retour à la ligne automatique (`wrap="char"`), avec défilement vertical.

### 5. Format des noms de fichiers

Le format attendu et produit est :

```
base - [tag1, tag2, tag3] - compteur.ext
```

| Section      | Détail                                                         |
|--------------|----------------------------------------------------------------|
| `base`       | Partie libre du nom (auteur, source…), conservée à l’identique |
| `[tags]`     | Liste de tags séparés par `, ` entre crochets                  |
| `compteur`   | Numéro à partir de 1000, incrémenté automatiquement si pris (plage 1000–9999) |
| `.ext`       | Extension originale du fichier                                 |

### 6. Panneau de renommage

Situé en bas à droite (50 % du footer), il contient :

1. **Champ « Nouveau nom »** — éditable, pré-rempli automatiquement au format `base - [tags]`. Modifiable manuellement.
2. **Affichage de l’extension** — non éditable, toujours visible à droite du champ.
3. **Résultat final** — aperçu en temps réel du nom complet avec compteur et extension.
4. **Indicateurs de longueur** :
   - Longueur totale du chemin complet (dossier + fichier).
   - Longueur du nom de fichier avec extension.
5. **Rappel du format** : un label affiche `Format : 'base - [tags] - count'`.
6. **Bouton « Renommer fichier »** — applique le renommage.

### 7. Renommage

Le processus de renommage suit cette séquence :

1. **Construction** du nom à partir du champ + compteur (1000 par défaut) + extension.
2. **Validation** : le nom doit différer de l’original.
3. **Résolution de conflit** : si le nom existe déjà, le compteur est incrémenté (1001, 1002…).
4. **Vérification de longueur** :
   - Avertissement si le chemin complet dépasse **235 caractères**.
   - Avertissement si le nom de fichier seul dépasse **120 caractères**.
   - Dans les deux cas, l’utilisateur peut choisir de continuer ou d’annuler.
5. **Exécution** : renommage effectif sur le disque.
6. **Rafraîchissement** : les tags sont recalculés, les cases à cocher et l’affichage sont mis à jour.
7. **Confirmation** : une messagebox affiche l’ancien et le nouveau nom.

### 8. Raccourcis et interactions

| Interaction     | Action                                                                 |
|-----------------|------------------------------------------------------------------------|
| `Entrée`        | Appliquer le renommage                                                 |
| `Drag & Drop`   | Déposer un dossier depuis l’Explorateur Windows pour charger ce dossier |

### 9. Drag & Drop de dossier

Il est possible de glisser-déposer un dossier depuis l’Explorateur Windows directement sur la fenêtre de l’application :

1. L’application valide que l’élément déposé est un dossier existant.
2. Les fichiers images du nouveau dossier sont chargés.
3. Le dictionnaire de tags est reconstruit (avec barre de progression).
4. Les cases à cocher, l’affichage et le titre de la fenêtre sont mis à jour.
5. Si le dossier déposé est vide ou ne contient aucune image, un avertissement est affiché et le dossier précédent reste actif.

### 10. Explorateur Windows

Le bouton **« Ouvrir dans l’explorateur »** ouvre le dossier dans l’Explorateur Windows avec le fichier courant pré-sélectionné.

### 11. Écran de chargement

Lors du chargement d’un dossier (au démarrage ou par drag & drop), une barre de progression modale s’affiche pendant le parsing des noms de fichiers pour extraire les tags.

---

## Formats d’images supportés

`.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.tif`, `.webp`

---

## Cas limites gérés

- **Dossier vide** : avertissement affiché ; l’application reste ouverte.
- **Dossier invalide** : erreur et arrêt en ligne de commande.
- **Dossier inaccessible** : messagebox d’erreur.
- **Image non chargeable** : texte de substitution affiché dans le panneau (`[Image non chargeable]` ou `[?]`).
- **Nom sans crochets** : les tags sont considérés comme vides, la partie gauche est conservée.
- **Conflit de noms** : incrémentation automatique du compteur (1000 → 9999).
- **Compteurs épuisés** : messagebox d’erreur si les 10 000 noms sont pris.
- **Chemin trop long** : avertissement avec possibilité de continuer.
- **Tous les fichiers conformes** : message informatif quand « Prochain non-taggué » ne trouve rien.
