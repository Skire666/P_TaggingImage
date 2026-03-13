# P_TaggingImage

### Description :
Application Win11_x64 permettant de parcourir des images et de renommer les fichiers selon un système de tags.

---

### Usage
Pour lancer l'application, passer par le script PowerShell "Launchme.ps1"

Exemples :

```powershell
.\Launchme.ps1
.\Launchme.ps1 "C:\chemin\vers\dossier"
```

Sans argument, l'application charge le dossier selon cet ordre :
- `config.json` (`last_opened_folder`) si valide
- sinon le dossier courant

Le fichier `config.json` est créé automatiquement s'il n'existe pas.

---

### Programmé en
Python 3.10+

---

### Documentation
- Utilisateur : "docs/DOC_FONCTIONNELLE.md"
- Technique   : "docs/DOC_TECHNIQUE.md"

---

![Aperçu de l'application (screenshot)](docs/Screenshot.jpg "Aperçu de l'application (screenshot)")

// FIN
