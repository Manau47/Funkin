# Week 3 v133 — décaler le fond ville vers la gauche

## Modification

À la hauteur approuvée sur v132, le fond ville est décalé de 27 unités monde vers la gauche, soit environ 40 pixels écran au zoom de 1,5×. Les deux tuiles arrière restent jointives. Leur parallaxe, leur hauteur, le quai, le train, les personnages et les caméras sont inchangés.

## Build et conservation

Les ressources converties sont réutilisées sans reconversion; `week3-scene.bin` reste à 524800 octets, SHA-256 `886D0CED3C52B63C2CDEC752D59B78ADCE86894FDA4AFAD17F9F00AFF48B4AED`. v128 à v132 restent dans leurs dossiers respectifs.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 réussie. Image contrôlée : 117 fichiers, `SYSTEM.CNF;1` en premier, `FUNKIN.EXE;1` en deuxième. BIN 338509248 octets, SHA-256 `BE624E13B1BB7D6B92A584AC84E83CB59F8B191260EF85D2D052186DA33EEABF`. CUE SHA-256 `4E0907DC9772E6E465DF7B1B23BD62C7FADF0EFEFD57262145EBB070163C11FC`.

## Validation

v133 est compilée mais n’a pas été exécutée dans DuckStation ni sur console réelle. L’essai utilisateur doit confirmer le décalage horizontal, le raccord des deux tuiles et l’absence de vide, ainsi que la hauteur v132.
