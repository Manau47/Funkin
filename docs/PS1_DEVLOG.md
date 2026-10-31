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
