# Harmonisation des assets PS1 — v1 corrigée

Date : 2026-11-08
Branche : `ps1-asset-harmonization-v1`
Base validée par l’utilisateur : v183, commit `7057882fa4c481fb878de4cc27d3a827179f7ddd`
Assets épinglés : `724eba9de9e76761d9cefd52169926bc51c760a5`

## Périmètre réellement livré

Cette v1 applique l’audit global demandé, avec deux réempaquetages sans perte : **Week 2 et Weekend 1**. W1 est conservée sans modification comme référence de lisibilité. W3, W4, W5, W6 et W7 restent strictement aux données converties v183. Un premier candidat de travail avait réempaqueté W6 ; cette cible était hors périmètre et a été abandonnée. Le BIN/CUE livré ici ne contient pas ce changement W6 : son paquet et son header sont restaurés byte pour byte depuis v183.

Aucune taille affichée, palette, couleur, pose, durée d’animation, composition, ancrage, caméra, chart, règle de jeu ou donnée audio n’est changée. Les cels indexées identiques sont mutualisées sans supprimer de descripteur ni raccourcir de séquence. Aucun fichier source officiel ni SDK propriétaire n’est ajouté à Git.

## Référence W1 et couverture de l’audit

W1 demeure la référence visuelle inchangée. Les fiches source et converties, planches d’atlas par paquet, données statiques des menus/HUD et l’audit des budgets sont conservés sous `audit/v1/`. Elles recensent la résolution source, canevas, trims, UV/pages, CLUT, transparence, doublons et transformations de scène disponibles. Les captures de planches sont des outils d’inspection, pas des ressources de jeu.

La simulation de réempaquetage est dans `audit/v1/corrected-build/repack-simulation.csv`. Elle indique une page de moins pour W2 et Weekend 1 ; W3/W4/W5/W7 n’ont pas de réduction estimée par cette stratégie et ne sont pas modifiées. Les fiches de frames et les planches annotées de toutes les pages du build corrigé sont sous `audit/v1/corrected-build/atlases/`. Les tableaux d’occupation et de transparence sont recalculés depuis les pages réellement empaquetées. Le rapport de chaque paquet documente le contrôle pixel indexé et CLUT. Le script reproductible `ps1/repack_lossless_scene.py` ne convertit pas les PNG et refuse d’écraser les sorties.

## Résultats statiques des deux paquets modifiés

| Paquet | Pages 8bpp avant → après | Descripteurs | Cels exactes mutualisées | Paquet CD avant → après | Gain |
|---|---:|---:|---:|---:|---:|
| W2 | 7 → 6 | 45 conservés | 2 | 459 264 → 393 728 B | 65 536 B / 32 secteurs |
| Weekend 1 | 9 → 8 | 48 conservés | 3 | 590 336 → 524 800 B | 65 536 B / 32 secteurs |

Pages actives du build corrigé par ensemble : W1 = 9 pages 8bpp + 2 pages 4bpp ; W2 = 6 pages 8bpp ; W3 = 8 ; W4 = 9 ; W5 = 12 ; W6 = 7 ; W7 = 4 ; Weekend 1 = 8. Chaque semaine est chargée indépendamment. Les CLUT sont comptées à part dans les fiches ; le framebuffer PS1 reste hors de ces nombres.

Les deux pages de scène fixes restent épinglées à leurs emplacements initiaux. Les autres cels sont réempaquetées avec des UV/pages actualisés ; le vérificateur recopie et compare chaque rectangle d’indices source/cible, et confirme que la CLUT finale reste byte-identique. Les palettes et pixels indexés ne sont jamais recalculés.

**Gain disque statique cumulé :** 131 072 B, soit 64 secteurs.

**Gain VRAM/transfert texture statique par scène :** une page 256×256 8bpp, soit 65 536 B pour W2 ou Weekend 1. Ce n’est pas un gain simultané de 131 072 B puisque les semaines ne résident pas ensemble.

**Gain RAM :** aucun. Le tampon de chargement de page reste 65 536 B, et le tampon secteur séparé reste 2 048 B.

**CLUT :** inchangée ; les palettes restent hors des pages de texture.
**Framerate :** aucun gain de performance n’est inféré de la seule diminution du nombre de pages.

Les changements de ressources comparés à v183 sont exactement W2 (`week2-scene.bin`, `bopeebo_visual_data.h`) et Weekend 1 (`weekend1-scene.bin`, `weekend1_visual_data.h`). Les fichiers W1/W3–W7, y compris `week6-scene.bin` et `week6_visual_data.h`, sont identiques. Les hashes complets sont dans `audit/v1/corrected-build/resource-hashes.csv`.

## Budgets et durée de vie

Les groupes sont chargés indépendamment par scène ; les atlases de toutes les semaines ne sont pas résidents en même temps. Le repack réduit le nombre de pages de texture à transférer/charger pour les deux scènes ciblées. Les surfaces transparentes et les trous dispersés restent comptés dans l’audit, mais ne sont pas revendiqués comme mémoire récupérée. W3, W4, W5 et W7 gardent leurs pages et compositions propres.

Les mesures RAM code/data/BSS sont issues de l’ELF compilé, et ne sont pas déduites des tailles de paquets : text 1 013 048 B, data 2 638 B, BSS 40 120 B, total 1 055 806 B. Par rapport à l’ELF v183 archivé (1 051 790 B pour ces sections), l’exécutable est supérieur de 4 016 B ; ce travail ne prétend donc à aucune économie RAM. Le rapport de build consigne les sections et hashes du binaire. Les lectures CD de scène terminent toujours avant le flux musical ; aucun streaming graphique ni accès CD concurrent n’est ajouté.

## Reproduction

Environnement déjà configuré hors dépôt : PSn00bSDK 0.24, GCC MIPS 12.3.0, CMake et Ninja. Le cache du build utilisé est `C:/Users/Manau47/Documents/Codex/ps1-asset-harmonization-v1-lossless-build/CMakeCache.txt`; son SHA-256 figure dans `audit/v1/corrected-build/build-manifest.csv`.

Les conversions v183 ont été réutilisées. Les deux paquets repackés proviennent de BIN/header convertis existants. Dry-run Ninja : compilation du programme, lien ELF et fabrication de l’image disque ; aucun convertisseur d’images, audio ou charts ne s’exécute. La sortie de fabrication ISO copie/emballe les ressources déjà converties dans le disque, sans les reconvertir. Après le build, `ps1/diagnostics/reorder_iso_system_cnf.py --exe-after-system-cnf` crée une image distincte avec SYSTEM.CNF puis FUNKIN.EXE en tête du répertoire racine.

Le nouveau build incrémental a réussi. Les vérifications de disque confirment 117 fichiers visibles dans la racine et SYSTEM.CNF/FUNKIN.EXE aux positions 1/2. Le CUE est livré dans un dossier distinct, sans écraser le précédent candidat v1.

## Résultats observés et limites

**Inspecté/calculé statiquement :** atlas et fiches de toutes les familles intégrées ; simulation de packing ; comparaison exacte des paquets finaux à v183 ; hashes des ressources et binaires ; ordre ISO.

**Implémenté :** repack sans perte de W2 et Weekend 1, outil source reproductible, rapports corrigés. Le paquet W6 du build correspond à v183.

**Compilé :** build normal avec ressources converties réutilisées ; aucune conversion globale relancée.

**Non exécuté/validé :** aucune interaction DuckStation dans cette passe et aucun test console. Les visuels en mouvement, navigations multi-semaines, retour Freeplay, pause, game over/retry et stabilité audio doivent être vérifiés par l’utilisateur avant de déclarer cette optimisation validée.

## Artefacts

Le manifeste et hashes sont dans `audit/v1/corrected-build/`. Le BIN/CUE normal est conservé hors Git dans :

`C:/Users/Manau47/Documents/Codex/ps1-asset-harmonization-v1-scenes-delivery/`

La livraison précédente `ps1-asset-harmonization-v1-lossless-delivery/` reste intacte pour comparaison, mais elle correspond au candidat W6 hors périmètre et ne doit pas être confondue avec le présent v1 corrigé.
