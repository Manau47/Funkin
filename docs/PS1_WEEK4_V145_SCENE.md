# Week 4 scene pass — v145

## But

Build d’essai pour corriger le décor invisible de Week 4 et rendre les proportions/cycles de Mom cohérents. La scène reste celle du jeu officiel épinglé; aucune nouvelle composition, position de caméra ou règle de jeu n’est introduite.

## Corrections

- Le générateur séparait auparavant une texture 512×256 en deux pages 256×256 en coupant le tableau RGBA en deux moitiés d’octets. Cela mélangeait les rangées au lieu de séparer les colonnes. Il copie maintenant, ligne par ligne, la moitié gauche et la moitié droite avant quantification.
- À 2,05×, les quads 256×256 du décor débordaient largement du viewport PS1. Le moteur les soumet maintenant après découpage CPU du rectangle et des UV à la fenêtre 320×240, comme le chemin éprouvé de Week 2.
- Les nouveaux cels de Mom gardent tous le canevas officiel 72×84, au lieu de 64×64 pour les poses ajoutées. Cela évite que sa taille apparente change au passage idle/chant.
- Idle et chants directionnels sélectionnent trois cels réellement échantillonnés dans le rig officiel. Leur cadence est dérivée de l’horloge audio et du tempo du chart, à 24 images/s; les durées de l’animation originale (9, 13 ou 14 images selon la séquence) règlent le cycle. La sélection reste indépendante des entrées et du jugement.

## Ressources et coûts statiques

Les stems, charts et pages déjà convertis ont été repris de `ps1/build/v143-animation-pass/preconverted`; aucune conversion audio ni conversion générale des ressources n’a été lancée. Seuls les paquets visuels Week 4 et leurs en-têtes ont été régénérés à partir des assets officiels déjà présents localement.

Le paquet `W4SCENE.BIN` passe de 262 656 à 393 728 octets, soit deux pages 8bpp supplémentaires (131 072 octets) pour les cels de Mom. La scène occupe six pages 8bpp — 384 Kio de VRAM — et la CLUT partagée reste à la même adresse. Le tampon de transfert temporaire demeure de 64 Kio; le ring audio et les fichiers audio sont inchangés. Le paquet ajoute 64 secteurs de lecture CD par rapport au paquet v143. Ce sont des tailles calculées à partir des fichiers, pas des mesures en exécution.

## Build reproductible

- Révision des assets : `724eba9de9e76761d9cefd52169926bc51c760a5`.
- SDK : PSn00bSDK 0.24, GCC MIPS 12.3, CMake/Ninja, build `Debug`.
- Répertoire préconverti Week 4 : `ps1/build/week4-scene-v145/preconverted/week4` (hors Git).
- Répertoire de build : `ps1/build/v143-animation-pass/build`.
- Cible jouable : `funkin-ps1-bopeebo-playable`.
- CUE livré : `ps1/build/week4-scene-v145/delivery-v145-week4-stage-mom/funkin-ps1-v145-week4-stage-mom.cue`.

Le build jouable a compilé puis lié l’exécutable et créé l’image disque. Le dry-run de cette cible après fabrication indique `no work to do`; il ne prévoit aucune reconversion. L’image de livraison est une copie distincte dont l’ordre du répertoire ISO a été normalisé pour démarrer avec `SYSTEM.CNF` puis `FUNKIN.EXE`. L’exécutable embarqué fait 1 028 096 octets. Extraction statique de `W4SCENE.BIN` depuis le BIN : 393 728 octets, identiques octet pour octet au paquet préconverti.

Hashes SHA-256 :

- `W4SCENE.BIN` : `1f178ae8fad8ec86d4914569050e8eac070702d6a1b336c56b734cf3679b5360`
- BIN livré : `7ea06c970517e1ac92f7f90905dd21973be27ebc99bdf34733f1ce18da59c08d`
- CUE livré : `d8ed08eac76f9ab390c1271aa21c61dcf7cfb3d5c71b67e1f843e389a2c43869`

## Vérification et limites

Le PNG de conversion confirme que le paquet de décor décodé contient la scène attendue; ce n’est pas une observation du GPU PS1. Le BIN/CUE n’a pas encore été exécuté dans DuckStation pour cette passe. L’essai utilisateur doit vérifier décor visible hors éclairs, proportions de Mom sur idle et les quatre chants, retours au repos et maintien de l’audio. Aucune validation sur console réelle.

Les couches mobiles `bgLimo` et `limo` ne sont pas animées dans ce jalon : la correction porte sur l’image de scène rendue et sur les cycles de Mom.
