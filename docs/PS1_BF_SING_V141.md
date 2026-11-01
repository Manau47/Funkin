# v141 — poses de chant de BF

## Changement

Le retour utilisateur signale que BF paraît moins fluide et semble manquer de poses de chant, alors que l’espacement Pico/BF de v140 est apprécié. Les atlas officiels épinglés contiennent 15, 30, 15 et 62 images pour les chants gauche, bas, haut et droite. Le convertisseur PS1 ne conservait que les deux premières images de chaque direction.

v141 conserve le début de l’animation, remplace la pose quasi redondante par une pose médiane, puis ajoute une pose tardive : trois poses échantillonnées début/milieu/fin par direction. Elles avancent à 15 images/s selon l’horloge d’échantillons audio, avec le hit réel comme origine. Les holds gardent leur état de chant jusqu’à l’échéance déjà calculée. Les règles de gameplay, les timings, Pico, la caméra, la scène, l’audio, l’idling et les réactions aux fautes ne changent pas.

## Ressources et chaîne incrémentale

Le script ciblé `ps1/augment_bf_sing_poses.py` reprend la palette BF convertie et remplace seulement quatre cels existants par leurs poses médianes. Quatre cels finaux de 52×52 pixels 8bpp (10 816 octets de pixels indexés) sont inscrits dans l’espace libre au bas de la page 7. La page et la taille de `W1SCENE.BIN` restent inchangées : aucun transfert VRAM supplémentaire n’est nécessaire, et le code réserve seulement quatre descripteurs de texture. Le même paquet de scène est restauré au lancement des semaines qui réutilisent l’atlas BF.

Le CMake relance seulement le générateur ciblé, compile le code du jeu, lie l’exécutable et fabrique l’image disque. Les ressources converties sont réutilisées depuis le staging v140. Le BIN brut et le CUE bruts sont gardés dans le dossier de build externe; l’image remise à l’utilisateur est une copie réordonnée pour placer `SYSTEM.CNF` puis `FUNKIN.EXE` au début du répertoire ISO. Le SDK et les assets officiels restent hors Git.

## Reproduction

- Branche locale : `ps1-port`, snapshot source de départ `4ca7f18cf2e458fa8792eb875ca3f605c5f770da`.
- Staging réutilisé : `C:\Users\Manau47\Documents\Codex\week3-pico-bf-spacing-v140\preconverted-base`.
- Build séparé : `C:\Users\Manau47\Documents\Codex\week3-bf-sing-v141\build`.
- SDK : PSn00bSDK 0.24 et toolchain GCC MIPS 12.3.0; générateur Ninja/CMake.
- Paramètres importants : `TEST_PLAYABLE_BOPEEBO=1`, 4 canaux, diagnostics et planche de flèches désactivés par défaut, `PS1_CHART_RATE=43008`.
- Cible : `ps1-bopeebo-playable-disc`.
- La passe `ninja -n` après compilation indique `no work to do`; aucun reconvertisseur complet d’images, de charts ou d’audio n’est demandé.

## Artefact livré

- BIN/CUE : `ps1/build/week3-bf-sing-v141/delivery-v141-bf-sing-poses/`.
- BIN : 338 511 600 octets, SHA-256 `DE3C2E23CDE9AE5BBD6302B9CA8B36C75107CD702A6662D7CC0B86774BED87E8`.
- CUE : SHA-256 `BDA46FD0A026D16A0676E12571FB4D6AA20543D022A974902780EE999771D653`.
- PS-X EXE : SHA-256 `0B31033B319463B7532D9988694989DA48857E8AED71819B14DBBF2B47E6CAD2`.
- BIN/CUE avant réordonnancement : BIN SHA-256 `C0D2A080C5A9153CC5645D9D711764CDC0D10F175AC6C255A33627B64D228E85`; le réordonnanceur recalcule EDC/ECC des seuls secteurs de répertoire ISO modifiés.

## État de validation

La compilation et les contrôles statiques du paquet ont réussi. Le générateur a conservé la taille de scène à 655 360 octets et n’a modifié que la page BF. `SYSTEM.CNF;1` et `FUNKIN.EXE;1` occupent les deux premières entrées du répertoire ISO.

Le CUE n’a pas été lancé par l’agent. L’essai utilisateur dans DuckStation doit vérifier la fluidité des chants de BF, les quatre directions, les holds, Week 3 et les cycles de retour/retry. v141 n’est pas encore validée par l’utilisateur et n’a pas été testée sur console réelle.

