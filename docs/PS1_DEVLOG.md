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

## 2026-10-30 — Week 4, build d’essai v100

L’utilisateur a indiqué que la build de démarrage est stable après ses essais et demande l’intégration Week 4. Ajout de Satin Panties, High et M.I.L.F avec Easy/Normal/Hard, soit neuf charts, trois flux VAGi quatre canaux à 43 008 Hz et une scène convertie indépendante. La scène partage les emplacements d’atlas gameplay existants. La version v100 conserve le parcours jouable existant et étend le catalogue à treize entrées.

La génération initiale a révélé que M.I.L.F Hard contient 674 notes, au-dessus de l’ancienne capacité de 451. La capacité des données a été portée à 674; aucun jugement, timing, score, santé ou comportement des tenues n’a été modifié. Une première sortie intermédiaire v99 a été conservée dans son propre dossier; v100 a ensuite été générée dans un dossier distinct.

Le build réutilise les ressources converties de v90 et le paquet Week 4 via les chemins CMake `FUNKIN_PS1_PRECONVERTED_BASE_DIR` et `FUNKIN_PS1_PRECONVERTED_WEEK4_DIR`. Le dry-run a confirmé l’absence de conversion/recompression globale : seuls les sources C modifiés, l’édition de liens et l’image disque ont été produits. PSn00bSDK 0.24 / GCC MIPS 12.3 / CMake 4.5 / Ninja. La création a aussi réordonné `SYSTEM.CNF` en tête du répertoire racine, en conservant les positions des fichiers, selon le correctif de boot utilisé après v98.

Artefacts v100 : `ps1/build/week4-v100/delivery/funkin-ps1-week4-test-v100.cue` et BIN adjacent. BIN 169 296 960 octets, SHA-256 `7083695845D2726FFBC446D5892446DF571CFF499EFC716B8AD1453C9C3B8AFE`; CUE SHA-256 `564DFCEE24E84C9F680CF4A1F43AC09E5DE64B56C9363CA7D183B09081602890`. Base locale `facbf1243875fe7e24819eff87d1879527f00584`; tree sale et contenu exact documentés dans le manifeste v100. Assets épinglés : `724eba9de9e76761d9cefd52169926bc51c760a5`.

Bilan statique : ELF `.text + .data + .bss` 899 514 octets; ring RAM audio 96 Kio; buffer scène temporaire 64 Kio puis libéré; pics estimés ~1,07 Mio de 2 Mio, non mesurés à l’exécution. Trois pages 8bpp / 196 608 octets de VRAM réutilisées et CLUT 512 octets. Double buffer SPU musical existant : 16 Kio. La scène est encore provisoire : décor statique, poses choisies pour Mom/GF; animations de voiture/henchmen absentes.

**Résultat :** compilation et contrôles statiques passés. L’utilisateur doit lancer le CUE et rapporter le résultat. Pas d’observation DuckStation par Codex, aucune validation utilisateur v100, aucun test console réelle.

## 2026-10-30 — Week 5, premier build à tester (v101)

L’utilisateur a confirmé v100 (Week 4) comme base parfaite et stable. v101 ajoute Cocoa, Eggnog et Winter Horrorland en Easy/Normal/Hard. Les charts proviennent des données classiques épinglées, et les trois flux conservent les pistes Instrumental L/R, BF et Parents/Monster à 43 008 Hz. Circle reste le mute de BF.

La scène est convertie depuis les ressources Week 5 du sous-module assets `724eba9de9e76761d9cefd52169926bc51c760a5`. Elle fournit le Mall de Noël, le Mall sombre, une pose fixe de Santa, des poses Mom/Dad et Monster, et la danse de GF Christmas dans trois pages 8bpp partagées avec le jeu. Le sprite BF demeure celui déjà utilisé, faute d’un sprite de Noël dans le checkout épinglé. Les arrière-plans et Santa sont statiques; les caractères sont réduits en 64×64, compromis provisoire à vérifier en jeu. Les variantes Erect/Pico ne sont pas exposées.

La génération audio initiale et les charts avaient été produits avant cette passe; ils ont été conservés, hachés et réutilisés avec `--reuse-audio`. Après constat que le canvas 768×768 coupait les rigs officiels et rendait Monster vide, ce choix a été abandonné. Le canvas 1200×1200 est conservé. Seul le calcul des limites alpha de `animate_preview.py` est passé à un balayage linéaire unique, sans modifier les bounds ni les pixels obtenus. Atlas généré : 197 120 octets; neuf charts (279/324/447 Cocoa, 288/354/458 Eggnog, 372/414/445 Winter Horrorland).

Configuration PSn00bSDK 0.24, GCC MIPS 12.3, CMake 4.5, Ninja; build séparé `ps1/build/week5-v101`. Les ressources de base v90 et le paquet Week 4 sont copiés depuis leurs répertoires préconvertis. Le dry-run a annoncé quatre opérations : compilation de `spu_probe.c`, compilation du `stream.c` du SDK, édition de liens, puis création de l’image disque. Build réussi. Le `size` de l’ELF indique `.text=859772`, `.data=2406`, `.bss=39564`, total 901742 octets. Aucune ressource SDK/propriétaire ou donnée générée n’est ajoutée au dépôt.

Le BIN brut a ensuite été copié vers un sous-dossier `delivery` et le répertoire racine ISO réordonné avec l’utilitaire existant, sans écraser le build brut ni v100. BIN livré : 208 262 544 octets, SHA-256 `658FBED595201177D1931FB14DFB84FFDBF1056963FC7125CC5AE68ED073AF12`. L’inspection du disque trouve `SYSTEM.CNF` en première entrée, 74 fichiers, `FUNKIN.EXE` au LBA 25, signature PS-X EXE et EXE extrait identique à celui du linker. Entrée `0x8001E5B0`, chargement `0x80010000`. SHA du CUE : `0D2E7C2829827366B413FF6B7D31A4245934F123C06DAE6E8FD532FCC41494D7`.

**État d’essai :** compilation et inspection statique réussies; aucune exécution DuckStation observée par Codex et aucune validation utilisateur v101. Prochaine action : l’utilisateur charge le CUE, puis rapporte le démarrage et teste les morceaux Week 5. Console réelle non testée.

## 2026-10-30 — Week 6, premier build à essayer (v103)

Ajout de Senpai, Roses et Thorns, avec charts Easy/Normal/Hard (285/341/385, 255/382/465 et 309/417/557 notes). Les stems classiques officiels sont convertis en VAGi à 43 008 Hz : instrumental L/R, BF mono et voix opposée mono. Les VAGi et les PCM décodés ont été générés une fois puis réutilisés pour le rebuild visuel (`--reuse-audio`).

La scène Week 6 est assemblée depuis les couches officielles de l’école normale et maléfique, les atlas Senpai/BF/GF pixel, Spirit, icônes et flèches pixel. Le premier rendu est statique pour les décors; personnages et GF ont un petit sous-ensemble de poses officielles, les corps des tenues sont des barres colorées provisoires. Paquet `W6SCENE.BIN` : cinq pages 8bpp et CLUT, 328 192 octets. Chargement paresseux et restauration des pages partagées au retour/relance. Le nettoyage de fin de morceau vide le paquet W6 comme celui des autres semaines.

Le build `ps1/build/week6-v103` a réutilisé les paquets de base v90 et Weeks 4/5, ainsi que la conversion W6. Le dry-run n’a annoncé que deux compilations C, édition de liens et ISO. Build compilé avec PSn00bSDK 0.24 / GCC MIPS 12.3 / CMake 4.5 / Ninja. Taille ELF `.text=862856`, `.data=2442`, `.bss=39612`, total 904 910 octets. Ring audio existant 96 Kio, staging RAM temporaire 64 Kio, cinq pages VRAM 320 Kio plus CLUT partagée. Le débit moyen des VAGi W6 est d’environ 99 kB/s; aucun CD de scène simultané à la musique.

Le BIN de livraison mesure 242 070 192 octets, SHA-256 `B70F551664AEBA18EA80F38DE0E9ACF37E65F162BB2D7F6BF80A123345B5411B`; le CUE fait 89 octets, SHA-256 `926B6307DD0A57E894F2E7C83EFB0F70822BFC8C4E78DC3F7EC8E26A4BAAC25F`. Le répertoire ISO contient 87 fichiers; `SYSTEM.CNF` est la première entrée et l’EXE extrait est identique au linker. Source identifiée par le commit `ee0bbd668eead59b1e77d06a0b3ab5a63e69b823` sur `ps1-port`; paquet généré et CUE livrés hors Git.

**État :** compilation et contrôles statiques réussis. CUE fourni pour essai utilisateur; pas encore exécuté dans DuckStation, pas de validation utilisateur v103 et pas de test console réelle.

## 2026-10-30 — Week 7, premier build d’essai (v104)

Ajout d’Ugh, Guns et Stress avec charts Easy/Normal/Hard depuis les assets épinglés. Les stems sont convertis en VAGi quatre canaux à 43 008 Hz. La scène Battlefield officielle est convertie en trois pages 8bpp; Tankman, BF, GF Tankmen (poses 0/15) et icônes sont présents. Le décor est statique et plusieurs animations Week 7 sont encore à compléter.

Build séparé `ps1/build/week7-v104`, paquet converti `ps1/build/week7-assets-v104`; tous les artefacts précédents restent intacts. Le dry-run n’a prévu que la compilation de `spu_probe.c`, le lien et la création ISO. Le build est compilé; l’ISO comporte 100 fichiers, `SYSTEM.CNF` en première entrée, et l’exécutable extrait correspond exactement au PS-X EXE lié. BIN livré : 282 232 944 octets, SHA-256 `66B2A773DD981BF987FAC50B54286461CDFB2BAECD177A497D300A3F9D6C57E5`; CUE SHA-256 `9C151AB23E78834CD2A624B037AC4AE5EAA2187E508956855C17647943839AC1`. Source v104 : commit `505e6038eb0a685afd725b450d5050417c7a3aa6` sur `ps1-port`. Détails, charts, budgets, hashes du paquet et procédure de test dans `docs/PS1_WEEK7_V104.md`.

Aucune exécution DuckStation observée pour v104 : l’utilisateur doit charger le CUE et vérifier lancement des trois morceaux, difficulté, notes/tenues, Tankman/BF, GF, audio/mute, fin et retour Freeplay. Aucune validation utilisateur ou console réelle revendiquée.

## 2026-10-30 — WeekEnd 1 classique, premier build d’essai (v105b)

Ajout de Darnell, Lit Up, 2Hot et Blazin, avec les trois difficultés Easy/Normal/Hard; Pico Erect et la collaboration Spaghetti restent hors périmètre. Les quatre lignes étaient déjà présentes et verrouillées dans Freeplay : le catalogue les rend jouables sans ajouter de doublons. Le chart maximal est 2Hot Hard à 1 035 notes. Les notes custom de Blazin ne sont pas encore interprétées comme mécaniques de combat; seul leur timing/lane/hold standard passe au format jouable.

Les flux utilisent quatre canaux VAGi à 43 008 Hz : instrumental stéréo et voix mono de l’adversaire et du joueur, alignées sur une origine commune. Circle coupe Pico pour Darnell, Lit Up et 2Hot. Blazin ne possède qu’un stem instrumental officiel dans la révision épinglée; ses canaux voix sont silencieux. La scène charge à la demande un décor statique Philly Streets/Blazin et un sous-ensemble de poses officielles Pico/Darnell, plus Nene intégrée au fond. Animations complètes, effets de scène et mécanique de combat Blazin sont encore différés.

Le premier v105 a été compilé avant la dernière modification de `spu_probe.c`, il est conservé mais n’est pas le disque livré. v105b a été reconstruit dans un dossier neuf en réutilisant le paquet WEnd1 converti et les paquets v90/W4–W7. Dry-run du seul objectif disque : deux compilations C, édition de liens et image ISO; aucune reconversion d’assets. Les quatre VAGi pèsent 47 816 704 octets, les douze charts 101 136 octets; le paquet de scène fait 524 800 octets (huit pages 8bpp et CLUT). ELF : `.text=866736`, `.data=2442`, `.bss=40080`, total 909 258 octets; tampon audio 96 Kio, staging de scène 64 Kio, pic RAM non mesuré.

Source identifiable : commit `ca6eb54157c257b2d3dd9cd9ca1fda1ff0d97142`, parent v104 `d01096a561c44188a46cf956af672e19157ac931`. BIN v105b : 337 885 968 octets, SHA-256 `CC491F701307EEAC16938611432797FCE8FB867658F0E43769CBEDD0F42A0BF1`; CUE SHA-256 `0025E04D2469D412797415D5085BA1AF0A5F51DB5E94CAA502C1F74BC8124180`. Audit statique : 117 fichiers racine, `SYSTEM.CNF` remis en première entrée et `FUNKIN.EXE` embarqué identique au fichier lié. Manifeste : `docs/PS1_WEEKEND1_V105.md`.

Compilation et vérifications statiques réussies. Aucun essai DuckStation observé par Codex, aucune validation utilisateur v105b et aucun test console réelle. L’utilisateur doit charger le CUE et vérifier les quatre titres/difficultés, audio, mute Pico, tenues, transitions, retry et retour Freeplay.

### Suivi — v105b bloquée au logo Sony

L’utilisateur rapporte ensuite que **v105b reste sur le logo Sony PlayStation**. La v105b d’origine reste intacte. Le contrôle statique confirme `SYSTEM.CNF` en première entrée, `FUNKIN.EXE` embarqué et identique au fichier lié, et un en-tête PS-X EXE avec entrée `0x8001FA64`, chargement `0x80010000`, texte `0x000D4800`; ces contrôles ne prouvent pas que le BIOS exécute le programme.

Un premier disque diagnostique conserve le source du commit `ca6eb54157c257b2d3dd9cd9ca1fda1ff0d97142` et toutes les ressources v105b. Le repère blanc à l’entrée de `main()` est la seule différence de comportement. Les 129 fichiers de ressources comparables sont identiques; le dry-run prévoyait uniquement deux compilations C, le lien et l’image disque. Le désassemblage confirme que le repère est dans l’exécutable livré et que celui-ci correspond octet pour octet à l’exécutable lié. **L’utilisateur a chargé cette sonde; l’écran Sony reste affiché.** Cela ne permet pas de distinguer à lui seul le CRT de l’initialisation GPU du repère.

Le deuxième disque ne change que le point d’arrêt : `_start` transfère à `startup_after_bss_marker.c`, qui efface la BSS réelle puis dessine un aplat ambre avant heap/constructeurs/`main`. Il réutilise les ressources v105b (hash `WEND1.BIN` identique); dry-run : trois compilations C, lien et image, sans reconversion. Compilation et vérification statique réussies; attente de l’essai DuckStation utilisateur. Voir [`PS1_STARTUP_V105B_PROBE.md`](PS1_STARTUP_V105B_PROBE.md). Pas de cause déterminée ni de test console réelle.

Publication note: local commits `ca6eb54157c257b2d3dd9cd9ca1fda1ff0d97142` and `61234072b04d83040ddae38cc958b65a3c696170` are present on the local `ps1-port`. `git push origin ps1-port` was attempted but Git for Windows could not acquire GitHub credentials (`SEC_E_NO_CREDENTIALS`). The remote draft PR was not changed; no force update or merge was performed.

### 2026-10-31 — v105b avant BSS : sonde corrigée après résultat utilisateur

L’utilisateur rapporte que la livraison `w1b` reste sur le logo Sony. Audit du binaire : l’EXE au LBA 27 correspond à celui du linker; entrée `0x8001FAC8`, GP `0`, chargement `0x80010000`, texte `0xD4800`; `_start` règle `$gp` puis saute au `_start_inner` de la sonde. Cependant, la sonde `w1b` envoyait un remplissage GP0 sans initialisation/configuration GPU, puis appelait `VSync()` sans démarrage CRT. Le logo Sony seul n’est donc pas un résultat négatif fiable sur l’atteinte de `_start_inner`.

Correction de diagnostic seulement, commit `3ad1540` : le point pré-BSS reprend maintenant la séquence d’initialisation GPU de v79 (référence validée), affiche un aplat cyan puis attend dans `VSync`. Le dry-run n’indique qu’une compilation C, le lien et l’image; aucune conversion de ressource. Le BIN/CUE initial `w1b` et ses fichiers bruts ont été préservés sous `ps1/build/w1b/reference-gp0-unconfigured/` et `ps1/build/w1b/delivery/`.

La nouvelle livraison distincte `ps1/build/w1c/delivery/` compile sans erreur. BIN : 337 885 968 octets, SHA-256 `2B3519664BBA80608E6091E7B24C6C181627155F0C14F5A3B18BAAE4519BA507`; CUE SHA-256 `91AF4305525326C771F648F6E51B95C913C92A05DF530E0AE490A2944BA1F662`. `SYSTEM.CNF` est le premier fichier du répertoire ISO; l’EXE extrait au LBA 27 est identique au linker (SHA-256 `8484CA51D23193091717B7375220668AFE65C35D0E27A22C513FF0F0E9156974`). Les charges utiles des fichiers ISO nommés sont inchangées, sauf l’exécutable; `WEND1.BIN` garde le hash `65D953BFF270548C66563CEB499950394645858865B60EA277A3FCCC3284139C`.

**État :** compilation et contrôles statiques réussis; la nouvelle image attend l’essai de l’utilisateur dans DuckStation. Ce n’est pas une validation d’exécution, et aucune validation console réelle n’est revendiquée. Voir `docs/PS1_STARTUP_V105B_PROBE.md`.

L’utilisateur rapporte que cette sonde reste elle aussi sur le logo Sony. Le désassemblage de la séquence pré-BSS montre une dépendance de `PutDispEnv()` à `_gpu_video_mode` en BSS, ainsi que l’accès de `ResetGraph()` aux états de callbacks/runtime. La variante SDK pré-BSS n’est donc pas un repère fiable. La prochaine différence isolée sera un repère par accès GP1/GP0 direct, avec les paramètres vidéo 320×240 NTSC dérivés de v79 et sans dépendance au SDK/à la BSS.

La variante pré-BSS SDK a été remplacée par une sonde plus isolée : commit source `264c41b`, écriture directe GP1/GP0, sans helpers SDK, BSS ni `VSync`. Le mode vidéo 320×240 NTSC et les valeurs de registre suivent le calcul du chemin v79. Le dry-run annonce une compilation C, lien et image seulement; aucun convertisseur d’assets. Les sorties du test précédent sont préservées dans `ps1/build/w1b/reference-sdk-gpu-init/` et `ps1/build/w1c/delivery/`.

Livraison `ps1/build/w1d/delivery/` : BIN 337 885 968 octets, SHA-256 `12071797F4B1997D3E9D6D99371BF754F4BC7524FD898D8C8B98302C3D8A368A`; CUE SHA-256 `FF80ADFEF50460BF49DC2223DFADD4FB4B842E9EDB09EAFCE90B69690328CB96`. `SYSTEM.CNF` est première; `FUNKIN.EXE` au LBA 27 correspond au linker (PC `0x8001FB18`, taille texte `0xD4800`). Tous les payloads ISO nommés restent identiques sauf l’exécutable; `WEND1.BIN` conserve son SHA et LBA précédents.

**État :** compilation et inspection statique réussies. Le CUE raw-GPU attend l’essai utilisateur. Aucune observation DuckStation par Codex ni validation console réelle.

L’utilisateur rapporte « logo Sony » sur le CUE raw-GPU. Comparaison avec le désassemblage `PutDispEnv()` de v79 : le code SDK prend une largeur de balayage par défaut de 256 (`screen.w=0`), donnant une plage horizontale `0x260..0xC60`. La sonde utilisait par erreur `0xDA0120`, calculée comme si la largeur vidéo 320 était la largeur de balayage. Le prochain essai corrige uniquement GP1(06) à `0x06C60260`; cela teste la validité de la fenêtre d’affichage et ne change ni scène ni gameplay.

Source corrigée commit `2e0c967`; l’unique différence est GP1(06) `0x06C60260`. Dry-run : une compilation C, lien et image; aucun convertisseur d’assets. Les fichiers précédents ont été archivés sous `ps1/build/w1b/reference-wrong-hrange/` et livrés séparément dans `ps1/build/w1d/delivery/`.

Nouveau CUE `ps1/build/w1e/delivery/funkin-ps1-v105b-before-bss-correct-hsync-probe.cue`, BIN SHA-256 `49AE8A9BD3E0A303FD2E561724B2871154776EFD141B497B1FAE8F1477954AFC`; CUE SHA-256 `208EEF8005010C7E5D022B8B33678500D7DC297BD5063C5561177F766E20B662`. Exécutable extrait identique au linker, entrée `0x8001FB18`; `WEND1.BIN` et les autres fichiers nommés du disque sont inchangés. Compilation et audits statiques réussis; test utilisateur en attente.

#### Vérification d’exécution — disque w1e et lancement direct

L’utilisateur rapporte que le CUE w1e corrigé reste sur le logo Sony. Pour séparer le boot BIOS/CD de l’exécution du programme, l’exécutable extrait de ce même BIN (LBA 27, SHA-256 `50ACE5D1906E40C7850BBE6250BC1AB508D075E22DEE44C05BAB6B2DBACBC3DC`) a été lancé directement dans DuckStation, sans reconstruire le disque. Codex a observé l’aplat jaune fixe prévu par la sonde et le titre de fenêtre `FUNKIN`. L’EXE correspond au fichier lié et à celui embarqué.

Ce résultat établit que le PS-X EXE atteint le code du repère en chargement direct; le CUE équivalent n’atteint pas un rendu visible depuis le boot BIOS. La différence est donc dans le chemin de chargement/démarrage depuis le disque ou dans l’état initial propre à ce chemin, mais la cause exacte reste à établir. L’audit du PVD/répertoire ISO9660 trouve le répertoire racine en LBA 22 (8 192 octets), `SYSTEM.CNF;1` en LBA 26 (55 octets), puis `FUNKIN.EXE;1` en LBA 27 (872 448 octets); le texte `BOOT=cdrom:\FUNKIN.EXE;1` correspond à ce nom. Pas de comparaison binaire à v79 : son image n’est pas disponible dans `ps1/build` inspecté. La boucle fixe de la sonde ne fait pas VSync; l’indicateur `Jeu : 0 IPS` n’est donc pas interprété comme un freeze ni comme une mesure de cadence. Console réelle non testée.

Comparaison de l’image v104 (dernière livraison précédente) et v105b : même identifiant volume, même `SYSTEM.CNF` et même nom de boot. Le répertoire racine passe de 6 144 à 8 192 octets; l’enregistrement `FUNKIN.EXE;1` passe de l’offset 1 496 (premier secteur de répertoire) à 2 222 (deuxième secteur). La prochaine sonde disque-only conserve w1e et ses extents, mais place l’enregistrement EXE immédiatement après `SYSTEM.CNF`. Elle teste si la recherche du boot par le BIOS est sensible à la position de cet enregistrement. Le helper de réordonnancement reçoit un commutateur explicite, inactif par défaut; ses anciennes sorties restent inchangées.

Livraison du test w1f : le BIN/CUE est dérivé du BIN w1e corrigé-hsync en changeant uniquement l’ordre des entrées du répertoire racine, `FUNKIN.EXE` remonté après `SYSTEM.CNF`. Vérifications EDC/ECC correctes; les données hors des quatre secteurs du répertoire racine sont identiques. `FUNKIN.EXE` reste LBA 27/872 448 octets et l’enregistrement passe à l’offset 156 dans le premier secteur. BIN SHA-256 `FE5496D4630101B5896CC944603D73ED10E059843A51A3BCA8002BDE260D6489`; CUE SHA-256 `ADD3E64A769E8DF17E9CD4D0560AAC7CD951A7437CD369844222E521D058285B`. Livraison locale `ps1/build/w1f/delivery/`. Aucun code de jeu recompilé ni ressource reconvertie. Source du générateur identifié par `f399899`; détails dans `docs/PS1_STARTUP_V105B_PROBE.md`.

**Essai manuel w1f :** l’utilisateur rapporte l’aplat jaune au boot BIOS. Comme seuls les enregistrements du répertoire racine différaient de w1e, cela confirme que remonter l’entrée EXE suffit à dépasser le blocage au logo pour la sonde. Pour appliquer le même changement sans sonde, un CUE w1g a été produit depuis le BIN v105b normal : seul le répertoire racine a été réordonné, l’exécutable de jeu et les ressources restent inchangés. BIN SHA-256 `E9D356B006D7D572D336BF9F9360AB0130A2D2EB7FB144B074F3D7247091C9E9`; CUE SHA-256 `5D41EAC9E918B0FB682C577C295C6867ABE585AB45EDF6569F87EA0E501AA718`, dossier `ps1/build/w1g/delivery/`. Attente du démarrage du jeu normal dans DuckStation; aucune compilation ni reconversion, aucune validation complète encore.

**Essai manuel w1g :** l’utilisateur confirme le démarrage normal. La cause est isolée au placement de l’enregistrement `FUNKIN.EXE;1` dans le répertoire racine ISO9660 : à l’offset 2 222 (deuxième secteur), le BIOS ne lançait pas l’exécutable; déplacé à l’offset 156 (premier secteur), avec le même LBA 27 et les mêmes 872 448 octets, le jeu démarre. Aucun code ou asset ne change. La limite est observée avec ce BIOS/DuckStation; console réelle et autres BIOS non vérifiés.
### 2026-10-31 — Week 2 framing and audio-clocked GF

The user supplied three current Week 2 screenshots and a gameplay reference video. The direct video path was not readable in this session; the existing extracted contact sheet plus the supplied screenshots were used for the comparison. The current build's Week 2 camera used Q8 zoom 582 (about 2.27×), which crops the opponents/BF against the 4:3 viewport and samples only a narrow part of the backdrop. The test build keeps the official Spooky Mansion positions and art unchanged, but uses Q8 zoom 384 (1.5×) for the 320×240 composition. Gameplay chart, audio, camera target events, judgement and controls are unchanged.

GF timing is tied to audio samples. Gameplay already reads the selected chart's tempo map, including Monster's BPM changes. The title screen now uses the pinned Freaky Menu metadata (102 BPM) and `Stream_GetSamplesPlayed()` to select its sampled dance pose; render-frame ticks remain only for menu-selection motion. No chart/audio/stage/sprite resource was regenerated. The new build reused the v90 base packages byte-for-byte; `bopeebo_visual_data.h` SHA-256 `35E72F266FA8DFE3B61D5888EA7EAC4D7A20CE5DD7C2EFCA994CFA09ECF0E5E4`, `W2SCENE.BIN` SHA-256 `3A4399DB5E58F05FD3902702960791D9134FF92EA3C97A845F7B574AF08B9439`.

PSn00bSDK 0.24 / GCC MIPS 12.3 build succeeded. Source commit `e8482b401fcb1e266c63214b6c8bb9d81314159b`; dry-run listed only `spu_probe.c`, the SDK `stream.c`, and link; the actual target then created the ISO. The deliverable BIN is 337,900,080 bytes, SHA-256 `85A4C9AA43D10CBDBB916116A2FB093888C26ED0248301A04D2949187B9ABFFC`; CUE SHA-256 `590747A7B5E4B31A6F052976D9DCDA95A7ACD579A0F29A04B8F2866A45673476`. The raw mkpsxiso image had `SYSTEM.CNF` as root record 93; the preserved delivery copy reorders it to record 1 and `FUNKIN.EXE` to record 2 for BIOS boot. Diagnostics are off by default. ELF resident sections total 922,442 bytes (`.text` 83,596, `.rodata` 796,204, `.data` 2,112, `.sdata` 382, `.sbss` 456, `.bss` 39,692). The chart, SPU, and VRAM budgets are unchanged from v105b.

**Validation:** compilation and static image checks succeeded. The new 4:3 framing and title animation have not yet been observed in DuckStation; the user will load the CUE for the agreed two-person test. No console test is claimed. This is a candidate Week 2 correction, not a user-validated build. Build details: [`PS1_WEEK2_V106.md`](PS1_WEEK2_V106.md).

### 2026-10-31 — Week 2 décor, idle cadence, Monster framing (v107)

The user reports that Spookeez and South opponent idles look too fast, the stage décor and lightning are missing, and the camera feels distant; Monster also appears cut off. Inspection found the converter was using only the nearly-flat `Sprite 0` background and did not consume the pinned `halloween_bg` Animate rig. A previous Monster conversion fit all poses against one combined rig envelope.

Source commit `b1fbcf6ca93826c7e7bc869a8f25963fcae16692` changes only `ps1/convert_bopeebo_visuals.py`, `ps1/spu_probe.c`, and `ps1/CMakeLists.txt`. It pre-renders three official background animation samples into patches in unused space on an existing Week 2 stage page; schedules them from the chart's audio sample/tempo mapping (first at beat 4 in Spookeez, beat 12 in South/Monster, then deterministic intervals in the original 8–24 beat range); selects eight distinct Spooky idle poses at half-beat steps; fits Monster's poses individually to their own alpha bounds while preserving aspect and floor anchor; and adjusts only Week 2 zoom to Q8 448. The strike schedule approximates the source's random intervals and is visual only. Charts, input/gameplay rules, audio stream, health, popups, and effects were not edited.

PSn00bSDK 0.24 / MIPS GCC 12.3 / CMake 4.5 / Ninja build succeeded. The converter checked 186 frame rectangles. Week 2 stays at five 8bpp pages (2 stage, 3 character), with three small lightning patches packed into free pixels: no extra VRAM page or CD read. Week 2 package is 328,192 bytes. Linked resident section estimate is 923,502 bytes (+1,060 vs v106); runtime allocation high-water was not measured. The build regenerated the shared Week 1/2/3 conversion: Week 1's 8bpp package differs from v106 (hash documented in `PS1_WEEK2_V107.md`), Week 3 is byte-identical. Week 1 needs a visual regression check.

Final boot-ordered image is under ignored `ps1/build/week2-scene-bpm-v107-20261031/delivery-v107-final/`; BIN SHA-256 `4BAECB81320746AFA65DDA88F0489377C55506873E5CD1E34B396B27FAAB0C16`, CUE SHA-256 `BA393E2E57CB82EE9EACCB6BD733630A5D2380A26CC9B9219910653CF679D558`. Previous candidates and generated inputs were preserved. Diagnostics are off by default. Compilation and ISO checks are observed; DuckStation execution, the requested scene checks, and real-console behavior remain unverified. No audio stability or drift result is newly claimed. Full build record: [`PS1_WEEK2_V107.md`](PS1_WEEK2_V107.md).

### 2026-10-31 — Week 2 and menu follow-up (v108)

The user authorized the previously reported corrections after reviewing the state. Source commit `4b5e1206d78f5afe04fe4e808f97dbd1e5e17045` composites the permanent Halloween stage frame into Week 2's existing base pages, slows the eight Spooky idle poses to one pose per chart beat, and uses direct official Monster character symbols rather than the clipped top-level scene export. Week 2's base camera zoom now uses the Week 1 Q8 640 constant while keeping the shared chart focus and transition behavior. Menu corrections map Fresh to Dad's icon, draw the custom OPTIONS label from a reserved area on the actual main-menu texture page, and move the navigation hint below the Credits row.

The four-channel 43,008 Hz music, charts, gameplay, SFX, menu/gameplay loading model and diagnostics defaults are unchanged. Existing preconverted audio and Week 4–Weekend 1 packages were reused; only the visual converter was rerun into a new v108 directory. The new visual header is 2,355,626 bytes; Week 1/2/3 packages are 655,360 / 328,192 / 262,656 bytes. The linker reports 923,650 bytes across `.text`, `.data`, and `.bss`; runtime RAM high-water remains unmeasured. No extra Week 2 VRAM page or CD read was added.

The SDK build completed with MIPS GCC 12.3.0 / PSn00bSDK 0.24. ISO root ordering was corrected in a separate delivery copy, with SYSTEM.CNF first and FUNKIN.EXE second. BIN SHA-256 `103D041A573BAC918B0F296F7183867DA9B6A7FA50F910F33E301C2CD52E2DDC`; CUE SHA-256 `882381B7AB419D25095A1AF5C1BCA0CA8ACE38CDD2EC5103DF0BBA53AEF9233D`. Full details and hashes are in [`PS1_WEEK2_V108.md`](PS1_WEEK2_V108.md). Compilation and static disc checks succeeded; no emulator run or console test was performed. The CUE awaits the user's DuckStation check.

### 2026-10-31 — Week 2 permanent décor and thunder audio (v109b)

After the v108 candidate, the user reported that Week 2 décor still appeared only during lightning and that lightning had no sound. The permanent-stage renderer had scaled from the full texture-atlas size and omitted the Animate root instance matrix (`AN.STI.SI.MX`). v109b applies the source root transform and 1/7 stage scale to the permanent and flash compositions, while excluding the rig's transient flash layer from the permanent base. A corrected intermediate render visibly contains the manoir window and room details without baking the flash into the base; the executed game has not yet been observed.

The pinned Week 2 script's official `thunder_1.ogg` and `thunder_2.ogg` are converted to 22,050 Hz mono SPU ADPCM, loaded before gameplay into the resident SFX bank, and selected on scheduled lightning strikes. The first Spookeez beat-4 flash remains silent as in the official script. Other visual strike timing remains the existing deterministic approximation. Thunder shares the existing four-voice SFX pool and its `0x3000` aggregate volume limit; no CD reads are added during the music stream.

The SPU bank is 269,056 bytes (up from 139,008), using 269,056 of the 385,024-byte reserved region at `0x22000`; 115,968 bytes remain there. ELF sections are `.text=1,011,212`, `.data=2,538`, `.bss=40,148`, total 1,053,898 bytes. Runtime RAM peak is unmeasured. Week 1/3 scene assets, menu VAGi, and game-over VAGi outputs were hash-checked byte-identical to v108; only Week 2's 328,192-byte scene package changed. No extra VRAM page or streaming bandwidth is used.

PSn00bSDK 0.24 / MIPS GCC 12.3.0 / CMake 4.5 / Ninja build and static ISO checks succeeded. BIN `ps1/build/week2-scene-bpm-v109b-20261031/delivery-v109b-final/fnf-ps1-week2-lightning-v109b.bin`, SHA-256 `BA1B46C6BD3450DDFA7406F25E84EB6041AB236BD99AEA8F08BD7B6C3691872F`; CUE SHA-256 `AB50080B5F29C16FAB62E0ECD897DD201F5D9BBD2447A9FDBEF135B91D498B9A`. Details in [`PS1_WEEK2_V109.md`](PS1_WEEK2_V109.md). No DuckStation run or console test has been performed by Codex; v109b awaits the user's two-person test.

Implementation is archived on `ps1-port` at commit `d37b7c078423d4c0b14cb67c3e288bffc81997d2`.

### 2026-10-31 — Week 2 décor composition and BPM cadence (v110b)

After the v109b report, an audit compared the converted PNG preview with the actual `W2SCENE.BIN` page and CLUT. The preview had the window, but the packed stage tile was uniform: `alpha_over()` returns a new buffer and its return value had been discarded. This is the concrete reason the permanent décor was still absent in the delivered game. v110b assigns the return value and applies the same Animate root translation to the atlas base and timeline layers. Decoding the emitted page and CLUT now shows the permanent room/window pixels in the background outside the lightning texture region.

The Week 2 GF CLUT atlas now includes all ten sampled dance poses (five per side), rather than only two. The eight Spooky idle poses now advance four poses per chart beat (two beats per full left/right cycle); `music_beat_q16()` derives these steps from the active song's audio sample count and tempo map. This targets the user's feedback that GF seemed to skip frames and the first two Week 2 opponents had become too slow. Runtime confirmation is still pending.

The dedicated Week 2 package grows by 131,072 bytes, from three to five character pages plus the two stage pages and CLUT (459,264 bytes total). It temporarily occupies 7 of the existing 9 8bpp page slots, restored when leaving Week 2; no global VRAM allocation increase. Scene staging remains one 64 KiB buffer. Week 1/3, audio and other preconverted package hashes match v109b. Linked ELF: `.text=1,011,284`, `.data=2,534`, `.bss=40,148`, total 1,053,966 bytes; runtime RAM peak remains unmeasured.

Compilation and static package/VRAM checks succeeded in a fresh Debug build configured like v109b. BIN/CUE are under `ps1/build/week2-scene-bpm-v110-20261031/delivery-v110b-final/`; hashes and procedure are in [`PS1_WEEK2_V110.md`](PS1_WEEK2_V110.md). No emulator execution or real-console validation is claimed; the user should load this CUE and report the visual/audio results.

Publication v110b — suivi : le commit source et la documentation sont présents localement sur `ps1-port` sous `44d99a980595bc397c7c014cc810223ddf1b460c`. Un commentaire de suivi a été ajouté à la PR brouillon #1. Le push du commit a échoué car Git for Windows n’a pas pu obtenir les identifiants GitHub (`SEC_E_NO_CREDENTIALS`) ; le code v110b n’est donc pas encore dans le diff distant. BIN livré : SHA-256 `50348A417FCD7839D324C8214F4ACC48024E09B5A364B019F98427D602BE8414`. CUE livré : SHA-256 `ABF7C84F350D5B5B18C3856BBD6181C5D34FBFC9B2098FEAAFCB01A69928D082`.

### 2026-10-31 — v111 : horloge SPU et poses Monster Week 2

Le retour utilisateur signale des poses Monster manquantes et un possible décalage de musique/notes d’au moins une mesure sur Spookeez, South et Monster. L’inspection des rigs officiels montre huit états d’attente distincts et plusieurs poses par direction. Le port ne gardait que deux poses d’attente et une pose de chant par direction. Le build v111 ajoute quatre poses officielles d’attente et deux poses pour chaque direction de chant, animées depuis l’horloge du chart.

La comparaison des charts Normal et métadonnées épinglés ne montre aucun `offset` déclaré. Les premières notes adverses/joueur sont respectivement aux mesures 4/6, 8/12 et 1/3, et les stems instrumentaux contiennent du signal dès leur origine. Cette structure est cohérente avec des intros propres à chaque morceau; elle n’explique pas à elle seule un écart d’une mesure. En revanche, le code PSn00bSDK cdstream appelle l’IRQ deux fois pendant `Stream_Start(..., false)` pour précharger les deux tampons SPU, et chaque appel incrémente déjà `play_time`. Le compteur retourné par `Stream_GetSamplesPlayed()` démarrait ainsi 14 336 échantillons (333 ms à 43 008 Hz) en avance sur le premier échantillon audible. v111 appelle `Stream_ResetSamplesPlayed()` après le démarrage réussi du flux. Cette correction commune est inférieure à une mesure; un écart résiduel doit être vérifié à l’écoute avant d’ajouter un quelconque offset de chart.

Le convertisseur a été exécuté dans un dossier candidat v111 avec FFmpeg 7.1.1. La première tentative avec FFmpeg 7.0 a échoué pendant le rendu du texte (`drawtext`) avant d’écrire les résultats; elle n’a touché ni aux builds livrés ni aux ressources v110. La tentative avec la version exacte a produit 40 frames Week 2 dans les deux pages de scène et cinq pages de personnages existantes, sans chevauchement ni page VRAM supplémentaire. VAGs, charts, packages Week 1/3 et les autres packages préconvertis ont été réutilisés; hashes dans [`PS1_WEEK2_V111.md`](PS1_WEEK2_V111.md). Aucun audio n’a été réencodé.

Build Debug PSn00bSDK 0.24 / GCC 12.3.0 : compilation et image CD réussies. BIN 338 203 488 octets (`3572333869AFA6AAE45560CE94FC00A9B88450BE7D6CAD285AAEA9B21384371F`); CUE `8579EEF0E6966AFD78659F364593E560C8384148E9258D14FA88B196A842B340`, dans `ps1/build/week2-monster-sync-v111-20261031/delivery-v111-final/`. Désassemblage : l’exécutable lié appelle bien `Stream_ResetSamplesPlayed()` après `Stream_Start()`. Compilation/atlas vérifiés; aucun lancement DuckStation par Codex ni essai console. Le CUE attend le test manuel de l’utilisateur. Voir [`PS1_WEEK2_V111.md`](PS1_WEEK2_V111.md).

### 2026-10-31 — v111b : correction de l’ordre de démarrage du disque

L’utilisateur a signalé que v111 restait au logo Sony. La comparaison de l’ISO avec v110b a trouvé `SYSTEM.CNF;1` en 93e entrée fichier, avec `FUNKIN.EXE;1` en 36e. Le disque v110b fonctionnel avait ces entrées en positions 1 et 2. L’étape de réordonnancement du répertoire racine utilisée pour v110b avait été omise à la livraison v111.

v111b réordonne uniquement les enregistrements ISO du répertoire racine, avec recalcul et vérification EDC/ECC. Le contenu de l’exécutable reste identique, à LBA 27 et 1 017 856 octets; les enregistrements `SYSTEM.CNF` et `FUNKIN.EXE` n’ont pas changé. Le script vérifie que tous les octets hors des secteurs du répertoire restent identiques. Le BIN/CUE original v111 est préservé.

BIN corrigé : `ps1/build/week2-monster-sync-v111-20261031/delivery-v111b-bootfix/funkin-ps1-bopeebo-playable-v111b.bin`, 338 203 488 octets, SHA-256 `D5B3423E38E78B794BFABD40D229F3CC54E229716CF3B37CBACE53B417304C3B`. CUE SHA-256 `DD44981C6385B66FA0DAE16A49FD7C965701DFDFAE2C870BCF220C1CD772FA2F`. Inspection statique réussie, mais attente de l’essai utilisateur DuckStation; aucune validation du démarrage, du timing ou de Monster revendiquée. Pas de console réelle.

### 2026-10-31 — v112 : timing Week 2 et cadrage du décor

L’utilisateur a confirmé que les flèches arrivent avant le son. Le chart Normal de Spookeez, South et Monster est décalé de +1 000 ms à l’horloge de 43 008 Hz (43 008 échantillons), notes, fins de tenues et changements de focus compris. La musique, la carte BPM et les fenêtres de jugement restent inchangées. Les marges de fin après décalage restent de 2,60 s, 6,52 s et 4,55 s respectivement. Cette correction attend encore l’écoute utilisateur; aucune dérive précise n’a été mesurée.

Pour le décor, la scène statique était déjà dans le package, mais le zoom/cadrage existant montrait principalement le sol sombre et coupait la fenêtre hors du cadre. Le calcul du viewport 320×240 au focus Dad montrait une tranche source approximative x=59–187, y=82–178. v112 translate le décor Week 2 et l’éclair ensemble de +70 unités monde sur x et y; le viewport atteint alors environ x=0–117, y=12–108 et révèle la partie supérieure de la pièce. Les chanteurs, notes, caméra, audio et règles restent inchangés. Cette composition attend le test manuel.

Le package v111 a été réutilisé, sans reconversion d’assets. Un essai de conversion intermédiaire a démontré que l’affectation de la première composition `alpha_over()` ne changeait pas `W2SCENE.BIN` (même SHA-256) : le sprite concerné est un fond opaque de même couleur que le remplissage. Cette modification a été retirée; elle n’est pas dans le build. Le dry-run CMake/Ninja annonçait uniquement compilation des deux sources C, édition de liens et création ISO. Compilation réussie; aucune exécution DuckStation/CUE par Codex, aucun test console.

Le build normal v112 conserve le réordonnancement ISO validé en v111b (`SYSTEM.CNF` enregistrement 1, `FUNKIN.EXE` 2). BIN SHA-256 `720C29AAC48164AA08DEA5DEE02008D447D1575BCF1A1160F7937058ED8F6633`, 338 203 488 octets; CUE SHA-256 `9EF5AC273E10AF18962CC12177191AF1691FC02E1004DF3B6BB8753EDC09C6DE`. Détails et chemins dans [`PS1_WEEK2_V112.md`](PS1_WEEK2_V112.md). En attente du chargement et du retour utilisateur; aucune validation visuelle ou audio revendiquée.

### 2026-10-31 — v113 : retrait du décalage Week 2 et nouveau cadrage du fond

Après le test de v112, l’utilisateur indique que tous les sons semblent environ une seconde en retard, avec Parsec comme cause possible, et demande de revenir sur l’ajustement de timing. v113 retire donc exactement l’ajout de 43 008 échantillons aux notes, tenues et événements caméra des trois charts Week 2. Aucun changement n’est fait à l’horloge de lecture audio, aux charts source, aux BPM, aux jugements ou aux règles de gameplay. La latence éventuelle de Parsec/DuckStation reste à isoler ; aucun décalage précis n’est mesuré.

Le décor statique reste absent selon le retour. Le package Week 2 n’a pas été régénéré. La piste investiguée est le cadrage : avec le zoom chanteur de 2,5×, seule une zone sombre du fond est montrée. v113 applique au fond et à l’éclair le même zoom visuel de 1,25× (plus l’impulsion musicale existante), sans changer les cibles de caméra ni la transformation des personnages et notes. Le calcul à la position Dad place la première page de fond dans le cadre 320×240 ; cela reste une hypothèse à vérifier dans DuckStation, pas une validation observée.

Build Debug PSn00bSDK 0.24 / GCC 12.3.0 / CMake 4.5 / Ninja dans un répertoire neuf. Les paquets convertis v111, les charts et le VAGi existants ont été réutilisés ; hashes du package Week 2, du VAGi, des trois VAG Week 2 et des trois charts Normal vérifiés identiques aux copies v112. Le dry-run de la seule cible jouable prévoyait deux compilations C, le lien et l’image CD. Le build et l’inspection de l’ordre ISO sont réussis. BIN `ps1/build/week2-sync-bg-v113-20261031/delivery-v113-final/funkin-ps1-week2-v113.bin`, SHA-256 `6046A9038F423C679EE726BE90927C109D8A186BBE34191FCD4F09465B61AE53`; CUE SHA-256 `26BCE8B63133A8221D216A1EEB94CAD2716C6CF8A29C565DCDF386C64F147CFE`. Aucun test DuckStation/console n’est revendiqué. Détails dans [`PS1_WEEK2_V113.md`](PS1_WEEK2_V113.md). En attente du test utilisateur.

### 2026-10-31 — v114 : cadrage du décor Week 2 et durée des éclairs

Le retour sur v113 demande un décor plus rapproché et plus bas, sans bords visibles, ainsi que le retour des éclairs. Le fond converti fait 362×256 après réduction de l’atlas officiel 2536×1837; il n’est pas lui-même au ratio 16:9. Le rendu PS1 conserve ses proportions et remplit le viewport 4:3 par recadrage. v114 augmente le zoom commun du fond et des éclairs de 1,25× à 1,5× et descend les deux de 16 unités monde. Le rectangle résultant (environ 543×384 pixels avant caméra) déborde le viewport 320×240 aux cibles Dad/BF calculées, ce qui devrait masquer les bords sans changer la caméra des personnages ou des notes.

La vérification des temps d’animation montre que le runtime ne gardait que 18 ticks à 24 ticks/s (0,75 s), bien que la séquence officielle dure 30 frames. La durée visuelle est portée à 30 ticks (1,25 s), et le premier éclair est programmé au beat 4 sur les trois pistes; les intervalles ultérieurs restent dans la plage déterministe 8–24 beats. Le mixage et les sons thunder ne changent pas; le premier éclair de Spookeez reste silencieux comme dans le script épinglé.

Le dry-run Debug n’a prévu que `spu_probe.c`, `stream.c`, le lien et l’image CD. Aucun asset n’a été reconverti. Les scènes, VAGs et charts ont été vérifiés identiques à v113. Compilation et réordonnancement ISO réussis (`SYSTEM.CNF` entrée 1, `FUNKIN.EXE` entrée 2). BIN/CUE dans `ps1/build/week2-scene-fix-v114-20261031/delivery-v114-debug-final/`; BIN SHA-256 `0374FF0BD452481D40553C5994B2A88022B586371DAC1D8128EAB8763A20E34D`, CUE SHA-256 `4D7E778B6F05DDBE7F84BE3FCCE2F15DB76C56F6A06F075C9EE95190F115B1EF`. Le build n’a pas été exécuté dans DuckStation ni sur console; le CUE attend l’essai manuel. Détails dans [`PS1_WEEK2_V114.md`](PS1_WEEK2_V114.md).

### 2026-10-31 — v115 : cadrage bas du décor et crop du flash Week 2

Retour utilisateur sur v114 : la région marquée en bas devait passer sous le cadre et les éclairs restaient invisibles. Le fond et l’overlay gardent le zoom 1,5×; leur décalage vertical passe de +16 à +85 unités monde. D’après la capture, cela déplace le haut de la région marquée d’environ 103 px, de y≈137 à y≈240. Une couleur unie correspondant au fond de la scène remplit la bande haute découverte. Les personnages, les cibles caméra, les notes et les règles restent inchangés.

Cause identifiée pour l’éclair invisible : le crop source précédent (92,81)–(255,211) excluait la fenêtre éclairée en haut à gauche du rendu Animate officiel. `ps1/rebuild_week2_lightning.py` produit les trois patches uniquement, avec le nouveau crop (10,0)–(173,130), et les place dans les réserves existantes de la page texture 1. La palette et les autres assets convertis restent byte-identiques; aucune page VRAM/CD/SPU supplémentaire. Le script complet de conversion utilise maintenant le même crop et ancrage corrigé. Un aperçu PNG reconstruit depuis la texture indique que l’échantillon 2 montre bien la fenêtre éclairée; cela ne valide pas le rendu runtime. Durée et calendrier de flash, sons, et décalage audio restent inchangés.

Build PSn00bSDK 0.24 / GCC 12.3 / Debug réussi dans `C:/Users/Manau47/Documents/Codex/w2v115c-week2-backdrop-lightning-cmake/`; dry-run limité aux deux compilations C, lien et création ISO. 117 fichiers racine, 338 203 488 octets; `SYSTEM.CNF` puis `FUNKIN.EXE` en entrées 1 et 2. BIN `ps1/build/week2-scene-fix-v115-20261031/delivery-v115-final/funkin-ps1-week2-v115.bin`, SHA-256 `AC663F620F6C3E33B34A78F5D8FCB3CE5059FBFC18634EE9A1B229C0E6DD3FFA`; CUE SHA-256 `F9AC44CEC24EAC8E37AA71B00F90DD844F9B2902BCF965254CF4FC80C27B40E4`. Aucun essai DuckStation/console n’est revendiqué; attente du test manuel. Détails dans [`PS1_WEEK2_V115.md`](PS1_WEEK2_V115.md).

### 2026-10-31 — v116 : zoom du décor Week 2 et cadrage adverse Spookeez/South

À la demande de l’utilisateur, le décor apprécié en v115 est agrandi d’un facteur 1,5 supplémentaire (zoom total 2,25×), puis légèrement remonté après agrandissement. Son origine est recalculée autour de la cible caméra actuelle afin de préserver le cadrage relatif; l’overlay d’éclair garde la même transformation et son alignement sur la fenêtre. Pour les deux premières pistes de Week 2 seulement, la cible de caméra Dad est abaissée de 5 unités monde, soit environ 12,5 pixels à l’écran au zoom de caméra actuel. Monster et les autres pistes ne sont pas touchés.

Le dry-run ne prévoit que la recompilation du programme et du lecteur SDK, l’édition de liens et la création du disque. Les ressources préconverties de v115 ont été conservées; les fichiers appariés ont les mêmes SHA-256, dont `week2-scene.bin` (`BA93EC25BDAEABFDC21AA4BF32D2E7910367517DD4CEF863A3EB9259137F11D4`). Compilation Debug et contrôle statique de l’ordre de démarrage réussis; `SYSTEM.CNF` est entrée 1, `FUNKIN.EXE` entrée 2, 117 fichiers, 338 203 488 octets. BIN SHA-256 `B4EFAE8CD74D5104304FF8FDC7185D1315E7F337086DE9A695D2353B7A6DFAFB`; CUE SHA-256 `8A9614E7DF9C9331BA01C48EB60760B9B1E014074C6F1567AFB9533C9C33C029`. Aucune exécution DuckStation ou console n’est revendiquée. Détails dans [`PS1_WEEK2_V116.md`](PS1_WEEK2_V116.md); le CUE attend l’essai manuel.

Retour utilisateur : v116 déplace la caméra dans le mauvais sens et le décor fixe disparaît, bien que l’éclair reste visible. Analyse du calcul : l’agrandissement avait conservé le coin supérieur gauche, ce qui ne montrait plus la zone centrale de la pièce. L’ajustement caméra était aussi appliqué au signe opposé à la direction voulue.

### 2026-10-31 — v117 : recentrage du crop et sens caméra corrigé

v117 conserve le zoom 2,25×, mais ancre maintenant l’agrandissement au centre du décor 362×256 afin que la zone de pièce reste dans le viewport; la remontée légère de 5 unités monde est maintenue. Sur Spookeez et South seulement, la coordonnée Y cible adverse augmente de 5 unités monde : la caméra descend et la scène remonte d’environ 12,5 px. Les ressources sont exactement celles de v115/v116 et le hash du package `week2-scene.bin` est inchangé (`BA93EC25BDAEABFDC21AA4BF32D2E7910367517DD4CEF863A3EB9259137F11D4`).

Dry-run sans conversion; compilation Debug et ordre statique ISO réussis (`SYSTEM.CNF` 1, `FUNKIN.EXE` 2; 117 fichiers). BIN SHA-256 `3CFC6FB77368BD6C8A2CBF007E600E9BAE1EE41F513594A15EC07C462E7EF449`; CUE SHA-256 `FF4C0E0D7CB51B7B5946BE8E54925D987A9B82FD4F2D6FF2AC08DE966367727F`. Aucun lancement DuckStation ni test console revendiqué; attendre l’essai utilisateur. Détails dans [`PS1_WEEK2_V117.md`](PS1_WEEK2_V117.md); les livraisons v116/v117 restent dans des dossiers distincts.

### 2026-10-31 — v118 : fond Week 2 recadré sans déplacer les caméras

Retour utilisateur : les caméras des personnages sont correctes, mais le décor fixe reste invisible. En comparant v115 et v117, le zoom du fond avait été porté à 2,25× puis centré géométriquement sur tout le canvas 362×256. L’illustration officielle est asymétrique et place la fenêtre/la pièce hors de ce centre ; le recadrage visait donc surtout sa grande zone sombre. v118 restaure le cadrage de fond v115 (1,5×, origine de scène et décalage vertical existant), tout en conservant les cibles caméra de v117. Le calendrier et le transform relatif des éclairs suivent le fond.

Le correctif d’affectation `alpha_over()` envisagé pendant l’inspection n’explique pas le défaut : le journal v112 avait déjà établi que cette première composition est un no-op, car le sprite source est opaque et de la même couleur que le remplissage. Elle n’est pas dans le build. Aucun asset n’a été converti. Le dry-run a listé seulement la compilation de `spu_probe.c` et `stream.c`, le lien et l’image disque. Le `week2-scene.bin` réutilisé garde le hash v115 `BA93EC25BDAEABFDC21AA4BF32D2E7910367517DD4CEF863A3EB9259137F11D4`.

Compilation Debug et création ISO réussies; 117 fichiers, 338 203 488 octets, `SYSTEM.CNF` puis `FUNKIN.EXE` en entrées 1 et 2. BIN SHA-256 `9661A7C08EE3B139B76E1A6B78B2052B0E1F206F265E75F3A026C43CB93B35FF`; CUE SHA-256 `8579EEF0E6966AFD78659F364593E560C8384148E9258D14FA88B196A842B340`. Dossier : `ps1/build/week2-background-v118-20261031/delivery-v118-final/`. Pas d’exécution DuckStation ni console revendiquée; attendre le test manuel. Détails dans [`PS1_WEEK2_V118.md`](PS1_WEEK2_V118.md).

Pendant l’analyse, un paquet candidat `preconverted-base-v4` et des aperçus ont été créés dans `ps1/build/week2-scene-fix-v118-20261031/` par `ps1/rebuild_week2_static_backdrop.py`. Ils n’ont pas été intégrés au disque v118 : cette conversion expérimentale ne change pas le résultat du cadrage, et le BIN livré reprend le package v115 byte pour byte. L’utilitaire est conservé comme artefact de diagnostic, pas comme convertisseur de production.

### 2026-10-31 — v119 : contraste du décor permanent Week 2

Retour utilisateur sur v118 : les cadrages des personnages sont désormais corrects, mais le décor statique reste invisible. Le décodage indépendant des deux tuiles `week2_stage_scene` de `W2SCENE.BIN`, avec leur CLUT, confirme que fenêtre et escalier sont bien présents dans les données. Leurs tons sont cependant très proches du fond de remplissage. v119 garde strictement la caméra, la géométrie, le zoom, les éclairs, le gameplay et l’audio ; la modulation GPU des deux tuiles permanentes passe seulement de 128 à 192, soit 1,5×. Il s’agit d’une hypothèse de contraste à confirmer dans DuckStation, pas d’une correction déclarée validée.

Le package de scène v115 a été réutilisé sans conversion (`W2SCENE.BIN` SHA-256 `BA93EC25BDAEABFDC21AA4BF32D2E7910367517DD4CEF863A3EB9259137F11D4`). Dry-run limité à `spu_probe.c`, `stream.c`, lien et création du disque. Compilation PSn00bSDK 0.24 / GCC 12.3 réussie ; les seuls avertissements sont ceux déjà présents dans `stream.c` sur le qualificatif `volatile`.

La vérification ISO a détecté que la sortie brute Ninja plaçait `SYSTEM.CNF;1` en 93e entrée racine. Cette sortie est conservée comme intermédiaire. Le BIN livré passe par `ps1/diagnostics/reorder_iso_system_cnf.py`, avec recalcul des checksums des secteurs modifiés ; les 117 fichiers sont présents et `SYSTEM.CNF;1`/`FUNKIN.EXE;1` sont les entrées 1/2. Image 338 203 488 octets. CUE/BIN final : `ps1/build/week2-background-v119-contrast-20261031/delivery-v119-rootfix/`; BIN SHA-256 `77460B1EAE38731BD57EC8C74D4D5653C84FBD51391AACAF2D0EF88A5D5066E2`, CUE SHA-256 `BDA46FD0A026D16A0676E12571FB4D6AA20543D022A974902780EE999771D653`. Aucun essai DuckStation ou console n’est revendiqué ; attendre le test manuel. Détails dans [`PS1_WEEK2_V119.md`](PS1_WEEK2_V119.md).

### 2026-10-31 — v120 : zoom supplémentaire du fond Week 2

Retour utilisateur sur v119 : décor visible et éclairs corrects; demande d’essayer un zoom supplémentaire de 1,5×. v120 augmente uniquement l’échelle de base du fond et de sa couche d’éclair alignée, de Q8 384 (1,5×) à 576 (2,25× total). La pulsation additive, le décalage vertical 85, l’origine/cadrage de v119, la teinte du fond (192), les caméras des personnages, les animations, le chart, le gameplay et l’audio restent inchangés. Le recadrage devient plus serré; sa qualité reste à vérifier par l’utilisateur dans DuckStation.

Build Debug PSn00bSDK 0.24 / GCC 12.3 / CMake 4.5 / Ninja dans `C:/Users/Manau47/Documents/Codex/b120w2`. Le dry-run prévoyait seulement recompilation de `spu_probe.c` et `stream.c`, lien et création ISO, sans conversion. Le fichier de scène réutilisé est identique à v119 (`week2-scene.bin`, SHA-256 `BA93EC25BDAEABFDC21AA4BF32D2E7910367517DD4CEF863A3EB9259137F11D4`). Compilation et création d’image réussies; avertissements SDK `volatile` inchangés. L’ISO brut est conservé séparément. Après réordonnancement et vérifications statiques : 117 fichiers, `SYSTEM.CNF;1` entrée 1, `FUNKIN.EXE;1` entrée 2, 338 203 488 octets. BIN SHA-256 `6B483984B4C6D96AEF4055A8E8AC1BA962A21A7C97240A0DE1BC69F5460D8D73`; CUE SHA-256 `BDA46FD0A026D16A0676E12571FB4D6AA20543D022A974902780EE999771D653`. Le CUE v120 est dans `ps1/build/week2-background-v120-zoom-20261031/delivery-v120-rootfix/`. Aucune exécution DuckStation ni validation console revendiquée; attendre le test manuel. Détails dans [`PS1_WEEK2_V120.md`](PS1_WEEK2_V120.md).

Retour de test ajouté après livraison : l’utilisateur signale que le décor statique a de nouveau disparu, alors que les éclairs restent visibles. L’analyse du transform explique le défaut de composition : à 2,25×, la fenêtre du fond commence vers x source 52, contre x≈16 au crop v119.

### 2026-10-31 — v121 : restaurer le bord gauche reconnaissable du décor

v121 conserve l’échelle v120 (2,25×), la teinte (192), le décalage Y (85), les caméras des personnages, l’impulsion rythmique et l’alignement de l’éclair. Le fond et l’éclair sont déplacés ensemble de +36 unités monde sur X. Avec la cible caméra Dad x=67, cela replace le bord gauche du viewport vers la source x≈16, comme en v119, au lieu de rogner la majeure partie de la fenêtre. Les charts, audio et règles de gameplay sont inchangés.

Build dans `C:/Users/Manau47/Documents/Codex/b121w2`; dry-run limité à la compilation `spu_probe.c` / `stream.c`, lien et image CD, sans conversion. `week2-scene.bin` est réutilisé byte à byte (SHA-256 `BA93EC25BDAEABFDC21AA4BF32D2E7910367517DD4CEF863A3EB9259137F11D4`). Compilation réussie; avertissements `volatile` préexistants du SDK. L’ISO brut est gardé dans `delivery-v121-pre-rootfix/`; après contrôle/réordonnancement, le disque contient 117 fichiers, `SYSTEM.CNF;1` en premier et `FUNKIN.EXE;1` en second, 338 203 488 octets. BIN SHA-256 `72D7312CC1FA0CCF61CD3693DDF68E0EFE8A7F725EA6A9721F094DADB01AA3BD`; CUE SHA-256 `BDA46FD0A026D16A0676E12571FB4D6AA20543D022A974902780EE999771D653`. CUE : `ps1/build/week2-background-v121-cropfix-20261031/delivery-v121-rootfix/`. Compilation et contrôles statiques réussis; test DuckStation en attente utilisateur, aucun test console. Détails dans [`PS1_WEEK2_V121.md`](PS1_WEEK2_V121.md).

Retour utilisateur sur v121 : toujours aucun décor statique, les éclairs restent visibles. Le déplacement du crop n’était donc pas suffisant.

### 2026-10-31 — v122 : clip GPU des tuiles statiques Week 2

v122 conserve le zoom 2,25× et le transform de v121. Au lieu de soumettre les tuiles de décor comme des FT4 de 576×576 dépassant les limites d’affichage, le nouveau chemin calcule leur rectangle visible dans le viewport 320×240 puis ajuste les UV avant la soumission. Le but est d’isoler le rendu des grands quads texturés; il ne change ni l’asset, ni la palette/CLUT, ni la teinte, les caméras, l’éclair, le gameplay ou l’audio.

Build Debug dans `C:/Users/Manau47/Documents/Codex/b122w2`. Le dry-run ne prévoit que compilation de `spu_probe.c`/`stream.c`, lien et création ISO; toutes les ressources préconverties sont réutilisées. `week2-scene.bin` hash `BA93EC25BDAEABFDC21AA4BF32D2E7910367517DD4CEF863A3EB9259137F11D4`. Compilation réussie, avertissements `volatile` existants du SDK. Après réordonnancement et vérification : 117 fichiers, `SYSTEM.CNF;1` puis `FUNKIN.EXE;1`, 338 203 488 octets. BIN SHA-256 `A2F133346B1A636D56E42CE2AB621D6339F89062E1B13FD88775E8EF3CCCBA7A`; CUE SHA-256 `ED7CD8E31BACDDD2F536505D5D25E763FD93C3F254CC2C5003A2F239A9E8CD2D`. Les fichiers explicitement versionnés `funkin-ps1-week2-v122.cue/.bin` sont dans `ps1/build/week2-background-v122-gpuclip-20261031/delivery-v122-rootfix/`. L’exécution DuckStation est en attente du test utilisateur; aucun résultat runtime ou console n’est revendiqué. Détails dans [`PS1_WEEK2_V122.md`](PS1_WEEK2_V122.md).

### 2026-10-31 — v123 : déplacer le décor Week 2 vers la droite

Après la validation visuelle de v122, l’utilisateur demande de décaler le décor d’environ 20–25 pixels vers la droite. v123 augmente le décalage partagé du fond et de l’éclair de 36 à 46 unités monde; au zoom 2,25×, cela déplace les deux de 22,5 pixels à l’écran et préserve leur alignement. Le clipping des tuiles statiques introduit en v122 reste actif. Aucun changement aux caméras des personnages, au gameplay, aux charts, à l’audio ou aux ressources converties.

Build Debug dans `C:/Users/Manau47/Documents/Codex/b123w2`; dry-run limité à compilation `spu_probe.c`/`stream.c`, lien et ISO, sans conversion. `week2-scene.bin` inchangé, SHA-256 `BA93EC25BDAEABFDC21AA4BF32D2E7910367517DD4CEF863A3EB9259137F11D4`. Compilation réussie, avertissements SDK `volatile` inchangés. Image réordonnée et vérifiée : 117 fichiers, `SYSTEM.CNF;1` puis `FUNKIN.EXE;1`, 338 203 488 octets. BIN SHA-256 `C1F13CEBF9FBCCA842BFC44032B8B62AD74389110F1C3E11922F77C1D0226222`; CUE versionné SHA-256 `3FA0273674A9AF41597C487913C6100B71E16E2B66E9A92EA7B72635372C1C1CDC`. CUE/BIN dans `ps1/build/week2-background-v123-shift-20261031/delivery-v123-rootfix/`. Compilation et contrôles statiques réussis; test DuckStation à faire par l’utilisateur, aucun test console réel. Détails dans [`PS1_WEEK2_V123.md`](PS1_WEEK2_V123.md).

### 2026-10-31 — v124 : profondeur et train Week 3, cycle GF complet

Passage à la Week 3 après la stabilisation du décor Week 2. L’inspection des assets épinglés confirme l’ordre des couches Philly : ville/lumières/derrière-train, train, puis rue/quai. Le convertisseur précédent avait aplati les couches arrière et la rue dans deux tuiles, empêchant d’insérer un train à la bonne profondeur. v124 génère deux tuiles arrière et deux tuiles de premier plan transparentes, puis dessine le train entre elles. Le train officiel 4096×512 est converti à la même échelle 1/6 et divisé en trois morceaux de texture.

Le script original ne fixe pas de timestamps : il tente un départ au beat 4 modulo 8, avec 30 % de chance, après un cooldown supérieur à huit beats. Le son démarre alors; le sprite bouge après 4700 ms, à 24 updates/s, par pas de 400 pixels source, avec une boucle pour huit voitures. Le port emploie une séquence pseudo-aléatoire déterministe par chanson pour que les essais/retries restent reproductibles. Les metadata épinglées donnent 150 BPM (Pico), 175 BPM (Philly Nice) et 165 BPM (Blammed). L’effet audio `train_passes` et les poses `hairBlow`/`hairFall` restent à intégrer; la présente étape livre le placement/animation du train sans ces éléments.

La conversion GF ne prenait que deux poses. v124 en stocke dix (cinq poses sur chaque côté, issues des frames officielles sélectionnées 0,3,…,27) et anime sur la phase de beat. L’alignement caméra Pico/BF est corrigé à partir des centres des cadres : la hauteur extraite de Pico induisait un écart de 10 unités monde; l’offset caméra de Pico est compensé de +10 pour viser la même hauteur que BF.

Audit des semaines futures : les générateurs Weeks 4, 5, 6 et 7 échantillonnent eux aussi seulement deux poses GF. Ils ne sont pas repackés dans v124 car leurs atlases et overlays VRAM sont distincts; une correction sûre nécessite de régénérer leurs packages individuels. Week 1 et Week 2 utilisent déjà dix poses.

Le package Week 3 passe à 4 pages de scène + 4 pages personnages/train, soit 8 pages 8bpp sur les 9 pages disponibles. Payload `W3SCENE.BIN`: 524800 octets. Les packages Week 1 (`C2444F17…A6CD0E8F`) et Week 2 (`BA93EC25…9259137F11D4`) sont réutilisés byte-à-byte. La conversion complète a été lancée dans un dossier temporaire hors dépôt, puis la base préconvertie existante (catalogues/audio et assets W1/W2) a été copiée dans un nouveau dossier externe et seuls l’en-tête et W3SCENE ont été remplacés. Le dry-run de build ne montre que `spu_probe.c`, le lien et l’image ISO (lors du second build, sans recompilation SDK stream.c), aucune conversion d’assets.

Build Debug PSn00bSDK 0.24 / MIPS GCC 12.3 réussi dans `C:/Users/Manau47/Documents/Codex/b124w3`. Le disque raw est conservé séparément; l’image livrée passe par le réordonnanceur ISO : 117 fichiers, `SYSTEM.CNF;1` puis `FUNKIN.EXE;1`, 338506896 octets. BIN SHA-256 `BCDAE9C21D128952F3AF6C2B0861C0625F2FA6548919931A39E064298EC73D55`; CUE SHA-256 `ADBA74115FF0BF2B45509B1F5804E7BCB6CDF5B875D6F0629C87A4931EF570A6`. CUE/BIN : `ps1/build/week3-v124-philly-20261031/delivery-v124-r2-rootfix/`. Compilation et vérifications statiques réalisées; DuckStation en attente de l’essai utilisateur, pas de validation console réelle. Détails et procédure dans [`PS1_WEEK3_V124.md`](PS1_WEEK3_V124.md).

### 2026-10-31 — v125 : intégrer la composition officielle, équilibrer Pico

L’utilisateur approuve la composition fixe de Philly faite avec les assets officiels et demande de l’utiliser dans le vrai niveau; il signale que Pico semble trop grand. v125 conserve les couches officielles de v124 (ville arrière, train, rue/quai, puis GF/Pico/BF), le cadrage, les notes, la musique et le gameplay. Le cadre texture Pico reste 72×84, mais sa primitive est dessinée en 56×60, ratio calculé depuis les limites des rigs officiels Pico et BF. L’ancre au sol reste identique. La cible caméra Pico est recalculée à y=105, égal à celle de BF, compte tenu de la taille affichée réelle 52×52 de BF.

Build séparé `C:/Users/Manau47/Documents/Codex/b125w3a`; branche `ps1-port`, base de source v124 (`f7ef9e2`), assets submodule `724eba9d`. Le dry-run montre compilation de `spu_probe.c` et SDK `stream.c`, lien et ISO seulement; aucune conversion d’assets. Compilation réussie avec les avertissements `volatile` déjà présents dans `stream.c`. Le payload Week 3 de v124 (524800 octets), les ressources des autres semaines, les charts et les sons sont réutilisés byte-à-byte. Le BIN est réordonné après création : 117 fichiers, `SYSTEM.CNF;1` en premier et `FUNKIN.EXE;1` en second; 338506896 octets. BIN SHA-256 `628DA54381F19AD9BF655A3A90B1D00571BFE14E516D60496433627BFC8E00A5`; CUE SHA-256 `4DC26C86D6B5E8C415A01B410FBB44B71C7BF047F876F754FF0283F021A51E4D`. Livraison : `ps1/build/week3-v125-philly-pico-scale-20261031/delivery-v125-rootfix/`. Aucune exécution DuckStation ni validation console réelle n’est revendiquée; essai manuel demandé. Le son officiel `train_passes` et les réactions GF `hairBlow`/`hairFall` restent différés. Détails dans [`PS1_WEEK3_V125.md`](PS1_WEEK3_V125.md).

### 2026-10-31 — v126 : rétablir la taille Pico du jeu

Correction du malentendu sur v125 : la remarque « Pico trop grand » visait la maquette, pas le gameplay. v126 annule uniquement les deux changements d’échelle/caméra Pico et restaure exactement le rendu v124 (cellule 72×84 et calcul de cible caméra d’origine). La composition officielle Philly en couches reste en place. Build dans le dossier déjà configuré `C:/Users/Manau47/Documents/Codex/b125w3a`; dry-run limité au fichier `spu_probe.c`, au lien et à la génération ISO. Pas de reconversion d’assets; la livraison v125 précédente reste intacte. Compilation et vérifications statiques ISO réussies : 117 fichiers, `SYSTEM.CNF;1` puis `FUNKIN.EXE;1`, 338506896 octets. BIN SHA-256 `B78DF300FA9FE78ACAF0898107AC2CA3DAFEC3145F8A5BD98FB02DAD1E9056C0`; CUE SHA-256 `40DB78B42D7F83E07EC6911F992D45F23FD361E1084DE35AE977477131E8E8D9`. Fichiers dans `ps1/build/week3-v126-pico-size-restore-20261031/delivery-v126-rootfix/`. Aucune validation DuckStation ou console revendiquée; le test utilisateur reste attendu. Détails dans [`PS1_WEEK3_V126.md`](PS1_WEEK3_V126.md).

### 2026-10-31 — v127 : recadrer la composition Philly

Retour utilisateur sur v126 : Pico est revenu à sa taille de jeu correcte, mais le reste de la scène reste très éloigné de la maquette approuvée. Comparaison du code avec `outputs/week3-philly-mockup-official/make_mockup.py` : la maquette utilise un zoom Q8 de 384 (1,5×), tandis que le niveau compilé emploie 640 (2,5×). Ce décalage recadrait la ville, poussait BF hors écran pendant le focus Pico et agrandissait le train jusqu’à n’en montrer que des fragments. v127 adopte le transform scène à 1,5× et maintient les transitions horizontales de focus. Pour respecter la précision de l’utilisateur, les rectangles monde des sprites GF/Pico/BF sont compensés par le ratio 640/384 : leur taille en pixels reste celle du gameplay v124. La caméra Y fixe à 75 garde les chanteurs ancrés au sol visibles à cette taille. Les notes et le HUD restent en coordonnées écran. Les assets, profondeurs, charts, audio et règles de gameplay sont réutilisés sans reconversion.

Build recompilé dans le dossier déjà configuré `C:/Users/Manau47/Documents/Codex/b125w3a`; dry-run : `spu_probe.c`, lien, image CD seulement. ISO réordonné et contrôlé : 117 fichiers, `SYSTEM.CNF;1` puis `FUNKIN.EXE;1`, 338506896 octets. BIN SHA-256 `77F6B66A84872BDA34EAD996F9C0B9A09A844B4B7EDC770870DA52226A1A6DA7`; CUE SHA-256 `05E5FEF6470275300BFA5EED92096B4CEACD423AC2983AD3908E823AED94ABB3`. Livraison dans `ps1/build/week3-v127-scene-compose-20261031/delivery-v127-rootfix/`. Compilation et vérifications statiques réussies; test DuckStation utilisateur en attente, aucun test console. Le son du train et les poses GF `hairBlow`/`hairFall` restent différés. Détails dans [`PS1_WEEK3_V127.md`](PS1_WEEK3_V127.md).

### 2026-10-31 — v128 : éviter l’écrasement de l’atlas BF par les pages Week 3

Retour utilisateur sur v127 : décor et train visibles, mais BF est corrompu pendant son idle lorsque le train passe. Le tableau d’assets montre que les poses idle/chant BF utilisent la page 8bpp 7 (`x=768,y=256`), alors que le chargement Week 3 remplace les pages VRAM 0–7 par les huit pages ville/rue/personnages/train. Le rendu BF lisait donc des pixels de la page train/personnage Week 3; ce défaut ne venait pas du rythme idle.

v128 réserve temporairement la page 8bpp 8, qui héberge le logo menu hors gameplay : à l’entrée Week 3, la page BF originale est copiée depuis `W1SCENE.BIN` page 7 vers la VRAM page 8, et les frames BF idle/chant utilisent cette page. À la sortie Week 3, la page 8 du logo est restaurée depuis le disque. Les palettes, l’animation du train, la composition, les caméras, les charts et l’audio ne changent pas. Aucun asset n’a été reconverti; le tampon d’upload existant de 64 Kio sert au transfert de la page.

Build dans `C:/Users/Manau47/Documents/Codex/b125w3a`; dry-run limité à `spu_probe.c`, lien et ISO. Compilation réussie. ISO réordonné/vérifié : 117 fichiers, `SYSTEM.CNF;1` puis `FUNKIN.EXE;1`, 338 506 896 octets. BIN SHA-256 `7C120F8D12728D5415ABCDFBF0C7BCC87C745C4F2DF8DB785F78BE4B50C63A57`; CUE SHA-256 `DC38F0D306754DC50BAC14B9C907AEB4A4E766D7F4B68EA2F485B2D2B874AA55`. Livraison : `ps1/build/week3-v128-bf-atlas-20261031/delivery-v128-rootfix/`. Contrôle statique et compilation réussis; test DuckStation de l’idle BF pendant le train et de la restauration menu à faire par l’utilisateur. Aucun test console. Détails dans [`PS1_WEEK3_V128.md`](PS1_WEEK3_V128.md).

### 2026-11-01 — v129 : parallaxe Philly, lumières et cheveux de GF

À partir de v128, ajout d’un mouvement parallaxe : la ville suit 30 % du déplacement de caméra tandis que le quai suit la caméra à 100 %, avec le train toujours entre les couches. Les fenêtres réutilisent une seule entrée de CLUT, animée au beat selon les cinq couleurs et le cycle du script officiel. La scène ne gagne donc ni page de texture ni ressource CD concurrente. GF utilise quatre poses extraites des séquences officielles `hairBlow` et `hairFall`; l’animation est cadencée à 24 images/s par l’horloge audio, avec retour à la danse après la retombée.

Le paquet Week 3 reste à 8 pages VRAM. Compromis : la couche `behindTrain`, fusionnée avec la ville, défile à 0,3 au lieu de sa vitesse officielle 1,0. Les cheveux de GF sont représentés par quatre poses et non les 60 images du rig. La v128 est préservée bit à bit : BIN SHA-256 `7C120F8D12728D5415ABCDFBF0C7BCC87C745C4F2DF8DB785F78BE4B50C63A57`; CUE SHA-256 `DC38F0D306754DC50BAC14B9C907AEB4A4E766D7F4B68EA2F485B2D2B874AA55`.

Compilation PSn00bSDK 0.24/GCC MIPS 12.3 réussie; W1/W2 préconvertis réutilisés. Image réordonnée et contrôlée : 117 fichiers, `SYSTEM.CNF;1` en premier, `FUNKIN.EXE;1` en deuxième. BIN v129 (338509248 octets) SHA-256 `57DA215840A773748124644E9E1D5AF68E9AEF0E8871184CEC9D14A1AB2E110D`; CUE SHA-256 `D018AB21DBE7EF55F977B66EF039D2E35FC1BC37FF07042766FCC60EF2DA4B6B`. Compilation et contrôles statiques seulement; DuckStation attend le test utilisateur, aucune validation console. Voir [`PS1_WEEK3_V129.md`](PS1_WEEK3_V129.md).


### 2026-11-01 — v130 : remonter le fond ville Week 3

Retour utilisateur sur v129 : seul le fond ville semblait avoir glissé vers le bas. v130 relève les deux tuiles de fond de 8 unités monde (environ 12 pixels à l’écran au zoom 1,5×). Le quai, train, personnages, caméra, facteurs de parallaxe, lumières, animation GF, chart et audio ne changent pas. Les assets W3 sont réutilisés; `week3-scene.bin` demeure identique, SHA-256 `886D0CED3C52B63C2CDEC752D59B78ADCE86894FDA4AFAD17F9F00AFF48B4AED`.

Build séparé PSn00bSDK 0.24 / GCC MIPS 12.3 : compilation réussie; avertissements `volatile` préexistants dans cdstream. Image réordonnée et contrôlée (117 fichiers, `SYSTEM.CNF;1` puis `FUNKIN.EXE;1`), 338509248 octets. BIN SHA-256 `9660E496BDAE906C7A3A41CE1921B2B9B7DA86391059296685CCF0BEB1AA3D99`; CUE SHA-256 `32F6069BC1FB3B5A563126E84749269BFE7818B2CD07DB2DB1799EAF1B87E597`. Livraison dans `ps1/build/week3-v130-city-raise-cmake/delivery-v130-rootfix/`. La v128 reste la référence stable et v129 est conservée pour comparaison. v130 n’a pas encore été exécutée dans DuckStation : la hauteur et les régressions visuelles attendent l’essai utilisateur. Aucun test console. Détails : [`PS1_WEEK3_V130.md`](PS1_WEEK3_V130.md).


### 2026-11-01 — v131 : relever davantage le fond ville Week 3

Retour utilisateur : même après v130, le fond ville doit encore remonter d’environ 30–40 px. v131 ajoute 23 unités monde de décalage vertical au fond ville (environ 34,5 pixels écran au zoom 1,5×); décalage total par rapport à v129 : 31 unités monde, environ 46,5 px. Aucun changement au quai, au train, personnages, caméras, parallaxe, lumières, cheveux GF, chart ou audio.

Ressources converties réutilisées, pas de reconversion; `week3-scene.bin` est inchangé (SHA-256 `886D0CED3C52B63C2CDEC752D59B78ADCE86894FDA4AFAD17F9F00AFF48B4AED`). Build séparé PSn00bSDK 0.24 / GCC MIPS 12.3 compilé. ISO vérifié : 117 fichiers, `SYSTEM.CNF;1` en premier, `FUNKIN.EXE;1` en deuxième, 338509248 octets. BIN SHA-256 `0ABC1392884DA8A352253417A65C6736632340D00A4361201CB3EAC7C75B6A5E`; CUE SHA-256 `21DEA8C78B05242B27F5ACFBB7F2BAB560B08E2C4644AFB246E260E77E9FC35D`. Livraison dans `ps1/build/week3-v131-city-raise-cmake/delivery-v131-rootfix/`. v131 n’a pas encore été observée dans DuckStation; essai utilisateur requis. Aucun test console. Détails : [`PS1_WEEK3_V131.md`](PS1_WEEK3_V131.md).

### 2026-11-01 — v132 : remonter le fond ville de 40 px supplémentaires

L’utilisateur demande encore environ 40 px de remontée après v131. v132 ajoute 27 unités monde de décalage (environ 40,5 pixels écran) au seul fond ville; le décalage total par rapport à v129 est de 58 unités monde (~87 pixels). Quai, train, personnages, caméra, parallaxe, lumières, cheveux GF, gameplay et audio inchangés.

Ressources préconverties réutilisées sans reconversion; `week3-scene.bin` inchangé, SHA-256 `886D0CED3C52B63C2CDEC752D59B78ADCE86894FDA4AFAD17F9F00AFF48B4AED`. Build PSn00bSDK 0.24/GCC MIPS 12.3 compilé; ISO contrôlé avec 117 fichiers, `SYSTEM.CNF;1` puis `FUNKIN.EXE;1`, 338509248 octets. BIN SHA-256 `24B1ACA08C70A85C21C1C18C6455F7AB0D7C81DCB58A9EC2EF4E2AB2D429DFED`; CUE SHA-256 `D71C375EF3A03FCFF7DFF0D47540C5B5047ACBEB472E70D8FAAE29CBF052D868`. Livraison dans `ps1/build/week3-v132-city-raise-cmake/delivery-v132-rootfix/`. v132 n’a pas été observée dans DuckStation ni sur console; la composition et les bords restent à vérifier par l’utilisateur. Détails : [`PS1_WEEK3_V132.md`](PS1_WEEK3_V132.md).

### 2026-11-01 — v133 : décaler le fond ville de 40 px vers la gauche

Après validation de la hauteur v132, l’utilisateur demande de déplacer le fond ville de 40 px vers la gauche. v133 décale les deux tuiles arrière de 27 unités monde (~40,5 px écran au zoom 1,5×), sans modifier leur hauteur, leur parallaxe, le quai, le train, les personnages, les caméras ou le gameplay.

Ressources préconverties réutilisées sans reconversion; `week3-scene.bin` inchangé (SHA-256 `886D0CED3C52B63C2CDEC752D59B78ADCE86894FDA4AFAD17F9F00AFF48B4AED`). Compilation PSn00bSDK 0.24/GCC MIPS 12.3 réussie. ISO vérifié : 117 fichiers, `SYSTEM.CNF;1` puis `FUNKIN.EXE;1`, 338509248 octets. BIN SHA-256 `BE624E13B1BB7D6B92A584AC84E83CB59F8B191260EF85D2D052186DA33EEABF`; CUE SHA-256 `4E0907DC9772E6E465DF7B1B23BD62C7FADF0EFEFD57262145EBB070163C11FC`. Livraison dans `ps1/build/week3-v133-city-shift-cmake/delivery-v133-rootfix/`. v133 n’a pas été exécutée dans DuckStation; le décalage et le raccord attendent l’essai utilisateur. Aucun test console. Détails : [`PS1_WEEK3_V133.md`](PS1_WEEK3_V133.md).

### 2026-11-01 — v134 : encore 40 px vers la gauche

v133 ne décalait pas encore assez le fond ville. v134 ajoute 27 unités monde vers la gauche (~40,5 px écran au zoom 1,5×), pour un total d’environ 81 pixels depuis v129. Hauteur, quai, train, personnages et parallaxe inchangés.

Ressources préconverties réutilisées; `week3-scene.bin` inchangé (SHA-256 `886D0CED3C52B63C2CDEC752D59B78ADCE86894FDA4AFAD17F9F00AFF48B4AED`). Compilation PSn00bSDK 0.24/GCC 12.3 réussie. Disque vérifié : 117 fichiers, `SYSTEM.CNF;1` puis `FUNKIN.EXE;1`, 338509248 octets. BIN SHA-256 `838AF71BEFB4543F427715F4C2015934D855D9000BA94BCFDFE8D7C6AF96BEDA`; CUE SHA-256 `FF78750116A72600F7435E17EF6DDCC1A9E722DADC3768B37BAC8C9DAD817445`. Livraison dans `ps1/build/week3-v134-city-shift-cmake/delivery-v134-rootfix/`. DuckStation/console non testés; attendre l’essai utilisateur pour confirmer composition, raccords et marges. Voir [`PS1_WEEK3_V134.md`](PS1_WEEK3_V134.md).

### 2026-11-01 — v135 : décaler le fond ville de 30 px vers la gauche

Après v134, l’utilisateur demande encore 30 px à gauche. v135 ajoute 20 unités monde de décalage horizontal (~30 px écran au zoom 1,5×), pour un total d’environ 111 px depuis v129. Hauteur approuvée, quai, train, personnages et caméra inchangés.

Aucune reconversion; `week3-scene.bin` inchangé (SHA-256 `886D0CED3C52B63C2CDEC752D59B78ADCE86894FDA4AFAD17F9F00AFF48B4AED`). Build PSn00bSDK 0.24/GCC 12.3 compilé. ISO contrôlé : 117 fichiers, `SYSTEM.CNF;1` puis `FUNKIN.EXE;1`, 338509248 octets. BIN SHA-256 `AD0E8A58C54B59717AB90A2B72090BF2FFF78AF3AF4F238FB182FB6BADF82E23`; CUE SHA-256 `89B42CA537E16FB2ACFF8365215311C36B29CFAE55C60291A10D06068683374E`. Livraison dans `ps1/build/week3-v135-city-shift-cmake/delivery-v135-rootfix/`. Pas d’exécution DuckStation/console; vérifier rognage et raccords à l’essai utilisateur. Voir [`PS1_WEEK3_V135.md`](PS1_WEEK3_V135.md).

### 2026-11-01 — v136 : remettre l’atlas VRAM à l’état de base au retour Freeplay

Retour utilisateur sur v135 : après revenir au Freeplay puis relancer un morceau, les visuels de scène sont fortement corrompus. Le code montre que pages/palettes partagées sont louées entre packages semaine et le DJ Freeplay; la restauration reposait sur des indicateurs de chargement partiel. v136 recharge donc l’atlas et les palettes Bopeebo complets depuis `W1SCENE.BIN` au retour Freeplay, remet les indicateurs de package à faux, puis permet au prochain lancement de recharger ses pages de scène. Le défaut est attribué au risque de restauration incomplète du VRAM partagé; la confirmation par cycle réel Freeplay → morceau → Freeplay → morceau reste attendue. Aucun asset converti ni gameplay n’est modifié.

Le build utilise les ressources préconverties, sans reconversion. `W3SCENE.BIN` reste identique à v135 (524800 octets, SHA-256 `886D0CED3C52B63C2CDEC752D59B78ADCE86894FDA4AFAD17F9F00AFF48B4AED`). PSn00bSDK 0.24 / GCC 12.3 compile; ISO contrôlé : 117 fichiers, `SYSTEM.CNF;1` puis `FUNKIN.EXE;1`, 338509248 octets. BIN SHA-256 `15A53475CC050D60B884D5A5B8572AD41F3788A185BF38406C51C859E61BCE1B`; CUE SHA-256 `054E3A25865253AB5009649E5F3607BA382DFF8811DB8B4882B2A3828F7B22A4`. Livraison `ps1/build/week3-v136-vram-reset-cmake/delivery-v136-rootfix/`. Compilation/statiques seulement, DuckStation en attente de l’essai utilisateur; aucune validation console. Voir [`PS1_WEEK3_V136.md`](PS1_WEEK3_V136.md).

### 2026-11-01 — décision de gestion VRAM après échange utilisateur

L’utilisateur précise que la VRAM doit être un espace de travail pour l’écran et le morceau actifs, et qu’il n’est pas nécessaire d’y garder les ressources des prochaines pistes puisque les données sont relues depuis le CD à chaque chargement. Cette approche est faisable et devient le principe d’architecture : charger les textures de la semaine sélectionnée et les éléments communs réellement requis, puis remplacer/libérer les ressources qui ne servent plus. Les ressources communes peuvent rester résidentes si elles doivent coexister et si le budget VRAM le permet; sinon, elles sont rechargées à la transition.

Le partage d’un emplacement de CLUT n’est pas imposé par la PS1. Les palettes peuvent accompagner le paquet de scène (ou disposer d’emplacements dédiés); leur volume est faible par rapport aux pages de texture. Il faut maintenir ensemble la correspondance texture/CLUT et remettre à jour les primitives qui les référencent. Le budget prioritaire porte sur les pages de textures, les framebuffers et les éléments nécessaires simultanément, pas sur toutes les semaines embarquées sur le disque.

La v136 recharge volontairement l’atlas/palette de base au retour Freeplay pour tester un état VRAM déterministe. C’est un rechargement conservateur, pas l’architecture mémoire finale : il relit des ressources qui pourraient être limitées au menu et au paquet de morceau suivant. Le cycle de retour puis relance v136 doit encore être observé dans DuckStation avant d’attribuer définitivement la corruption à cette cause. À terme, cartographier les zones VRAM et gérer explicitement les paquets Menu/Commun/Semaine active, avec chargement CD à la transition et sans garder les autres semaines en VRAM.

### 2026-11-01 — v137 : retirer les chargements remplacés à la transition

Audit du code v136 avant modification : `main()` charge l’atlas W1 complet, puis la page logo et sa palette sont relues depuis `W1SCENE.BIN` alors que le premier `load_menu_screen_art()` écrase immédiatement cette page avec l’art empaqueté. Au lancement d’un morceau, `load_song_stage_visuals()` appelait aussi plusieurs chargeurs inactifs qui réécrivaient la CLUT de base avant que le paquet actif ne la remplace. Au retour Freeplay, les pages de la semaine étaient restaurées, puis immédiatement écrasées par le rechargement complet W1. Au Retry, toutes les pages du paquet actif étaient relues alors que l’écran Game Over n’altère que la CLUT et la région de mort sur la page 8 (W3 y conserve aussi la page BF de secours).

v137 garde la remise à zéro W1 complète au retour Freeplay, mais retire la restauration de semaine qui la précédait. Le chargement du logo W1 intermédiaire est supprimé; la palette de base reste fournie par l’atlas W1 et l’art de menu est écrit dans cette page avant dessin. L’entrée chanson charge seulement le paquet de sa scène. Le retry restaure la CLUT active, et pour W3 uniquement la page BF de secours depuis W1. La région partagée dispose d’un propriétaire de scène explicite (base, semaine ou transition invalide); le chargeur base invalide les anciens drapeaux de semaine après remplacement.

Gains calculés statiquement : −65 536 octets CD et VRAM sur chaque chargement de page logo intermédiaire au démarrage/retour; au retour, retrait des pages restaurées avant d’être remplacées (W2 458 752, W3 589 824, W4/W5/W7 196 608, W6 327 680, Weekend 1 524 288 octets) et −4 096 octets d’écritures CLUT redondantes. Le Retry évite W2 458 752, W3 524 288, W4/W5/W7 196 608, W6 327 680 ou Weekend 1 524 288 octets de pages CD/VRAM; W3 relit toujours sa page BF de secours de 65 536 octets. Les charts, le FIFO 96 Kio et les formats audio ne changent pas. Aucun compteur de volume runtime ni pic heap n’est disponible; les transitions doivent être testées dans DuckStation.

Carte calculée sur v136 : ELF résident 1 058 502 octets; 64 Kio de staging temporaire; chart alloué au lancement et conservé jusqu’au retour; FIFO SDK de 96 Kio seulement après libération du staging. VRAM réservée : framebuffers 307 200 o, neuf pages 8bpp 589 824 o, deux pages 4bpp 65 536 o, espace CLUT 20 480 o, total 983 040 o sur 1 Mio, laissant 65 536 o. SPU : flux musical quatre voix et double buffer 32 768 o, banque SFX menu 269 056 o à 0x22000, voix musicales 0–3, SFX 4–7, menu 8–10, Game Over 11; 12–23 libres. Détails et tables avant/après : [`PS1_VRAM_LOADING_AUDIT_V136.md`](PS1_VRAM_LOADING_AUDIT_V136.md).

Build v137b configuré dans un dossier distinct avec les options v136. Le dry-run final n’annonce que `spu_probe.c`, le lien et la création ISO; aucune conversion de ressource. Le build final a compilé uniquement `spu_probe.c`, lié et produit l’image. 116 fichiers ressource `.bin/.vag` comparés au build v136 sont byte-identiques. L’ISO contient 117 fichiers; le réordonnanceur place `SYSTEM.CNF` en entrée racine 1 et `FUNKIN.EXE` en entrée 2. ELF résident calculé : 1 058 330 octets (v136 : 1 058 502, −172). Les avertissements vus lors du premier build concernent les conversions `volatile` déjà présentes dans `stream.c` du SDK; la passe finale incrémentale ne l’a pas recompilé.

BIN `338 509 248` octets, SHA-256 `9CD4415B05D2B21D2DFA22AC6FB47057A440B447448453ABB36CE00E56EA6444`; CUE SHA-256 `665C9369D112A9C57A9FDFCDA497170958F8464031FFCD941DBD943E510A3751`. Livraison dans `ps1/build/vram-loading-v137-cmake/delivery-v137b-memory-loading-rootfix/`; configuration, hashes et plan de validation : [`PS1_VRAM_LOADING_V137.md`](PS1_VRAM_LOADING_V137.md). La compilation et les vérifications statiques ISO sont réussies. Aucun essai DuckStation ni validation utilisateur à ce stade; l’utilisateur chargera le CUE et vérifiera les cycles entre semaines, retour Freeplay et retry. Aucune validation console réelle.

### 2026-11-01 — v138 : compromis d’animation Pico et GF Week 3

Après la première passe mémoire, l’utilisateur remarque des poses manquantes à Pico et dans la réaction des cheveux de GF au passage du train. v138 échantillonne quatre images officielles de l’idle Pico (source `0,4,8,12`), conserve deux poses par chant directionnel comme pour BF mais les espace davantage dans l’animation source, puis prend quatre images de souffle de cheveux et six images de retombée de leurs timelines officielles de 30 images. La sélection GF reste synchronisée sur l’horloge audio. Les cels à marges transparentes sont rognées en stockage, avec offsets d’ancrage pour conserver leur taille et leur composition à l’écran. Aucun trigger de train ni timing de gameplay n’est changé.

L’atlas personnage W3 reste à quatre pages 8bpp et le paquet W3 reste à 524 800 octets; le secours BF, les quatre pages de décor et la CLUT sont conservés. Les quatre pages de décor et la CLUT ont été vérifiées identiques à la base. W1, W2, musique quatre canaux et chart Bopeebo Normal sont byte-identiques à v137b. L’ELF augmente de 836 octets au total; le BSS reste à 40 184 octets.

Le dry-run prévoit uniquement compilation `spu_probe.c`, lien et image disque; aucune reconversion n’est déclenchée par CMake. Compilation PSn00bSDK 0.24/GCC 12.3 réussie. ISO contrôlé (117 fichiers, `SYSTEM.CNF;1` premier, `FUNKIN.EXE;1` deuxième), BIN 338 509 248 octets. BIN SHA-256 `09CABCD4A323A7C662C5436E74994CD4C4669E5DE65E3AFC471A9F6C9CF3E375`; CUE SHA-256 `29227A2C07AAE64828498B64FC24DBD85699561BD1E25AC1D1794A2C32F7ACB2`. Livraison `ps1/build/week3-animation-compromise-v138/delivery-v138-pico-gf-compromise-final/`. Pas d’essai DuckStation : l’utilisateur chargera le CUE; animations, composition, audio et cycles restent à confirmer. Aucun essai console. Détails : [`PS1_WEEK3_ANIMATION_COMPROMISE_V138.md`](PS1_WEEK3_ANIMATION_COMPROMISE_V138.md).

### 2026-11-01 — v139 : restaurer la palette de base et corriger les ancrages Pico/GF

L’utilisateur signale des couleurs incorrectes sur GF à l’écran titre, l’option Options, Tutorial/Bopeebo, ainsi qu’un placement Pico incohérent en Week 3. Analyse de l’en-tête généré v138 : 240 entrées sur 256 de `bopeebo_visual_palette8` divergeaient du paquet de base v129b alors que les pages W1 déjà empaquetées étaient réutilisées. Le build mélangeait donc des pixels indexés issus de l’ancienne conversion et une CLUT recalculée. La génération a aussi pris l’image Options officielle comme solution de repli, car la source locale approuvée n’était pas présente dans cet environnement. Ce n’était pas un défaut GPU en exécution.

La correction conserve les ressources globales/menu, la CLUT, les pages et les descripteurs non-W3 de la base v129b, puis fusionne uniquement les nouveaux descripteurs et poses W3 issus de v138. Le script reproductible `ps1/merge_week3_animation_header.py` valide les tables de pages, palettes et noms de frames avant d’écrire l’en-tête fusionné. Le fichier v138 remplacé a été conservé sous `ps1/build/week3-animation-compromise-v138/preconverted-base/bopeebo_visual_data.h.v138-palette-mismatch`; aucune ressource officielle ni SDK n’est ajouté au dépôt.

Le placement des cels W3 recadrés utilisait des plages numériques de numéros de frame. L’ordre d’empaquetage ne rend pas ces plages monotones (les frames Pico/GF pertinentes sont numérotées dans l’ordre inverse), donc des poses recevaient parfois le mauvais ancrage. `BopeeboVisualFrame` porte maintenant une classe d’ancrage explicite; les frames Pico et GF utilisent chacune leur point d’ancrage adapté. Aucune animation, taille d’affichage, caméra ou règle de gameplay n’est modifiée.

Compilation incrémentale PSn00bSDK 0.24/GCC MIPS 12.3 réussie; le dry-run de `ps1-bopeebo-playable-disc` ne comportait que compilation de `spu_probe.c`, édition de liens et création du disque. Aucun convertisseur ni générateur audio/chart ne s’est exécuté. L’ISO est de 338 509 248 octets. BIN SHA-256 `AF7390FD068FAA46D5DA0E18D390A8B2ED294E6E6965F9BFC91182F77112A40F`; CUE SHA-256 `BF60EF5FC7517B3DF32AC5BC0C7DB3BC4DC619AC983160B4D559624F1BC068A6`. Livraison `ps1/build/week3-animation-compromise-v138/delivery-v139-palette-anchor-correction/`; manifeste : [`PS1_V139_PALETTE_ANCHOR_FIX.md`](PS1_V139_PALETTE_ANCHOR_FIX.md).

**État :** différences de palette et d’ancrage établies statiquement; compilation réussie. Le nouveau disque n’a pas encore été exécuté dans DuckStation et n’est pas validé par l’utilisateur. À vérifier : couleurs du titre/options et de Tutorial/Bopeebo, poses Pico et GF pendant le train, puis parcours Freeplay → jeu → retour. Aucun essai console réelle.

### 2026-11-01 — v139b : correction de l’ordre du répertoire ISO

Retour utilisateur : le premier CUE v139 reste au logo Sony. Comparaison avec v138 : l’exécutable et `SYSTEM.CNF` v139 sont valides, mais l’entrée racine ISO `SYSTEM.CNF;1` était en position 93 au lieu de la première position attendue par la chaîne BIOS validée; `FUNKIN.EXE;1` suivait en deuxième position dans v138. Le fichier CUE initial ciblait correctement son BIN, le défaut était l’ordre racine du disque.

Sans recompiler ni reconvertir, v139b repart du BIN brut du même build et applique uniquement `ps1/diagnostics/reorder_iso_system_cnf.py --exe-after-system-cnf` dans un nouveau dossier de livraison. L’image v139 initiale est préservée. Vérification statique v139b : 117 entrées, `SYSTEM.CNF;1` puis `FUNKIN.EXE;1`; directive `BOOT=cdrom:\\FUNKIN.EXE;1`; PS-X EXE 1 021 952 octets byte-identique au v139 initial, SHA-256 `54131AB733936A82676EFE91CE7D9B3D0771EEA32C883B68CDA8788AC70D727D`. BIN v139b SHA-256 `0E9F1852D97F89F2771AA6AC9196214EE55C3374D2F81B2FEFF4320EE3410B5F`; CUE SHA-256 `AAE35D9F4730932B0D2EE363D4B99761C71422846A8ED1FB0CDE4004D90BD3E6`. Livré sous `ps1/build/week3-animation-compromise-v138/delivery-v139b-iso-boot-order/`.

**État :** ordre et contenu ISO contrôlés statiquement; DuckStation n’a pas encore confirmé le démarrage de v139b. L’essai utilisateur est requis avant de poursuivre l’inspection visuelle. Aucun test console réelle.

### 2026-11-01 — v140 : espacer Pico et BF en Week 3

À la demande de l’utilisateur, les chanteurs Week 3 sont éloignés chacun de 10 unités de monde : Pico vers la gauche, BF vers la droite. À la composition 1,5× cela ajoute environ 30 pixels entre leurs centres. Les offsets caméra sont compensés de +10 pour Pico et −10 pour BF : leurs cibles caméra restent strictement identiques (Pico 111, BF 137), de sorte que la caméra, le fond/parallaxe, les proportions, animations, charts et gameplay ne changent pas. Le convertisseur encode ces offsets pour que la disposition reste reproductible.

Les ressources préconverties de v139b ont été copiées dans une nouvelle zone de staging; seules quatre macros de position dans leur en-tête ont été ajustées. Dry-run : compilation de `spu_probe.c` et `stream.c`, édition de liens et image disque; aucun asset, chart ou audio reconverti. L’image ISO v140 a été comparée fichier par fichier à v139b : seul `FUNKIN.EXE;1` change. Les 116 autres ressources sont byte-identiques. Le réordonnanceur BIOS place `SYSTEM.CNF;1` puis `FUNKIN.EXE;1` en tête du répertoire racine.

PSn00bSDK 0.24 / GCC MIPS 12.3 : compilation réussie. BIN 338 509 248 octets, SHA-256 `C691A74571FEFE2587C5DEA56C284C868DC9EB535143FDCD961528404B470E6A`; CUE SHA-256 `B9CC1B288089DF4CD0C0BFA5053A2AC6589F85F1BE839C4A255E2D0AE66A32E7`. Livraison : `ps1/build/week3-pico-bf-spacing-v140/delivery-v140-pico-bf-spacing/`; manifeste [`PS1_WEEK3_V140_SPACING.md`](PS1_WEEK3_V140_SPACING.md).

**État :** build et comparaison statique réussis; le CUE n’a pas encore été lancé dans DuckStation. L’utilisateur doit confirmer l’espacement en jeu et la lisibilité pendant les focus Pico/BF. Aucun test console réelle.

### 2026-11-01 — BF : poses de chant plus variées (build d’essai après v140)

L’inspection du code explique l’impression de raideur : le convertisseur ne gardait que les deux premières images de chaque animation `BF NOTE LEFT/DOWN/UP/RIGHT`, alors que les atlas officiels en contiennent respectivement 15, 30, 15 et 62. Le rendu alternait ces deux images par demi-beat. La correction échantillonne trois poses représentatives par direction (début, milieu, fin) et les joue à 15 images/s depuis la position d’échantillon audio du hit; une tenue conserve cette animation jusqu’à son échéance. L’idle à 14 étapes, les animations de faute et les règles de hit/hold ne changent pas.

Le script ciblé `ps1/augment_bf_sing_poses.py` réutilise la palette BF existante : il remplace le deuxième cel proche du premier par la pose médiane et ajoute une pose tardive dans la rangée libre au bas de la page 8bpp 7. Quatre cels supplémentaires représentent 10 816 octets de pixels indexés. La page garde la même taille; aucune palette, page VRAM, lecture CD, audio, caméra, placement ou animation Pico n’est ajoutée ou modifiée. La sauvegarde de page Week 1 déjà utilisée par Week 3 transporte aussi les nouvelles poses.

Le CMake ne relance pas le convertisseur général : il génère uniquement ces huit cels BF (quatre images médianes et quatre finales), leur petit tableau de descripteurs et une copie de `W1SCENE.BIN` de même taille avec la page 7 patchée. Le build PSn00bSDK 0.24 / GCC MIPS 12.3 a réussi. La livraison v141 et ses hashes sont consignés dans [`PS1_BF_SING_V141.md`](PS1_BF_SING_V141.md). Le CUE attend maintenant l’essai DuckStation de l’utilisateur. À vérifier en particulier : fluidité des quatre chants, orientation des poses, tenue longue, Week 3 après copie de la page BF, faute/récupération, relance et retour Freeplay. Aucun essai console réelle ni validation utilisateur pour cette passe.

## v142 — poses de chant pour Week 6, Week 7 et Weekend 1 (2 novembre 2026)

La remarque utilisateur est que Pico est convaincant mais BF semble moins fluide et manque de poses. L'atlas partagé qui couvre Week 1–5 avait déjà reçu les poses échantillonnées v141. Cette passe étend ce principe à BF pixel Week 6 et au rig BF de Week 7; Weekend 1 utilise Pico comme joueur sur Darnell/Lit Up/2Hot. Blazin et ses poses de combat ne sont pas modifiés.

Le nouvel outil `ps1/augment_week_sing_poses.py` complète les paquets déjà convertis avec leurs CLUT existantes, sans relancer les conversions générales. Week 6 gagne deux poses par direction (trois visibles au total) dans de l'espace de texture libre et conserve les 328 192 octets de scène. Week 7 n'a que deux rendus distincts parmi les instants init/milieu/fin examinés dans le rig officiel : elle alterne ces deux poses à 15 images/s et gagne une page 8bpp (+65 536 octets VRAM/CD pour la scène active). Weekend 1 ajoute une pose alternative par direction de Pico dans l'espace libre de sa page 7, sans grossir le paquet. Les sélections suivent l'horloge d'échantillons audio, à partir de l'événement chant; cadrage, gameplay, charts, sons, audio et compositions restent inchangés.

PSn00bSDK 0.24 / GCC MIPS 12.3 / CMake-Ninja : compilation et image BIN/CUE produites. Les ressources Week 4/5 et le son/chart préconvertis ont été réutilisés; aucune reconversion audio, générale, chart ou décor. L'ELF compte 1 061 858 octets texte+données+BSS; staging de scène 64 Kio et ring audio 96 Kio inchangés. La seule hausse de paquet est la page Week 7. Les détails, hashes, configuration et commande de reproduction sont dans [`PS1_SINGING_POSES_V142.md`](PS1_SINGING_POSES_V142.md).

Le CUE n'a pas été lancé dans DuckStation pendant cette passe. Merci de l'essayer; je ne revendique ni fluidité observée dans l'émulateur, ni validation utilisateur, ni test console réelle.

## v143 — cycles d’animation étendus, Weeks 4–7 et Weekend 1 (2 novembre 2026)

En réponse au retour sur les GF tardives limitées à deux poses et les adversaires rigides, ajout de cels officiels de danse GF, d’idles et de poses de chant dans Week 4, Week 5, Week 6, Week 7 et Weekend 1. Weeks 1–3 conservent les cycles déjà présents; Blazin et Spirit (dont le rig ne fournit pas de poses distinctes supplémentaires exploitables) restent limités aux cels disponibles. Pico/Darnell classiques reçoivent plus d’états dans Weekend 1. Les sélections sont synchronisées sur l’horloge audio. Aucun gameplay, timing, chart, caméra, composition, qualité audio ou son n’est modifié.

Le script `ps1/augment_week_animations_v143.py` reprend les paquets préconvertis et leurs CLUT, ajoute sept pages 8bpp réparties par scène (+1 W4, +2 W5, +2 W6, +1 W7, +1 WEnd1). Chaque niveau reste chargé indépendamment. Pas de conversion générale. Le détail des poses, budgets et limites est dans [`PS1_ANIMATIONS_V143.md`](PS1_ANIMATIONS_V143.md).

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 à jour; dry-run final sans tâche. Le BIN brut est préservé. La copie de livraison change uniquement l’ordre racine de l’ISO : `SYSTEM.CNF` était en entrée 93; le CUE fourni a `SYSTEM.CNF` en entrée 1 et `FUNKIN.EXE` en entrée 2. BIN 339 116 064 octets, SHA-256 `0D48786850065B0018E9AAAC3BBEEC51651262F94E270E7EAE9F245CB25DC8AD`; CUE SHA-256 `6CDFC57781348025AD36D8A2F86732D762E04114F94CF8B1C5E12B1D8294FE7A`. Livraison hors Git `ps1/build/v143-animation-pass/delivery-v143-week-animations-rootfix/`.

**État :** build et contrôles statiques réussis. DuckStation n’a pas été lancé; les animations ne sont pas observées sur ce build. Essai manuel requis sur W4–W7 et Weekend 1, avec les retours idle et contrôle stabilité audio. Pas de test console réelle.

## Retry W4 après Game Over — v144 (2 novembre 2026)

Le signalement utilisateur concerne un retry après game over sur MILF : la piste avait joué avant la défaite, puis DuckStation a affiché « SPU STREAM ERROR / CODE » sans valeur lisible. La capture confirme le titre, mais ne permet pas de relever le numéro ni les compteurs.

**Cause identifiée par inspection du code :** `begin_retry_countdown()` restaure la palette de la scène active et conserve `vram_scene_owner_stage` à l’identifiant de sa semaine. À la fin du décompte, `enter_bopeebo()` appelle `load_song_stage_visuals()`, qui n’acceptait que le propriétaire 1 (base Freeplay/W1). Pour MILF, le propriétaire légitime est 4 : le chargeur déclenchait `FAIL_ASSET_LOAD` (code 10) avant de démarrer le nouveau flux. La capture ne montre pas le code numérique, donc ce code attendu par le chemin n’est pas revendiqué comme observation utilisateur.

**Correction :** si la VRAM appartient déjà à la semaine de la chanson active, le chargement de scène est sauté. Au retry, la palette est restaurée et les pages sont conservées ; depuis Freeplay, l’acquisition habituelle du paquet de semaine reste inchangée. Aucun changement au gameplay, aux animations, aux scènes, aux charts ou à l’audio.

**Diagnostics :** `show_error()` utilisait `FntPrint(-1)`, dont la zone par défaut ne rendait pas les lignes de détails dans le cadre visible. Une région 304×224 est maintenant ouverte après `FntLoad`; les erreurs et données CD/SPU s’affichent dans cette zone. Le titre est devenu générique car toutes les erreurs ne viennent pas du flux SPU.

**Build v144 :** compilation incrémentale PSn00bSDK 0.24/GCC 12.3. Le dry-run prévoyait seulement trois tâches : compilation de `spu_probe.c`, lien ELF et fabrication de l’image disque ; aucune conversion d’assets. Les anciens artefacts v143 et le cache/configuration ont été copiés avant build dans `ps1/build/v144-milf-retry-fix/archive-v143-before-fix/`. Contrôle statique ISO : `SYSTEM.CNF` puis `FUNKIN.EXE` dans les deux premières entrées racine, en-tête PS-X EXE reconnu, et EXE extrait identique à l’EXE lié.

**Résultats :** compilation et contrôles ISO réussis. Le CUE v144 n’a pas encore été exécuté dans DuckStation ; le retry MILF reste à confirmer par l’utilisateur. Pas de validation console réelle.

### v144b — portée de la police d’erreur et image finale

Avant la livraison, la déclaration de la police dédiée a été déplacée hors du bloc réservé au gameplay, car `show_error()` est aussi présent dans les probes. La cible secondaire `funkin-ps1-bopeebo-4ch-audio` n’a pas été compilée : son dry-run prévoyait la régénération de `bopeebo_sfx_data.h`/`.vag`, inutile à ce correctif. Pour le build jouable, le dry-run final reste limité à la compilation de `spu_probe.c`, au lien et à l’image CD. Le disque final est la variante séparée `delivery-v144b-milf-retry-fix/`; BIN SHA-256 `E8EDE48C7E08A7ED00328B2F267DEA6F1508E7F0C2A95B84BDC62B523EAD1A3C`, CUE SHA-256 `0619CAD3085313DB3DF21998B644ACF012AD0A7155AB72EB6870F5BB4459251F`. Exécution DuckStation toujours en attente.

## Week 4 — décor visible et poses Mom cohérentes (v145, essai)

La scène Week 4 avait un défaut de découpe du bitmap 512×256 en deux pages : les moitiés étaient prises dans le tableau d’octets, ce qui séparait les données par rangées au lieu de couper l’image par colonnes. La conversion copie maintenant chaque demi-rangée vers sa page. Au rendu, les quads de fond agrandis sont découpés au viewport avec UV ajustées sur CPU.

Les poses Mom ajoutées gardent le canevas officiel uniforme 72×84. Les cycles idle et chant prélèvent trois cels du rig officiel et tournent à 24 images/s depuis l’horloge audio, avec les durées officielles des séquences. Cela vise à stabiliser ses proportions et son animation; ce n’est pas encore une validation en jeu.

Le paquet Week 4 passe de 262 656 à 393 728 octets (+131 072, deux pages 8bpp). Build jouable PSn00bSDK 0.24/GCC 12.3 compilé et livré. Contrôle statique : exécutable de 1 028 096 octets; W4SCENE extrait du disque identique au paquet préconverti (SHA-256 `1f178ae8fad8ec86d4914569050e8eac070702d6a1b336c56b734cf3679b5360`). BIN SHA-256 `7ea06c970517e1ac92f7f90905dd21973be27ebc99bdf34733f1ce18da59c08d`; CUE SHA-256 `d8ed08eac76f9ab390c1271aa21c61dcf7cfb3d5c71b67e1f843e389a2c43869`.

**État :** compilé et vérifié statiquement; DuckStation attend le chargement manuel et le retour utilisateur. La prévisualisation convertie n’est pas une observation d’exécution. Les couches mobiles `bgLimo`/`limo` restent statiques dans cette étape; audio, charts, caméra et gameplay ne changent pas. Aucun test console réelle. Détails : [`PS1_WEEK4_V145_SCENE.md`](PS1_WEEK4_V145_SCENE.md).


## Audit global des atlas et compactage sans perte (v146, 4 novembre 2026)

L’outil d’audit couvre les pages base/W1, Weeks 2–7, Weekend 1, ainsi que les pages statiques titre/menu, Freeplay/DJ, icônes, capsules et game over. Les planches et mesures détaillées sont conservées dans `ps1/build/atlas-audit-v146/` (ignoré par Git); les scripts reproductibles et le rapport sont [`PS1_ATLAS_AUDIT_V146.md`](PS1_ATLAS_AUDIT_V146.md). Les gains viennent du réempaquetage indexé sans changement de texels : −1 page 8bpp pour W4 et −1 pour W7, CLUT et décors byte-identiques. Aucun autre atlas n’est réduit dans cette passe.

Le build PSn00bSDK/GCC est compilé et contrôlé statiquement. W4/W7 représentent ensemble −131 072 octets utiles sur disque et dans les transferts page GPU calculés; image BIN raw −150 528 octets. Le retry précédemment confirmé par l’utilisateur est préservé. Le CUE v146 est en attente de l’essai DuckStation utilisateur; aucune validation d’image runtime ou console réelle n’est revendiquée.

## Week 4 — intégration de la composition Mother v7 (v147, essai)

Intègre dans les deux pages de décor le ciel officiel, la limousine lointaine agrandie et les quatre danseurs henchmen aux positions de la maquette v7. La pose officielle de danse utilisée pour les quatre instances est fixe dans cette passe. L’ordre dans les pages est limousine lointaine → danseurs → limousine principale. Mom, GF et BF gardent leur placement et leurs tailles du moteur, ainsi que les caméras, animations, chart, gameplay et audio.

Le script [`../ps1/compose_week4_background.py`](../ps1/compose_week4_background.py) repart du paquet v146 sans le modifier. Il remplace uniquement les texels des deux pages de décor, garde les trois pages d’acteurs et la CLUT identiques, et projette les coordonnées v7 vers le monde Week 4 au zoom existant. Les couleurs ajoutées sont rapprochées de la CLUT existante; leur correspondance est approximative.

Le paquet reste à 328 192 octets / cinq pages 8bpp; VRAM et volume de transfert CD ne changent pas. Le BIN/CUE v147 a été compilé et le système de fichiers vérifié statiquement. **DuckStation n’a pas encore été testé**; l’utilisateur chargera le CUE. Aucun test sur console réelle. Détails, hashes et limites : [`PS1_WEEK4_V147_COMPOSITION.md`](PS1_WEEK4_V147_COMPOSITION.md).

## Week 4 — correction de composition et d’échelle GF (v148, essai)

Retour utilisateur sur v147 : composition non conforme et GF changeant visiblement de taille au fil de la mesure. Causes statiques relevées : le décor lointain était extrait en 222×39 au lieu d’environ 455×79; les danseurs henchmen de 517×410 étaient réduits à 29×22; les poses GF de 64×64 étaient dessinées à cette taille tandis que les poses originales font 87×79. v148 corrige les tailles d’extraction du décor et impose une enveloppe d’affichage GF fixe de 87×79, sans changer les timings ni ajouter de pages. Le placement du premier plan reste inchangé.

Build séparé et ISO racine vérifié; paquet W4 toujours cinq pages / 328 192 octets. BIN/CUE et hashes : [`PS1_WEEK4_V148_FIX.md`](PS1_WEEK4_V148_FIX.md). DuckStation et console réelle non testés; attendre le retour utilisateur avant de conclure sur le rendu.


## Week 4 — restauration des détails et poses GF (v149, build d’essai)

Retour utilisateur sur v148 : composition toujours insatisfaisante et GF semble avoir perdu des détails et des images. L’inspection du rig épinglé confirme que seules 10 poses sur les 30 de la timeline officielle étaient affichées; huit nouvelles poses étaient converties en 64×64 puis étirées vers 87×79. v149 conserve les deux poses existantes et génère les 28 autres à 87×79 dans le même canevas ancré. Le choix des 15 poses de chaque moitié de danse est piloté par l’horloge audio, une moitié par beat; la table comprend 30 cellules dont 27 rendus distincts.

Le réempaquetage vérifié garde la CLUT byte-identique et les pages décor byte-identiques; les rectangles d’images référencés restent texel-identiques à travers le réempaquetage. Week 4 passe de 5 à 8 pages 8bpp (le pool W4 permet 9), le paquet de 328 192 à 524 800 octets (+196 608). Le tampon RAM de transfert reste à 65 536 octets; pas d’ajout de buffer d’animation résident. Aucun changement composition, caméra, audio, chart ou gameplay. Le décor lointain reste un point de composition non résolu.

Build PSn00bSDK 0.24/GCC terminé. Le dry-run prévoyait une génération existante des poses BF (relancée à cause du chemin du nouveau dossier de build), la compilation C, le lien et l’image CD; aucune reconversion audio, chart ou source de scène W4. Le paquet W1 réémis a le même hash que v148. Exécutable SHA-256 `3ce926cb2571d30ad024d24d0abc48095857f45b10aec6d6b5a3089e1a32a249`; BIN `a86a3083217c2f45358a2436cdc79b5e367cef11a007bffdcfb1a27ad5630e0d`; CUE `8579eef0e6966afd78659f364593e560c8384148e9258d14fa88b196a842b340`. Livraison : `ps1/build/week4-composition-v149/delivery-v149-gf-animation/`. L’utilisateur doit encore exécuter le CUE dans DuckStation; aucun test console réelle. Détails : [`PS1_WEEK4_V149_GF.md`](PS1_WEEK4_V149_GF.md).

### v149b — correction du gel au logo Sony

Retour utilisateur : v149 reste au logo Sony/PlayStation. Comparaison ISO v148/v149 : l’entrée fichier `SYSTEM.CNF;1` est la 93e de v149, contre la première entrée fichier du disque v148 qui démarre. L’EXE et le contenu de `SYSTEM.CNF` sont présents et valides; la cause isolée est l’ordre des entrées racine. v149b applique uniquement le réordonnancement ISO déjà utilisé par les builds de démarrage validés. Pas de recompilation ou reconversion; l’EXE v149 reste identique. Les quatre secteurs du répertoire racine sont les seuls secteurs modifiés. BIN/CUE et hashes : [`PS1_WEEK4_V149B_BOOT_FIX.md`](PS1_WEEK4_V149B_BOOT_FIX.md). Contrôle statique réussi; démarrage DuckStation v149b attendu du test utilisateur, sans validation console réelle.

### v150b — préserver l’atlas BF pendant Week 4

Retour utilisateur après v149b : GF est meilleure, mais BF a disparu et la composition Week 4 reste à revoir. L’audit des descripteurs confirme que les poses BF utilisent la page 8bpp physique 7 (`x=768,y=256`); le chargeur v149 écrivait pourtant les huit pages Week 4 dans les slots 0–7. La page Week 4 logique 7 (icône Mom) remplaçait donc l’atlas BF. v150b garde la page physique 7, mappe les sept premières pages W4 aux slots 0–6 et la dernière au slot 8, puis restaure ce slot après déchargement. Comme l’écran Game Over utilise aussi le slot 8, le retry recharge la page W4 empruntée avant le compte à rebours.

Les changements n’affectent ni composition/caméra, tailles/animations, charts, règles de jeu ou audio. W4SCENE reste identique (524 800 octets, SHA-256 `A91F0C52422B59E3067A0A006A5C655D5F554B7FD1EB6D6C71E09E9D35F49505`); le sidecar BF W1 régénéré a conservé son hash `D3C6F317C0B108233C5D81774FA97775AFE2B2D40D98F46528EAD70543B67310`. Compilation et image réussies; le dry-run final ne prévoit que compilation C, lien et ISO. SYSTEM.CNF et FUNKIN.EXE ont été replacés aux deux premières entrées fichier. BIN/CUE et limites : [`PS1_WEEK4_V150B_BF_PAGE_FIX.md`](PS1_WEEK4_V150B_BF_PAGE_FIX.md). Essai DuckStation utilisateur requis; ni composition validée ni console réelle testée.

### v151 — correction de la composition Week 4 (2026-11-05)

Retour utilisateur : la correction BF v150b est satisfaisante, mais la composition reste incorrecte. L'inspection du pipeline révèle trois causes : la limousine lointaine extraite en 455×79 était compositée dans une boîte de 222×39; la limousine principale était écrasée dans une cible 44×88; enfin, GF était dessinée par-dessus le décor aplati, empêchant la limousine de la masquer.

Le script `ps1/compose_week4_layers_v151.py` repart du paquet W4 v149 et de la révision d'assets épinglée. Il corrige la taille de composition de la limousine lointaine et des danseurs, puis range la limousine de premier plan en 240×76 dans l'espace inutilisé de la page logique 7, avec la CLUT existante. L'ordre GPU devient décor lointain/danseurs → GF → limousine avant-plan → Mom → BF. Le mapping v150b garde l'atlas BF intact et utilise la page physique 8 pour cette page W4; aucune page ou lecture CD supplémentaire n'est ajoutée. Le paquet reste à 8 pages et 524 800 octets. Les pages d'acteurs 2–6, la CLUT et l'icône Mom restent identiques; seuls les deux pages du décor et le rectangle de limousine sur page 7 changent. La position scène, chart, caméra, timings d'animation, gameplay et audio restent inchangés.

PSn00bSDK 0.24 / GCC MIPS 12.3 : dry-run de 5 actions, sans reconversion audio, chart ou conversions générales de graphismes; compilation, lien et création de l'image disque réussis. La comparaison statique confirme le paquet W4 attendu et l'ordre ISO `SYSTEM.CNF;1`, puis `FUNKIN.EXE;1`. BIN SHA-256 `CF400E0915039BF69FE9790337DEC6ADF2282D0DE467D9B26C723B3CA2D57871`; CUE SHA-256 `A8DFF2001A5344E38916D95FE451A8307E574A1CB7165A36C9A2F20E90FCC3B7`. Manifeste livré avec le disque et rapport [`PS1_WEEK4_V151_COMPOSITION.md`](PS1_WEEK4_V151_COMPOSITION.md).

**État :** build et contrôles statiques réussis; le rendu intégré n'a pas été observé dans DuckStation. Le CUE attend le test manuel de l'utilisateur; la composition v151 n'est donc pas déclarée validée. Les danseurs lointains restent statiques; roues, cheveux au vent et effets de passage restent différés. Console réelle non testée.
### v152 — ancrage officiel de la limousine Week 4 (2026-11-05)

Retour utilisateur sur les captures v151 : la composition reste incorrecte. Les captures montrent la limousine principale coupant le bas du cadre et ne servant pas de support visuel clair à Mom/BF. Le code v151 la plaçait en `(16,152)`. Dans le JSON officiel épinglé `limoRide.json`, sa position est `(-120,528)`. Les coordonnées PS1 des personnages suivent déjà le facteur 1/6 (par exemple Mom 329,5/913 → 55/152, GF 787/779 → 131/130, BF 1217,5/592 → 203/99). La position de la voiture cohérente dans cet espace est donc `(-20,88)`. Avec le zoom 524/256, l’ancien ancrage la plaçait d’environ 74 px trop à droite et 131 px trop bas à l’écran.

Le script `ps1/compose_week4_layers_v152.py` vérifie la position officielle puis dérive cet ancrage, sans changer les pixels du paquet W4 v151. L’ordre de rendu conservé suit les zIndex officiels : scène/danseurs, GF, limousine principale, Mom, BF (100/150/200/300). La limousine doit donc masquer GF et rester derrière Mom/BF. Les poses, compositions du décor lointain, coordonnées des personnages, caméra, charts, règles du jeu et audio ne changent pas. La voiture et les danseurs restent statiques.

Le build final reprend la configuration `Debug` de v151. Une première configuration non-Debug a été identifiée par comparaison avant livraison; elle est archivée séparément et n’est pas le disque fourni. Le dry-run du build final prévoyait 5 actions : génération connue du sidecar BF sans changement de hash, compilation de deux objets C, lien et ISO; aucune conversion chart/audio ou conversion générale de graphismes. Compilation PSn00bSDK 0.24/GCC MIPS 12.3 réussie. Les exécutables v151/v152 font chacun 1 028 096 octets et ne diffèrent que sur 3 octets correspondant aux coordonnées. Le paquet W4 garde 8 pages, 524 800 octets et la même CLUT. `SYSTEM.CNF;1` et `FUNKIN.EXE;1` sont les deux premières entrées racine du disque livré.

BIN SHA-256 `44CDD729D30F920FA7F77CAB30E29932EB2EE6ABB0DB311E57808E49BF72698C`; CUE SHA-256 `4998D0C3DA85740DFE82B5154918BAF34259EE8BED181F29F1445AE36FC87EB6`. Manifeste et détail : [`PS1_WEEK4_V152_OFFICIAL_ANCHOR.md`](PS1_WEEK4_V152_OFFICIAL_ANCHOR.md).

**État :** compilation et contrôles statiques réussis. Aucun lancement DuckStation ni essai console pour v152; test manuel utilisateur requis. Les captures précédentes motivent le changement mais ne valident pas ce nouveau rendu.

## Week 4 v153 — séparation du plan lointain

Après la comparaison avec `limoRide.json` épinglé et les captures, la cause du manque de profondeur est isolée : le sunset, la limousine distante et les danseurs partageaient une même texture de fond et recevaient donc le même scroll caméra. v153 repart du paquet converti v152, laisse le sunset seul sur les pages de fond, et place la limousine distante avec quatre cels officiels dans une zone libre de la page logique 7. Cette primitive utilise le scroll officiel `0.4`; la limousine principale reste à `1.0`. Son ancrage, sa taille, l’ordre de dessin et les personnages restent inchangés.

Le paquet demeure à 8 pages 8bpp + CLUT, 524 800 octets; aucune page, lecture CD, palette, chart ou donnée audio supplémentaire. Le script reproductible est `ps1/compose_week4_layers_v153.py`; les assets épinglés et FFmpeg restent hors Git. Rapport et hashes : `docs/PS1_WEEK4_V153_PARALLAX.md`.

Build PSn00bSDK 0.24 / GCC MIPS 12.3 / CMake-Ninja réussi en réutilisant les ressources préconverties. BIN 339 346 560 octets, 144 280 secteurs; CUE et BIN livrés sous `ps1/build/week4-composition-v153/delivery-v153-far-plane-parallax/`. BIN SHA-256 `3482B62297B81AFEB7A57FFDBB8C7CD067FCD7589ADA08CD67D0959E97BA8699`.

Compilation et contrôles statiques uniquement. DuckStation attend le chargement utilisateur; aucun rendu, démarrage, audio ou stabilité n’est encore validé sur v153. Console réelle non testée.

### v153 rootfix — gel au logo PlayStation

Retour utilisateur : le CUE v153 reste bloqué au logo PlayStation. L’analyse directe de l’ISO livré révèle que son répertoire racine a été trié par nom : `SYSTEM.CNF;1` était la 93e entrée fichier et `FUNKIN.EXE;1` la 36e. Le v152 place `SYSTEM.CNF;1` puis `FUNKIN.EXE;1` en tête et constitue la comparaison de démarrage disponible. Le XML v153 listait bien les fichiers de boot au début, mais cela n’a pas garanti cet ordre dans les enregistrements ISO.

Correction limitée au disque : `ps1/diagnostics/reorder_iso_system_cnf.py --exe-after-system-cnf` a réordonné les enregistrements racine et recalculé les contrôles EDC/ECC des secteurs touchés. Le nouvel artefact est séparé dans `ps1/build/week4-composition-v153/delivery-v153-rootfix/`. Aucun code, asset, audio, chart ou exécutable n’a été modifié ni recompilé. Vérification statique : `SYSTEM.CNF;1` fichier 1, `FUNKIN.EXE;1` fichier 2; les secteurs des fichiers restent identiques au BIN v153 initial. L’en-tête PS-X EXE v153 (entrée `0x80025cbc`, chargement `0x80010000`, taille `0x000fb000`) correspond à l’exécutable lié. Une annonce antérieure d’en-tête trop court était erronée : elle résultait d’une extraction absente et d’octets v152 réutilisés par erreur.

BIN rootfix SHA-256 `1CF2554D7DFEB70221B10EDAC45094CD3D5FCD91755A71631C532D9EFB3C66FB`; CUE SHA-256 `D9C9FB58E5CBD6762A26C3CE149AD0B74A107A8B7F8BCA4BCCBBF9E39A6DA2B9`. Le répertoire ISO a 117 fichiers; seules ses zones racine (LBA 22–24) diffèrent du BIN v153 initial. Contrôle statique réussi. L’utilisateur doit charger le nouveau CUE; son démarrage n’est pas encore validé. Pas de test console réelle.

### Week 4 v155 — première passe de valeurs utilisateur (2026-11-05)

L’utilisateur a proposé ses premiers réglages de composition et a autorisé
l’utilisation de l’Analyzer mémoire DuckStation pour les relever. Le scanner a
lu les trois tableaux du tuner v154e en RAM : Stage `(18,0,100%)`, Camera
`(6,0,100%)`, Far Limo `(-14,-8,200%)`, GF `(-24,6,100%)`, Front Limo
`(4,26,100%)`, Mom `(-2,0,100%)`, BF `(-30,22,100%)`. Ces nombres sont des
offsets et échelles par couche, pas des coordonnées d’écran absolues. Aucun
octet n’a été écrit dans la mémoire de DuckStation.

Le build v155 initialise le tuner avec ces valeurs. Le seul changement source
est l’initialisation de ses trois tableaux; les scènes, caméra, gameplay,
charts, graphismes convertis et audio sont réutilisés. Le dry-run annonçait
uniquement une compilation C, le lien et la création ISO. Aucun convertisseur
d’assets/chart/audio n’a été lancé. Le contrôle statique de l’image finale
confirme `SYSTEM.CNF;1` puis `FUNKIN.EXE;1` en tête des 117 fichiers.

L’audit explique aussi pourquoi le plan lointain reste peu défini malgré son
zoom : le convertisseur v153 réduit la cel officielle de limousine (2199×379)
à 240×42 et les danseurs (394×394) à 40×32, puis les regroupe dans un seul
rectangle 240×64. La prochaine passe pourra ré-exporter ces deux ressources et
les séparer, après mesure du budget d’atlas/VRAM. v155 ne modifie pas ces pixels
ni le facteur de parallaxe `102/256`.

Compilation réussie. Le CUE v155 est livré séparément sous
`week4-composition-tuner-v154/delivery-v155-values/`. Le nouveau build n’a pas
encore été exécuté dans DuckStation : il attend le chargement et le retour de
l’utilisateur. Les valeurs proviennent bien d’une session v154e observée dans
l’émulateur, ce qui ne valide pas le rendu de v155. Console réelle non testée.
Voir [`PS1_WEEK4_V155_VALUES_TEST.md`](PS1_WEEK4_V155_VALUES_TEST.md).

### Week 4 v156c — limousine et danseurs lointains séparés

À partir du snapshot v155, la limousine lointaine et les quatre danseurs sont
ré-exportés depuis les assets officiels épinglés dans deux pages 8bpp distinctes.
La limousine utilise 4 cels à 24 fps; les danseurs reprennent les séquences gauche/
droite officielles (6 poses distinctes par direction et 15 pas temporisés par beat).
Le tuner de scène expose désormais Far Limo et Far Dancers comme couches séparées.
Select ouvre l’éditeur, Start fige/reprend l’horloge audio, Triangle affiche les
valeurs X/Y/échelle; les couches s’ajustent indépendamment. La démo de scène évite
que santé et game over interrompent le réglage.

Le paquet W4 passe de 524 800 à 655 872 octets (+128 Kio, +64 secteurs CD); les
8 anciennes pages et la CLUT sont inchangées. Le scratch RAM reste à 64 Kio. Deux
pages supplémentaires sont chargées dans des emplacements prêtés/réservés et
restaurées à la sortie/retry. Dry-run ciblé: compilation C, lien, création ISO,
sans reconversion chart/audio/graphismes. Compilation et vérification statique ISO
réussies (SYSTEM.CNF fichier 1, FUNKIN.EXE fichier 2, EXE embarqué identique).

Le BIN/CUE est livré sous `C:/Users/Manau47/Documents/Codex/week4-composition-editor-v156b/delivery-v156c/`;
les sources/config/hashes sont archivés hors dépôt dans `source-v156c/`. Le test
DuckStation utilisateur reste en attente; aucune validation runtime ou console réelle
n’est revendiquée. Voir `PS1_WEEK4_V156C_FAR_LAYERS_EDITOR.md`.

### Week 4 v157 — textures lointaines et page BF

L’utilisateur a indiqué que les couches lointaines semblaient encore trop réduites,
que l’éditeur plafonnait trop tôt et que BF affichait le mauvais sprite; les positions
de scène actuelles sont à conserver. L’audit a trouvé que le pack v156c plaçait la
limousine lointaine sur la page VRAM 7, également utilisée par l’atlas BF. Le paquet
v157 repacke les quatre cels de limousine dans la page Week 4 existante avec la
limousine avant, et réserve la page libre `(896,0)` aux danseurs. Le BF n’est donc
plus écrasé pendant le chargement W4.

Les danseurs officiels passent de 48×38 à 72×57 par cel, avec 12 poses distinctes
et le même timing; le plafond de zoom de l’éditeur passe de 200 % à 400 %. Les offsets
de scène restent inchangés. Les pages 0–6 et la CLUT sont identiques à v156c; le
paquet W4 baisse de 65 536 octets (32 secteurs CD). Dry-run ciblé: compilation C,
lien et image ISO uniquement. Compilation et contrôle statique ISO réussis;
l’affichage BF et les nouvelles tailles restent à tester par l’utilisateur dans
DuckStation. Aucun test console réelle. Détails et livraison dans
`PS1_WEEK4_V157_FAR_ART_BF_PAGE_FIX.md`.

The final CUE for the next manual test is v157b at `C:/Users/Manau47/Documents/Codex/week4-composition-editor-v156b/delivery-v157b/`. It is the build matched by the archived `source-v157b/manifest-v157b.json`; no DuckStation run has been made.

### Week 4 v158 — front limousine restored

The user reported the foreground limousine missing, requested the distant dancers
about 20 pixels higher, and asked to remove the scene editor. The missing sprite
was traced to the v157 exporter copying from an empty destination page; v158
restores the converted front-limo rectangle from the preserved v156c package.
Only that indexed rectangle and the Week 4 dancer Y anchor change. Dancers move
up 10 world units (~20 screen pixels at the current zoom); their animation and
texture data are reused. The editor and camera-demo build modes are disabled.

Dry-run: two C object builds, link and ISO only; no asset conversions. Build
completed. The final ISO reorder verified 117 root files, with SYSTEM.CNF at
index 1 and the game EXE at index 2, and validated sector EDC/ECC. The
front-limo rectangle contains 12,531 nonzero indices after restoration.
DuckStation execution and the visual result are awaiting the user; no console
test is claimed. BIN/CUE, code/config snapshot and hashes are archived outside
Git in `C:/Users/Manau47/Documents/Codex/week4-composition-editor-v156b/`.
Reproduction details: [`PS1_WEEK4_V158_FRONT_LIMO_DANCERS.md`](PS1_WEEK4_V158_FRONT_LIMO_DANCERS.md).

### Week 4 v159 — composition transforms retained without editor

The user reported that all expected elements were present in v158, but their
layout was wrong. Comparing v157's editor state with the normal build showed
the cause: the transform values were applied only inside
`GAME_WEEK4_COMPOSITION_EDITOR`; turning that feature off also discarded the
saved scene offsets and far-limo scale. v159 keeps the editor disabled and
applies its saved transform values in the normal Week 4 render path. This
restores the composition/camera offsets, doubled far-limo scale, and the
GF/Mom/BF/front-limo positions; the dancers remain raised by 10 world units
(about 20 screen pixels at the current camera scale). No chart, timing,
animation, audio, gameplay, or texture conversion changed.

The incremental dry-run contained only the changed C object, link, and ISO
creation. Build and static ISO checks passed; `SYSTEM.CNF` is root entry 1 and
the executable root entry 2. The temporary scene editor, demo, and startup
diagnostics remain off. The composition still awaits the user's DuckStation
test; no runtime or console validation is claimed. Artifacts and exact source,
configuration, and hashes are archived under
`C:/Users/Manau47/Documents/Codex/week4-composition-editor-v156b/source-v159/`
and `delivery-v159-ordered/`. See
[`PS1_WEEK4_V159_LAYOUT_BAKED.md`](PS1_WEEK4_V159_LAYOUT_BAKED.md).

### Week 4 v160 — characters left, dancers up

Following the v159 composition report, the user requested that the four distant
dancers rise another 40 screen pixels and Mom, GF, and BF shift left 30 pixels.
At the saved W4 zoom 524/256 (2.046875×), this is implemented as `dy=-20` world
units for dancers and `dx=-15` for each character (about 40.9/30.7 screen
pixels). Mom/BF camera focus targets deliberately retain their original X
anchors so following the moved singers does not cancel the visible move. Other
layer transforms remain as v159; no assets, animations, gameplay, charts, or
audio changed.

The normal build keeps editor/demo/diagnostics off. Build, static ISO order and
sector checks are recorded in the v160 manifest. The user still needs to test
the composition in DuckStation; no runtime or console validation is claimed.
Source and artifact hashes are archived under
`C:/Users/Manau47/Documents/Codex/week4-composition-editor-v156b/source-v160/`;
the CUE/BIN are in `delivery-v160-ordered/`. See
[`PS1_WEEK4_V160_LAYOUT_NUDGE.md`](PS1_WEEK4_V160_LAYOUT_NUDGE.md).

### Week 4 v161 — camera focus follows adjusted characters

The user reports v160's object placements are right but the cameras did not
move with them. W4 focus X targets for Mom, GF, and BF now use the same tuned
anchor offsets as their visible sprites; GF focus also uses its existing Y
offset. The v160 placement values, dancer lift, camera zoom/translation tuning,
and all other layers remain unchanged. No assets, animation, chart, gameplay,
or audio changed. The normal build keeps editor/demo/diagnostics off. Build and
static ISO checks are recorded in the v161 manifest; DuckStation validation is
pending. Source and artifacts are archived under
`C:/Users/Manau47/Documents/Codex/week4-composition-editor-v156b/source-v161/`
and `delivery-v161-ordered/`. See
[`PS1_WEEK4_V161_CAMERA_FOLLOWS.md`](PS1_WEEK4_V161_CAMERA_FOLLOWS.md).

### Week 4 v162 — GF lower, distant dancers right

From v161, GF moves down approximately 4 screen pixels and the far dancers move
right approximately 40. With W4 zoom 524/256 (2.046875×), these are GF `dy=+2`
and dancers `dx=+20` world units. GF's camera target remains attached to her
updated anchor. Other v161 placements and camera settings, animations, audio,
charts, and gameplay are unchanged. The normal build keeps editor/demo and
diagnostic overlays disabled. Compilation and ISO checks are recorded in the
manifest; user DuckStation validation remains pending. Source and delivery are
archived at `source-v162/` and `delivery-v162-ordered/` under the external build
archive root. See [`PS1_WEEK4_V162_GF_DANCERS_NUDGE.md`](PS1_WEEK4_V162_GF_DANCERS_NUDGE.md).

### Week 4 v163 — dancers 10 pixels farther right

The user requested another 10-pixel right shift for the dancers. At the W4
zoom this is `dx=+5` world units; their cumulative X offset is +11. GF and all
other v162 placements remain unchanged. The incremental build and static ISO
checks passed without resource conversion. Awaiting the user's DuckStation
test. See [`PS1_WEEK4_V163_DANCERS_NUDGE.md`](PS1_WEEK4_V163_DANCERS_NUDGE.md).

### Week 4 v164 — dancers 10 pixels farther right

The dancers move another ~10.2 screen pixels to the right from v163 (`dx=+5`
world units at 524/256 zoom); their cumulative X offset is +16. All other
v163 settings are preserved. Incremental build and static ISO checks passed,
with converted resources reused. Awaiting the user's DuckStation test. See
[`PS1_WEEK4_V164_DANCERS_NUDGE.md`](PS1_WEEK4_V164_DANCERS_NUDGE.md).

### Week 5 v165 — Mall extraction and composition pass

The user accepted the current Week 4 scene and moved work to Week 5, which was
reported as visually very poor. Inspection found that the old W5 extractor
made a small static composite and did not extract the official upper/lower
Mall crowd animations. It also clipped most of the baked snow layer at runtime
and left a horizontal gap in the 320x240 background fit.

The v165 Week 5-only package re-extracts the official Mall/evil Mall plates,
keeps the escalator, tree and Santa proportional, adds four sampled source
cels for each official Mall crowd prop, and draws separate Christmas/evil snow
foreground cels. Crowd animation is driven from the audio sample clock at
24fps and uses separate 0.28/0.90 parallax factors. The Week 5 visual package
uses seven 8bpp pages including existing sampled character animations (two
pages more than the previous five-page package). Charts, catalog, music, audio
quality, gameplay and Week 4 are unchanged.

Package extraction, build and static ISO checks succeeded. The incremental
dry-run showed only C compilation, link and ISO creation; no audio/chart or
other-week conversion ran. The user must still load the new CUE in DuckStation
to validate the scene, parallax, animation, streaming and transitions. No
runtime or console validation is claimed. Details and reproduction command are
in [`PS1_WEEK5_V165_SCENE.md`](PS1_WEEK5_V165_SCENE.md); the exact package and
binary hashes are in the external v165 archive.

### Week 5 v166 — pause/resume starvation fix

The user reported `FUNKIN PS1 ERROR / CODE 8` after pausing and resuming a
song. The supplied diagnostic frame shows zero CD errors, 78 SPU underruns and
an empty stream buffer. Source inspection found that the pause path aborted an
asynchronous CD read after its sectors had already been reserved and advanced
in `next_sector`; the pause screen also did not feed the ring. On resume this
could exhaust the partial buffer and skip the cancelled range. v166 no longer
aborts the pending read, keeps feeding while paused, and waits for a bounded
refill threshold plus one interleave chunk before resuming the SPU stream.

Only `spu_probe.c` was recompiled; the v165 preconverted scene/audio/chart
package was reused. Compilation and ISO creation succeeded, and the ISO
reorder check placed `SYSTEM.CNF` first and `FUNKIN.EXE` second. DuckStation
verification remains pending. This build deliberately leaves the v165 scene
composition and character extraction unchanged so the pause fix can be tested
separately. The Drive reference was returned as metadata but could not be
opened as video frames through the available connector path; request a directly
attached/local copy before changing composition or sprite resolution.

### Week 5 v167 — split scene layers and official character frames

The user reports that v166 appears to resolve the pause issue and asks to focus
on the Week 5 scene, providing the attached video `Screen_Recording_20261105_210840.mp4`.
The local recording was inspected: the Mall layout separates the stage/crowd,
escalator/tree and snow layers, with Santa at the left and GF on speakers behind
the singers. The pinned official assets revision remains
`724eba9de9e76761d9cefd52169926bc51c760a5`.

The new Week 5-only extraction script emits separate Christmas/Evil stage,
prop, crowd and snow frames; Parents, Monster and GF use 80x96 source frames
with trim offsets. The renderer applies the layer scroll factors to camera
movement, samples the four crowd cels on the audio sample clock at 24fps,
draws Santa as a separate Christmas prop, and uses official BF Christmas idle,
singing and miss frames. Charts and audio packages were reused; no scene
composition, gameplay rule, chart or audio-quality work was done in other weeks.

Build: `ps1-bopeebo-playable-disc`, PSn00bSDK 0.24 / GCC MIPS toolchain / Ninja.
The successful incremental build contains only C compilation, link and disc
creation; no resource conversion was scheduled. Week 5 payload is 9 8bpp pages
plus one 512-byte CLUT (590,336 bytes); the runtime scene loader uses a 65,536
byte page scratch buffer and reads 288 sectors before starting music. Static
budgets are not runtime measurements.

The ordered BIN/CUE is in the external v167 delivery folder, with
`SYSTEM.CNF` and `FUNKIN.EXE` at root entries 1 and 2. Compilation and static
ISO reorder checks passed. DuckStation and real-console execution have not been
performed; the user must load the CUE and report composition, animation, pause,
audio and transition behavior. See [`PS1_WEEK5_V167_SCENE.md`](PS1_WEEK5_V167_SCENE.md).

## Week 5 v168 — composition correction after v167 review

This pass compares the user's v167 DuckStation captures with the supplied
reference recording and the pinned stage JSON (`mallXmas.json`, `mallEvil.json`).
The previous v167 captures show (1) Winter Horrorland's transparent stage plate
exposing framebuffer black over a large area and its official evil tree absent,
and (2) a Mall plate shifted down/right despite the overscan comment. The
renderer also drew the upper crowd after the escalator/tree, contrary to the
official z order.

Changes are limited to Week 5 scene drawing and camera targets:

- Center the 256x192 stage plates at their 1.5x (384x288) draw size. The old
  top-left offset `(-128,-96)` placed them at screen `(32,24)`; it is now
  `(-192,-144)`, yielding the intended 32x24 overscan around 320x240.
- Fill the Mall Evil viewport with the stage's official `#23062D` solid color
  before drawing its alpha-transparent PNG; draw the omitted Evil Tree layer.
- Restore the Mall's official layer order: background, upper crowd, escalator,
  Christmas tree, lower crowd, snow fill/foreground, GF, opponent, Santa, BF.
  Add the official `snowUnder` fill below the thin `fgSnow` strip.
- Apply the pinned Dad/BF camera offsets, scaled from source coordinates to the
  PS1 scene coordinate system, instead of aiming directly at character centers.
  Keep the same character scale, scene assets, animations, charts, gameplay and
  audio data.

No visual assets were regenerated. `W5SCENE.BIN` is byte-identical to v167
(SHA-256 `F728D0086461EFD649EED113D930CD33AE82CFA1F0BEE3CC7FB7D49F5846D840`);
the four-channel music payload is also byte-identical. Static ISO verification
places `SYSTEM.CNF` at root entry 1 and `FUNKIN.EXE` at entry 2.

### Build and evidence

- Build: `ps1-bopeebo-playable-disc`, PSn00bSDK 0.24 / GCC 12.3 / Ninja.
- Dry-run: only `spu_probe.c`, SDK `stream.c`, link and ISO creation; no resource
  conversion command was scheduled.
- Compile/link/ISO: succeeded. Two existing SDK `volatile` qualifier warnings
  appeared in `stream.c`; no project compile errors.
- Delivered BIN: `C:\Users\Manau47\Documents\Codex\week5-scene-v168-delivery\funkin-ps1-week5-scene-v168.bin`
  (339,708,768 bytes, SHA-256
  `A9CBDD0133CAB85284925AC9D06F5C73261F39F9976AC141BB151A650352D908`).
- CUE: adjacent file `funkin-ps1-week5-scene-v168.cue`.
- DuckStation and real hardware: not run by Codex. The user must load this CUE;
  the correction is not visually validated yet.

The next check should compare Mall and Winter Horrorland in the normal build,
then confirm the visible background coverage, evil tree placement, 4:3 crop,
layer overlap and camera transition. See also `PS1_WEEK5_V168_COMPOSITION.md`.
## 2026-11-06 — Week 5 composition transform correction (v169)

Retour utilisateur : la composition v168 reste très éloignée des références.
L'audit du code a trouvé une cause concrète : le renderer appliquait l'échelle
de chaque image au déplacement monde, et plaçait les accessoires avec des
coordonnées écran choisies à la main plutôt qu'avec les données mallXmas/
mallEvil épinglées. v169 utilise une conversion commune 1:10, les positions,
offsets caméra, parallaxes et profondeurs du JSON original, et dissocie
zoom caméra et taille locale des images. Le fond 256×192 à 1,5× est centré
avec 32×24 pixels d'overscan.

Le paquet converti Week 5 est réutilisé octet pour octet; aucune conversion
d'image, de chart ou d'audio n'a été lancée. Dry-run : compilation de
`spu_probe.c`, édition de liens et création ISO uniquement. Compilation et
création du disque réussies. BIN SHA-256 :
`661CE1D91A73A7E7B417A07D32E0232867245F542594947E8B2E3B16145486C2`.
Essai DuckStation par l'utilisateur en attente; composition visuelle non
validée par cet état. Voir `PS1_WEEK5_V169_COMPOSITION.md`.

## 2026-11-06 — Week 5 v169b : correction finale des ancres

Avant la livraison, comparaison de la source officielle et des macros
converties : les macros `BOPEEBO_WEEK5_*_X/Y` décrivaient déjà l'espace monde
PS1 adapté. Leur division supplémentaire par dix avait déplacé personnages et
cibles caméra. La source utilise maintenant directement les positions brutes
des personnages dans `mallXmas.json` / `mallEvil.json`, puis ne les convertit
qu'une fois. Aucun asset reconverti ou gameplay/audio/chart n'a changé.

Build incremental depuis le cache v168 : dry-run limité à la compilation C,
l'édition de liens et l'ISO ; aucune conversion. Le build s'est terminé avec
succès et une seconde invocation Ninja a répondu `no work to do`. BIN SHA-256
`8652835D4A2AB442C7298BE8431F0EF570920FB843F1159766D14B86F8D8BA4D`, CUE
SHA-256 `8579EEF0E6966AFD78659F364593E560C8384148E9258D14FA88B196A842B340`.
Livraison et snapshot source/cache dans
`C:\Users\Manau47\Documents\Codex\week5-scene-v169b-delivery` ; le premier
v169 préflight reste conservé séparément. Aucun test DuckStation par Codex et
aucune validation visuelle utilisateur à ce stade.

## 2026-11-06 — v169b bloquée au logo Sony, v169c réordonnée

Retour utilisateur : v169b reste au logo Sony/PlayStation. La vérification
directe de l'ISO trouve `SYSTEM.CNF;1` en 93e entrée fichier et `FUNKIN.EXE;1`
en 36e; les contenus sont présents et corrects, mais l'ordre racine répète le
défaut de démarrage déjà rencontré sur les anciennes images. La v75 de référence
et v168 plaçaient ces entrées dans le premier secteur du répertoire.

v169c est dérivée de la v169b par le seul outil existant
`reorder_iso_system_cnf.py --exe-after-system-cnf`. La vérification du script
confirme EDC/ECC valides et aucun changement hors des quatre secteurs bruts
contenant le répertoire racine. `SYSTEM.CNF`, PS-X EXE, code et ressources sont
inchangés; la première entrée fichier est maintenant SYSTEM.CNF, la deuxième
FUNKIN.EXE. Pas de compilation ni de reconversion. BIN SHA-256
`AD82EA9B22ABA753EB0D2BFBC5592FC534FF9342EE187359DCB17B675A0C710A`; CUE
SHA-256 `0FD36D0C8454C756C6AC70B9CD5AED0662FD5F4F0960072D0C54862F86EA1AD1`.
Le nouveau disque est livré dans `week5-scene-v169c-rootfix`. Démarrage
DuckStation à confirmer par l'utilisateur; aucune validation runtime n'est
revendiquée.

## 2026-11-07 — Week 5 v170b, échelle et palettes

Retour v169c : placements jugés nettement meilleurs, mais échelles/détails de
Mom/Dad et GF, étage supérieur du mall et foule encore insuffisants. v170b
agrandit les cels Mom/Dad et GF de 80x96 à 96x112, garde BF/Monster en 80x96
pour rester dans les neuf pages, attribue une CLUT par page et dessine la foule
supérieure au-dessus de l'escalator avec une échelle de décor accrue. La taille
du paquet W5 augmente de 4 Kio; les charts et pistes audio restent identiques.

Dry-run : compilation des deux sources C, link et création ISO uniquement.
Compilation/ISO réussies. Le réordonnancement racine place SYSTEM.CNF puis
FUNKIN.EXE en premières entrées. BIN SHA-256
`D7CC97424C98AF233D34B9EECEC2B7C85BE853F7F177017DEFBAC14CC2937709`, CUE
SHA-256 `31992FEC0A7795285531EAEE3083F7DDE8D4D1BB4223D71B58F15AF6748FBC5A`.
Pas d'essai DuckStation/console par Codex : le rendu, les transitions, l'audio
et le gameplay attendent l'essai utilisateur. Détails et budgets dans
[`PS1_WEEK5_V170B_SCALE_PALETTE.md`](PS1_WEEK5_V170B_SCALE_PALETTE.md).

## 2026-11-07 — Week 5 v171, plans officiels et échelle

Après retour v170b, comparaison des couches et tailles avec `mallXmas.json`,
les rigs/XML épinglés et la vidéo de référence. La foule supérieure était
beaucoup trop élargie par son facteur de rendu et l’ordre GPU mettait
`bgEscalator` derrière `upperBoppers`, contrairement aux z officiels. v171
ramène la foule à une projection calculée depuis sa largeur source de 2596 px,
remet l’ordre des plans officiel, augmente les cels parents/GF de 96×112 à
104×116 et leur échelle Q8 de 171 à 190. Le nombre/cadence des poses restent
inchangés; BF, Monster, gameplay et audio ne sont pas retouchés.

Pour tenir la VRAM, les pages communes sont séparées des pages Noël/Monster;
les variantes réutilisent leurs emplacements physiques à tour de rôle.
11 pages logiques (2 fonds alternatifs, 6 communes, 2 Noël, 1 Monster), au
maximum 9 pages 8bpp simultanées pour Noël. Paquet graphique : 726 528 octets
(+132 096 sur disque); les audios et charts sont repris sans modification du
paquet v170b.

Dry-run : code C, lien et image disque; aucune reconversion générale
graphismes/audio/charts. Compilation et génération ISO réussies dans
`week5-scene-v171-build`; BIN/CUE livrés séparément. Pas d’exécution
DuckStation par Codex ni de test console : composition, transitions, audio et
animations de cette version restent à vérifier par l’utilisateur. Rapport :
[`PS1_WEEK5_V171_LAYERS_SCALE.md`](PS1_WEEK5_V171_LAYERS_SCALE.md).

## 2026-11-07 — v171 écran Sony : correction du répertoire ISO

L’utilisateur a signalé que v171 restait au logo Sony. L’inspection du BIN a révélé que l’ordre racine n’était pas celui annoncé dans le manifeste v171 : `FUNKIN.EXE;1` était à l’entrée fichier 36 et `SYSTEM.CNF;1` à l’entrée 93, car le générateur d’ISO les trie alphabétiquement. v171b reprend le BIN v171 sans recompiler ni régénérer de ressources et réordonne uniquement les enregistrements du répertoire racine. Les secteurs modifiés sont les secteurs 22–24; les payloads et extents de `SYSTEM.CNF` et `FUNKIN.EXE` restent identiques. Les entrées fichier sont désormais `SYSTEM.CNF` puis `FUNKIN.EXE`. Le correctif statique n’est pas encore validé en DuckStation ou sur console; l’essai manuel est requis. BIN SHA-256 `63995D898CE740053C741CE41F1E4DB510CEAD89F91C1AB7DB51E022CBF8F7DD`, CUE SHA-256 `BDA46FD0A026D16A0676E12571FB4D6AA20543D022A974902780EE999771D653`.

## 2026-11-07 — Week 5 v172, repère commun du décor

Après le retour v171, l’audit a trouvé une incohérence de repère : les fonds `bgWalls`/`evilBG` étaient recadrés au centre en 4:3 puis dessinés comme des plaques plein écran, alors que les couches et personnages utilisaient les coordonnées de scène officielles. v172 préserve l’aspect source, applique les positions, échelles de sprite et scrolls officiels dans le même mapping/caméra que les autres couches. Seules les deux pages d’arrière-plan et leurs CLUT sont reconstruites; les autres pages, charts, catalogues et pistes sont réutilisés byte-à-byte. Le dry-run n’indiquait que deux compilations C, le lien et l’ISO. Compilation et vérifications statiques d’ordre ISO réussies. Aucun essai DuckStation/console : validation de l’image, composition et alignement reste attendue de l’utilisateur. BIN SHA-256 `28A5345E31163CF6FA4E090227C19E77D7C6AE423A175AB9D5332A19BF7744E4`; CUE SHA-256 `BDA46FD0A026D16A0676E12571FB4D6AA20543D022A974902780EE999771D653`. Rapport : [`PS1_WEEK5_V172_BACKGROUND_TRANSFORM.md`](PS1_WEEK5_V172_BACKGROUND_TRANSFORM.md).
# Week 5 v173 — échelle native des fonds

- Retour utilisateur : v172 confondait encore débordement hors cadre et échelle du décor. Les bords hors écran sont attendus ; ils ne doivent pas servir à réduire l’image pour la faire tenir en 4:3.
- Correction isolée : les fonds gardent leur position de scène et leur rapport d’aspect, mais leur taille de destination reprend l’échelle effective de la scène officielle 1280×720 réduite uniformément à 320×240. Noël : 661×392 px (contre 445×265 en v172). Mall Evil : 698×428 px (contre environ 376×230). Les débordements sont donc rognés naturellement par le viewport.
- Seul le facteur d’échelle de destination du fond change (`bg_art_scale` : Noël 248→368, Evil 210→389). Pages, CLUT, audio, charts, caméra, personnages et gameplay restent identiques à v172.
- Dry-run après réutilisation des poses BF : compilation de `spu_probe.c`, lien et image disque uniquement ; aucune conversion de graphismes, audio ou charts. Build réussi avec PSn00bSDK 0.24 / GCC 12.3. Root ISO réordonné : SYSTEM.CNF entrée 1, FUNKIN.EXE entrée 2 ; secteurs modifiés EDC/ECC recalculés.
- Aucune observation DuckStation ni console pour v173. Le rendu et la composition restent à valider par l’utilisateur.
- Livraison et empreintes : `C:/Users/Manau47/Documents/Codex/week5-scene-v173-delivery/build-manifest.md`.

## 2026-11-07 — Week 5 v174, éditeur temporaire de composition

Après plusieurs passes de composition qui ne correspondaient pas au modèle,
l’utilisateur a demandé un éditeur en jeu comparable au tuner temporaire de
Week 4. v174 expose séparément les couches des variantes Mall de Noël et Evil,
y compris la caméra. Select ouvre l’éditeur, Haut/Bas choisit une couche,
Gauche/Droite modifie X, L1/R1 modifie Y, Croix/Rond règle l’échelle, R2
accélère, Carré remet la couche à zéro, Start met la musique et l’horloge de
scène en pause, Triangle affiche toutes les valeurs. Les réglages restent
temporaires et indépendants entre variantes. Le build de démonstration suit les
charts visuellement mais neutralise score, santé, pénalités et game over afin
que la navigation ne juge pas les notes.

La compilation incrémentale et l’ISO ont réussi. Le dry-run ciblé ne planifiait
que la compilation de `spu_probe.c` et du `stream.c` du SDK, le lien et la
création disque; aucune conversion d’assets/audio/charts. Les paquets Week 5
et poses BF sont byte-identiques à v173. L’ISO place statiquement SYSTEM.CNF
et FUNKIN.EXE aux entrées racine 1 et 2. Deux avertissements `volatile`
existants proviennent du `stream.c` SDK. L’éditeur n’a pas encore été exécuté
dans DuckStation; l’essai utilisateur est requis avant d’adopter des valeurs.
Console réelle non testée. Détails, commandes, SHA-256 et snapshot source :
[`PS1_WEEK5_SCENE_EDITOR_V174.md`](PS1_WEEK5_SCENE_EDITOR_V174.md) et le dossier
de livraison externe `C:/Users/Manau47/Documents/Codex/week5-scene-editor-v174-delivery/`.

## 2026-11-07 — Week 5 v175, premier jet repris de l’éditeur

L’utilisateur a fourni un premier placement réglé dans le tuner v174. Les onze
couches Christmas Mall ont été relevées par lecture du scanner mémoire DuckStation
sur les symboles de la map v174, puis installées comme valeurs de départ du build.
Carré restaure maintenant ce premier jet pour le calque choisi ; le mode éditeur
reste disponible. La rangée Evil Mall est restée à ses valeurs neutres.

Les cibles de caméra suivent déjà les ancrages édités BF/Dad/GF dans le code v174.
La caméra a donc repris son déplacement indépendant relevé dans le même tableau,
sans ajout d’un offset de correction supplémentaire. La composition et le focus
avec ces valeurs dans v175 restent à valider par l’utilisateur. L’escalator et la
foule sont inclus aux tailles réglées ; l’amélioration de leurs détails est différée.

Build incrémental terminé avec les options v174. Dry-run limité à deux unités C,
lien et image disque ; aucun asset, chart ou audio reconverti. Le paquet Week 5 et
le flux musical sont inchangés. BIN SHA-256
`C50264FFB7CDD08848A7DFC1E981FCEAE5C7CFAB05E5F8F48B696DB759CD7D90`, CUE
`65A155397AB1B2F21B6525C8734953826EF9CD9384AD28DB7751C7CEE03EC126`. L’image
est préparée pour l’essai utilisateur ; elle n’a pas encore été exécutée dans
DuckStation ni sur console. Snapshot, configuration, ELF/MAP et image sont
archivés dans `C:/Users/Manau47/Documents/Codex/week5-first-pass-v175-delivery/`.
Rapport : [`PS1_WEEK5_FIRST_PASS_V175.md`](PS1_WEEK5_FIRST_PASS_V175.md).
## 2026-11-08 — Week 5, correction ciblée du focus caméra BF (v176)

La capture v175 montre BF au bord droit et inférieur. En appliquant la formule de projection au focus BF, la cible codée (`BF -30 X`, `-20 -28 Y`) combinée aux décalages d’édition v175 place l’ancre théorique autour de `(259,242)` à 1,8×. J’ai modifié uniquement la cible caméra BF : elle devient `BF X`, `BF Y -20`, ce qui donne une projection estimée `(205,192)`. Les focus Dad/GF, les positions d’acteurs, le décor et les autres réglages restent inchangés.

Le dry-run ciblé prévoyait uniquement recompilation de `spu_probe.c`, lien de l’ELF et création du BIN/CUE. Build réussi ; aucune reconversion des graphismes, charts ou audio. Le disque v176 est livré séparément. Le changement de cadrage n’a pas encore été vérifié par l’utilisateur dans DuckStation : attendre son essai avant de le déclarer validé. Détails et hashes dans `docs/PS1_WEEK5_BF_CAMERA_V176.md` et le dossier d’archive local v176.

Essai utilisateur v176 : blocage observé au logo Sony/PlayStation, donc ce build est refusé. Aucun correctif ni nouveau disque n’a été produit pendant le diagnostic.

Comparaison statique avec v175 : le CUE v176 référence bien son BIN. Les secteurs `SYSTEM.CNF` et l’en-tête PS-X EXE (entrée `0x80022314`, chargement `0x80010000`, taille texte `0x000F7800`) correspondent ; l’exécutable embarqué est identique au FUNKIN.EXE livré. Le désassemblage du point d’entrée `0x80022314–0x80022400` est identique. Les seules différences de code sont trois constantes dans `camera_target_for_focus()`.

Essai direct autorisé dans DuckStation sur le FUNKIN.EXE v176 extrait : le programme s’exécute et atteint `FUNKIN PS1 ERROR / CODE 4`, avec 59 IPS et zéro secteur reçu, résultat attendu sans disque monté pour cette voie de lancement. Cela confirme que l’exécutable extrait s’exécute, mais ne valide ni le démarrage BIOS par CUE ni l’accès CD. Le gel spécifique au démarrage depuis le disque reste inexpliqué. L’émulateur a été laissé sur cet écran d’erreur CD ; aucun test console réelle.

## 2026-11-08 — v176 BIOS boot-order diagnostic image

After the user reported that v176 remained at the Sony/PlayStation logo, static ISO inspection found a packaging difference from v175: both discs have 117 root files, but v175 places `SYSTEM.CNF` and `FUNKIN.EXE` at root records 1 and 2, while v176 places them at 93 and 36. The PSn00bSDK 0.24 ISO template warns that the PS1 BIOS root directory is limited to 30 entries. This is a strong candidate cause, not yet confirmed by an emulator run.

A targeted image was created from the exact v176 BIN, without rebuilding code or converting assets. It moves only the two boot records to positions 1 and 2 and recalculates EDC/ECC for root-directory sectors LBA 22–25. The source and embedded executable hashes remain unchanged. An initial `mkpsxiso`-only repack did not fix the ordering: it emitted alphabetical root records again, so that intermediate image is not the test CUE.

Test CUE: `C:/Users/Manau47/Documents/Codex/v176-boot-record-fix/funkin-ps1-v176-bootfixed.cue`; BIN SHA-256 `C7BC524922143849F3DAE34457F69BD7E4C3D1D712AAA0A6CD684DF214640E96`. Static checks show SYSTEM record 1 and FUNKIN record 2, with unchanged file extents. DuckStation and console execution are still pending user confirmation.


## 2026-11-08 — Week 5 second-pass capture (v177)

See [PS1_WEEK5_SECOND_PASS_V177.md](PS1_WEEK5_SECOND_PASS_V177.md) for captured Memory Analyzer offsets, camera change, VRAM feasibility calculations, build configuration and pending validation.

## 2026-11-08 — Week 5 background sprite detail (v178)

Clarification utilisateur : BF est déjà convaincant et les sprites Mom/Dad/GF ne sont pas la cible de cette passe. Le besoin porte sur les sprites de décor, en priorité la foule du balcon et l’escalator. Les quatre poses de foule et l’animation existante sont conservées; aucune nouvelle frame ni modification de cadence.

Le nouveau générateur `ps1/rebuild_week5_backdrop_detail.py` repart du paquet converti v171 et ne relit que les sources officielles `upperBop` et `bgEscalator`. Il reconstruit la foule du balcon et l’escalator à 1,5× de densité, les découpe en rectangles compatibles avec les pages 256×256, conserve les offsets alpha, puis compense leur taille d’affichage pour garder les ancres et dimensions v177. BF, Mom, Dad, GF, compositions, cibles caméra, gameplay, charts et audio restent inchangés.

Le paquet passe de 11 à 12 pages logiques : +66 048 octets sur disque (une page texture et une CLUT). Les pages 0–7, 9 et l’ancienne page Evil 10 déplacée en page 11 sont identiques par hash, de même que leurs palettes. Les deux nouvelles pages réutilisent la CLUT Christmas existante. Le chargement Christmas occupe toujours 10 pages VRAM physiques; le tampon temporaire reste 64 Kio, sans chargement des PNG haute résolution dans la RAM du jeu. La foule et l’escalator utilisent trois quads chacun, soit +4 quads par frame active et 10 entrées de frame dans le tableau. La CLUT de 12 pages tient exactement dans les 3 secteurs déjà lus. Les UV et dimensions des 79 entrées ont été vérifiés pour tenir dans les limites 256×256.

Dry-run du disque : recompilation de `spu_probe.c` et du module cdstream SDK, lien ELF puis génération BIN/CUE; aucune reconversion hors des deux sprites de décor. Compilation PSn00bSDK 0.24 et création ISO réussies. Deux avertissements `volatile` préexistants proviennent du `stream.c` du SDK. Le BIN brut de mkpsxiso avait des entrées racine alphabétiques; il n’est pas le disque livré. Le CUE final utilise ensuite `ps1/diagnostics/reorder_iso_system_cnf.py --exe-after-system-cnf`, vérifie les EDC/ECC et place `SYSTEM.CNF` puis `FUNKIN.EXE` en entrées 1 et 2; les octets hors répertoire racine sont inchangés. L’exécutable du disque final correspond octet pour octet au PS-X EXE compilé.

Le CUE final (répertoire racine corrigé) est livré séparément dans `C:/Users/Manau47/Documents/Codex/week5-backdrop-hires-v178-rootfixed-delivery/`. Le build n’a pas encore été observé dans DuckStation ni sur console; le gain de détail et l’absence de régression audio restent à valider par l’utilisateur. Détails et procédure dans [PS1_WEEK5_BACKDROP_DETAIL_V178.md](PS1_WEEK5_BACKDROP_DETAIL_V178.md). L’état local avait HEAD `7057882fa4c481fb878de4cc27d3a827179f7ddd` et contenait des modifications de travail préexistantes; les hashes du code construit et le CMakeCache sont archivés avec le disque.

## 2026-11-08 — Week 5 v178 composition regression and v179 correction

L’utilisateur a signalé que le build haute densité v178 avait dégradé la composition. Comparaison du générateur et du paquet : la page texture Evil d’origine (page logique 10 en v177) n’était pas recopiée à la nouvelle page logique 11; une seconde copie de la page Christmas remplaçait ses pixels. L’extraction personnalisée des danseurs recentrait aussi verticalement les cadres alors que le convertisseur v177 les enregistrait par le bas; enfin les pixels alpha <128 étaient rognés même si le moteur les traite comme transparents. Ces différences sont maintenant corrigées dans le générateur v179, sans toucher aux personnages, caméras ou placements.

Contrôles statiques v179 : le hash de la page Evil logique 11 égale celui de la page v177 déplacée; les rectangles escalator/foule reprojetés à l’échelle v177 sont à moins de 0,34 pixel d’écart sur dimensions et offsets. Le CUE v179 doit encore être observé par l’utilisateur dans DuckStation. v178 demeure archivé comme variante rejetée; aucune validation visuelle ni console réelle n’est revendiquée.

Le précédent compte rendu v178 indiquait à tort que l’ancienne page Evil était déplacée à l’identique. La vérification après le retour utilisateur a établi que les pixels de cette page avaient été remplacés; cette erreur est réparée en v179 et documentée ici.

Build v179 : Ninja dry-run limité à `spu_probe.c`, `stream.c` du SDK, lien et disque. Aucun nouvel encodage audio/chart et aucune conversion générale. Le build a réussi sous PSn00bSDK 0.24 (deux avertissements `volatile` déjà présents dans le SDK). Vérification ISO : SYSTEM.CNF/FUNKIN.EXE en entrées visibles 1/2, chaîne BOOT correcte, exécutable PS-X EXE embarqué identique à celui compilé. BIN SHA-256 `9F3880640E755407E9DBE01271F85B56FF14E2DDD72F1582A0C345C6EDCAB45B`; CUE SHA-256 `BDA46FD0A026D16A0676E12571FB4D6AA20543D022A974902780EE999771D653`. Fichiers et configuration exacts archivés dans le dossier local `week5-backdrop-hires-v179-delivery/source-snapshot`. Exécution DuckStation en attente; rendu non validé, console non testée.
## 2026-11-08 — Week 5 scene editor restored (v180)

The user reported that the Week 5 composition was unacceptable and asked to restore the level editor. Prepared a separate Week 5 scene-editor build on the corrected v179 package, without changing scene coordinates, assets, charts, gameplay art, or audio. CMake enables `FUNKIN_PS1_WEEK5_COMPOSITION_EDITOR=ON` and `FUNKIN_PS1_SCENE_DEMO_DEFAULT=ON`; dry-run listed only the gameplay source/SDK stream compiles, link, and ISO creation. No asset conversion was scheduled. The Week 5 package and generated visual-data header match v179 byte-for-byte.

The editor is hidden at boot and toggled by Select in a Week 5 song. D-pad selects/moves layers; L1/R1 changes Y; Cross/Circle scales; R2 increases step; Square resets; Triangle prints the transform summary; Start pauses/resumes. Scene-demo bypasses scoring, health, misses, and game over while keeping chart animation for safe editing. Changes are temporary and not saved to disc.

Build and root-order repair completed; static checks put `SYSTEM.CNF;1` first and `FUNKIN.EXE;1` second. Delivery: `week5-scene-editor-v180-delivery`. DuckStation execution and user validation are pending; no runtime behavior is claimed as verified.

## 2026-11-08 — Week 5 memory capture and BF camera correction (v181)

The user performed another DuckStation Memory Scanner pass on the Week 5
Christmas Mall editor. I copied the eleven signed X/Y offsets, in the
`W5_EDIT_*` layer order, into both the baked scene defaults and the editor's
initial state. The Evil variant and existing layer scales remain unchanged.
The user clarified that the earlier camera request was reversed: raising the
BF camera should move BF down on screen. I changed only the BF-focus camera
target by -11 world units. At zoom 460/256, the projected displacement is
approximately 20 screen pixels downward; this is a calculation pending the
user's visual confirmation.

Build v181 used a separate copy of the v180 build directory. Dry-run scheduled
only the game source, PSn00bSDK cdstream source, link, and disc generation; no
resource conversions. All 133 checked generated BIN/VAG/header resource files
match v180. The raw image put SYSTEM.CNF at root record 93, so the existing
root-order repair created a separate delivered BIN/CUE with SYSTEM.CNF and
FUNKIN.EXE at root records 1 and 2. Build succeeded; two existing SDK
`volatile` warnings remain. The user has not loaded this CUE yet. DuckStation
visual validation and console testing remain pending. Hashes, exact config,
source diff, and snapshot are in `PS1_WEEK5_MEMORY_PASS_V181.md` and
`C:/Users/Manau47/Documents/Codex/week5-memory-pass-v181-delivery/`.

## Week 5 GF zoom and crowd registration v182 — 2026-11-08

The user clarified that Christmas GF looked too small and supplied the
current enlarged value from the scene editor. DuckStation Memory Scanner
value `0x0160` (352 Q8) is now the baked normal-build GF scale as well as the
editor default. The global Weeks 1–5 detail-matching pass remains deferred.

The four official upper-crowd cels and their 24 fps sequence are unchanged.
Their independently trimmed source rectangles had heights 52–55 and vertical
offsets 8–5. The targeted packer now uses one 384×55 canvas and y offset 5 for
each cel, then splits it into the same page-safe strips. This addresses
per-pose dimension/rounding differences; whether this removes the user's
observed crowd jump still requires the CUE test.

The package remains 12 logical pages / 792,576 bytes. SHA comparisons against
v181 found all matching VAG and chart files identical; only the Week 5 scene
payload/header changed. Ninja dry-run listed only the main source, SDK
`stream.c`, link and ISO. Build and root-order repair succeeded; 117 ISO root
files were checked, with SYSTEM.CNF and FUNKIN.EXE first. The CUE was not run
in DuckStation in this pass, and console hardware was not tested. See
[`PS1_WEEK5_GF_CROWD_V182.md`](PS1_WEEK5_GF_CROWD_V182.md) and the external
`week5-gf-crowd-v182-delivery` directory for hashes, configuration and source
snapshot.
# 2026-11-08 — v183 : correction ciblée de la foule basse Week 5

L’utilisateur a précisé que le défaut de clipping concerne la foule basse derrière Mom, Dad, GF et BF, et non la foule supérieure. La v182 précédente avait ciblé le mauvais groupe.

Le diagnostic statique des rectangles `CROWD_LOWER_0..3` dans le paquet v182 montrait des tailles recadrées de 158×53/54 et des offsets différents (`+9,+1`, `+9,+1`, `-9,0`, `+9,0`). Le cel 2 avait donc un écart de 18 px. v183 extrait les quatre cels officiels sur un canevas commun 176×54, réempaquette uniquement les rectangles de la page 9 et conserve sa CLUT, l’animation, l’échelle et la cadence. Les autres pages, ressources, gameplay et audio restent réutilisés.

Compilation et création du disque réussies ; dry-run final limité à compilation, lien et ISO. L’image n’a pas été lancée dans DuckStation. Le clipping et le mouvement de la foule basse restent à confirmer par l’essai utilisateur. Rapport détaillé : `docs/PS1_WEEK5_LOWER_CROWD_V183.md`.

## 2026-11-08 — Asset harmonization line, v183 baseline and v1 build

L’utilisateur désigne v183 comme base validée. Son BIN/CUE et son snapshot source restent conservés dans `C:/Users/Manau47/Documents/Codex/week5-lower-crowd-v183-delivery/`; hashes de référence : BIN `63EAD9541EA8690C40DD2866E3DA976EC115BAC4D967C6F063D6DB52011C5B6E`, CUE `B86117223C353E77BF7AD9312C9835D65DA7A30986B3A1DCCB7A17D785BE33A6`. La confirmation utilisateur remplace l’état « essai en attente » noté lors de la livraison initiale; aucun nouvel essai DuckStation ni test console n’est affirmé.

Nouvelle ligne dédiée `ps1-asset-harmonization-v1`, avec numérotation de livraison repartant à v1. Le premier build reprend les paquets convertis v183 et désactive uniquement les éditeurs temporaires de scène et le mode démo dans sa configuration de livraison. Aucun redimensionnement, recoloration ou réempaquetage graphique supplémentaire n’est appliqué : l’audit statique ne révèle pas de réduction de page sûre au-delà des réempaquetages W4/W7 déjà présents. Les espaces transparents dispersés ne libèrent pas une page et les UV/CLUT ne peuvent pas être dissociées.

Les résultats de dry-run, compilation, tailles et hashes du nouveau BIN/CUE sont ajoutés après le build. L’essai utilisateur dans DuckStation reste requis avant toute validation de cette nouvelle image. Rapport et commandes : `PS1_ASSET_HARMONIZATION_V1.md`.

### Résultats de compilation — harmonisation v1

Dry-run Ninja : quatre tâches uniquement (compilation du jeu, compilation de `cdstream/stream.c` du SDK, lien ELF, création disque). Aucun convertisseur de ressource. La compilation réelle réussit avec deux avertissements `volatile` préexistants dans le lecteur du SDK. 133 fichiers produits `.bin`/`.vag`/`.h` comparés au build v183 : 0 différence de hash.

La sortie fait 1 388 652 octets ELF et 1 017 856 octets EXE. Sections ELF : text 1 013 048, data 2 638, BSS 40 120 octets. Le ELF archivé v183 comptait text 1 008 920, data 2 766, BSS 40 104 : le total text+data+BSS est supérieur de 4 016 octets en v1. La désactivation éditeur/démo n’a donc pas prouvé de gain mémoire, et aucun gain RAM n’est revendiqué.

Le BIN brut plaçait `SYSTEM.CNF` à l’entrée racine 93. La réparation ISO existante a produit une copie distincte où `SYSTEM.CNF` et `FUNKIN.EXE` sont aux entrées 1 et 2. L’EXE embarqué extrait du disque a le même SHA-256 que le résultat du lien. BIN final 339 939 264 octets, SHA `DDF9FF1782A6D6286EEB9A427BB33180F739CC20134D74AA2E4D7F67BC338E55`; CUE SHA `5684CE682125CF690946107B8B1F299CC49D6385E6CCB62D7118162CBA5B1E5D`. Livraison hors dépôt : `C:/Users/Manau47/Documents/Codex/ps1-asset-harmonization-v1-delivery/`.

La v1 n’a pas été exécutée dans DuckStation ni sur console. La v183 demeure la référence validée par l’utilisateur; l’essai de la v1 reste en attente.
