# Week 3 v129 — parallax, lumières et réaction de GF au train

## Objectif

À partir de la composition v128, ajouter un défilement parallaxe entre la ville et le quai, animer les lumières des bâtiments selon le script officiel et réagir au passage du train avec les cheveux de GF. La v128 est conservée sans modification comme référence stable.

## Changements

- La ville (couches sky/city/windows) suit 30 % du déplacement de caméra; le quai suit 100 %. Le train reste dessiné entre l’arrière-plan et le premier plan.
- Les fenêtres de Philly sont extraites dans un masque d’index de palette dédié. Le programme change une seule entrée de la CLUT réservée au rythme des beats, avec les cinq couleurs officielles et une variation progressive. Cette méthode ne charge ni nouvelle texture ni page VRAM.
- Le convertisseur extrait quatre images du rig officiel de GF : deux poses `hairBlow` (source 124 et 139) et deux poses `hairFall` (154 et 169). Pendant le train, les deux premières alternent à 24 images/s; après son passage, les poses de retombée sont jouées pendant 30 images source, puis GF reprend sa danse.
- Le paquet Week 3 reste à quatre pages de décor et quatre pages de personnages. L’icône Pico est rangée dans l’espace inutilisé de l’atlas train; la disposition de BF et la sauvegarde/restauration de sa page VRAM introduites en v128 restent en place.

## Compromis connus

Dans les données officielles, `behindTrain` défile à vitesse 1.0, contrairement à la ville à 0.3. Il reste fusionné avec la couche ville, donc il suit ici le facteur 0.3. Le séparer correctement demanderait une couche et du stockage supplémentaires; cette étape conserve l’occlusion du train et la limite de huit pages validée dans la composition précédente.

L’animation de cheveux est une approximation compacte de l’animation officielle : quatre poses représentatives, pas les 30 images de chaque séquence du rig. La cadence est pilotée par les échantillons audio et 24 images/s. Le changement de lumière écrit un mot de CLUT avec synchronisation GPU au changement de beat; il ne relit pas le CD et ne modifie pas le flux musical.

## Construction et fichiers

- Branche : `ps1-port`, source build commit `d46317353583ba095f29eb5859e6d8bc4634fce0`.
- Ressources officielles : sous-module `assets` à `724eba9de9e76761d9cefd52169926bc51c760a5`.
- SDK PSn00bSDK 0.24 et GCC MIPS 12.3.0; compilation CMake/Ninja réussie.
- Les ressources W1/W2 préconverties sont réutilisées byte-à-byte : W1 SHA-256 `C2444F178F0A9A7F28B4B24476B9058E74FB15237DDD4BB786907F73A6CD0E8F`; W2 SHA-256 `BA93EC25BDAEABFDC21AA4BF32D2E7910367517DD4CEF863A3EB9259137F11D4`.
- W3 converti : 524800 octets, SHA-256 `886D0CED3C52B63C2CDEC752D59B78ADCE86894FDA4AFAD17F9F00AFF48B4AED`.
- Image finale : 117 fichiers; le réordonnanceur place `SYSTEM.CNF;1` en premier et `FUNKIN.EXE;1` en deuxième. BIN : 338509248 octets, SHA-256 `57DA215840A773748124644E9E1D5AF68E9AEF0E8871184CEC9D14A1AB2E110D`. CUE SHA-256 `D018AB21DBE7EF55F977B66EF039D2E35FC1BC37FF07042766FCC60EF2DA4B6B`.
- Le BIN/CUE v128 est inchangé : BIN SHA-256 `7C120F8D12728D5415ABCDFBF0C7BCC87C745C4F2DF8DB785F78BE4B50C63A57`; CUE SHA-256 `DC38F0D306754DC50BAC14B9C907AEB4A4E766D7F4B68EA2F485B2D2B874AA55`.

## Vérification

La conversion, la compilation, la création de l’image et le contrôle/réordonnancement de son répertoire racine sont réussis. Le son, le jeu, les changements de parallaxe, les couleurs de fenêtres et les réactions de GF n’ont pas encore été observés en DuckStation pour v129. Aucun essai sur console réelle n’a été fait. La prochaine étape est l’essai utilisateur à deux mains : charger le CUE v129, vérifier les mouvements de caméra pendant les sections Pico/BF, le train, les lumières et les cheveux de GF, puis nous attendreons ce retour avant toute correction.

## Reproduction

Le build CMake/Ninja réutilise les sorties préconverties et ne convertit pas les ressources d’autres semaines. La création du disque produit d’abord une image brute, puis `ps1/diagnostics/reorder_iso_system_cnf.py --exe-after-system-cnf` crée le BIN/CUE de livraison dans un dossier distinct. Les SDK, assets officiels bruts et fichiers intermédiaires restent hors de l’historique Git.

