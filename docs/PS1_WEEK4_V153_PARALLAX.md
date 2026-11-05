# Week 4 v153 — séparation du fond et parallaxe

## Référence et comparaison

Cette passe part du paquet converti Week 4 v152, sans régénérer les sons ni les charts. L’asset de scène officiel épinglé reste `724eba9de9e76761d9cefd52169926bc51c760a5`.

Le défaut visible dans les essais précédents venait du fait que le coucher de soleil, la limousine lointaine et les danseurs étaient composés dans la même image de fond. Le renderer appliquait alors à l’ensemble le déplacement de caméra plein écran. Il ne pouvait donc pas reproduire le facteur de défilement `0.4` des éléments lointains décrit dans `assets/preload/data/stages/limoRide.json`, distinct du facteur `1.0` de la limousine principale.

La limousine principale conserve son ancrage officiel converti (`-20,88`), sa taille, son ordre d’occlusion et les positions relatives des personnages. La comparaison avec le JSON de scène et les captures montre qu’elle doit rester assez large pour que Mom et BF soient visuellement sur la voiture. Cette passe ne la réduit ni ne la déplace.

## Changement

`ps1/compose_week4_layers_v153.py` repart du paquet immuable v152, reconstruit uniquement les deux pages de fond avec le coucher de soleil seul et place la limousine lointaine plus quatre cels officiels des henchmen dans une région libre de la page Week 4 existante. Le renderer dessine cette nouvelle couche séparément avec un scroll caméra de `102/256` (≈0,4). La limousine principale garde un scroll de `256/256` (1,0). Les deux couches utilisent la même CLUT 8bpp.

La région ajoutée est `240×64` texels à `(8,112)` dans la page logique 7. Aucun nouvel atlas, transfert de page, lecture CD ou format n’est ajouté. Le dessin ajoute une primitive de décor et n’alloue pas de tampon RAM persistant.

## Ressources et configuration

- Paquet Week 4 v152 : SHA-256 `CE3872A1C10E14AEDE358F3D9824000C7DC4199E1EEF58298B4E65AE7B23F743`.
- Paquet Week 4 v153 : SHA-256 `C7B0B033426833CC0A6F054F31C3987FCE2C77A8B82F15337743702EC55CB6D6`.
- CLUT inchangée : SHA-256 `ED2E297F98DA203D96ADCB1280A2C4BCD0D450CA296C083C6012EFF667EC95E1`.
- Format inchangé : huit pages 256×256 en 8bpp plus une CLUT 512 octets, soit 524 800 octets.
- Pages 2–6, pages BF partagées, et fichiers audio/chart : inchangés. Le sidecar BF garde le SHA-256 `D3C6F317C0B108233C5D81774FA97775AFE2B2D40D98F46528EAD70543B67310`.
- Source locale utilisée : HEAD Git `7057882fa4c481fb878de4cc27d3a827179f7ddd`, avec modifications de travail déjà présentes; SHA-256 de `ps1/spu_probe.c` compilé : `A404AA95A48EC69430534D056B9A6DFC43C0B5169820445E063ECEC87D54C485`. Cette référence locale n’est pas présentée comme un commit propre correspondant à lui seul au binaire.
- Répertoire CMake/Ninja conservé : `C:/Users/Manau47/Documents/Codex/week4-v153-debug-build/`, configuré `Debug`, PSn00bSDK 0.24, GCC MIPS 12.3.0; diagnostics de démarrage et de jeu désactivés, pistes Dad activées.
- Le dry-run a annoncé cinq actions : génération existante du sidecar BF, compilation de `spu_probe.c`, compilation de `stream.c`, édition de liens et création ISO. Aucune conversion générale audio/chart/graphique n’a été prévue.

## Build et contrôles

Compilation et image disque terminées. BIN : 339 346 560 octets (`MODE2/2352`, 144 280 secteurs). PS-X EXE : 1 030 144 octets. `SYSTEM.CNF` et `FUNKIN.EXE` sont conservés en tête du répertoire racine ISO.

- PS-X EXE SHA-256 : `AFD349249E601DD59AE3FF2242AA0B53C24C3AAC88772EEECA99D5B6B448A732`.
- BIN SHA-256 : `3482B62297B81AFEB7A57FFDBB8C7CD067FCD7589ADA08CD67D0959E97BA8699`.
- CUE SHA-256 livré : `DDC05B754047E073BC37B52CE7B66B827422A793F00C3699A700F448F6647EE5`.

Le CUE/BIN a été copié dans un nouveau dossier, sans écraser les livraisons précédentes. La ligne `FILE` du CUE a été ajustée au nom du nouveau BIN.

## État de validation

**Vérifié statiquement et compilé :** dimensions/format/empreintes du paquet, CLUT inchangée, région de page libre, réutilisation de huit pages, fichiers audio et charts inchangés, construction de l’exécutable et de l’ISO.

**À observer par l’utilisateur :** démarrage, fond et quatre danseurs visibles sans éclair, déplacement relatif de la couche distante entre focus Mom/BF, continuité du plan principal, transitions et stabilité musicale pendant un morceau complet. DuckStation n’a pas été manipulé dans cette passe et aucun rendu d’exécution n’est déclaré validé. Console réelle non testée.

## Reproduction

Les assets épinglés et FFmpeg restent hors Git. Depuis la racine du dépôt, fournir le répertoire d’assets officiel et FFmpeg, puis lancer le script vers un répertoire de sortie neuf :

```powershell
python ps1/compose_week4_layers_v153.py `
  --assets <repertoire-assets-724eba9> `
  --ffmpeg <chemin-vers-ffmpeg.exe> `
  --input-dir <paquet-v152/week4> `
  --output-dir <nouveau-paquet-v153>
```

Configurer ensuite CMake avec `FUNKIN_PS1_PRECONVERTED_WEEK4_DIR` pointant sur le paquet produit et construire `ps1-bopeebo-playable-disc` dans un dossier de build neuf ou préservé. Le script refuse d’écraser un dossier de sortie existant.

