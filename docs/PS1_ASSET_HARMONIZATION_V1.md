# Harmonisation des assets PS1 — v1

Date : 2026-11-08
Branche : `ps1-asset-harmonization-v1`
Référence utilisateur : v183, commit `7057882fa4c481fb878de4cc27d3a827179f7ddd`
Commit parent de cette passe : `b5f22bcc76bb8be8dd06c16f3079412ec9fb9e93`

## But et périmètre de cette version

Cette branche applique la méthode d’harmonisation au nouveau build v1. Elle ne se limite pas à réutiliser les ressources v183 : elle établit un inventaire reproductible des ressources converties, compare les couches source et les frames PS1, puis applique une optimisation **sans perte** au paquet Week 6. La scène W1 v183 est la référence de lisibilité et reste inchangée.

La passe ne change ni les scènes/placements, ni les échelles d’affichage, palettes, couleurs, poses, séquences, cadences, charts, règles de jeu ou audio. Aucun asset officiel brut ni SDK n’est ajouté au dépôt. Les éditeurs temporaires de composition et le mode démo restent désactivés au démarrage comme sur le candidat v1 précédent.

## Référence visuelle W1

La fiche source est dans [`PS1_ASSET_SCENE_AUDIT_V183.md`](PS1_ASSET_SCENE_AUDIT_V183.md). W1 reste le point de comparaison, pas une cible de réduction automatique : scène d’origine à zoom caméra 1,1 ; stageback 2560×1400 en (-600,-200), scale 1, scroll 0,9, z=10 ; stagefront 2560×581 en (-650,600), scale 1,1, scroll 0,9, z=20 ; rideaux 2560×1400 en (-500,-300), scale 0,9, scroll 1,3, z=30.

Exemples de tailles d’images converties dans l’atlas commun/W1 : Dad idle 53×96, GF idle 87×79, BF idle 52×52 texels. Avec les facteurs d’échelle actuels, les rectangles nominaux projetés sont respectivement d’environ 133×240, 218×198 et 130×130 pixels, avant transparence, ancrages, clipping et caméra. Ce sont des calculs de dimensions, pas une mesure de lisibilité en mouvement. Le tableau des frames montre aussi que plusieurs grandes cels officielles sont ajustées dans des canevas PS1 plus petits : cela peut coûter du détail, contrairement au réempaquetage, qui ne modifie pas les texels.

## Fiches et planches reproductibles

Les résultats se trouvent sous `audit/v1/` :

- `source-layer-fiches.csv` : 76 couches des stages épinglés, avec fichier PNG source, dimensions, zoom de caméra, position, échelle, scroll et ordre Z.
- `converted-frame-fiches.csv` : rectangles/cels convertis, dimensions et UV, page, profondeur, CLUT, pixels index 0, boîte opaque, trim/anchor, hash indexé et doublons exacts.
- `final-build/converted-frame-fiches.csv` : mêmes fiches contre les données du build v1 final.
- `final-build/atlases/` : planches annotées par famille (base/W1, Weeks 2–7, Weekend 1), légendes et `atlas-audit.json`.
- `final-build/static/` : planches des pages fixes de menus, titre, Freeplay, DJ, game over et icônes, quand ces données existent dans le build.
- `dedup-pack-simulation.csv` : simulation d’alias exacts; c’est un indicateur de potentiel, pas une preuve qu’un repack complet de chaque atlas tient dans les rôles VRAM actuels.
- `final-build/resource-hashes.csv` : comparaison des artefacts générés v183/v1.

La fiche couche source et la fiche frame convertie sont liées par les labels de la chaîne de génération, mais ne constituent pas encore une trace image-par-image de chaque transformation source. La résolution/rectangle/canevas des atlas officiels animés et les marges alpha sont consultables dans les sources épinglées et les extraits convertis ; les coordonnées affichées exactes de chaque quad dépendent des transformations d’exécution. Elles sont documentées au niveau de la scène dans l’audit v183. Une capture 320×240 de chaque pose animée exigerait une exécution et une mesure de quads en runtime, non réalisées ici.

### Lecture correcte des mesures

- Une page PS1 représente 256×256 texels : 65 536 octets en 8bpp ou 32 768 en 4bpp. Les CLUT sont comptées à part.
- « transparent index 0 » compte des texels, pas de la mémoire libre. « trous » sont les espaces non couverts dans les rectangles; ils ne sont récupérables qu’après repack démontré.
- Les pages de paquets CD sont une mesure de stockage/transfert. Les ressources de toutes les semaines ne sont pas résidentes simultanément en VRAM.
- La VRAM totale est 1 MiB; les deux framebuffers 320×240×16bpp utilisent 307 200 octets. Pages et palettes partagent le reste et sont remplacées entre écrans/scènes.
- Les PNG de planches servent à l’inspection humaine, pas au jeu.

## Optimisation sans perte appliquée : Week 6

Le paquet converti v183 avait 7 pages 256×256 en 8bpp plus une CLUT de 512 octets. La transformation `ps1/repack_indexed_scene.py` conserve les deux premières pages aux mêmes emplacements, puis repacke les rectangles restants en pages compatibles. Elle détecte 13 cels indexées strictement identiques et leur fait partager les mêmes texels; les 77 références/frame IDs et l’ordre des animations restent présents. Palette/CLUT copiée byte-à-byte. Le script relit le paquet produit et compare les pixels source/cible avant de réussir.

| Mesure Week 6 | Référence v183 | v1 | Écart |
|---|---:|---:|---:|
| Pages 8bpp | 7 (458 752 B) | 6 (393 216 B) | −1 page, −65 536 B |
| CLUT | 512 B | 512 B | 0 |
| Paquet CD | 459 264 B | 393 728 B | −65 536 B, soit 32 secteurs de 2 048 B |
| Descripteurs de frames | 77 | 77 | 0 |
| Cels exactes aliasées | — | 13 | texels partagés, aucun changement de séquence/cadence |
| RAM de staging à l’exécution | 65 536 B page + lecture séparée de 2 048 B CLUT | identique | aucun gain RAM |
| Transfert texture vers GPU | 7 pages = 458 752 B | 6 pages = 393 216 B | −65 536 B pour cette scène |

La formule du runtime charge une page par 32 secteurs, puis lit la CLUT après le compteur de pages : Week 6 utilise donc 224 secteurs de texture + 1 secteur de palette dans v183, contre 192 + 1 en v1. Le débit n’est pas mesuré en exécution; ce sont les tailles/offsets statiques du lecteur. Le réempaquetage ne change pas le maximum du tampon page (64 Kio), n’abaisse pas la consommation de framebuffer et ne garantit pas une hausse de framerate.

Le contrôle de la géométrie issue de l’atlas v1 donne 6 pages (393 216 texels alloués), union des rectangles de 291 344 texels, 101 872 texels hors union et 249 782 texels index 0 sur les pages. Les rectangles peuvent se chevaucher lorsqu’ils sont des alias vérifiés; la somme d’aires des références est donc supérieure à l’union. Les pixels transparents conservés ne sont pas déclarés comme gain récupéré.

## Autres groupes et budgets statiques

Seule Week 6 est modifiée dans le contenu converti. Les tailles suivantes sont les paquets v183 réutilisés, avec Week 6 remplacée par sa taille v1 :

| Groupe chargé indépendamment | Pages et format | Paquet CD v1 |
|---|---:|---:|
| Commun + W1 | 9×8bpp + 2×4bpp, CLUTs incluses | 655 360 B |
| W2 | 7×8bpp | 459 264 B |
| W3 | 8×8bpp | 524 800 B |
| W4 | 9×8bpp | 590 336 B |
| W5 Christmas/Mall | 12×8bpp, 6 144 B de CLUT | 792 576 B |
| W6 | 6×8bpp, 512 B de CLUT | 393 728 B |
| W7 | 4×8bpp | 262 656 B |
| Weekend 1 | 9×8bpp | 590 336 B |

Total stockage paquet des scènes listées : 4 269 056 B contre 4 334 592 B v183 (−65 536 B). Cette somme est une mesure disque, pas un ensemble résident. Les pages communes et de scène nécessaires ensemble sont gérées dans les emplacements VRAM partagés; leurs budgets exacts et transferts par transition sont récapitulés dans l’audit v183. Pages 4bpp supplémentaires : seules celles qui conservent exactement chaque couleur après validation palette/index sont éligibles; aucune conversion 8→4bpp nouvelle n’est tentée ici.

RAM code/data/BSS est mesurée via les sections ELF, et non déduite de la taille des images. ELF v1 : text 1 013 048 B, data 2 638 B, BSS 40 120 B (1 055 806 B au total). ELF v183 : 1 008 920 + 2 766 + 40 104 = 1 051 790 B; v1 est donc +4 016 B, sans économie RAM revendiquée. Les PNG sources, outils de conversion et disques restent hors du binaire Git.

## Reproductibilité

Références : dépôt de travail `Funkin`, commit source v183 `7057882fa4c481fb878de4cc27d3a827179f7ddd`; sous-module assets `724eba9de9e76761d9cefd52169926bc51c760a5`. Outils externes : PSn00bSDK 0.24, GCC MIPS 12.3.0, CMake et Ninja. L’archive/SDK ne sont pas dans Git.

Le transformateur prend les BIN/header déjà convertis v183 en entrée; il ne lance pas de conversion PNG/audio/chart :

```powershell
python ps1\asset_harmonization_fiches.py --help
python ps1\repack_indexed_scene.py --help
```

Le build distinct est `C:/Users/Manau47/Documents/Codex/ps1-asset-harmonization-v1-lossless-build/`; son CMakeCache SHA-256 est `09739237C46EAE06A4A165DEA802F05DC8D62415040E5C3917CA68CAF1A4BF68`. Ninja dry-run pour `ps1-bopeebo-playable-disc` a listé quatre actions : compile `spu_probe.c`, compile SDK `cdstream/stream.c`, link ELF, création ISO. Aucune tâche de conversion de ressource. Build réel réussi; deux avertissements `volatile` préexistants dans le `stream.c` du SDK.

L’ISO brut a ensuite été copié dans un dossier distinct et réparé par l’outil existant `ps1/diagnostics/reorder_iso_system_cnf.py` pour conserver `SYSTEM.CNF` en entrée racine 1 et `FUNKIN.EXE` en 2. L’exécutable extrait de l’ISO final a le même hash que le PS-X EXE lié. La référence v183 n’a pas été modifiée. Le détail de la configuration et les hashes se trouvent dans `audit/v1/final-build/build-manifest.csv` et les manifestes voisins.

Livraison hors dépôt : `C:/Users/Manau47/Documents/Codex/ps1-asset-harmonization-v1-lossless-delivery/`.

| Artefact | Taille | SHA-256 |
|---|---:|---|
| BIN final | 339 864 000 B | `87F1B210D1625BB5EED91E82084C94CCB8DC4B28476AF817291806DD5CD0E833` |
| CUE final | 96 B | `476CA379B459A8354FA7E278BB22958435F94775329428ED61AF8A20D31CC1AA` |
| PS-X EXE | 1 017 856 B | `A3F912124738F150A33133FFE27E0BB50A38BFA2785FC37419816A9935712C4E` |
| ELF | 1 388 672 B | `14522567F15C8B69747261E2778062D745E7BB92A927AA437CBF2CB0037B7E49` |
| Week 6 package | 393 728 B | `CBA20A8090A8C54D432405766CB53158D08B49F6A424171A9EEE68F3D46DECCD` |
| Week 6 visual header | 6 758 B | `38F46AE39849053A8F3E37CBEED0BBF5142777E69A8DB4A0F9357D6F7E289150` |

## Ce qui est établi et ce qui reste à tester

**Établi statiquement / à la compilation :** W1 reste byte-identique; 129 des 131 produits `.bin/.vag/.h` comparés sont byte-identiques; les deux différences sont le paquet Week 6 et son header visuel optimisés. Les pixels indexés/couleurs/CLUT de Week 6 sont identiques et tous les UV/descripteurs restent référencés. Le build et les contrôles ISO/EXE ont réussi.

**Non observé dans cette passe :** rendu comparatif des poses dans DuckStation, navigation multi-semaines, retour Freeplay, game over/retry, stabilité audio, performances/framerate et console réelle. v183 reste la version validée par l’utilisateur. La nouvelle v1 est livrée pour essai; ne pas considérer l’optimisation comme validée visuellement avant son retour.

## Étapes suivantes

1. Attendre l’essai manuel de cette v1 et comparer W1 de référence aux poses Week 2–Weekend 1.
2. Ne commencer qu’ensuite la prochaine famille cohérente, avec mêmes fiches avant/après, preuve pixel-identique et mesure des pages réellement utilisables simultanément.
3. Toute amélioration de détail, recadrage, changement de palette ou animation supplémentaire nécessitera une passe distincte et une validation graphique; ce n’est pas inclus dans ce réempaquetage.
