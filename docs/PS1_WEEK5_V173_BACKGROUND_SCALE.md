# Week 5 v173 — échelle du fond

## Correction

Le retour utilisateur distingue le débordement normal du décor hors écran de son échelle erronée. Le fond n’a pas à être ajusté pour tenir dans le viewport 4:3. v172 conservait l’aspect et l’ancrage officiel, mais calculait encore une taille de destination trop petite.

Les fonds sources mesurent 3102×1840 (mall de Noël) et 2625×1613 (Mall Evil). Ils sont représentés par des textures 256×152 et 256×157. Pour convertir les coordonnées du jeu 1280×720 au viewport PS1 320×240 en conservant l’échelle uniforme verticale, le facteur de sortie natif est 1/3. Avec l’échelle de sprite officielle 0,8 et le zoom caméra du stage (0,8 Noël; 1,0 Evil), les rectangles attendus font environ 661×392 et 698×428 px. Leur dépassement du cadre est voulu.

v173 ne touche qu’à `bg_art_scale` dans `spu_probe.c` : Noël 248→368; Evil 210→389. La position de stage, le rapport d’aspect, le viewport, les personnages, la caméra, les autres props, les palettes et toutes les règles de jeu restent ceux de v172. Aucun asset n’est reconverti.

## Compilation et contrôle

- Configuration dérivée du cache v172; les poses BF préconverties sont réutilisées et leurs SHA-256 correspondent à v172.
- Dry-run : compilation de `spu_probe.c` et de l’exemple `stream.c` du SDK, édition de liens, création du disque. Aucune conversion de textures, audio ou charts.
- Build PSn00bSDK 0.24 / GCC MIPS 12.3 réussi. Deux avertissements `volatile` proviennent du fichier `stream.c` du SDK.
- Le réordonnancement ISO place `SYSTEM.CNF` et `FUNKIN.EXE` aux entrées de fichier 1 et 2; le script vérifie EDC/ECC.
- Le rendu de v173 n’a pas encore été observé dans DuckStation; aucune validation utilisateur ou console réelle.

## Livraison

BIN/CUE et manifeste avec hashes : dossier externe `week5-scene-v173-delivery`. Les assets et SDK restent hors dépôt.
