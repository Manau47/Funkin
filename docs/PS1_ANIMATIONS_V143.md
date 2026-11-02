# Animations des semaines tardives — v143

## But et périmètre

Cette passe répond au retour selon lequel les GF des semaines suivantes semblaient limitées à deux poses et plusieurs adversaires paraissaient rigides. Elle étend les cycles officiels de danse, d’attente et de chant pour Weeks 4 à 7 et Weekend 1, en conservant les scènes déjà présentes.

Weeks 1 à 3 ne sont pas reconverties : GF y possède déjà ses cycles audio de dix cels, ainsi que le cycle spécifique des cheveux de Week 3 au passage du train. Dad, les Spooky Kids, Monster et Pico disposent déjà de poses d’attente et de chant définies dans le paquet et le renderer. Leur rendu reste inchangé. Les poses BF v141/v142 sont conservées. Weekend 1 classique ne présente pas GF dans la composition portée; cette passe anime Pico et Darnell sur Darnell/Lit Up/2Hot. Blazin garde ses poses de combat. Spirit n’a pas de poses supplémentaires distinctes exploitables dans son rig empaqueté.

Aucune caméra, composition, taille d’affichage, chart, règle de jeu, audio, SFX, menu ou flux CD n’est modifié. Les sélections utilisent `music_beat_q16()` calculé depuis l’horloge d’échantillons audio, pas un compteur d’images.

## Changements

| Scène | Cels ajoutés | Sélection dans le renderer | Paquet avant → après |
|---|---:|---|---:|
| Week 4 | GF danse +8; Mom idle +2 et chant alternatif +4 | GF 10 cels répartis sur les deux côtés; Mom alterne les poses de chant et parcourt 3 idles | 197 120 → 262 656 o; +1 page |
| Week 5 | GF +8; Parents +9; Monster +6 | GF 10 cels; Mom/Dad et Monster alternent leurs poses de chant; idles parcourus sur le beat | 197 120 → 328 192 o; +2 pages |
| Week 6 | GF +8; Senpai et Angry Senpai +10 | GF 10 cels; Senpai alterne 2 poses de chant et 2 idles; Spirit garde la pose disponible | 328 192 → 459 264 o; +2 pages |
| Week 7 | GF +8; Tankman +6 | GF 10 cels; Tankman a 2 poses de chant et 3 idles | 262 656 → 328 192 o; +1 page |
| Weekend 1 | Pico +6; Darnell +6 | Pico a 3 poses de chant/3 idles; Darnell a 2 poses de chant/3 idles | 524 800 → 590 336 o; +1 page |

Les nouvelles images viennent des rigs/atlas officiels épinglés, sont ajustées aux ancres des poses existantes, puis quantifiées avec la CLUT 8bpp de chaque paquet. Aucune palette supplémentaire n’est chargée. Le script refuse une taille de paquet inattendue ou une seconde augmentation.

## Budgets

Les paquets ajoutent sept pages 8bpp de 256×256 au total, soit 458 752 octets sur disque. Une seule scène de semaine est chargée à la fois; l’augmentation VRAM par niveau actif est de 64, 128, 128, 64 et 64 Kio. La plus grande scène de cette passe est Weekend 1 : 590 336 octets (9 pages + CLUT 512 octets).

Le tampon de lecture de scène de 65 536 octets est réutilisé; aucune allocation RAM persistante n’est ajoutée pour les cels. Les descripteurs ajoutent du code/données statiques. Le nouvel ELF mesure 1 335 560 octets sur disque; ce n’est pas une mesure du pic RAM en jeu. Aucun transfert SPU, son ou stream supplémentaire.

## Sources et reproduction

- Assets officiels : sous-module `assets` épinglé à `724eba9de9e76761d9cefd52169926bc51c760a5`; originaux et sorties préconverties restent hors Git.
- Convertisseur ciblé : `ps1/augment_week_animations_v143.py`; renderer : `ps1/spu_probe.c`.
- Les paquets convertis ont été copiés sous `ps1/build/v143-animation-pass/preconverted/`, augmentés une fois avec leur CLUT existante, puis assemblés par CMake. Pas de conversion générale.
- Build : `ps1/build/v143-animation-pass/build`, cible `ps1-bopeebo-playable-disc`; PSn00bSDK 0.24, GCC MIPS 12.3, CMake/Ninja.
- Dry-run final Ninja : aucune tâche restante.
- Le BIN brut de CMake est conservé. La copie livrée corrige uniquement l’ordre du répertoire racine ISO avec `ps1/diagnostics/reorder_iso_system_cnf.py`, car `SYSTEM.CNF` était en entrée 93. L’image livrée place `SYSTEM.CNF` en premier et `FUNKIN.EXE` en deuxième; le contenu des fichiers n’est pas altéré.

## Résultat et validation

Build PSn00bSDK/GCC réussi et image statiquement contrôlée; l’ISO contient 117 fichiers.

- CUE : `ps1/build/v143-animation-pass/delivery-v143-week-animations-rootfix/funkin-ps1-v143-week-animations.cue`.
- BIN : 339 116 064 octets; SHA-256 `0D48786850065B0018E9AAAC3BBEEC51651262F94E270E7EAE9F245CB25DC8AD`.
- CUE SHA-256 : `6CDFC57781348025AD36D8A2F86732D762E04114F94CF8B1C5E12B1D8294FE7A`.
- ELF lié : 1 335 560 octets; SHA-256 `848F6E25FC92241D2060A514646EF28FEEB2FB3DB1D8A84CE9E227D37E0DC672`.

DuckStation n’a pas été exécuté par Codex. La fluidité, les retours idle, la lisibilité, les transitions/retry et l’absence d’underrun doivent être vérifiés par l’utilisateur. Aucune validation utilisateur de v143 ni aucun test console réelle n’est revendiqué.

