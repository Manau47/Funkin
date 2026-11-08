# Week 5 — cadrage focus BF, v176

## Modification

À partir du code et de la configuration archivés en v175, seule la cible de caméra du focus BF a changé. Les ancrages d’acteurs, le cadrage Dad/GF, les compositions, l’échelle de scène, les charts, le gameplay et l’audio restent identiques.

Le focus BF utilisait `bf_x / 10 - 30` et `bf_y / 10 - 20 - 28`. Avec l’échelle de caméra Week 5 de 460/256 (environ 1,8×), le décalage relatif prévu entre l’ancre de BF et le centre de caméra était de 55 unités horizontales et 68 verticales après les valeurs d’édition v175. Cela projetait l’ancre vers environ X=259, Y=242 sur l’écran 320×240, avant les marges du sprite : cohérent avec BF repoussé au bord droit et inférieur dans la capture.

La cible BF utilise maintenant `bf_x / 10` et `bf_y / 10 - 20`. En conservant les déplacements BF et caméra v175, l’ancre projetée est estimée à environ X=205, Y=192. Ce sont des calculs statiques issus des coordonnées codées et du zoom ; le rendu en jeu doit encore être confirmé par l’utilisateur. Les cibles Dad et GF gardent leur biais v175.

## Build et ressources

- Base : `ps1-port`, HEAD `7057882fa4c481fb878de4cc27d3a827179f7ddd`; référence jouable livrée : v175.
- Configuration conservée : PSn00bSDK 0.24, GCC MIPS 12.3, composition editor Week 5 activé, démo de scène activée, diagnostics de démarrage désactivés.
- Dry-run du seul disque jouable : compilation de `spu_probe.c`, édition de liens, création BIN/CUE. Aucune conversion d’assets, de charts ou d’audio.
- Ressources v175 réutilisées : `week5-scene.bin` SHA-256 `827FC943FC0429785B3C61C0CA4740E9812063498B1568D1AFFB34D1DFA85245`; `stream-playable.vag` SHA-256 `205EA3A13D2EBA739E250F4DA41AA44E5ABF78202EE0A1F81AB02B8647026D0`.
- Build réel : réussi, 3 étapes Ninja (objet C, ELF, image disque). Taille BIN : 339 861 648 octets.
- Hashes, snapshot de source/configuration et diff exact v175→v176 : `C:/Users/Manau47/Documents/Codex/week5-bf-camera-v176-delivery/`.

## Validation

La capture DuckStation v175 confirme le problème visuel général : BF se trouve près du bord droit/bas. Le réglage caméra testé en v176 n’a pas encore été exécuté dans DuckStation ni validé par l’utilisateur. Aucune validation console réelle n’est revendiquée. L’éditeur de scène est conservé pour la suite.
