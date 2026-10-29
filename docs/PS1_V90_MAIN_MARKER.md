# v90 — arrêt du jeu au début de `main()`

## Question de cet essai

Le véritable exécutable jouable atteint-il le début de `main()` et peut-il y initialiser le GPU minimal, avant les initialisations du jeu (écran de chargement, SPU, CD, manettes, assets et menus) ? Un écran blanc fixe est le repère attendu. Cette image ne teste pas encore le démarrage normal du jeu.

## Source archivée

- Commit source publié sur `ps1-port` avant la génération du disque : `2d2a335ce14d312865f90124eb148b2165c68f82` — `Add early main-entry marker to playable PS1 target`.
- Cible : `funkin-ps1-bopeebo-playable` / `ps1-bopeebo-playable-disc`.
- Le code normal de `main()` reste après un garde `volatile`, et l’exécutable conserve les références du véritable chemin jouable. Le marqueur appelle `ResetGraph`, configure un écran 320×240, dessine un aplat blanc, attend `DrawSync`, active l’affichage puis reste dans `VSync`. Il précède les appels à `init_video`, au chargement d’écran, à `SpuInit`, `CdInit`, à l’initialisation des manettes et aux lectures de scène.
- Ce marqueur se trouve après le démarrage runtime qui appelle `main()` : il ne teste pas les constructeurs/runtime avant `main`.

## Configuration

- PSn00bSDK 0.24, GCC `mipsel-none-elf` 12.3.0, CMake 4.4.4, Ninja 1.11.1; générateur Ninja, `CMAKE_BUILD_TYPE` vide comme dans la configuration de référence du checkout actuel.
- Configure : `cmake -S ps1 -B ps1/build/main-entry-marker-v90-fcd8040 -G Ninja -DCMAKE_TOOLCHAIN_FILE=<PSn00bSDK>/lib/libpsn00b/cmake/sdk.cmake -DPSN00BSDK_TC=<PSn00bSDK> -DPSN00BSDK_TARGET=mipsel-none-elf -DFUNKIN_PS1_ASSETS_DIR=<checkout>/assets -DFUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH=<fichier local> -DFUNKIN_PS1_BOPEEBO_CHART_JSON=<fichier local> -DFUNKIN_PS1_FFMPEG=<ffmpeg local> -DFUNKIN_PS1_DAD_LANES_DEFAULT=ON -DFUNKIN_PS1_DIAGNOSTICS_DEFAULT=OFF -DFUNKIN_PS1_STARTUP_MAIN_MARKER=ON`.
- Build : `cmake --build ps1/build/main-entry-marker-v90-fcd8040 --target ps1-bopeebo-playable-disc --parallel 6`.
- Les QA diagnostics et visual tests sont désactivés. La fréquence reste 43 008 Hz, quatre canaux; le même chart Bopeebo Normal et les scènes Week 1/2/3 sont générés et placés sur le disque. Assets, SDK et entrées générées restent hors Git.
- Assets : sous-module `assets` à `724eba9de9e76761d9cefd52169926bc51c760a5`.
- SHA-256 des entrées locales : VAGi Bopeebo 4 canaux `205EA3A13D2EBA739E250F4DA41AA44E5EABF78202EE0A1F81AB02B8647026D0`; chart `2D1FD06F6668E00BB0FE3A24077620610F998A48FD934D5CEC15F355402B6B6D`.

## Artefacts v90

- BIN : `outputs/FNF-PS1-v90-main-entry-marker/funkin-ps1-bopeebo-playable.bin`, 131 944 848 octets / 56 099 secteurs MODE2/2352, SHA-256 `6FDE7723FB0B886E51690C509CCE6B99F401B30967CCE97A7C1818BE11686ACA`.
- CUE : `outputs/FNF-PS1-v90-main-entry-marker/funkin-ps1-bopeebo-playable.cue`, SHA-256 `8579EEF0E6966AFD78659F364593E560C8384148E9258D14FA88B196A842B340`.
- EXE autonome : 862 208 octets, SHA-256 `089F465BB96B8BA691B5F7FF034C3078823C660047460DFA918F220669CF4E4C`; l’EXE extrait de l’ISO (LBA 25) est identique octet par octet.
- En-tête PS-X EXE vérifié : PC `0x8001D8EC`, adresse de chargement `0x80010000`, taille text `0xD2000`; champs BSS de l’en-tête à zéro. `SYSTEM.CNF` garde `BOOT=cdrom:\FUNKIN.EXE;1` et la pile `0x801FFFF0`.
- Le désassemblage de `main` montre la lecture du garde puis l’appel à `ResetGraph` et au rendu de l’aplat avant la branche vers le chemin de démarrage normal.

## Références et résultat d’exécution

Les disques v75 et v76 restent inchangés et disponibles séparément : v75 SHA-256 `6C09832B3BB2BABE77EA5411EFE83D5445AA34F189FBB5882C773A3DB1B760F6`; v76 SHA-256 `828489413342768586115C99AD5C1A6B82FC65F88800A17F16308A3BC9E08402`. Ils restent des références binaires, pas des sources exactes reconstruites.

v90 est compilé et son ISO/EXE ont été vérifiés statiquement. Il n’a pas encore été exécuté dans DuckStation ni sur console. L’observation de l’écran blanc, si elle se produit, est à fournir par l’essai utilisateur.

