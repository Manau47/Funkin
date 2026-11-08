# Week 5 — foule basse derrière les personnages (v183)

Date : 2026-11-08. Référence de build : v182, dont les sorties et ressources restent conservées. Cette passe corrige le groupe `Bottom Level Boppers`, derrière Mom, Dad, GF et BF. La passe v182 avait touché `Upper Crowd Bob` ; ce n’était pas le groupe signalé par l’utilisateur.

## Diagnostic et changement

- Les quatre cels officiels distincts utilisent les indices Sparrow 0, 2, 4 et 6. Leur canevas source commun est 1978×674. L’ancien atlas PS1 les recadrait indépendamment en rectangles de 158×53/54 avec des offsets différents : les cels 0/1 étaient à `(+9,+1)`, le cel 2 à `(-9,0)` et le cel 3 à `(+9,0)`. Le cel 2 avait donc un écart horizontal de 18 pixels avant même le mouvement de caméra.
- Les quatre images sont maintenant extraites sur un canevas commun 176×54, avec les marges transparentes et l’alignement Sparrow conservés dans le canevas. Cadence, séquence, nombre d’images, taille affichée, GF et couches de scène ne changent pas.
- La page 9 est réempaquetée de façon déterministe pour y loger les cels et les trois ressources déjà présentes (arbre, neige avant-plan, Santa). La CLUT 9 et les autres pages/CLUT du paquet restent identiques. Le paquet garde 12 pages ; la texture de page 9 et ses UV changent.

## Vérifications

- Vérification statique : les quatre cels ont des rectangles 176×54, offsets `(0,0)`, dans les limites de la page 256×256. L’extraction utilise les mêmes cels officiels et le même rééchantillonnage nearest-neighbour que l’ancienne génération.
- Le dry-run final ne prévoit que la compilation de `spu_probe.c`, du lecteur SDK, l’édition de liens et l’image disque. Les ressources de scène, charts et audio préconverties sont réutilisées.
- Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 réussie. Le CUE livré a `SYSTEM.CNF;1` à l’entrée racine 1 et `FUNKIN.EXE;1` à l’entrée 2. L’image contient 117 fichiers.
- Aucun lancement dans DuckStation ni test sur console réelle n’a été fait dans cette passe. Il reste à vérifier visuellement que le clipping et le saut signalés sont corrigés dans la foule basse.

Livraison : `C:/Users/Manau47/Documents/Codex/week5-lower-crowd-v183-delivery/week5-lower-crowd-v183.cue`.
