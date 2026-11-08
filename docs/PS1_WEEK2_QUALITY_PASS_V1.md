# Passe visuelle Week 2 — build de première vérification

Date : 2026-11-08  
Branche : `ps1-asset-harmonization-v1`  
Base de code avant cette passe : `fd91745c72ff7149d76dfd83d9e71cad3e30dc17`  
Base de contenu : conversion v183 archivée, assets épinglés `724eba9de9e76761d9cefd52169926bc51c760a5`.

## Portée

Cette livraison est la première passe testable **Week 2 seulement**. Elle repart des sources officielles épinglées pour les textures Week 2 concernées. Elle conserve Week 1 comme référence de lisibilité et v183 comme base de comparaison. Weekend 1 n’est pas modifié dans ce premier disque ; la même analyse de définition et de composition est prévue ensuite, après le retour sur cette scène.

Les charts, le gameplay, l’audio, les durées et le nombre de poses, les autres semaines et Weekend 1 sont conservés. Aucun diagnostic n’est activé au démarrage. Le nouveau disque n’a pas été lancé dans DuckStation : les captures de texture ci-dessous sont des comparaisons de conversion, pas une validation du build.

## Assets reconvertis depuis les sources officielles

Le convertisseur ciblé `ps1/convert_bopeebo_visuals.py` a régénéré les seules ressources graphiques du paquet Week 2 à partir des fichiers officiels suivants : décor `halloween_bg`, rig et atlas Spooky Kids, rig/atlas Monster, rig/atlas GF, icônes Spooky et Monster. Les frames sélectionnées et leurs durées restent identiques : 8 poses idle Spooky Kids, 4 idle Monster et 2 poses de chant par direction, 10 poses de danse GF, 3 images d’éclair. Les sprites d’acteurs conservent leurs ancres au sol.

| Famille | Ancienne définition d’atlas | Nouvelle définition convertie | Taille dans le monde PS1 | Traitement |
|---|---:|---:|---:|---|
| Spooky Kids et Monster | 72×84 | 85×100 | 72×84 | extraction des rectangles officiels, Lanczos pour les cels raster/rig, dimensions d’affichage conservées |
| GF | 87×79 | 94×85 | 87×79 | cycle complet de 10 poses conservé, canevas converti agrandi, taille affichée conservée |
| Fond fixe | image réduite dans 362×256 | 362×256 | 362×256 | conversion du redimensionnement `area` vers Lanczos, aucune réduction de couverture |
| Éclairs | 3 cels officielles | cels officielles, même taille/UV | 163×130 | même page de scène, pas de nouvelle lecture CD |
| Icônes | 24×24 | 24×24 | 24×24 | dimensions inchangées |

Les contours ne sont pas uniformément appliqués à une même taille. Les acteurs gardent leur empreinte à l’écran ; le gain de définition vient de rectangles sources plus grands avant quantification. Le paquet utilise une CLUT 8bpp dédiée de 255 couleurs plus l’index transparent ; erreur RGB moyenne mesurée par le convertisseur : 4,81 niveaux. Cette mesure est statique et ne décrit pas le rendu du téléviseur ou de DuckStation.

Comparaisons de conversion à l’empreinte de rendu prévue, chacune avec deux vues 320×240 côte à côte (v183 à gauche, candidat à droite) :

- [GF, empreinte de caméra native](../audit/v1/week2-quality-v3/asset-comparisons/week2_gf_v183-v2_640-camera_native.png)
- [Monster, empreinte de caméra native](../audit/v1/week2-quality-v3/asset-comparisons/week2_monster_v183-v2_640-camera_native.png)
- [Spooky Kids, empreinte de caméra native](../audit/v1/week2-quality-v3/asset-comparisons/week2_spooky_v183-v2_640-camera_native.png)

Ces prévisualisations montrent l’extraction et la quantification, pas la scène exécutée. Elles ne prouvent ni la qualité finale en mouvement, ni les ancrages dans DuckStation.

## Comparaison de scène source → PS1

La scène épinglée `spookyMansion.json` fixe `cameraZoom=1.0`, le décor `halloweenBG` à `(-395,-505)` avec échelle `(1,1)`, profondeur `-100`, scroll `(1,1)`. Ces réglages du fond, son cadrage et son ordre ne sont pas changés dans cette passe. Le zoom porté est Q8 `582`, conversion déjà utilisée pour ce stage en 320×240 ; aucune diminution du décor n’est faite pour masquer son débordement horizontal en 4:3.

Les positions de personnages et offsets caméra officiels sont maintenant utilisés au lieu des ancres génériques portées. La conversion vers l’espace PS1 divise ces coordonnées par 7, le même étalonnage utilisé par la conversion du décor :

| Acteur | Source officielle : position / offset caméra | Coordonnées PS1 v183 | Coordonnées/offset PS1 candidat | Delta d’ancre PS1 |
|---|---|---:|---:|---:|
| Dad / adversaire | `(382,865)` / `(150,-100)` | `(48,108)` | `(55,124)` / `(21,-14)` | `(+7,+16)` |
| GF | `(751.5,787)` / `(0,0)` | `(94,98)` | `(107,112)` / `(0,0)` | `(+13,+14)` |
| BF | `(989.5,885)` / `(-100,-100)` | `(124,111)` | `(141,126)` / `(-14,-14)` | `(+17,+15)` |

L’ancre verticale est le pied/le bas du canevas, comme le placement PS1 existant. Les cibles de focus sont recalculées à partir de ces ancres, de la moitié des dimensions d’affichage et des offsets caméra ; la poursuite lissée de focus et les changements de section chart restent en place. Les cibles de focus monde passent approximativement Dad `(67,55)→(76,68)`, GF `(94,58)→(107,73)`, BF `(111,72)→(127,86)`. Les deux morceaux Spookeez/South gardent leur ajustement vertical local déjà présent. L’ordre d’affichage GF → Dad → BF reste identique.

Cette conversion garde les relations de la scène officielle tout en reprenant le cadrage 4:3 du port. Elle ne garantit pas que les bords et le focus seront visuellement préférés : il faut les vérifier avec le CUE dans DuckStation.

## Coût mémoire et transferts

| Mesure statique Week 2 | v183 | Candidat |
|---|---:|---:|
| Pages texture 8bpp actives | 6 | 9 (limite allouée à cette semaine) |
| VRAM pages 8bpp | 393 216 B | 589 824 B |
| CLUT | 512 B | 512 B |
| Paquet disque | 393 728 B | 590 336 B |
| Écart | — | +196 608 B, +96 secteurs CD, +3 pages / +192 Kio VRAM |

Les pages forment l’ensemble de textures Week 2 chargé pour le morceau ; les autres semaines ne sont pas résidentes simultanément dans cet atlas. La réserve de 9 pages est entièrement occupée par Week 2. Le tampon de page/temporaire de 64 Kio et le tampon de secteurs de 2 Kio ne changent pas ; aucun gain ou coût RAM supplémentaire n’est revendiqué. La mémoire SPU, les voix, le VAGi et les débits audio sont inchangés. Il n’y a pas de lecture graphique en concurrence avec la musique. La baisse/hausse du nombre de pages ne permet pas d’inférer un gain/perte de framerate.

## Build et contrôles

- Dry-run ciblé `ps1-bopeebo-playable-disc` : 4 tâches, compilations du lecteur `cdstream` SDK et du jeu, lien ELF, fabrication disque. Aucune conversion d’images, d’audio ou de charts n’était planifiée.
- Compilation PSn00bSDK 0.24 réussie. Deux avertissements préexistants du `stream.c` du SDK sur le qualificateur `volatile`.
- Sections ELF : text 1 013 012 B, data 2 630 B, BSS 40 120 B, total 1 055 762 B.
- Les fichiers VAG et charts du nouveau build sont identiques à la base de build immédiate v2 ; les autres paquets de scène W1/W3–W7 et Weekend 1 sont également identiques. La comparaison normalisée du header confirme les tables et palettes hors Week 2 inchangées.
- ISO : 117 fichiers racine ; après la réparation de démarrage habituelle, `SYSTEM.CNF` est le premier fichier et `FUNKIN.EXE` le second. L’exécutable extrait de l’ISO correspond octet pour octet à celui lié.
- Hashes et configuration complets : `audit/v1/week2-quality-v3/` et le snapshot externe de livraison.

## État de validation

**Observé statiquement/compilé :** sources officielles épinglées inspectées, frames/dimensions/CLUT/pages contrôlées, relations de placement et offsets comparés au JSON officiel et à `Stage.hx`, dry-run, compilation et structure ISO vérifiés.

**À faire par l’utilisateur :** charger le CUE et juger le cadrage, les tailles, la lisibilité des contours et la stabilité des animations en jeu. Aucun résultat DuckStation ou console n’est affirmé ici. Après son retour sur Week 2, appliquer la même passe à Weekend 1.

## Artefacts

- BIN/CUE normal hors Git : `C:/Users/Manau47/Documents/Codex/ps1-asset-harmonization-v1-week2-quality-v3-delivery/`
- Le BIN/CUE v2 et toutes les bases précédentes sont conservés dans leurs dossiers d’origine.
- Aucun asset officiel, SDK ou binaire volumineux n’est ajouté au dépôt.
