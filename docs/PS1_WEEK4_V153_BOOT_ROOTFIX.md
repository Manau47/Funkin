# Week 4 v153 — correction du démarrage ISO

## Diagnostic

Après le signalement d’un gel au logo PlayStation, l’inspection du BIN v153 a trouvé `SYSTEM.CNF;1` à la 93e entrée fichier du répertoire racine et `FUNKIN.EXE;1` à la 36e. Le v152 de référence place ces deux fichiers en entrées 1 et 2. Le générateur ISO avait trié les fichiers, malgré l’ordre indiqué dans son XML.

Le contenu de `SYSTEM.CNF` est valide (`BOOT=cdrom:\\FUNKIN.EXE;1`) et l’EXE est présent à LBA 27. Son en-tête `PS-X EXE`, son point d’entrée (`0x80025cbc`), son adresse de chargement (`0x80010000`) et sa taille (`0x000fb000`) correspondent à l’exécutable v153 lié. La fausse piste précédente sur un en-tête d’EXE trop court provenait d’une extraction v153 manquante qui avait réutilisé des octets v152; elle est invalidée par cette vérification directe de l’ISO.

## Correction livrée

Le BIN a été copié et corrigé avec `ps1/diagnostics/reorder_iso_system_cnf.py --exe-after-system-cnf`. Cette opération réordonne uniquement les enregistrements du répertoire ISO et recalcule EDC/ECC des secteurs touchés. Elle ne compile pas et ne modifie aucun contenu de fichier.

- CUE : `ps1/build/week4-composition-v153/delivery-v153-rootfix/funkin-ps1-v153-week4-parallax-rootfix.cue`
- BIN : `ps1/build/week4-composition-v153/delivery-v153-rootfix/funkin-ps1-v153-week4-parallax-rootfix.bin`
- Répertoire racine ISO : LBA 22, 4 secteurs, 117 fichiers.
- Ordre vérifié : `SYSTEM.CNF;1` fichier 1, `FUNKIN.EXE;1` fichier 2.
- Seuls les secteurs racine LBA 22–24 diffèrent du BIN v153 initial; les extents des fichiers restent inchangés.
- `SYSTEM.CNF` SHA-256 : `47F527BE2BB4A755DEE290388416D7133FFD88D6053035D1BF40728D03645A63`.
- `FUNKIN.EXE` SHA-256 : `AFD349249E601DD59AE3FF2242AA0B53C24C3AAC88772EEECA99D5B6B448A732` (identique au build v153).
- BIN corrigé SHA-256 : `1CF2554D7DFEB70221B10EDAC45094CD3D5FCD91755A71631C532D9EFB3C66FB`.
- CUE corrigé SHA-256 : `D9C9FB58E5CBD6762A26C3CE149AD0B74A107A8B7F8BCA4BCCBBF9E39A6DA2B9`.

## Validation

Le contrôle ISO statique confirme l’ordre et l’intégrité des fichiers de boot. Aucun nouveau build logiciel n’a été compilé et DuckStation n’a pas été manipulé. Le démarrage avec ce CUE reste à confirmer par l’utilisateur; aucun test console réelle n’est revendiqué.
