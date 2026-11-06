# Week 3 v132 — relever encore le fond ville

## Modification

À la demande de relever le fond d’environ 40 pixels supplémentaires, v132 décale uniquement les deux tuiles de ville de 27 unités monde par rapport à v131, soit environ 40,5 pixels écran au zoom de 1,5×. Le décalage total atteint 58 unités monde (~87 pixels) par rapport à v129. Le quai, le train, les personnages, les caméras, les facteurs de parallaxe et les animations ne changent pas.

## Build et conservation

Les ressources converties sont réutilisées sans reconversion. `week3-scene.bin` reste à 524800 octets, SHA-256 `886D0CED3C52B63C2CDEC752D59B78ADCE86894FDA4AFAD17F9F00AFF48B4AED`. Les builds v128 à v131 restent préservés dans leurs dossiers.

Build PSn00bSDK 0.24 / GCC MIPS 12.3 compilé. Image vérifiée : 117 fichiers, `SYSTEM.CNF;1` en premier et `FUNKIN.EXE;1` en deuxième. BIN 338509248 octets, SHA-256 `24B1ACA08C70A85C21C1C18C6455F7AB0D7C81DCB58A9EC2EF4E2AB2D429DFED`. CUE SHA-256 `D71C375EF3A03FCFF7DFF0D47540C5B5047ACBEB472E70D8FAAE29CBF052D868`.

## Validation

Compilation et vérification du disque réussies. v132 n’a pas été exécutée dans DuckStation ni sur console. L’essai utilisateur doit vérifier le nouveau cadrage, l’absence de vide en bas/aux bords, et la conservation du quai, du train et des animations.
