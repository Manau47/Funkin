# Poses de chant étendues — v142

## Portée

v142 étend l'échantillonnage des poses de chant officielles aux scènes qui n'utilisaient pas l'atlas BF classique : BF pixel de Week 6, BF de Week 7, puis Pico joueur dans Weekend 1 (Darnell, Lit Up et 2Hot). L'atlas commun qui sert aux Weeks 1 à 5 reste celui de v141. Blazin garde ses poses de combat officielles déjà converties; le traitement de Pico de Weekend 1 ne s'applique pas à cette piste.

Le cadrage, la composition des scènes, le chart, les fenêtres de jugement, l'audio, le score, la vie, les tenues, les fautes et les menus ne changent pas.

## Conversion et sélection des poses

`ps1/augment_week_sing_poses.py` complète les paquets déjà convertis, sans relancer la conversion générale. Il réutilise leurs CLUT 8bpp, ajoute seulement des cels quantifiés à ces palettes, préserve les dimensions/ancres des rigs, et refuse les paquets déjà modifiés ou de taille inattendue.

- Week 6 : deux échantillons additionnels par direction (milieu et fin), joués après la pose initiale à 15 images/s depuis l'horloge audio. Les 12 rendus (4 directions × 3 poses) sont distincts.
- Week 7 : une pose alternative par direction, alternée avec la pose initiale à 15 images/s pendant le chant. Les instants source initial/milieu/fin examinés donnent deux rendus distincts par direction dans le rig épinglé; aucune troisième pose différente n'a été ajoutée artificiellement.
- Weekend 1 : même alternance à deux poses pour Pico joueur sur Darnell/Lit Up/2Hot. Les instants échantillonnés du rig Pico donnent deux rendus distincts. Le rig Darnell et les poses combat Blazin restent inchangés.

La phase est calculée avec les échantillons audio écoulés depuis l'événement de chant. Il n'y a ni compteur d'images indépendant ni modification des événements qui déclenchent les animations.

## Budgets et ressources

Assets officiels épinglés sur `assets` commit `724eba9de9e76761d9cefd52169926bc51c760a5`; atlas, rigs sources et sorties converties restent hors Git. Les nouveaux cels réutilisent les palettes existantes : aucune CLUT supplémentaire.

| Paquet de scène | Avant → après | Variation CD / VRAM de scène | Tampon RAM de chargement |
|---|---:|---:|---:|
| Week 6 | 328 192 → 328 192 octets (5 pages + CLUT) | 0 octet; cel ajoutés dans la moitié libre de la page 4 | 65 536 octets temporaires, inchangé |
| Week 7 | 197 120 → 262 656 octets (3 → 4 pages + CLUT) | +65 536 octets; une page d'acteur supplémentaire chargée pour cette semaine | 65 536 octets temporaires, inchangé |
| Weekend 1 | 524 800 → 524 800 octets (8 pages + CLUT) | 0 octet; cels dans l'espace libre de la page 7 | 65 536 octets temporaires, inchangé |

Les pages restent des ressources de scène chargées à la demande; elles ne sont pas toutes maintenues ensemble en VRAM. Le ring RAM audio reste à 96 Kio, les flux/CD, charts et allocations SPU restent inchangés. Sections ELF v142 : texte 1 019 080, données 2 594, BSS 40 184 octets, total 1 061 858 octets. C'est une mesure statique de l'ELF, pas un relevé du pic de RAM incluant pile/heap/SDK en jeu.

## Reproduction

- Base de travail locale : commit `7057882fa4c481fb878de4cc27d3a827179f7ddd` (v141 local).
- Branche GitHub : `ps1-port`, v141 distant `71f81bc06e5399d7434e5a10f96827c3bcb16dae`; le patch v142 a été appliqué comme enfant de cette révision.
- Assets submodule : commit ci-dessus; source PSn00bSDK 0.24 et GCC MIPS 12.3.0 hors dépôt; CMake 4.5 et Ninja.
- Les répertoires `FUNKIN_PS1_PRECONVERTED_WEEK6_DIR`, `...WEEK7_DIR` et `...WEEKEND1_DIR` pointent vers des copies des paquets v140 déjà convertis. L'augmentation doit être exécutée sur ces copies vierges, jamais sur les répertoires déjà patchés :

```powershell
python ps1/augment_week_sing_poses.py `
  --assets assets `
  --ffmpeg <ffmpeg.exe> `
  --week6 <copie-preconvertie-week6> `
  --week7 <copie-preconvertie-week7> `
  --weekend1 <copie-preconvertie-weekend1>
```

Puis configurer CMake avec les chemins de toolchain et paquets préconvertis, vérifier `cmake --build <build> --target ps1-bopeebo-playable-disc -- -n`, et compiler avec la même cible. Le build v142 a réutilisé le chart/audio et tous les paquets existants; aucun convertisseur général, encodeur audio ni génération de chart n'a été relancé. Diagnostics, planche d'arrow QA, démo scène et options de probes sont désactivés au démarrage.

## Artefacts et état de validation

Build distinct : `ps1/build/v142-all-week-singing/build`; livraison : `ps1/build/v142-week-singing-complete/delivery-rootfix/` (fichiers ignorés par Git, sans remplacement des builds antérieurs).

- BIN : 338 586 864 octets; SHA-256 `98E4AE6C5C5AF8A764FA7727FB567964D522A9470680F8D16A302AD286B1D507`.
- CUE : 90 octets; SHA-256 `BDA46FD0A026D16A0676E12571FB4D6AA20543D022A974902780EE999771D653`.
- ELF : 1 329 324 octets; SHA-256 `16A4DA11A0E16C3377450F99C387B1EC4F37AF1B48AE5303B15D19CC1EE6C250`.
- `W6SCENE.BIN` 328 192 octets, SHA-256 `530A2C47ECB22062DEE1DAC595B1D3DD10DA02A7BDBF6446FCD842E8DB4CDD6A`.
- `W7SCENE.BIN` 262 656 octets, SHA-256 `11881F2D6EDE0FE65774BCF0A4A5636A3EEBD4C6D9DD0C8212A79EAB69C288CC`.
- `WEND1.BIN` 524 800 octets, SHA-256 `7549AD4B68A528B75ED453953531043DACEA2D66C649D78B0A54BC94DA58E72E`.

Compilation PSn00bSDK/GCC et création BIN/CUE réussies. Le réordonnancement ISO produit 117 fichiers visibles avec `SYSTEM.CNF` en entrée 1 puis `FUNKIN.EXE` en entrée 2; l’exécutable extrait est identique à l’exécutable lié. Pas d'exécution DuckStation dans ce tour : le CUE attend l'essai utilisateur. La fluidité des quatre directions et les transitions W6/W7/Weekend1 restent à observer dans DuckStation. Aucun test console réelle.
