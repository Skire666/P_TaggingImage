<#
.SYNOPSIS
    Lance l'application Gallery Tagger sur un dossier d'images.

.DESCRIPTION
    Script de lancement pour Gallery Tagger (Windows 11 / PowerShell 5.1+).

    Ce script effectue les étapes suivantes dans l'ordre :
      1. Validation du dossier fourni en paramètre (existence, permissions, contenu).
      2. Résolution des chemins internes (point d'entrée Python, fichier requirements.txt).
      3. Détection et vérification de l'interpréteur Python (version minimale, présence de pip).
      4. Installation/mise à jour des dépendances Python via pip.
      5. Lancement de l'application gallery_tagger.py.

    Chaque étape est protégée par un bloc try/catch avec des messages d'erreur explicites.
    Le script retourne le code de sortie de l'application Python (0 = succès).

.PARAMETER FolderPath
    Chemin (absolu ou relatif) vers le dossier contenant les images à parcourir.
    "./" est utilisé par défaut si aucun chemin n'est fourni.
    Le dossier doit exister, être accessible en lecture, et idéalement contenir des images

.EXAMPLE
    .\Launchme.ps1
    .\Launchme.ps1 ./

    Lance Gallery Tagger sur un chemin absolu (ou défaut si non spécifié).

.EXAMPLE
    .\Launchme.ps1 .\images

    Lance Gallery Tagger sur un chemin relatif au répertoire courant.

.NOTES
    Auteur       : IA
    Prérequis    : Python 3.10+, pip, PowerShell 5.1+
    Fichiers     : src\gallery_tagger.py (point d'entrée), src\requirements.txt (dépendances)
    Codes sortie : 0 = succès, 1 = erreur de validation/lancement, autre = code retourné par Python.
#>

# ============================================================================
# DÉCLARATION DES PARAMÈTRES
# ============================================================================

[CmdletBinding()]
param(
    # Chemin vers le dossier d'images (optionnelle).
    # - Mandatory       : le script peut démarrer sans cette valeur.
    [Parameter(Mandatory = $false, HelpMessage = "Chemin vers le dossier d'images.")]
    [string]$FolderPath
)

# ============================================================================
# CONFIGURATION GLOBALE
# ============================================================================

# Mode strict : interdit les variables non déclarées, les propriétés inexistantes, etc.
Set-StrictMode -Version Latest

# Toute erreur non interceptée arrête immédiatement l'exécution.
$ErrorActionPreference = 'Stop'

# --- Version Python minimale requise (3.10+) ---
$MinPythonVersion = [version]'3.10'

# ============================================================================
# ÉTAPE 1 : VALIDATION DU DOSSIER D'IMAGES
# Objectif : s'assurer que le dossier existe, est accessible, et contient des images.
# En cas d'échec, le script s'arrête avec un message d'erreur clair (exit 1).
# ============================================================================

try {
    # Nettoyer les éventuelles quotes ou espaces en début/fin de chaîne
    # (utile si le chemin est copié-collé depuis l'explorateur avec des guillemets).
    $FolderPath = $FolderPath.Trim('"', "'", ' ')

    # Si aucun chemin n'est fourni, utiliser le répertoire courant (./).
    if ([string]::IsNullOrWhiteSpace($FolderPath)) {
        $FolderPath = "./"
        Write-Warning "Aucun chemin fourni, utilisation du repertoire courant : '$FolderPath'"
    }

    # Résoudre le chemin relatif en chemin absolu.
    # -ErrorAction Stop : lève une exception si le chemin n'existe pas.
    $ResolvedFolder = (Resolve-Path -Path $FolderPath -ErrorAction Stop).Path

    # Vérifier que le chemin résolu pointe bien vers un dossier (et non un fichier).
    if (-not (Test-Path -Path $ResolvedFolder -PathType Container)) {
        throw "Le chemin '$FolderPath' n'est pas un repertoire valide."
    }

    # Tenter de lire le contenu du dossier pour vérifier les permissions d'accès.
    # On récupère un seul élément (-First 1) pour minimiser le coût de l'opération.
    # -Force : inclut les fichiers/dossiers cachés dans la vérification.
    $null = Get-ChildItem -Path $ResolvedFolder -Force -ErrorAction Stop | Select-Object -First 1
}
catch [System.Management.Automation.ItemNotFoundException] {
    # Le chemin fourni ne correspond à aucun élément du système de fichiers.
    Write-Error "Le dossier '$FolderPath' n'existe pas."
    exit 1
}
catch [System.UnauthorizedAccessException] {
    # L'utilisateur courant n'a pas les droits de lecture sur le dossier.
    Write-Error "Acces refuse au dossier '$FolderPath'. Verifiez les permissions."
    exit 1
}
catch {
    # Toute autre erreur inattendue (disque inaccessible, chemin malformé, etc.).
    Write-Error "Validation du dossier echouee : $_"
    exit 1
}

# ============================================================================
# ÉTAPE 2 : RÉSOLUTION DES CHEMINS INTERNES
# Objectif : construire les chemins absolus vers le point d'entrée Python
# et le fichier de dépendances, à partir de l'emplacement de ce script.
# ============================================================================

# Récupérer le dossier parent du script en cours d'exécution.
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Point d'entrée principal de l'application Python (obligatoire).
$SrcEntryPoint = Join-Path $ScriptDir 'src\gallery_tagger.py'

# Fichier de dépendances pip (optionnel, mais recommandé).
$Requirements = Join-Path $ScriptDir 'src\requirements.txt'

# Vérifier que le fichier Python principal existe.
if (-not (Test-Path -Path $SrcEntryPoint)) {
    Write-Error "Point d'entree introuvable : '$SrcEntryPoint'. Verifiez l'integrite de l'installation."
    exit 1
}

# ============================================================================
# ÉTAPE 3 : VÉRIFICATION DE L'INTERPRÉTEUR PYTHON
# ============================================================================
# Objectif : localiser un interpréteur Python compatible dans le PATH,
# vérifier que sa version est suffisante et que pip est fonctionnel.

try {
    # --- 3a. Recherche de l'exécutable Python ---
    # On cherche d'abord "python" (convention Windows), puis "python3" en fallback
    # (convention Linux/macOS, parfois présent sur Windows via le Microsoft Store).
    $Python = Get-Command python -ErrorAction SilentlyContinue |
              Select-Object -First 1 -ExpandProperty Source

    if (-not $Python) {
        $Python = Get-Command python3 -ErrorAction SilentlyContinue |
                  Select-Object -First 1 -ExpandProperty Source
    }

    if (-not $Python) {
        throw "Python n'est pas installe ou n'est pas dans le PATH."
    }

    # --- 3b. Vérification de la version (>= 3.10) ---
    # Exécuter "python --version" et comparer avec $MinPythonVersion via [version].
    $VersionRaw = & $Python --version 2>&1

    if ($VersionRaw -match '(\d+\.\d+\.\d+)') {
        $DetectedVersion = [version]$Matches[1]

        if ($DetectedVersion -lt $MinPythonVersion) {
            throw "Python $MinPythonVersion+ requis, version detectee : $DetectedVersion"
        }

        Write-Host "Python detecte : $DetectedVersion ($Python)" -ForegroundColor Cyan
    } else {
        throw "Impossible de determiner la version de Python (sortie : '$VersionRaw')."
    }

    # --- 3c. Vérification de pip ---
    # pip est nécessaire pour installer les dépendances.
    # On vérifie sa disponibilité via "python -m pip --version".
    & $Python -m pip --version | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "Le module pip n'est pas disponible. Installez-le avec : python -m ensurepip --upgrade"
    }
}
catch {
    Write-Error "Verification Python echouee : $_"
    exit 1
}

# ============================================================================
# ÉTAPE 4 : INSTALLATION / MISE À JOUR DES DÉPENDANCES
# ============================================================================
# Objectif : si un fichier requirements.txt existe, installer ou mettre à jour
# les paquets Python nécessaires via pip. L'option --quiet limite la verbosité.

if (Test-Path -Path $Requirements) {
    try {
        Write-Host "Verification des dependances..." -ForegroundColor Yellow

        # Exécuter pip install avec le fichier requirements.txt.
        # --quiet : n'affiche que les erreurs et les avertissements.
        & $Python -m pip install --quiet --requirement $Requirements

        if ($LASTEXITCODE -ne 0) {
            # pip a rencontré une erreur (paquet introuvable, conflit de versions, etc.).
            throw "pip a retourne une erreur (code $LASTEXITCODE). Consultez la sortie ci-dessus."
        }

        Write-Host "Dependances OK." -ForegroundColor Green
    }
    catch {
        Write-Error "Echec de l'installation des dependances : $_"
        exit 1
    }
} else {
    # Le fichier requirements.txt est absent. Ce n'est pas bloquant,
    # mais les dépendances ne seront pas vérifiées automatiquement.
    Write-Warning "Fichier requirements.txt introuvable ('$Requirements'). Les dependances ne seront pas verifiees."
}

# ============================================================================
# ÉTAPE 5 : LANCEMENT DE L'APPLICATION
# ============================================================================
# Objectif : exécuter le script Python principal avec le dossier d'images
# en argument. Le code de sortie de Python est propagé au script appelant.

try {
    Write-Host "Lancement de Gallery Tagger sur : $ResolvedFolder" -ForegroundColor Cyan
    Write-Host ("-" * 50) -ForegroundColor DarkGray

    # Appel de l'interpréteur Python avec le point d'entrée et le dossier résolu.
    # L'opérateur & (call) permet d'exécuter un chemin contenant des espaces.
    & $Python $SrcEntryPoint $ResolvedFolder

    # Vérifier le code de sortie de l'application.
    # Un code différent de 0 indique une erreur côté Python.
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Gallery Tagger s'est termine avec le code de sortie $LASTEXITCODE."
    }
}
catch {
    Write-Error "Erreur lors de l'execution de Gallery Tagger : $_"
    exit 1
}

# Propager le code de sortie de l'application Python au processus parent.
exit $LASTEXITCODE
