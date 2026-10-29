# Journal de développement et de diagnostic PS1

Ce journal garde une trace chronologique du portage et des essais manuels. Il complète le détail technique de [PS1_PORT.md](PS1_PORT.md). Les fichiers BIN/CUE et ressources générées restent dans `outputs/` ou dans les dossiers de build ignorés par Git; le SDK reste hors dépôt.

## Règles de lecture

- **Validé utilisateur** : l’utilisateur a confirmé le comportement dans DuckStation.
- **Compilé / vérifié statiquement** : l’image ou les fichiers ont été construits et inspectés, sans observation d’exécution équivalente.
- **À essayer** : l’image a été remise à l’utilisateur; aucun résultat d’exécution n’est encore connu.
- **Console réelle** : aucun des jalons consignés ici ne constitue une validation sur matériel PS1.

Les numéros de version désignent les builds de travail communiqués pendant l’échange; ils ne remplacent pas les références de commit. Les points non mesurés (par exemple la dérive audio) restent explicitement non mesurés.

## Progression

### Fondations — chaîne PS1 et entrées

- Dépôt de portage isolé sur `ps1-port`; le travail PS1 est séparé du moteur Haxe/Flixel du jeu PC.
- La chaîne retenue est PSn00bSDK 0.24 avec GCC MIPS 12.3, CMake et Ninja, installée hors dépôt. PsyQ 4.6 et CodeWarrior de l’archive utilisateur ont été inventoriés, mais le SDK propriétaire et l’archive n’ont pas été ajoutés au dépôt.
- Un premier exécutable PS-X avec écran 320×240 et lecture de la première manette a été compilé et observé dans DuckStation. Les états de joueurs sont distincts dans la structure d’entrée afin de réserver l’architecture à un futur mode local à deux.

### Audio — streaming et synchronisation

- Le probe de streaming stéréo a d’abord échoué au préchargement. Le diagnostic a progressé des timeouts de tampon jusqu’au contrat réel du CD SDK : événement callback, retours de `CdRead`/`CdReadSync`, association des callbacks, secteurs livrés et alimentation de `Stream_Feed`.
- **Commit 46dbb5d — stéréo validée par l’utilisateur dans DuckStation** : essai de 4 min 02 s, 0 underrun, 0 erreur CD et aucun problème d’écoute signalé. La dérive précise n’a pas été mesurée; aucune console réelle n’a été testée.
- **Commit c89d519 — quatre canaux synthétiques validés par l’utilisateur** : instrumental L/R et voix L/R dans un flux commun; Circle coupe/rétablit les voix sans arrêter leur lecture. Essai de 3 min 08 s, 0 underrun et 0 erreur CD rapportés.
- Bopeebo officiel a ensuite été converti avec une origine commune, puis évalué en six canaux à 43 008 Hz. L’utilisateur a préféré la variante quatre canaux comparative, commit fad4fde, avec panoramique initial 5/7 et réglage à conserver. Le mute BF seul avec Circle a été confirmé.
- Le SFX provisoire Square/J a été corrigé : l’utilisateur a confirmé que les déclenchements automatiques et manuels fonctionnent. Les SFX sont jugés un peu faibles; ce point est conservé pour le mixage final, sans nouveau jalon dédié au bip de test.
- Le son de faute synthétique a été remplacé par les variantes officielles choisies selon le moteur d’origine. Leur déclenchement rapproché et les réactions de faute ont été confirmés par l’utilisateur; le bip de debug reste réservé aux probes.

### Premier gameplay et scène Bopeebo

- Le chart Normal officiel a été converti en conservant attribution BF/Dad, timing, notes tenues, score, santé, combo, jugements et mute de voix. Les premiers visuels utilisaient des formes simples avant l’intégration progressive des ressources officielles.
- **Commit 01e84a0 — correction de tenue validée par l’utilisateur** : le relâchement anticipé d’une note tenue produit le drop attendu, mute BF, puis BF récupère sa voix selon les règles retenues. Dad et l’instrumental continuent. Le placement Dad à gauche / BF à droite a également été confirmé.
- La scène, les ancrages, la caméra, les récepteurs et les flèches ont fait plusieurs passes. Une correction de flèche droite rouge, validée en v24, a ensuite coexisté avec plusieurs régressions temporaires lors des menus et transitions.
- Les règles de gameplay déjà confirmées (timing, santé, jugements, tenues, score) sont à préserver lors des travaux visuels et de démarrage.

### Jugements, popups et combo

- Une version antérieure (v32) avait des popups visibles en jeu; plusieurs versions suivantes ont perdu leur affichage malgré des tests QA fonctionnels. Le diagnostic a séparé événement de hit, résultat, durée audio, soumission de primitive, ordre GPU, texture/CLUT et essais de lecture VRAM. La sonde `StoreImage` v41 a provoqué un gel; les lectures VRAM ont ensuite été isolées des builds jouables.
- Des rectangles solides ont établi que les positions/commandes GPU étaient visibles, ce qui a orienté l’enquête vers le chemin des textures et palettes. Des tentatives successives ont corrigé puis réintroduit des défauts d’affichage.
- La cause finalement retenue pour la disparition des popups était le chargement des palettes en VRAM. Les synchronisations correspondantes ont été conservées dans le chargeur.
- **v52 — validée par l’utilisateur dans DuckStation** : jugements et compteur de combo visibles et animés; taille et mouvement alignés selon son retour, avec le popup réduit et le mouvement du combo appliqué au popup. Les essais précédents distinguaient les captures QA des hits réels; seule la confirmation utilisateur de v52 est retenue comme validation du rendu normal.

### Menus et catalogue

- Le parcours titre → menu principal → Freeplay a été construit à partir des ressources épinglées. L’élément OPTIONS remplace le lettrage Merch par une image approuvée; sa navigation aux flèches et son animation ont été ajustées. L’animation a été conservée en l’état lorsque l’utilisateur a décidé d’y revenir plus tard.
- Le Freeplay a été reconstruit à partir des références 4:3, avec capsules, catalogue extensible et état verrouillé pour les entrées non jouables. Plusieurs builds ont gelé ou divergé visuellement; v65 a servi de base fonctionnelle, puis la taille/cadrage des titres ont été corrigés. Les quatre chansons de la Week 1 sont jouables dans cette branche de travail.
- Le DJ BF reste une adaptation de menu. Sa taille a été signalée trop petite par l’utilisateur; le point n’est pas déclaré résolu.

### Week 2, chargement indépendant et Week 3

- v73 a ajouté Spookeez, South et Monster en Easy/Normal/Hard, avec charts et stems convertis et une première scène Week 2. Le décor initial était incomplet et Monster était coupé selon le retour utilisateur.
- v74 a déplacé charts et packages de scène vers le CD pour charger chaque morceau indépendamment, conformément à la préférence utilisateur de garder davantage de RAM libre pour les scènes plus lourdes. Cela ne constitue pas une preuve de pic RAM mesuré.
- **v75 — validée par l’utilisateur dans DuckStation** : Week 1 à la demande, Week 2 enrichie et base Freeplay. v75 reste la référence fonctionnelle de cette série.
- v76 a commencé l’adaptation Week 3 et ajouté un écran de chargement, mais l’utilisateur a signalé un gel au logo Sony PlayStation. v77 a réordonné les fichiers de scène pour les mettre au début du disque et avancé l’écran de chargement; le gel persistait. v78 ajoutait un repère GPU très précoce; l’utilisateur n’a vu ni repère ni changement du logo.

### Diagnostic du démarrage — état actuel au 2026-10-29

- Comparaison ISO v75/v78 : `SYSTEM.CNF` est identique (`BOOT=cdrom:\FUNKIN.EXE;1`, `TCB=4`, `EVENT=10`, `STACK=801FFFF0`); l’exécutable est présent au LBA 25, porte la signature `PS-X EXE`, charge à `0x80010000`, et son PC déclaré est dans la plage chargée. Les champs PS-X de remplissage mémoire sont nuls. L’ELF v78 disponible situe la fin BSS à `0x800EB1A0`, sous la pile; l’ELF v75 n’est pas conservé, donc sa fin BSS exacte n’a pas pu être mesurée.
- Les en-têtes `.ctors` de v78 et de la sonde v79 ne contiennent aucun constructeur à exécuter. Le CRT PSn00bSDK suit le même chemin : `_start` règle `$gp`, `_start_inner` efface BSS, initialise le heap, parcourt `.ctors`, puis appelle `main`.
- **v79 — validée par l’utilisateur** : sonde minimale PS-X avec un aplat bleu fixe. Elle prouve que la chaîne de compilation et de création du disque peut démarrer dans sa configuration DuckStation.
- **v80 — observée par capture utilisateur** : sonde avec une BSS de 39 640 octets, proche des 39 152 octets de v78, et repères persistants autour des initialisations. La capture couleur correspond au repère final après `CdInit` et PAD; elle est traitée comme confirmation de ce parcours de sonde, pas comme validation du jeu.
- **v81 — confirmée par l’utilisateur** : repère jaune-orangé, indiquant que `CdControlB(CdlPause)` a retourné succès.
- **v82 — confirmée par l’utilisateur** : l’écran blanc stable indique que l’allocation de 65 536 octets, `CdSearchFile("\\W1SCENE.BIN")`, la validation de sa taille (655 360 octets) et la libération du tampon ont abouti. Aucun secteur n’a été lu.
- **v83 — confirmée par l’utilisateur** : le blanc stable signifie que `CdPosToInt`/`CdIntToPos` puis `CdControl(CdlSetloc)` ont réussi. Le tampon a été libéré; aucun secteur n’a été lu.
- **v84 — confirmée par l’utilisateur** : écran blanc après `CdRead` d’un secteur et polling `CdReadSync(1)`; les 2048 octets reçus correspondent au CRC-32 attendu `0x569EEEF7`. Aucun transfert VRAM.
- **v85 — résultat DuckStation utilisateur : bleu** : le callback unique `CdlDataReady` (1) a été observé, mais son pointeur payload était nul. La branche de v85 s’arrête avant le CRC dans ce cas; la lecture avec callback reste à valider par contenu.
- **v86 — confirmée par l’utilisateur : vert** : `CdReadSync` et CRC sont conformes avec callback unique `CdlDataReady`, malgré le pointeur payload nul constaté en v85. Aucun transfert VRAM.
- **v87 — confirmée par l’utilisateur : vert** : lecture et CRC conformes sur la première page 8bpp de 32 secteurs, callback unique `CdlDataReady`, payload nul. Aucun transfert VRAM.
- **v88 — confirmée par l’utilisateur : vert** : lecture des 320 secteurs de `W1SCENE.BIN` en onze blocs via un tampon réutilisé de 64 Kio; CRC-32 attendu `0xF32FB433`, callbacks et lecture complète passés avec pointeurs payload nuls. Aucun transfert VRAM. BIN : 1 150 128 octets; SHA-256 `849D0E9EA5ACBA251B3F03890D40D0B4C765E1E6F4A9871CDC6D4C8FB75DA6BE`.
- **v89 — compilée, essai utilisateur à faire** : repart du démarrage minimal et lit uniquement la première page 8bpp de 32 secteurs, vérifie son CRC `0xA3BEABD8`, charge la page à `(384,0)` et la CLUT officielle à `(0,496)`, puis dessine un quad texturé 320×240. Un petit carré vert en haut à gauche confirme qu’une primitive postérieure au quad a été affichée. Repères persistants avant/après transfert de page, CLUT et dessin. Pas de gameplay, d’audio ni de balayage des autres pages. BIN : 1 150 128 octets; SHA-256 `7E474DDAAB0C79555737DFDDA6627446DBD4DB50A07E209FF74B13EF1B282BFC`.

### Audit de régression v75 → v76

- Les BIN/CUE v75 et v76 sont présents et lisibles, mais leurs sources/ELF/maps et configurations historiques ne sont pas toutes récupérables. Le dossier de build `ps1/build/freeplay-v76-week2-week3-loading` ne représente plus v76 : son BIN est octet-pour-octet le v78 connu (SHA-256 `54411573BB187CBC6E626B9604006CCE37AE4A3020F268EE5AEDF344F1553AC2`), et son EXE actuel ne correspond pas à l’EXE embarqué dans l’ISO v76. Aucun dossier/cache de build v75 n’a été trouvé. Le cache restant pointe vers PSn00bSDK 0.24/GCC MIPS, les assets locaux, des charts/VAGi temporaires et FFmpeg; ces chemins existent encore, mais ce cache ne reconstitue pas les sources historiques.
- Comparaison ISO : `SYSTEM.CNF` est identique dans les deux disques (`BOOT=cdrom:\\FUNKIN.EXE;1`, pile `801FFFF0`), et `FUNKIN.EXE` est au LBA 25. Les deux EXE chargent à `0x80010000`, avec champs BSS/memfill de l’en-tête PS-X à zéro. v75 : taille 868 352, PC `0x8001F910`, taille texte déclarée `0xD3800`; v76 : taille 860 160, PC `0x8001D864`, texte `0xD1800`. Les ELF historiques manquent, donc leur BSS/runtime exact avant le premier repère ne peut pas être comparé depuis les seules images disque.
- Contenu commun contrôlé par hash : musique de menu, flux Bopeebo, charts Week 1/2 et paquets `W1SCENE.BIN`/`W2SCENE.BIN` sont identiques. v76 ajoute Pico, Philly Nice et Blammed (charts Easy/Normal/Hard et pistes VAG), ainsi que `W3SCENE.BIN` (262 656 octets). L’image passe de 98 666 400 à 131 942 496 octets. `W1SCENE.BIN` est déplacé du LBA 39 258 au LBA 53 257 (écart 13 999 secteurs); W2 se déplace du LBA 39 097 au LBA 53 096. `MENU.VAG` et `STREAM.VAG` ont même taille et même hash dans les deux disques.
- Les notes décrivent aussi l’ajout du cadrage par stage, des couches/données Week 3, de l’écran de chargement et du chargement CD par paquets. Les données statiques documentées baissent de 905 398 octets (v75) à 897 242 octets (v76), tandis que la scène reste paginée et le tampon audio à 96 Kio. Il n’y a pas de preuve que la seule présence de `W3SCENE.BIN` ou le décalage de LBA cause le gel : v77 a réordonné les scènes et le gel logo a persisté; v78 n’a pas montré son repère GPU. Ces tentatives regroupaient plusieurs changements et ne localisent donc pas la régression.
- **Conclusion d’audit :** la comparaison binaire/ISO est reproductible; la comparaison des sources de code et une reconstruction contrôlée v75→v76 ne le sont pas avec l’état disponible. Je ne marque aucun groupe comme cause. Pour le prochain A/B dans le vrai exécutable, il faut les sources/ELF/cache originaux v75 et v76, ou un checkout/commit identifiable correspondant à chacun. Le test v89, lui, reste un essai GPU séparé en attente et ne tranche pas cette régression.

## État à reprendre

1. Obtenir le résultat utilisateur v89 : il tranche uniquement l’upload page/CLUT et le rendu texturé, pas le gel v75→v76.
2. Pour un A/B causal dans le vrai jeu, retrouver une source/ELF/cache v75 et v76 cohérente; ensuite isoler en un seul build instrumenté le groupe choisi, en gardant les autres entrées et réglages identiques.
3. Garder v75 comme référence fonctionnelle et v79 comme référence de boot. Ne pas confondre compilation, exécution utilisateur dans DuckStation et validation console réelle.
4. Conserver le gameplay, l’audio, les popups et les comportements confirmés; ne pas fusionner dans `main` sans demande explicite.

## Mise à jour du journal

À chaque prochain jalon, ajouter une entrée datée/versionnée avec : objectif et changement; commande/build ou fichiers produits; vérifications statiques/compilation; résultat observé par l’utilisateur; éléments encore non testés. Ne marquer « validé » que sur confirmation utilisateur ou preuve d’exécution explicitement observée.



### 2026-10-30 — v90 → v91, repère après le BSS

- v90 reste conservée intégralement avant modification dans `ps1/build/archive-v90-main-entry-marker-20261030` (113 fichiers, 765 377 656 octets). Les BIN/CUE v90 livrés restent identiques à l’archive par SHA-256. Le résultat utilisateur v90 était le logo Sony après deux minutes.
- Le build v91 réutilise le répertoire et la configuration de v90. Le dry-run a montré uniquement compilation du fichier de sonde, liaison de l’ELF et création de l’image disque : aucune reconversion de chart, sprite, scène ou audio. Les 49 ressources dont les empreintes sont archivées sont restées identiques.
- La sonde remplace `_start_inner`, effectue le clear BSS conforme au SDK PSn00bSDK 0.24, puis affiche un aplat ambre persistant avant initialisation du heap, copie argv, constructeurs et `main()`. Le code de jeu est conservé dans le lien par une référence conditionnelle dont le gate initialisé reste non nul.
- Source publiée sur `ps1-port` : commits `d9f01add`, `48635d2` et `a12a1b4` (final). Désassemblage : `_start` à `0x8001D9DC` saute vers la sonde `_start_inner` à `0x8001808C`; `main` demeure lié à `0x80014B20`.
- BIN v91 : 131 944 848 octets, SHA-256 `AAC0DF78054FC6CA1C48C678B8EF7B6D372609451267D4051642B175A1C29D4B`. Le dossier de livraison distinct archive le diff, le cache, les fichiers Ninja, les empreintes des ressources et le manifeste.
- **État : compilé et vérifié statiquement; essai DuckStation à faire par l’utilisateur.** Aucun comportement v91 n’est déclaré observé et aucune console réelle n’a été testée.
