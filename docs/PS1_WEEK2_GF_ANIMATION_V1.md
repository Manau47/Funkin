# Week 2 GF — cycle de danse complet (v1)

## But

Le retour utilisateur confirme que BF de Week 2 est maintenant correct, mais que GF n'expose pas assez de poses. Cette passe restaure un mouvement gauche/droite complet à partir du rig officiel épinglé, tout en respectant les dix rectangles déjà réservés dans l'atlas Week 2.

## Diagnostic

Le rig officiel `shared/images/characters/gf` contient une animation Idle de 30 frames. Les données officielles du personnage découpent le cycle en `danceLeft` (frames 0–14) et `danceRight` (15–29). La conversion précédente stockait les frames 0–9 seulement. Or le moteur interprétait déjà les indices 0–4 comme les cinq poses d'un côté et 5–9 comme celles de l'autre : la moitié droite du mouvement était donc absente.

## Conversion et cadence

Les dix cels existants sont maintenant échantillonnés aux frames officielles `0, 3, 6, 9, 12, 15, 18, 21, 24, 27` : cinq poses réparties dans chacune des deux moitiés du cycle. Les dix images sont ajustées avec les bornes communes des 30 frames afin de garder la même échelle et le même ancrage au sol entre les poses.

Le moteur alterne le côté de la danse à chaque beat et parcourt ses cinq poses pendant ce beat à partir de la position musicale calculée depuis les échantillons audio et le BPM du chart. Le mouvement n'est donc pas cadencé par le nombre d'images vidéo. Il s'agit d'un compromis PS1 : cinq poses clés par côté au lieu des quinze frames source, mais les deux directions et le mouvement complet sont présents.

## Ce qui reste identique

- Dix cels GF de 94×85 pixels et leurs rectangles UV/pages actuels.
- Même CLUT Week 2, conservée byte pour byte ; les nouveaux cels sont quantifiés avec cette palette, sans la recalculer.
- Les neuf pages et la taille du paquet W2 (590 336 octets, CLUT incluse).
- BF, Spooky Kids, Monster, scènes, caméra, ancrages, charts, commandes, jugements et gameplay.
- Flux audio, sons et réglages SPU.

L'outil dédié `ps1/update_week2_gf_animation.py` ne réécrit que les dix rectangles GF. Il contrôle leurs limites, leur non-chevauchement, la taille du paquet, la palette conservée et l'absence de modification hors de ces rectangles. Son manifeste consigne les SHA-256 avant/après.

## Build et vérification

Branche : `ps1-asset-harmonization-v1`. Assets officiels épinglés : `724eba9de9e76761d9cefd52169926bc51c760a5`.

Le dry-run du target disque prévoyait seulement la relocation W2 BF déjà utilisée, la génération ciblée des cels GF, la compilation/link du programme et la création de l'image disque. Aucune conversion globale des personnages, décors, charts ou audios n'a été demandée. La compilation et les contrôles statiques de l'image disque ont réussi. Les diagnostics et le mode démo restent désactivés au démarrage.

Le CUE est livré séparément dans `ps1-asset-harmonization-v1-week2-gf-cycle-v1-delivery`. L'essai DuckStation est en attente du chargement et du retour utilisateur ; aucune validation visuelle ou console réelle n'est revendiquée.
