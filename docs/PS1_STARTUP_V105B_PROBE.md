# WeekEnd 1 v105b — test d’entrée dans `main()`

Date : 2026-10-30  
Branche : `ps1-port`  
Source : commit `ca6eb54157c257b2d3dd9cd9ca1fda1ff0d97142`  
Build de référence : [WeekEnd 1 v105b](PS1_WEEKEND1_V105.md)

## Signalement et question du test

L’utilisateur rapporte que le CUE v105b reste sur le logo Sony PlayStation. Ce résultat est rapporté par l’utilisateur; Codex n’a pas exécuté v105b dans DuckStation.

Le premier test conservait le vrai exécutable et ses données, avec le seul paramètre `FUNKIN_PS1_STARTUP_MAIN_MARKER=ON`. Le repère blanc se trouve à l’entrée de `main()`, avant `init_video`, le CD, SPU, manette, menus et scènes. L’utilisateur rapporte que **l’écran reste au logo Sony**. Cela ne prouve pas à lui seul si `main()` a été atteint : l’affichage du repère dépend lui-même de l’initialisation GPU qu’il contient.

Le deuxième test conserve la même base et remplace seulement `_start_inner` par `startup_after_bss_marker.c`. Le point d’entrée `_start` installe `$gp`, puis saute dans ce remplacement. Celui-ci efface la vraie plage BSS du jeu et dessine un aplat ambre avant l’initialisation du heap, les constructeurs et `main()`. Il répond à cette question : **le chemin CRT atteint-il la fin de l’effacement BSS et peut-il dessiner depuis ce point ?**

- Ambre visible : `_start`, `$gp`, l’effacement BSS et le chemin GPU du repère ont fonctionné. Le point suivant à isoler sera l’initialisation du heap/constructeurs puis l’entrée de `main()`.
- Logo Sony persistant : ce repère n’est pas atteint. Un repère avant effacement BSS permettra ensuite de séparer le lancement CRT de l’effacement et du rendu GPU.

Ces tests ne modifient pas le code source du jeu ni ses ressources et n’ajoutent pas de fonctionnalité. Le source reste au commit v105b indiqué ci-dessus. Les anciennes images et les conversions v105b sont conservées.

## Configuration et contrôle de compilation

Build dans `ps1/build/w1p`, à partir de la configuration v105b. Un seul paramètre de comportement diffère : `FUNKIN_PS1_STARTUP_MAIN_MARKER=ON`. Les autres diagnostics restent désactivés. PSn00bSDK 0.24 et GCC MIPS 12.3.

Les ressources converties v105b ont été réutilisées. Comparaison des fichiers de ressources communs entre v105b et ce build : **129 correspondances exactes**; les cinq autres écarts recensés sont la nouvelle image disque, deux sorties propres à l’ancienne livraison et les métadonnées d’identification ABI de CMake, sans différence de paquet de jeu. Le dry-run Ninja n’a prévu que deux compilations C, l’édition de liens et la création de l’image. Aucun convertisseur d’asset n’était planifié.

Pour le premier test, l’option est présente dans la commande de compilation (`GAME_STARTUP_MAIN_MARKER=1`). Le désassemblage de `main` confirme le chemin : branche vers `ResetGraph`, configuration 320×240, `DrawPrim`, `DrawSync`, activation de l’affichage et boucle `VSync`.

Le réordonnancement déjà utilisé pour les livraisons place `SYSTEM.CNF` en première entrée du répertoire racine; l’exécutable demeure à LBA 27. Le réordonnancement ne change aucun extent de fichier.

## Livraison diagnostique 1 — repère `main()`

- CUE : `ps1/build/w1p/delivery/funkin-ps1-v105b-main-entry-probe.cue`
- BIN : `ps1/build/w1p/delivery/funkin-ps1-v105b-main-entry-probe.bin` — 337 885 968 octets
- SHA-256 BIN : `7974288C756F6A998FC7D31FE5F443AD60E182B8892F87A317AABD1C9C273537`
- SHA-256 CUE : `3643DD74E55AFE7E746C78DECAF199B1FCCC1BB7E1AC936048C84DD3B084258B`
- SHA-256 `FUNKIN.EXE` : `86CB6EF1A07EC0A604D162195E5383FF4BF85D63B8CC01B7497D0C55B29D42FF`
- En-tête PS-X EXE : PC `0x8001FA88`, chargement `0x80010000`, texte `0x000D4800`.

## Livraison diagnostique 2 — après BSS

- Build : `ps1/build/w1a`; cache repris de v105b, avec `FUNKIN_PS1_STARTUP_AFTER_BSS_MARKER=ON` et `FUNKIN_PS1_STARTUP_MAIN_MARKER=OFF`.
- Dry-run : trois compilations C, édition de liens et image disque; aucun convertisseur d’asset planifié.
- `WEND1.BIN` a le même SHA-256 que dans v105b : `65D953BFF270548C66563CEB499950394645858865B60EA277A3FCCC3284139C`.
- Le désassemblage confirme que `_start` règle `$gp` puis saute au `_start_inner` de `startup_after_bss_marker.c`; ce code efface `[__bss_start, _end)`, appelle `ResetGraph`, dessine l’aplat ambre et attend dans `VSync`. `main()` n’est pas appelé.
- Exécutable : 872 448 octets, PC `0x8001FB54`, chargement `0x80010000`, texte `0x000D4800`. `FUNKIN.EXE` extrait du disque à LBA 27, identique à l’exécutable lié.
- CUE : `ps1/build/w1a/delivery/funkin-ps1-v105b-after-bss-probe.cue`
- BIN : `ps1/build/w1a/delivery/funkin-ps1-v105b-after-bss-probe.bin` — 337 885 968 octets
- SHA-256 BIN : `342990ADD34E7490702C441479D25CD169802FFFB2ED44335E97C48772E91EEF`
- SHA-256 CUE : `E509D03591EC8DBA0E57822F2D77CA2D5F48D34823F1D9B606E57BC13D441561`
- SHA-256 `FUNKIN.EXE` : `1F6382CA6B05A1D1EC98BE29EA3A7E0A924B7B9703536B2C31624560AEC02554`

## État du test

Compilation, inspection des désassemblages et vérifications statiques des BIN/CUE réussies. L’utilisateur a rapporté le logo Sony pour le test 1 (repère `main`) et le test 2 (après BSS).

### Livraison diagnostique 3 — avant BSS, premier essai non concluant

- Build `ps1/build/w1b`, même cache de compilation et ressources préconverties de v105b; seul remplacement de démarrage actif : `FUNKIN_PS1_STARTUP_BEFORE_BSS_MARKER=ON`.
- L’EXE embarqué est au LBA 27, identique octet pour octet au `.exe` du linker; PS-X EXE PC `0x8001FAC8`, GP `0`, chargement `0x80010000`, taille texte `0x000D4800`. Le désassemblage montre que `_start` règle `$gp`, puis saute bien à `_start_inner` de `startup_before_bss_marker.c`.
- BIN livré : `ps1/build/w1b/delivery/funkin-ps1-v105b-before-bss-probe.bin`, 337 885 968 octets, SHA-256 `1E41243851B576A0603752A9536EA55ADC13CB29E1DF0709B1F3250F5FE1528F`.
- CUE : `ps1/build/w1b/delivery/funkin-ps1-v105b-before-bss-probe.cue`, SHA-256 `B4DD31ED9FAE3D99C0F38BF2D5A33D53C6E45B469CBB3A44A34A9A9D1757732D`.
- L’utilisateur rapporte de nouveau le logo Sony. **Ce test ne permet pas de conclure que `_start_inner` n’est pas atteint** : le repère écrivait GP0 brut sans configurer la sortie GPU et appelait `VSync()` avant le démarrage CRT normal. En l’absence de BSS effacée et d’initialisation vidéo, l’absence de cyan est un faux négatif possible.

### Livraison diagnostique 4 — avant BSS, initialisation d’affichage de v79

- Source : commit `3ad1540` (`Make pre-BSS startup marker use v79 GPU setup`), sur la même base jeu v105b et le même cache/configuration de build.
- Le changement de comportement unique est le corps de `startup_before_bss_marker.c` : il ne fait toujours aucun effacement BSS et n’appelle pas le jeu, mais configure le GPU comme v79 (`ResetGraph`, environnements dessin/affichage, remplissage cyan, `DrawSync`, activation de l’affichage), puis attend dans `VSync`.
- Le dry-run indique exactement une compilation C, l’édition de liens et la création d’image disque. Aucun convertisseur n’est planifié. Les fichiers ISO nommés ont les mêmes hashes que le test 3, sauf `FUNKIN.EXE`; `WEND1.BIN` reste au LBA 1515 et son SHA-256 est inchangé (`65D953BFF270548C66563CEB499950394645858865B60EA277A3FCCC3284139C`).
- L’ELF et le PS-X EXE concordent : point d’entrée `0x8001FB20`, chargement `0x80010000`, texte `0x000D4800`, `$gp=0`. L’exécutable du disque, au LBA 27, est identique au `.exe` lié.
- BIN : `ps1/build/w1c/delivery/funkin-ps1-v105b-before-bss-gpu-init-probe.bin`, 337 885 968 octets, SHA-256 `2B3519664BBA80608E6091E7B24C6C181627155F0C14F5A3B18BAAE4519BA507`.
- CUE : `ps1/build/w1c/delivery/funkin-ps1-v105b-before-bss-gpu-init-probe.cue`, SHA-256 `91AF4305525326C771F648F6E51B95C913C92A05DF530E0AE490A2944BA1F662`.
- Résultat utilisateur : l’utilisateur rapporte encore le logo Sony. Cette absence de cyan reste ambiguë : le désassemblage de v79 montre que `PutDispEnv()` lit `_gpu_video_mode` à `0x800E43D0`, symbole situé dans la BSS du jeu; `ResetGraph()` écrit aussi dans l’état des callbacks et variables GPU en BSS. Appeler ces helpers avant le nettoyage BSS peut donc produire un résultat invalide même si `_start_inner` est bien atteint.

### Livraison diagnostique 5 — avant BSS, accès directs GP1/GP0

- Source : commit `264c41b` (`Use raw GPU registers for pre-BSS marker`), même exécutable réel du jeu v105b, mêmes options et ressources.
- Différence unique : `startup_before_bss_marker.c` écrit directement les registres GPU GP1/GP0; aucun helper SDK, état callback, accès BSS ou attente `VSync`. Les timings et le mode 320×240 NTSC sont dérivés du chemin v79; la routine affiche un remplissage cyan statique sans entrer dans `main()`.
- Dry-run : une compilation C, édition de liens, image disque. Aucune conversion d’asset.
- Les fichiers ISO nommés sont identiques au test 4 sauf `FUNKIN.EXE`; `WEND1.BIN` garde le SHA-256 `65D953BFF270548C66563CEB499950394645858865B60EA277A3FCCC3284139C` au LBA 1515. `SYSTEM.CNF` est la première entrée du répertoire racine.
- Exécutable au LBA 27, identique au linker; PS-X EXE PC `0x8001FB18`, GP `0`, chargement `0x80010000`, texte `0x000D4800`; SHA-256 EXE `57896B54B4899B2A18F11E42F76C692059691EB678BADFBF05DADB7EF37A6DC6`.
- BIN : `ps1/build/w1d/delivery/funkin-ps1-v105b-before-bss-raw-gpu-probe.bin`, 337 885 968 octets, SHA-256 `12071797F4B1997D3E9D6D99371BF754F4BC7524FD898D8C8B98302C3D8A368A`.
- CUE : `ps1/build/w1d/delivery/funkin-ps1-v105b-before-bss-raw-gpu-probe.cue`, SHA-256 `FF80ADFEF50460BF49DC2223DFADD4FB4B842E9EDB09EAFCE90B69690328CB96`.
- Test utilisateur en attente. Aucun démarrage ou résultat visuel de cette livraison n’est revendiqué.

### Correction GP1 après retour « logo Sony »

L’utilisateur rapporte que le test 5 reste sur le logo Sony. La comparaison statique avec le `PutDispEnv()` du SDK montre une erreur de calcul dans la sonde brute : quand `DISPENV.screen.w` vaut zéro, le SDK utilise 256 comme largeur de balayage, puis calcule la plage horizontale de départ autour de `0x760` avec une demi-largeur de `0x500`, soit `0x260..0xC60`. Le mot correct est `GP1(06)=0x06C60260`; la sonde avait envoyé `0x06DA0120`. La fenêtre pouvait donc exclure le framebuffer de l’affichage. La prochaine image ne changera que ce registre; elle répondra à la question précise de la validité de la sortie vidéo brute avant BSS.

Codex n’a pas observé DuckStation. Aucun journal DuckStation n’a été trouvé dans l’installation portable ni dans les emplacements standards inspectés. Aucune validation console réelle n’est revendiquée.

### Livraison diagnostique 6 — GP1 horizontal corrigé

- Source : commit `2e0c967` (`Correct raw GPU horizontal display range`). Changement unique par rapport au test 5 : le registre GP1(06) passe de `0x06DA0120` à `0x06C60260`, valeur confirmée par le chemin `PutDispEnv()` du SDK v79.
- Dry-run : une compilation C, lien, image disque. Aucun convertisseur d’assets.
- Exécutable au LBA 27, identique au linker; entrée `0x8001FB18`, chargement `0x80010000`, texte `0xD4800`; SHA-256 EXE `50ACE5D1906E40C7850BBE6250BC1AB508D075E22DEE44C05BAB6B2DBACBC3DC`. `WEND1.BIN` reste identique au LBA 1515, SHA `65D953BFF270548C66563CEB499950394645858865B60EA277A3FCCC3284139C`.
- BIN : `ps1/build/w1e/delivery/funkin-ps1-v105b-before-bss-correct-hsync-probe.bin`, 337 885 968 octets, SHA-256 `49AE8A9BD3E0A303FD2E561724B2871154776EFD141B497B1FAE8F1477954AFC`.
- CUE : `ps1/build/w1e/delivery/funkin-ps1-v105b-before-bss-correct-hsync-probe.cue`, SHA-256 `208EEF8005010C7E5D022B8B33678500D7DC297BD5063C5561177F766E20B662`.
- Compilation et contrôles statiques réussis. L’utilisateur a ensuite chargé ce CUE dans DuckStation et rapporte que le logo Sony reste affiché. Une capture de la fenêtre montre le titre `funkin-ps1-v105b-before-bss-correct-hsync-probe` et `Jeu : 0 IPS`.

### Vérification complémentaire — lancement direct du même PS-X EXE

Pour séparer le chargement BIOS depuis le disque de l’exécution de l’exécutable, `FUNKIN.EXE` a été extrait du BIN w1e (LBA 27) et ouvert directement dans DuckStation via **Système → Démarrer le fichier**. Ce fichier est identique octet pour octet à l’exécutable lié et embarqué; SHA-256 `50ACE5D1906E40C7850BBE6250BC1AB508D075E22DEE44C05BAB6B2DBACBC3DC`, 872 448 octets. Aucun build ni disque n’a été régénéré.

**Observation réelle dans DuckStation :** le lancement direct affiche l’aplat jaune stable de la sonde pré-BSS; la fenêtre prend le titre `FUNKIN`. Cela confirme que le PS-X EXE peut atteindre et afficher son repère quand il est chargé directement. En revanche, le lancement du CUE correspondant reste au logo Sony selon l’utilisateur. Cette comparaison déplace le diagnostic vers le chemin BIOS/CD (ou l’état initial différent entre les deux méthodes); elle ne prouve pas encore quelle étape précise échoue. La sonde tourne dans une boucle d’attente sans VSync, donc `Jeu : 0 IPS` n’est pas une mesure de stabilité temporelle.

Un nouvel audit du disque brut confirme le PVD ISO9660 et les enregistrements du répertoire : répertoire racine LBA 22 (8 192 octets), `SYSTEM.CNF;1` en LBA 26 (55 octets), puis `FUNKIN.EXE;1` en LBA 27 (872 448 octets). Le contenu de `SYSTEM.CNF` pointe bien vers `cdrom:\FUNKIN.EXE;1`; les 2 048 octets de charge utile du premier secteur de l’EXE commencent par `PS-X EXE`. Cela rend cohérents le chemin référencé et son extent, sans prouver que le BIOS lit/parse effectivement ces données. Il reste à examiner l’exécution du boot depuis CD avec les outils de traçage/débogage disponibles dans cette version de DuckStation et à comparer avec une image connue fonctionnelle. L’image exacte v79 n’est pas présente dans le répertoire `ps1/build` inspecté; aucune comparaison binaire v79 n’est revendiquée.

### Comparaison avec le dernier disque antérieur, v104

Les images livrées v104 (Week 7) et v105b ont le même identifiant de volume `FUNKIN_BOPEEBO_PLAY`, le même `SYSTEM.CNF` (55 octets, `BOOT=cdrom:\FUNKIN.EXE;1`, `STACK=801FFFF0`) et le même chargement fichier `SYSTEM.CNF` en tête de la liste. Le répertoire racine v104 mesure 6 144 octets (3 secteurs de données) contre 8 192 (4 secteurs) en v105b. L’enregistrement `FUNKIN.EXE;1` se trouve à l’offset 1 496, dans le premier secteur du répertoire, en v104; en v105b il est à l’offset 2 222, dans le deuxième secteur. Les extents sont respectivement 26 et 27, car la disposition et la taille des fichiers ont changé.

### Prochain essai contrôlé, disque seulement

Un nouveau CUE est préparé depuis l’image diagnostique w1e, en gardant exactement le même exécutable pré-BSS, les mêmes fichiers et extents. L’unique différence sera la position de l’enregistrement racine `FUNKIN.EXE;1` : il sera placé immédiatement après `SYSTEM.CNF;1`, à côté du début du répertoire. Les secteurs modifiés auront leurs EDC/ECC recalculés; aucun fichier de ressource ni secteur de payload ne sera modifié. La question testée est : **le BIOS échoue-t-il à localiser l’exécutable lorsque son entrée de répertoire est au-delà du premier secteur ?** Un aplat de la sonde après cette disposition confirmerait cette piste; logo Sony inchangé la réfuterait et maintiendrait le focus sur l’interprétation BIOS/CD ou l’état initial.

**Livraison w1f — répertoire EXE en tête :** source/outil identifiable au commit `f399899` (`Add isolated boot-directory order probe`). CUE `ps1/build/w1f/delivery/funkin-ps1-v105b-exe-directory-first-probe.cue`; BIN adjacent, 337 885 968 octets, SHA-256 `FE5496D4630101B5896CC944603D73ED10E059843A51A3BCA8002BDE260D6489`; CUE SHA-256 `ADD3E64A769E8DF17E9CD4D0560AAC7CD951A7437CD369844222E521D058285B`. Le répertoire racine conserve LBA 22 et 8 192 octets. `SYSTEM.CNF` reste LBA 26/55 octets; `FUNKIN.EXE` reste LBA 27/872 448 octets. Son entrée est maintenant à l’offset 156 du secteur 0. Le fichier EXE et toutes les données des autres fichiers sont inchangés; le générateur a vérifié EDC/ECC et identité de tous les octets hors des secteurs racine modifiés.

Compilation : non nécessaire pour cette variante disque-only. Résultat de l’essai utilisateur w1f consigné ci-dessous. Console réelle non testée.

**Résultat w1f :** l’utilisateur confirme l’aplat jaune au boot BIOS. L’image ne changeait que les enregistrements de répertoire racine par rapport à w1e; son EXE pré-BSS, son emplacement, sa taille et les payloads sont identiques. Cela confirme que la position de l’enregistrement `FUNKIN.EXE` dans le répertoire racine est suffisante pour faire avancer le démarrage BIOS jusqu’au code pré-BSS. Cela ne valide pas encore le jeu, car w1f contient volontairement la sonde au lieu de l’entrée `main()` normale.

### Livraison w1g — v105b normal, entrée EXE remontée

Pour vérifier si la même correction restaure le démarrage de la version normale, w1g part du BIN v105b original (`CC491F701307EEAC16938611432797FCE8FB867658F0E43769CBEDD0F42A0BF1`) et remonte seulement l’enregistrement `FUNKIN.EXE;1` juste après `SYSTEM.CNF;1`. L’EXE de jeu d’origine, ses 872 448 octets à LBA 27, toutes les ressources et tous les extents sont conservés; seuls les quatre secteurs du répertoire racine ont été réécrits, avec EDC/ECC recalculés.

- CUE : `ps1/build/w1g/delivery/funkin-ps1-weekend1-test-v105b-root-exe-first.cue`
- BIN : `ps1/build/w1g/delivery/funkin-ps1-weekend1-test-v105b-root-exe-first.bin` — 337 885 968 octets; SHA-256 `E9D356B006D7D572D336BF9F9360AB0130A2D2EB7FB144B074F3D7247091C9E9`
- SHA-256 CUE : `5D41EAC9E918B0FB682C577C295C6867ABE585AB45EDF6569F87EA0E501AA718`
- L’enregistrement EXE est à l’offset 156 du premier secteur du répertoire; son LBA/taille et son contenu sont inchangés.

Pas de compilation ni de conversion d’assets. L’essai utilisateur dans DuckStation déterminera si le jeu v105b normal démarre; ne pas déclarer la régression résolue avant ce résultat.

**Résultat w1g :** l’utilisateur confirme que le jeu démarre correctement dans DuckStation. Comme w1g diffère du v105b d’origine uniquement par l’ordre des entrées du répertoire racine, le défaut est isolé à la résolution BIOS de `FUNKIN.EXE` depuis le répertoire ISO9660 lorsque son enregistrement se trouve au-delà du premier secteur de répertoire. Le BIOS n’a pas réussi à atteindre le fichier à l’offset 2 222 (secteur 1); après déplacement de ce même enregistrement à l’offset 156 (secteur 0), sans changer LBA, taille ou contenu de l’EXE, le boot normal fonctionne. Cela confirme le diagnostic empirique pour la chaîne BIOS/DuckStation testée; le comportement exact d’autres BIOS ou de consoles réelles reste à vérifier.
