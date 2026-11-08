# Week 5 — zoom GF et stabilité des poses de foule (v182)

Date : 2026-11-08. Référence source : checkout `ps1-port`, HEAD `7057882fa4c481fb878de4cc27d3a827179f7ddd`, avec modifications préexistantes dans l’arbre de travail. Le build v181 et ses fichiers restent conservés.

## Changements

- La valeur GF Christmas relevée dans le Memory Scanner de DuckStation est `0x0160` (352 en Q8, multiplicateur éditeur 1,375). Elle devient la valeur initiale de l’éditeur et s’applique aussi en jeu normal. La scène utilise toujours sa compensation d’asset de base : le changement ne touche qu’à l’échelle GF. À titre de comparaison, l’ancien défaut éditeur était 288 Q8 ; la dimension projetée augmente donc de 22,2 % par rapport à ce défaut. Les autres transformations et la composition restent celles de v181.
- Les quatre cels officiels `Upper Crowd Bob` (indices Sparrow 0, 2, 4 et 6) sont conservés avec leur cadence 24 fps et leur séquence. Chaque cel est maintenant découpé dans la même fenêtre logique `384×55`, offset vertical 5, puis en bandes de 128 pixels. Avant cette passe, les rectangles rognés séparément faisaient 52, 53, 54 et 55 pixels de haut avec des offsets verticaux 8, 7, 6 et 5. Le nouvel atlas évite que des dimensions/offsets différents passent par les arrondis entiers du rendu PS1. Les pixels d’animation ne sont ni supprimés ni interpolés.
- Le paquet Week 5 garde 12 pages 8bpp et 792 576 octets, comme v179/v181. Il n’y a pas de coût supplémentaire de page VRAM ou de volume disque. Les charts et fichiers VAG sont repris à l’identique. Le générateur de détails ne lit que les cels de foule ciblés et l’escalator ; cette passe garde les mêmes dimensions de détail et ne retravaille pas BF.

## Vérifications statiques et compilation

- Le nouvel en-tête a été vérifié : les quatre cels utilisent les mêmes dimensions et le même offset vertical ; les bandes ont des UV dans la page 256×256. Le paquet généré a deux pages de détails et conserve le découpage logique 12 pages.
- Comparaison SHA-256 entre le build v181 et le nouveau build : tous les fichiers `.vag` et charts `.BIN` correspondants sont identiques. Les seules ressources de jeu qui changent sont `week5-scene.bin` et `week5_visual_data.h`.
- Build PSn00bSDK 0.24 / GCC MIPS 12.3, avec configuration v181 et paquet Week 5 préconverti : le dry-run ne prévoyait que `spu_probe.c`, `stream.c`, le lien et l’ISO. Aucun audio, chart ou autre atlas n’a été reconverti. Compilation et génération ISO réussies. Les deux avertissements `volatile` de `stream.c` existent déjà dans l’exemple du SDK.
- La sortie brute est gardée dans `C:/Users/Manau47/Documents/Codex/week5-gf-crowd-v182c-build/`. La livraison utilise une copie distincte avec `SYSTEM.CNF;1` et `FUNKIN.EXE;1` aux entrées racine 1 et 2 ; 117 fichiers ISO vérifiés. Le BIN fait 339 936 912 octets.

## Validation

Le comportement de l’éditeur, l’échelle de GF et la stabilité visuelle de la foule dans DuckStation restent à vérifier par l’utilisateur avec le CUE livré. La normalisation d’ancrage est une correction ciblée appuyée par les offsets et dimensions des rectangles ; elle ne prouve pas encore que la sensation de mouvement signalée est corrigée. Pas d’exécution DuckStation observée dans cette passe, pas de test sur console réelle. La mise à niveau générale des détails des Weeks 1–5 est reportée comme demandé.

Livraison : `C:/Users/Manau47/Documents/Codex/week5-gf-crowd-v182-delivery/week5-gf-crowd-v182.cue`.
