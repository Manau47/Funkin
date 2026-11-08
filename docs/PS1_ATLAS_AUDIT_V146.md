# Audit et compactage lossless des atlas PS1 — v146

Date : 4 novembre 2026. Cette passe établit une base reproductible, inventorie les pages graphiques de toutes les scènes actuellement intégrées et applique un réempaquetage sans perte à Week 4 et Week 7.

## Référence et niveau de validation

- Base locale : commit `7057882fa4c481fb878de4cc27d3a827179f7ddd`, branche `ps1-port`, plus les modifications locales v144/v145 capturées dans `ps1/build/atlas-audit-v146/reference/source/working-tree.diff`. Les fichiers de code/configuration et l’état Git sont copiés dans `reference/source/`.
- L’instantané de build antérieur, son BIN/CUE/ELF/EXE/MAP, la configuration Ninja/CMake et les ressources préconverties sont archivés dans `ps1/build/atlas-audit-v146/reference/`. Les hashes des entrées sont dans `reference/resource-hashes.csv`.
- Révision des assets officiels : `724eba9de9e76761d9cefd52169926bc51c760a5`. Les assets officiels, SDK, paquets convertis, planches et disques restent hors Git.
- La scène v145 est le point de départ de cette passe. L’utilisateur a confirmé le comportement retry; ce comportement et le code de restauration du propriétaire VRAM sont conservés. Les autres scènes et leur rendu v145 ne sont pas déclarés validés par cet audit.
- Les résultats de rendu ci-dessous sont des analyses de fichiers/rectangles et des comparaisons binaires. v146 a été compilé et contrôlé statiquement, mais n’a pas encore été lancé dans DuckStation ni sur console réelle. L’utilisateur chargera le CUE.
- BIN brut de référence v145 archivé : 339 268 944 octets, SHA-256 `733C04E83A0A5411D2DC15D5318CB1FC6FE8DA7F89B63E15DDC02E93AEC4B719`; CUE SHA-256 `8579EEF0E6966AFD78659F364593E560C8384148E9258D14FA88B196A842B340`. Les copies sont sous `reference/outputs-before/`; les livraisons précédentes ne sont pas modifiées.

Les paquets sources exacts sont des sorties préconverties conservées localement, non des ressources Git. W1/W2/W3 viennent de `C:/Users/Manau47/Documents/Codex/week3-pico-bf-spacing-v140/preconverted-base/`; W4 de `ps1/build/week4-scene-v145/preconverted/week4/`; W5/W6/W7/Weekend1 de `ps1/build/v143-animation-pass/preconverted/<week>/`. Leurs hashes avant transformation :

| Entrée | Octets | SHA-256 |
|---|---:|---|
| W1 `week1-scene.bin` | 655 360 | `C2444F178F0A9A7F28B4B24476B9058E74FB15237DDD4BB786907F73A6CD0E8F` |
| W2 `week2-scene.bin` | 459 264 | `BA93EC25BDAEABFDC21AA4BF32D2E7910367517DD4CEF863A3EB9259137F11D4` |
| W3 `week3-scene.bin` | 524 800 | `13EA807953A9AB7E840F81C8E837CC4A8F6EB0F81CECF863E506587D6BB87052` |
| W4 `week4-scene.bin` | 393 728 | `1F178AE8FAD8EC86D4914569050E8EAC070702D6A1B336C56B734CF3679B5360` |
| W5 `week5-scene.bin` | 328 192 | `191A35A90DAC08F791F4831359AB21CFB73BC6B0997B9B9E4BDC787299325C67` |
| W6 `week6-scene.bin` | 459 264 | `9E6842A26C4ABE04D5987B04468223CDDFE4A4B6485A57DC6BB1569C27C9F5C7` |
| W7 `week7-scene.bin` | 328 192 | `3DE49C0009D4936EA32FE42F70E4B410CA6FFCED51E0A100CB36C7879219096E` |
| Weekend 1 `weekend1-scene.bin` | 590 336 | `8C253ACDCCEC577DBAC6D094AC842EFE6B1192E1843A364376D5AE26EC2A091E` |

## Inventaire des planches

Les outils reproductibles sont `ps1/audit_graphic_atlases.py`, `ps1/audit_static_graphic_assets.py` et `ps1/repack_indexed_week_atlas.py`. Ils lisent les conversions déjà produites; aucun outil ne quantifie à nouveau les images.

Les planches des pages/rectangles sont dans `ps1/build/atlas-audit-v146/sheets-after/` : W1/base, Weeks 2–7 et Weekend 1. Les pages statiques empaquetées de titre/menu, Freeplay/DJ, icônes, capsules et game over sont dans `ps1/build/atlas-audit-v146/static-sheets/`. Le HUD, les notes, les tenues, jugements et chiffres utilisés en jeu sont inclus dans la planche indexée de base selon les rectangles de `bopeebo_visual_data.h`.

Les fichiers static sont des cels 8bpp transportés par des tableaux `uint16_t` (deux texels par mot) puis écrits dans une page 8bpp. Les boutons/capsules font 128×36 pixels, les icônes 28×28, les cels de game over 80×96 et les pages menu/DJ 256×256. La feuille de game over est rendue avec sa CLUT propre; le reste utilise la palette 8bpp de base. Pour le contact sheet de la base W1, les indices sont colorés avec une CLUT illustrative unique : le jeu emploie plusieurs CLUT selon les sprites. La feuille n’est donc pas une preuve de couleur runtime.

Résultats du relevé des pages avant → après (surface d’une page 8bpp : 65 536 octets; la CLUT des paquets hebdomadaires ajoute 512 octets au fichier) :

| Ensemble actif | Pages 8bpp livrées | Taille paquet avant → après | Aire de l’union des rectangles de frames |
|---|---:|---:|---:|
| Base W1 / ressources communes | 9 pages 8bpp + 2 pages 4bpp | 655 360 → 655 360 o | 564 255 texels sur les 11 pages; la table contient aussi des descriptors W2/W3 |
| Week 2 | 7 | 459 264 → 459 264 o | 357 794 texels |
| Week 3 | 8 | 524 800 → 524 800 o | 476 391 texels; la page BF W1 est restaurée séparément si le game over l’écrase |
| Week 4 | **6 → 5** | **393 728 → 328 192 o** | 268 882 texels, inchangés |
| Week 5 | 5 | 328 192 → 328 192 o | 290 816 texels |
| Week 6 | 7 | 459 264 → 459 264 o | 329 364 texels |
| Week 7 | **5 → 4** | **328 192 → 262 656 o** | 262 144 texels, inchangés |
| Weekend 1 | 9 | 590 336 → 590 336 o | 501 760 texels |

Les valeurs de surface sont l’union des rectangles définis par les frames, pas une mesure de pixels opaques visibles. Les pixels d’index zéro sont comptés séparément par le CSV. Les rectangles d’animations peuvent se chevaucher dans le temps; la somme de leur aire compte ces répétitions. Les trous entre rectangles et l’espace hors de leur union sont également indiqués dans `atlas-pages.csv`; des trous dispersés ne représentent pas une page libérable. Les scènes W2/W3 réutilisent la table de descripteurs combinée de la base et sont filtrées par préfixe.

L’analyse statique ne supprime pas une frame uniquement parce qu’elle ressemble à une autre : plusieurs poses identiques peuvent encoder une cadence ou un temps de maintien intentionnel. Elle n’affirme pas qu’une ressource est inutilisée sans preuve de chemin d’exécution. Aucun UV invalide n’a été relevé dans les atlas passés au scanner. Les doublons détectés sont listés dans le JSON; ils sont conservés car leur mutualisation modifierait les tables de séquences et n’est pas nécessaire pour récupérer une page entière dans cette passe.

## Changements sans perte

Le réempaqueteur conserve les pages de décor 0 et 1 octet pour octet. Il replace les rectangles des poses dans les pages personnage disponibles, sans rotation ni padding ajouté, puis met à jour uniquement page/U/V dans les descripteurs. Largeur/hauteur, texels indexés, CLUT, ordre des poses, nombre de poses et durées restent identiques.

| Scène | Frames comparées | Pages décor byte-identiques | Texels de chaque frame identiques | CLUT identique |
|---|---:|---|---|---|
| Week 4 | 26 | oui, 2 | oui | oui |
| Week 7 | 32 | oui, 2 | oui | oui |

Week 4 passe de quatre pages personnages à trois pages compactées; Week 7 passe de trois pages personnages à deux. Les manifests détaillés et les SHA-256 par frame sont dans les fichiers `week4-repack-report.json` et `week7-repack-report.json` sous `ps1/build/atlas-audit-v146/optimized/`.

Aucune réduction de dimensions, couleur, pose ou durée n’est faite. Aucun changement gameplay, chart, audio, caméra, ancrage ou composition n’est inclus. Aucun nouveau streaming graphique ni lecture concurrente avec la musique n’est ajouté.

## Budgets statiques

### RAM principale

`mipsel-none-elf-size -A` sur l’ELF v146 donne : `.text` 93 716 o, `.rodata` 928 608 o, `.data` 2 112 o, `.sdata` 514 o, `.sbss` 492 o, `.bss` 39 692 o, `.ctors/.dtors` 16 o. Les sections chargées et le BSS totalisent **1 065 150 octets**. Le PS-X EXE fait 1 028 096 octets. Ce calcul ELF n’est pas une mesure de mémoire libre runtime.

Les tableaux statiques des écrans menu/DJ, boutons, capsules, icônes et 22 frames de mort représentent 644 528 octets de données graphiques empaquetées dans l’image. Les paquets de scènes sont lus vers un tampon de staging de 65 536 octets; il est libéré avant le démarrage du stream. Une chart est allouée pour le morceau actif (taille arrondie au secteur, inchangée). Le FIFO de streaming audio reste 98 304 octets et n’est créé qu’après les chargements de scène. Le compactage W4/W7 ne crée aucune allocation RAM additionnelle; le header de frames conserve son nombre de lignes et des dimensions inchangées. Le pic heap/stack runtime n’a pas été mesuré.

### VRAM et CLUT

Carte physique : 1 048 576 octets, 1024×512 texels à 16 bpp. Les deux framebuffers 320×240 occupent 307 200 o. Les 9 pages de texture 8bpp réservent 589 824 o; les 2 pages 4bpp, 65 536 o; la zone CLUT disponible (x=0..319, y=480..511), 20 480 o. Cette carte ne change pas. Les semaines remplacent des slots partagés, elles ne s’ajoutent pas toutes simultanément. L’index 8bpp utilise une CLUT 256×16bpp (512 o); 4bpp utilise 16×16bpp (32 o). Les palettes restent cohérentes avec leurs pixels indexés et sont chargées/restaurées via le propriétaire de scène existant.

Les deux pages compactées par scène récupèrent réellement un slot de texture lors de W4 et W7 : une page de 65 536 o chacune, sans changer l’adresse des framebuffers ni les autres slots. Cela ne promet pas une hausse de framerate. Le tampon de staging reste à 64 Kio : la page récupérée en VRAM ne libère pas cette RAM.

### CD et transfert GPU par scène

Les chiffres GPU sont le volume de pages envoyé par `LoadImage`, plus la même CLUT qu’avant. La lecture CD de palette est arrondie au secteur de 2 048 octets. Les chiffres sont calculés depuis les tailles des paquets et le chargeur; aucun compteur runtime n’a mesuré ces volumes.

| Transition vers la scène | Paquet scène | Pages envoyées | Lecture CD calculée pages + secteur CLUT |
|---|---:|---:|---:|
| W2 | 459 264 o | 458 752 o + CLUT | 460 800 o |
| W3 | 524 800 o | 524 288 o + CLUT | 526 336 o |
| W4 | 393 728 → 328 192 o | 393 216 → 327 680 o + CLUT | 395 264 → 329 728 o |
| W5 | 328 192 o | 327 680 o + CLUT | 329 728 o |
| W6 | 459 264 o | 458 752 o + CLUT | 460 800 o |
| W7 | 328 192 → 262 656 o | 327 680 → 262 144 o + CLUT | 329 728 → 264 192 o |
| Weekend 1 | 590 336 o | 589 824 o + CLUT | 591 872 o |

Les lectures de scène sont terminées avant le stream musical. Dans cette passe, les volumes W4/W7 diminuent chacun de 65 536 o CD et de 65 536 o de transfert page GPU. Le gain disque combiné dans le paquet ISO est 131 072 octets utiles; l’image raw BIN diminue de 150 528 octets (64 secteurs bruts de 2 352 octets), en raison du rangement par secteurs. Les autres transitions sont inchangées.

## Construction et livraison

Référence : PSn00bSDK 0.24, GCC MIPS 12.3, CMake/Ninja, configuration Debug; diagnostics et planche de flèches par défaut OFF. Le CMake réutilise les pages base/W2/W3, W5/W6/Weekend1 existantes et les sorties W4/W7 produites par le réempaqueteur. Le dry-run avant compilation ne planifiait que compilation de `spu_probe.c`, édition de liens et création du disque. La compilation réelle a terminé avec succès; le dry-run suivant était « no work to do ». Aucun convertisseur de scène, d’audio ou de chart n’a été lancé.

Contrôle statique du BIN final : 119 entrées; `SYSTEM.CNF;1` est la première entrée fichier du répertoire racine et `FUNKIN.EXE;1` la seconde. L’EXE extrait est identique au PS-X EXE lié (1 028 096 octets). W4SCENE/W7SCENE extraits sont identiques aux paquets réempaquetés. Comparé au BIN v145 archivé, seuls le répertoire ISO, `FUNKIN.EXE`, `W4SCENE.BIN` et `W7SCENE.BIN` diffèrent; les autres 114 ressources fichier sont identiques. Le retry reste dans le code de départ et n’a pas été modifié.

- BIN : `ps1/build/atlas-audit-v146/delivery-v146-lossless-atlases/funkin-ps1-v146-atlas-audit.bin`, 339 118 416 octets, SHA-256 `75E847F31D78562F1325AF72EEFE6561DADC576058C9372F9A45DA1CB3948EDD`.
- CUE : `ps1/build/atlas-audit-v146/delivery-v146-lossless-atlases/funkin-ps1-v146-atlas-audit.cue`, SHA-256 `A0D761A136FCB48E293118636F5FD4D281F926689840BC4B9307E7232E408460`.
- EXE : 1 028 096 octets, SHA-256 `C11C19CF363980F35DEF528536660C3CC33FDB496851B6216FB99C3891788CD0`.
- Paquet W4 : 328 192 octets, SHA-256 `9D1A67E8661B1C9A505442057871D83D0B1807B2AF7BE60BE75CF6486BD8D296`.
- Paquet W7 : 262 656 octets, SHA-256 `6051693C36347AF28FC7837747EE8E94F41D0883E4B3C9A4D4448CAB9AE978CC`.

Les sorties v145 et le BIN/CUE brut antérieur sont préservés dans leurs dossiers précédents et dans `reference/outputs-before/`. Les sorties v146 et les planches restent ignorées par Git; seuls les scripts et la documentation sont publiés pour reproduire l’audit et l’empaquetage.

## Essais à faire

À comparer par l’utilisateur dans DuckStation : poses/couleurs/tailles/placements W4 et W7, puis Week 3/4, changements entre plusieurs semaines, retour Freeplay, Game Over et retry. Vérifier que les palettes se restaurent et que le streaming conserve son comportement. Le CUE v146 n’a pas été exécuté ici; aucune stabilité audio ou visuelle runtime n’est affirmée. Aucun test sur console réelle.

## Reproduction des planches et des paquets

Les chemins de préconversion précis et le cache sont conservés sous `ps1/build/atlas-audit-v146/reference/` et `reference/config/`. Exemple de réempaquetage avec les sources externes préconverties inchangées :

```powershell
python ps1/repack_indexed_week_atlas.py --week 4 --header ps1/build/week4-scene-v145/preconverted/week4/week4_visual_data.h --package ps1/build/week4-scene-v145/preconverted/week4/week4-scene.bin --out-dir ps1/build/atlas-audit-v146/optimized-rerun/week4
python ps1/repack_indexed_week_atlas.py --week 7 --header ps1/build/v143-animation-pass/preconverted/week7/week7_visual_data.h --package ps1/build/v143-animation-pass/preconverted/week7/week7-scene.bin --out-dir ps1/build/atlas-audit-v146/optimized-rerun/week7
```

Le réempaqueteur refuse d’écraser des sorties existantes : choisir un nouveau dossier de sortie pour chaque reproduction. Le lancement de `audit_graphic_atlases.py` exige les paquets W1/W2/W3 et les headers/paquets W4–WEnd1 tels qu’ils sont listés dans son `--help`. Les pages fixes se rendent avec `audit_static_graphic_assets.py --header <header base préconverti> --out <dossier>`.
