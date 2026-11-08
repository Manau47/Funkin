# v149b — correction de l’ordre de démarrage ISO

## Diagnostic du gel au logo Sony

L’utilisateur a signalé que le CUE v149 restait au logo Sony/PlayStation. La comparaison statique avec le disque v148 montre la cause : dans le répertoire ISO v149, `SYSTEM.CNF;1` était la 93e entrée fichier (95e en comptant `.` et `..`), alors que le disque v148 fonctionnel place `SYSTEM.CNF;1` au début des entrées fichier, suivi de `FUNKIN.EXE;1`. Le contenu de `SYSTEM.CNF` et l’exécutable v149 étaient présents et valides; l’ordre des fichiers au démarrage BIOS était la différence établie.

## Correction isolée

v149b repart du BIN v149 déjà livré et exécute uniquement `ps1/diagnostics/reorder_iso_system_cnf.py --exe-after-system-cnf`, vers un nouveau dossier. Aucune compilation, conversion de ressources, modification de code, ni écriture audio/graphique n’a eu lieu. Les BIN/CUE v149 d’origine restent intacts.

Le répertoire ISO corrigé place `SYSTEM.CNF;1` en entrée fichier 1 et `FUNKIN.EXE;1` en entrée fichier 2 (entrées physiques 3 et 4 en incluant `.` et `..`). `SYSTEM.CNF` contient toujours `BOOT=cdrom:\FUNKIN.EXE;1`, `TCB=4`, `EVENT=10`, `STACK=801FFFF0`. L’EXE extrait est identique octet pour octet à v149, 1 028 096 octets, SHA-256 `3ce926cb2571d30ad024d24d0abc48095857f45b10aec6d6b5a3089e1a32a249`, signature `PS-X EXE`, load `0x80010000`, PC `0x800254d8`, text `0xfa800`.

Le contrôle du réordonnanceur et la comparaison binaire confirment que seuls les quatre secteurs Mode 2 contenant les deux secteurs logiques du répertoire racine ont changé; tous les autres octets de l’image sont identiques à v149.

## Fichiers et validation

- CUE d’essai : `ps1/build/week4-composition-v149/delivery-v149b-iso-rootfix/funkin-ps1-v149b-rootfix.cue`
- BIN : `ps1/build/week4-composition-v149/delivery-v149b-iso-rootfix/funkin-ps1-v149b-rootfix.bin`
- BIN SHA-256 : `D598744889539E395EF5E93F2D78F898F9473DF1DF2D448CE09DF3F6BDBAC896`
- CUE SHA-256 : `2F3A334C9FEE42FAB0EA91563CDCDEC736847A0F190D5E800F72CD27123A4D1F`

La correction d’ordre est vérifiée statiquement; le démarrage de v149b dans DuckStation reste à confirmer par l’utilisateur. Aucun test console réelle n’est revendiqué. Si v149b dépasse le logo Sony, cela confirmera le diagnostic de démarrage; il faudra ensuite vérifier la scène et les animations séparément.
