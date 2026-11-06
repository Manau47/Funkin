# Week 3 v131 — remonter davantage le fond ville

## Modification

Après le premier ajustement v130 (+12 px écran environ), le retour indique que la ville reste trop basse. v131 relève les deux tuiles du fond de 23 unités monde supplémentaires, soit environ 34,5 pixels écran au zoom 1,5×. Le décalage total atteint 31 unités monde (~46,5 pixels) par rapport à v129. Le quai, le train, les personnages, les caméras et le facteur de parallaxe ne changent pas.

## Build et conservation

Build séparé dans `ps1/build/week3-v131-city-raise-cmake/`; ressources converties réutilisées, aucune nouvelle conversion. `week3-scene.bin` reste inchangé (524800 octets, SHA-256 `886D0CED3C52B63C2CDEC752D59B78ADCE86894FDA4AFAD17F9F00AFF48B4AED`). v128, v129 et v130 restent préservées dans leurs dossiers distincts.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 réussie. Le disque contrôlé contient 117 fichiers, avec `SYSTEM.CNF;1` puis `FUNKIN.EXE;1`. BIN : 338509248 octets, SHA-256 `0ABC1392884DA8A352253417A65C6736632340D00A4361201CB3EAC7C75B6A5E`. CUE SHA-256 `21DEA8C78B05242B27F5ACFBB7F2BAB560B08E2C4644AFB246E260E77E9FC35D`.

## Vérification

Compilation et contrôle/réordonnancement du disque réussis. v131 n’a pas été exécutée dans DuckStation ni sur console. L’essai utilisateur doit vérifier la hauteur de la ville, l’absence de vide, et que le quai, les chanteurs, le train, les lumières et les cheveux de GF restent corrects.
