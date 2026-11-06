# Week 3 v135 — décaler encore le fond ville vers la gauche

## Modification

v135 ajoute 20 unités monde de décalage horizontal à gauche par rapport à v134, environ 30 pixels écran au zoom 1,5×. Le décalage total depuis v129 est de 74 unités monde (~111 pixels). La hauteur approuvée et le placement du quai restent inchangés.

## Build et conservation

Aucune ressource n’a été reconvertie; `week3-scene.bin` reste identique à 524800 octets, SHA-256 `886D0CED3C52B63C2CDEC752D59B78ADCE86894FDA4AFAD17F9F00AFF48B4AED`. Build PSn00bSDK 0.24 / GCC MIPS 12.3 réussi. Image contrôlée : 117 fichiers, `SYSTEM.CNF;1` premier, `FUNKIN.EXE;1` second. BIN 338509248 octets, SHA-256 `AD0E8A58C54B59717AB90A2B72090BF2FFF78AF3AF4F238FB182FB6BADF82E23`. CUE SHA-256 `89B42CA537E16FB2ACFF8365215311C36B29CFAE55C60291A10D06068683374E`.

## Validation

La compilation et les contrôles disque sont réussis. v135 n’a pas été exécutée dans DuckStation ni sur console. L’essai doit contrôler que le fond n’est pas trop rogné et que les tuiles restent raccordées.
