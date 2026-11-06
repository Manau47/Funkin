# Week 3 v140 — espacement Pico/BF

## Modification

Pico est décalé de 10 unités monde vers la gauche et BF de 10 unités vers la droite. À 1,5×, l’écart horizontal des centres augmente d’environ 30 px. Les tailles, poses, ancrages, piste, arrière-plan et rythme restent inchangés.

Les offsets caméra sont compensés afin de garder exactement les mêmes cibles de focus : Pico `x=111`, BF `x=137` avant et après. La caméra ne se déplace donc pas davantage et le fond/parallaxe garde sa composition. Positions monde avant → après : Pico `78→68`, BF `170→180`; offsets caméra X : Pico `33→43`, BF `−33→−43`.

Le calcul est désormais dans `ps1/convert_bopeebo_visuals.py`. Le paquet v139b a été copié en staging hors Git, et seules les quatre macros concernées de l’en-tête ont été modifiées. Les conversions d’images, chart/audio et tous les autres paquets ont été réutilisés.

## Build / vérifications

- PSn00bSDK 0.24, GCC MIPS 12.3, CMake/Ninja.
- Dry-run : compilation de `spu_probe.c` et `stream.c`, édition de liens, génération ISO. Aucun convertisseur d’assets/chart/audio n’est lancé.
- Compilation réussie; ISO 117 fichiers, `SYSTEM.CNF;1` en entrée 1 et `FUNKIN.EXE;1` en entrée 2.
- Comparaison du contenu ISO v140 avec v139b : seul `FUNKIN.EXE;1` diffère; les 116 autres fichiers sont byte-identiques. `W3SCENE.BIN;1` et `BOPN.BIN;1` sont notamment identiques.
- BIN : 338 509 248 octets, SHA-256 `C691A74571FEFE2587C5DEA56C284C868DC9EB535143FDCD961528404B470E6A`.
- CUE SHA-256 `B9CC1B288089DF4CD0C0BFA5053A2AC6589F85F1BE839C4A255E2D0AE66A32E7`.
- Livraison : `ps1/build/week3-pico-bf-spacing-v140/delivery-v140-pico-bf-spacing/`.

DuckStation n’a pas encore été utilisé pour ce build. À vérifier par l’utilisateur : espacements pendant les focus Pico et BF, transitions de caméra, scène/parallaxe et piste. Aucun résultat console réelle n’est revendiqué.

