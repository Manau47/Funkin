# v139 — correction palette de base et ancrages Week 3

## Problèmes visés

Les captures de l’utilisateur montraient des couleurs incorrectes sur GF au titre, l’option Options et des éléments de Tutorial/Bopeebo, ainsi qu’un cadrage Pico incohérent en Week 3. Ce build corrige deux causes trouvées dans le code et l’en-tête converti; aucune validation visuelle utilisateur n’est encore acquise.

## Causes établies

- L’en-tête v138 remplaçait la CLUT de base alors que des pages W1 préconverties restaient inchangées. 240 des 256 couleurs de la CLUT 8bpp différaient du jeu de ressources v129b correspondant. Des indices de pixels étaient donc interprétés avec des couleurs différentes. La cause est un mélange de génération globale récente et de pages réutilisées, pas une saturation de palette au runtime.
- La source locale approuvée pour le graphisme Options n’était pas présente; le convertisseur avait utilisé une image officielle de secours. La fusion restaurée conserve les données menu de la base préconvertie connue.
- L’ancrage de cels recadrés Pico/GF dépendait de tests de plages numériques. L’ordre des descripteurs n’était pas monotone pour ces plages, donc certaines poses n’utilisaient pas leur ancrage voulu.

## Changement

`ps1/merge_week3_animation_header.py` fusionne l’en-tête W3 nouvellement converti sur l’en-tête de base v129b, mais ne remplace que les métadonnées/descripteurs `week3_*`. Il vérifie que les pages et les données de CLUT restent identiques et que les frames non W3 sont préservées. `BopeeboVisualFrame.anchor` distingue explicitement les ancrages Pico et GF; le rendu n’essaie plus de déduire l’identité à partir d’un intervalle de numéro de frame.

Le paquet W3 réutilisé et ses nouvelles poses demeurent hors Git. La copie antérieure de l’en-tête v138 est conservée dans le dossier de build sous le suffixe `.v138-palette-mismatch`. Aucun asset officiel ni SDK n’est ajouté au dépôt.

## Compilation et disque

- Outil : PSn00bSDK 0.24, GCC MIPS 12.3, CMake/Ninja Windows.
- Le dry-run de `ps1-bopeebo-playable-disc` ne prévoyait que compilation de `spu_probe.c`, édition de liens et génération du disque; pas de conversion de sprites, chart ou audio.
- Compilation incrémentale réussie. Les contrôles statiques du script de fusion confirment CLUT, pages et descripteurs de base identiques, et les nouveaux frames W3 présents.
- BIN : 338 509 248 octets, SHA-256 `AF7390FD068FAA46D5DA0E18D390A8B2ED294E6E6965F9BFC91182F77112A40F`.
- CUE : SHA-256 `BF60EF5FC7517B3DF32AC5BC0C7DB3BC4DC619AC983160B4D559624F1BC068A6`.
- Fichiers : `ps1/build/week3-animation-compromise-v138/delivery-v139-palette-anchor-correction/funkin-ps1-v139-palette-anchor-fix.cue` et `.bin`.

## À vérifier par l’utilisateur

Charger le CUE dans DuckStation et vérifier : écran titre/Options, Tutorial, Bopeebo, puis Week 3 et les positions Pico/GF durant les poses et le passage du train. Le parcours complet et les transitions ne sont pas observés par Codex. Ce résultat est une compilation et une validation statique, pas une validation DuckStation ni console réelle.



## Correctif de démarrage du disque (v139b)

Le CUE v139 initial restait au logo Sony. L’audit a isolé l’écart ISO : `SYSTEM.CNF;1` était la 93e entrée racine au lieu de la première, contrairement au disque v138 fonctionnel. La directive boot, le CUE et l’exécutable étaient corrects. Le BIN v139 initial est conservé mais ne doit pas être utilisé pour l’essai.

v139b réordonne uniquement les enregistrements du répertoire racine du BIN brut avec `ps1/diagnostics/reorder_iso_system_cnf.py --exe-after-system-cnf`; aucun exécutable ni asset n’a été recompilé/reconverti. Vérifications statiques : 117 fichiers, `SYSTEM.CNF;1` en première position, `FUNKIN.EXE;1` en deuxième, directive `BOOT=cdrom:\\FUNKIN.EXE;1`. L’exécutable extrait (1 021 952 octets) est byte-identique à celui du v139 initial, SHA-256 `54131AB733936A82676EFE91CE7D9B3D0771EEA32C883B68CDA8788AC70D727D`.

À tester : `ps1/build/week3-animation-compromise-v138/delivery-v139b-iso-boot-order/funkin-ps1-v139b-boot-order-fix.cue`. BIN SHA-256 `0E9F1852D97F89F2771AA6AC9196214EE55C3374D2F81B2FEFF4320EE3410B5F`; CUE SHA-256 `AAE35D9F4730932B0D2EE363D4B99761C71422846A8ED1FB0CDE4004D90BD3E6`. Le boot reste à confirmer par l’utilisateur dans DuckStation.
