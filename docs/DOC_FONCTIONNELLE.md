# Gallery Tagger — Documentation fonctionnelle

## Présentation

**Gallery Tagger** est une application de bureau Windows permettant de parcourir un dossier d'images, de visualiser chaque image dans une galerie triptyque, et de renommer les fichiers selon un système de tags structuré.

L'objectif est de normaliser les noms de fichiers images au format :

```
base - [tag1, tag2, tag3] - 1000.png
```

---

## Lancement

```bash
python gallery_tagger.py <chemin_vers_dossier>
```

Le chemin est optionnel :

```bash
python gallery_tagger.py
```

L'application scanne le dossier fourni, charge toutes les images reconnues, puis ouvre la fenêtre graphique maximisée.

Un script PowerShell `Launchme.ps1` est également fourni pour automatiser la vérification de Python, l'installation des dépendances et le lancement :

```powershell
.\Launchme.ps1 "C:\chemin\vers\dossier"
```

Le chemin est aussi optionnel avec le script :

```powershell
.\Launchme.ps1
```

Sans chemin fourni, l'application démarre sur le dernier dossier ouvert enregistré,
ou sur le dossier courant si aucune valeur valide n'est disponible.

### Configuration persistante (`config.json`)

Un fichier `config.json` est stocké à la racine du projet.

- S'il n'existe pas, il est généré automatiquement avec une configuration par défaut.
- S'il existe, il est chargé au démarrage et utilisé.
- Cles supportees : `last_opened_folder`, `max_path_len`, `max_filename_len`.

Exemple :

```json
{
   "last_opened_folder": "C:\\Users\\moi\\Pictures",
   "max_path_len": 220,
   "max_filename_len": 110
}
```

Priorité du dossier chargé au démarrage :
- dossier passé en argument CLI (si valide)
- sinon `last_opened_folder` (si valide)
- sinon dossier courant

---

## Fonctionnalités

### 1. Galerie triptyque

L'écran principal affiche trois images côte à côte :

| Panneau       | Poids (proportion) | Rôle                         |
|---------------|---------------------|------------------------------|
| **Gauche**    | 2 (20 %)            | Image précédente (cliquable) |
| **Centre**    | 6 (60 %)            | Image courante               |
| **Droite**    | 2 (20 %)            | Image suivante (cliquable)   |

- Les images sont redimensionnées dynamiquement pour s'adapter à la taille de la fenêtre tout en conservant leur ratio d'aspect.
- Cliquer sur l'image de gauche ou de droite navigue directement vers cette image.
- Le redimensionnement est géré avec un debounce (en ms) pour éviter les recalculs excessifs.

### 2. Navigation

- **Boutons de navigation** : « ◀  Préc. » et « Suiv.  ▶ » situés dans le panneau "Actions" en bas à droite.
- **Clic sur les panneaux latéraux** de la galerie.
- **Bouton « 🔍  Prochain à tagguer »** : saute au prochain fichier dont le nom ne respecte pas le format `base - [tags] - compteur.ext`. Si tous les fichiers sont conformes, un message informatif est affiché. Situé dans la barre d'information (en haut à droite).
- La navigation est **cyclique** : après la dernière image, on revient à la première.

### 3. Barre d'information

Affiche en permanence une barre en haut du footer contenant :

- **Bouton « ↻  Recharger gallerie »** : recharge les images du dossier courant.
- **Bouton « 📁  Ouvrir un dossier »** : ouvre un sélecteur pour choisir un nouveau dossier.
- Au **centre** : le **nom du fichier courant** entre guillemets et l'**index** du fichier dans la liste
- **Bouton « 📁  Localiser dans l'explorateur »** : ouvre l'explorateur Windows avec le fichier courant pré-sélectionné.
- **Bouton « 🔍  Prochain à tagguer »** (à droite) : saute au prochain fichier non-conforme.

### 4. Panneau de tags (cases à cocher)

- Situé en bas à gauche du footer (colonne 1 de 3).
- Affiche **tous les tags** détectés dans l'ensemble du dossier, avec leur nombre d'occurrences entre parenthèses (ex : `chat (32)`).
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
| `base`       | Partie libre du nom (auteur, source…), conservée à l'identique |
| `[tags]`     | Liste de tags séparés par `, ` entre crochets                  |
| `compteur`   | Numéro à partir de 1000, incrémenté automatiquement si pris (plage 1000–9999) |
| `.ext`       | Extension originale du fichier                                 |

### 6. Panneau de renommage

Situé en bas au centre du footer (colonne 2 de 3), il contient :

1. **Champ « Base du nom »** — éditable, pré-rempli automatiquement avec la portion non-taggée du nom de fichier.
2. **Champ « Tags »** — éditable, pré-rempli automatiquement avec la liste des tags détectés dans le nom courant (séparés par `, `).
3. **Champ « Compteur »** — affichage en lecture seule du compteur (1000 par défaut), incrémenté en cas de conflit de nom.
4. **Champ « Extension »** — affichage en lecture seule de l'extension originale du fichier.
5. **Longueurs** :
   - Longueur totale du chemin complet (dossier + fichier).
   - Longueur du nom de fichier avec extension.

### 7. Panneau d'actions

Situé en bas à droite du footer (colonne 3 de 3), il contient :

1. **Boutons de navigation** :
   - « ◀  Préc. » : navigue vers l'image précédente.
   - « Suiv.  ▶ » : navigue vers l'image suivante.
2. **Bouton « ✔  Renommer fichier »** — applique le renommage avec le nom et les tags du panneau de renommage.

### 8. Renommage

Le processus de renommage suit cette séquence :

1. **Construction** du nom à partir des champs (base + tags) + compteur (1000 par défaut) + extension.
2. **Validation** : le nom doit différer de l'original.
3. **Résolution de conflit** : si le nom existe déjà, le compteur est incrémenté (1001, 1002…).
4. **Vérification de longueur** :
   - Avertissement si le chemin complet dépasse **220 caractères**.
   - Avertissement si le nom de fichier seul dépasse **110 caractères**.
   - Dans les deux cas, l'utilisateur peut choisir de continuer ou d'annuler.
5. **Exécution** : renommage effectif sur le disque.
6. **Rafraîchissement** : les tags sont recalculés, les cases à cocher et l'affichage sont mis à jour.
7. **Confirmation** : une messagebox affiche l'ancien et le nouveau nom.

### 9. Raccourcis et interactions

| Interaction     | Action                                                                 |
|-----------------|------------------------------------------------------------------------|
| `Entrée`        | Appliquer le renommage                                                 |
| `Drag & Drop`   | Déposer un dossier depuis l'Explorateur Windows pour charger ce dossier |

### 10. Drag & Drop de dossier

Il est possible de glisser-déposer un dossier depuis l'Explorateur Windows directement sur la fenêtre de l'application :

1. L'application valide que l'élément déposé est un dossier existant.
2. Les fichiers images du nouveau dossier sont chargés.
3. Le dictionnaire de tags est reconstruit (avec barre de progression).
4. Les cases à cocher, l'affichage et le titre de la fenêtre sont mis à jour.
5. Si le dossier déposé est vide ou ne contient aucune image, un avertissement est affiché et le dossier précédent reste actif.
6. Le dossier chargé est enregistré comme dernier dossier ouvert dans `config.json`.

### 11. Explorateur Windows

Le bouton **« 📁  Localiser dans l'explorateur »** (dans la barre d'information en haut) ouvre le dossier dans l'Explorateur Windows avec le fichier courant pré-sélectionné.

### 12. Écran de chargement

Lors du chargement d'un dossier (au démarrage ou par drag & drop), une barre de progression modale s'affiche pendant le parsing des noms de fichiers pour extraire les tags.

---

## Formats d'images supportés

`.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.tif`, `.webp`

---

## Cas limites gérés

- **Dossier vide** : avertissement affiché ; l'application reste ouverte.
- **Dossier invalide** : erreur et arrêt en ligne de commande.
- **Dossier inaccessible** : messagebox d'erreur.
- **Configuration absente** : `config.json` est créé automatiquement.
- **Configuration invalide** : valeurs par défaut réappliquées automatiquement.
- **Image non chargeable** : texte de substitution affiché dans le panneau (`[Image non chargeable]` ou `[?]`).
- **Nom sans crochets** : les tags sont considérés comme vides, la partie gauche est conservée.
- **Conflit de noms** : incrémentation automatique du compteur (1000 → 9999).
- **Compteurs épuisés** : messagebox d'erreur si les 10 000 noms sont pris.
- **Chemin trop long** : avertissement avec possibilité de continuer.
- **Tous les fichiers conformes** : message informatif quand « 🔍  Prochain à tagguer » ne trouve rien.