# Week 5 v172 — correction du repère de fond

## Diagnostic confirmé sur les sources

Le fond des deux variantes était converti par `scale ... force_original_aspect_ratio=increase` puis recadré au centre en 256×192. Au rendu, il était traité comme une plaque plein écran 384×288 centrée autour de la caméra. Les couches de scène, en revanche, utilisaient les coordonnées et la parallaxe du JSON officiel. Le fond et les éléments de scène ne partageaient donc pas le même repère : c’est la cause concrète du décalage de composition constaté sur les captures.

Les assets officiels font 3102×1840 (`bgWalls.png`) et 2625×1613 (`evilBG.png`). Le recadrage 4:3 précédent supprimait respectivement environ 20,9 % et 18,1 % de la largeur source.

## Correction v172

- Préserve le rapport d’aspect des deux fonds : 256×152 pour `bgWalls`, 256×157 pour `evilBG` (écart d’arrondi raster inférieur à 0,2 %).
- Utilise les positions officielles : `bgWalls` (-630,-492), `evilBG` (-400,-500), leur échelle de sprite 0,8 et le scroll 0,2, dans le mapping scène `/10` utilisé par les autres props.
- Applique la caméra active au fond et dérive son échelle d’affichage depuis la taille source : Q8=248 pour le fond Noël et Q8=210 pour Evil. Il ne s’agit plus d’une image plein écran centrée.
- N’ajuste pas séparément les positions des personnages, les caméras de gameplay, les charts ou les notes.
- Le patch de conversion modifie seulement les deux pages de fond et leurs deux lignes CLUT. Les neuf autres pages/CLUT, les catalogues, les charts et l’audio sont copiés byte-à-byte depuis v171.

## Build et validation

- Assets/source : révision `724eba9de9e76761d9cefd52169926bc51c760a5`; base source Git `7057882fa4c481fb878de4cc27d3a827179f7ddd` avec changements locaux préexistants conservés.
- PSn00bSDK 0.24 / GCC MIPS 12.3. Dry-run : deux sources C, édition de liens et création de l’image disque; aucune conversion audio/chart ni conversion des autres pages graphiques.
- Compilation et création ISO réussies. Le répertoire ISO a été réordonné avec l’outil existant : `SYSTEM.CNF` puis `FUNKIN.EXE` sont les deux premières entrées fichier; EDC/ECC vérifiés pour les secteurs retouchés.
- **DuckStation et console non testées** : le cadrage corrigé, l’alignement des plans, les transitions et le démarrage demandent l’essai utilisateur.

Les dimensions et mappings sont une correction basée sur les données officielles, pas une validation visuelle. BIN/CUE, sources et empreintes sont dans le dossier externe `week5-scene-v172-delivery`.
