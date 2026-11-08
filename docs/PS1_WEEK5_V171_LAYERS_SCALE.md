# Week 5 v171 — profondeur, échelle et variantes d’atlas

## Référence

- Sources de gameplay : checkout `ps1-port`, commit `7057882fa4c481fb878de4cc27d3a827179f7ddd`.
- Révision des assets classiques : `724eba9de9e76761d9cefd52169926bc51c760a5`.
- Scène officielle consultée : `assets/preload/data/stages/mallXmas.json` et les rigs/XML sous `assets/week5/images/christmas` et `assets/shared/images/characters`.
- Référence vidéo locale consultée : `Screen_Recording_20261105_210840.mp4`, images extraites autour de 12 s et 35 s. Le rapport d’image 16:9 est adapté par recadrage au 4:3 ; aucun étirement n’est appliqué.
- Référence build : paquet v170b conservé dans `C:/Users/Manau47/Documents/Codex/week5-scene-v170b-package`; BIN/CUE v170b conservés dans `week5-scene-v170b-delivery`.

## Ce que montrent la scène officielle et la vidéo

La scène n’est pas un fond unique. Pour la variante Noël, l’ordre officiel est :

| Couche | Position design | Échelle | Parallaxe | Profondeur |
|---|---:|---:|---:|---:|
| `bgWalls` | (-630, -492) | 0,8 | 0,2 | 10 |
| `upperBoppers` | (-396, -98) | 0,85 | 0,28 | 20 |
| `bgEscalator` | (-1100, -540) | 0,9 | 0,3 | 30 |
| `christmasTree` | (370, -250) | 1,0 | 0,4 | 40 |
| `bottomBoppers` | (-300, 120) | 1,0 | 0,9 | 50 |
| neige sous-jacente | (-1200, 800) | — | 1,0 | 59 |
| `fgSnow` | (-1150, 680) | — | 1,0 | 60 |

Les personnages restent devant ces couches : GF (808,5; 854), les parents Mom/Dad (42; 882), Santa (-840; 150), puis BF (1177,5; 871). Les images de référence confirment trois plans lisibles : architecture et balcon, foule/escalator/arbre, puis neige et personnages. Le cadrage de 35 s déplace le focus vers BF ; les personnages du côté opposé sont alors partiellement hors cadre.

## Corrections appliquées

1. **Échelle de la foule supérieure.** Le strip officiel a une largeur design de 2596 px. La conversion PS1 passe de 256 texels, puis applique l’échelle de scène 0,85, l’unité monde 1/10 et le zoom 460/256. La largeur écran attendue est donc `2596 × 0,85 ÷ 10 × 460 ÷ 256 ≈ 397 px`; l’échelle de texture correspondante est Q8=221. Le précédent facteur 420 produisait une foule presque deux fois trop large. Les cels sont conservés à 256×40 texels et leurs silhouettes ne sont pas étirées.
2. **Ordre GPU.** `upperBoppers` est dessiné avant `bgEscalator`, puis l’arbre, la foule basse, `snowUnder` et `fgSnow`, conformément aux profondeurs officielles. Les personnages sont ensuite dessinés au premier plan dans leur ordre de profondeur existant.
3. **Taille et détail des parents et de GF.** Leurs cellules de conversion passent de 96×112 (v170b) à 104×116, toujours avec rognage transparent et ancrage de pied/centre conservé. Leur échelle d’affichage passe de Q8=171 à Q8=190 (environ +11 %). Avec la hausse de texels, cela représente environ +20 % de largeur visible attendue pour ces deux rigs. Les poses restent 18 cels parents et 10 cels GF, avec les mêmes séquences et cadences. BF et Monster gardent leurs dimensions et leur échelle actuelles.
4. **Variantes et pages VRAM.** Les alternatives Noël/Monster sont empaquetées dans des plages distinctes, puis réutilisent les mêmes emplacements physiques car elles ne sont jamais actives ensemble. Six pages communes, deux pages Noël et une page Monster sont présentes dans le paquet. Le nombre de frames reste 69. À l’entrée d’une scène, seuls le fond choisi, les pages communes et les pages de sa variante sont lus et uploadés ; les ressources de l’autre variante ne sont pas chargées.

## Budget statique

- Paquet graphique v170b : 9 pages logiques, 594 432 octets.
- Paquet graphique v171 : 11 pages logiques (2 arrière-plans alternatifs + 6 communes + 2 Noël + 1 Monster), 726 528 octets. Le supplément disque est de 132 096 octets; ce n’est pas une hausse équivalente de VRAM.
- VRAM simultanée maximale Noël : 1 page de fond + 6 pages communes + 2 pages Noël = 9 pages 8bpp, soit 589 824 octets de texels. Monster : 1 + 6 + 1 = 8 pages, soit 524 288 octets. Le paquet réserve 11 lignes CLUT à partir de y=481 (5 632 octets), sans dépasser la ligne de palette de base à y=496.
- Dans la carte globale existante, 9 pages 8bpp représentent 589 824 octets et les deux pages 4bpp communes 65 536 octets. Les deux framebuffers 320×240×16bpp occupent 307 200 octets. Ces sommes sont un calcul statique de zones, pas une mesure de VRAM libre observée en exécution.
- Les fichiers audio et charts de Week 5 proviennent byte-à-byte du paquet v170b. Ils ne sont ni reconvertis ni modifiés.

## Résultats et limites

- **Conversion** : atlas régénéré seulement pour les graphismes Week 5. La compilation CMake a été configurée avec les paquets préconvertis des autres semaines.
- **Compilation** : réussie avec PSn00bSDK 0.24 et GCC MIPS 12.3. Le dry-run ne prévoyait que `spu_probe.c`, le lien et l’image disque.
- **Exécution** : DuckStation n’a pas été manipulé. Aucun rendu de v171 n’a été observé dans l’émulateur ni sur console.
- **À vérifier manuellement** : présence du balcon et de sa foule, tailles relatives Mom/Dad/GF, visibilité lors des focus Dad/BF, transitions de variante Noël/Monster, animations et audio. Cette livraison est un essai, pas une validation utilisateur.

## Erratum démarrage v171

Après que l’utilisateur a signalé un retour au logo Sony, une inspection directe du BIN a montré que le générateur ISO trie le répertoire racine alphabétiquement : `FUNKIN.EXE;1` apparaissait à l’entrée fichier 36 et `SYSTEM.CNF;1` à l’entrée 93. La mention de l’ordre correct dans la première édition de ce rapport était erronée. v171 est conservé intact; v171b ne change que l’ordre des entrées racine, plaçant `SYSTEM.CNF` puis `FUNKIN.EXE` aux deux premières entrées fichier. L’exécutable et les ressources sont identiques. Le démarrage v171b attend toujours l’observation utilisateur dans DuckStation.
