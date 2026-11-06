# Week 3 v134 — nouveau décalage vers la gauche du fond ville

## Modification

v134 décale la ville de 27 unités monde supplémentaires vers la gauche par rapport à v133, environ 40,5 pixels écran au zoom 1,5×. Le décalage horizontal total atteint 54 unités monde (~81 pixels) depuis la composition v129. La hauteur v132/v133 et le quai restent inchangés.

## Build

Ressources converties réutilisées, aucune reconversion. `week3-scene.bin` : 524800 octets, SHA-256 `886D0CED3C52B63C2CDEC752D59B78ADCE86894FDA4AFAD17F9F00AFF48B4AED`. Build PSn00bSDK 0.24 / GCC MIPS 12.3 réussi. ISO vérifié : 117 fichiers, `SYSTEM.CNF;1` premier et `FUNKIN.EXE;1` second. BIN 338509248 octets, SHA-256 `838AF71BEFB4543F427715F4C2015934D855D9000BA94BCFDFE8D7C6AF96BEDA`. CUE SHA-256 `FF78750116A72600F7435E17EF6DDCC1A9E722DADC3768B37BAC8C9DAD817445`.

## Validation

Build compilé, pas encore exécuté dans DuckStation ni sur console. Vérifier le décalage, le raccord des tuiles et l’absence de vide; le décor du quai et la hauteur de v132 doivent rester en place.
