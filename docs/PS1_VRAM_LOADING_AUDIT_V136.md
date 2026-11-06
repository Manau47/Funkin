# Audit de chargement VRAM/RAM — base v136 et optimisation suivante

## Références et niveau de preuve

- Snapshot de départ : commit `71274dc3441d9d4c6e4e9330ef3e504ca5bc22c1`; correctif v136 de réinitialisation VRAM : `f3106b5b72d699b072a479f86925e2e68b405137`.
- Le manifeste [`PS1_VRAM_AUDIT_BASELINE_V136.md`](PS1_VRAM_AUDIT_BASELINE_V136.md) enregistre la configuration exacte et la copie de `CMakeCache.txt`. Les BIN/CUE v136 restent dans leur dossier de build.
- Le retour utilisateur de corruption après Freeplay concerne v135. La v136 devait traiter ce cycle, mais l’utilisateur n’a pas encore confirmé un essai v136. L’état v136 est donc une référence source/configuration, pas un comportement validé.
- Les volumes ci-dessous sont calculés depuis le code, les constantes du paquet généré et les rectangles `LoadImage`. Aucun compteur runtime de CD, de transfert GPU ou de pic heap n’existe dans cette version.

## Carte mémoire actuelle

### RAM principale

L’ELF v136 mesure, pour ses sections chargées : `.text=89 136`, `.rodata=926 620`, `.data=2 112`, `.sdata=434`, `.sbss=492`, `.bss=39 692`, plus 16 octets de `.ctors/.dtors`, soit **1 058 502 octets résidents**. La `.rodata` contient notamment les écrans de menu empaquetés, les icônes, les polices/atlas et la banque audio de menu; les scènes et les VAGi musicaux restent sur le disque. Ce chiffre est un calcul ELF, pas une mesure de RAM libre au runtime.

Allocations dynamiques repérées :

| Allocation | Taille / durée de vie | Propriétaire |
|---|---:|---|
| Tampon de staging d’une page 8bpp | 65 536 o, temporaire pendant les lectures d’atlas | Chargeur de scène ou restauration BF W3 |
| Tampon d’une page 4bpp | au plus 32 768 o utiles, même allocation de 65 536 o réutilisée | Chargeur de base |
| Tampon secteur palette | 2 048 o, temporaire | Chargeur de paquet / retry |
| Chart sélectionné | `ceil(taille_fichier/2048)*2048` o, du lancement au retour Freeplay/game over | `active_chart_blob` |
| FIFO cdstream | 98 304 o, du préchargement audio à `Stream_Destroy` | SDK `Stream_Context` |

Le chart est lu avant les scènes et gardé pendant le morceau. Le staging de 64 Kio est libéré avant `Stream_Init`; le FIFO de 96 Kio n’est donc pas simultané au staging de scène. À l’arrêt, `release_song_resources()` détruit le FIFO avant les lectures de transition; le chart est libéré au retour Freeplay. Le pic exact dépend du chart sélectionné et du runtime/stack, et n’a pas été mesuré en exécution.

### VRAM

VRAM physique : 1 048 576 octets (1024×512 pixels à 16 bpp).

| Région | Emplacement | Occupation |
|---|---|---:|
| Deux framebuffers 320×240 | x=0, y=0 et y=240 | 307 200 o |
| 9 pages texture 8bpp | slots x=384/512/640/768, y=0/256; slot 8 x=896,y=256 | 589 824 o |
| 2 pages texture 4bpp | x=320, y=0/256 | 65 536 o |
| Plage CLUT disponible sous les framebuffers | x=0..319, y=480..511 | 20 480 o |
| Total de la carte réservée |  | **983 040 o** |
| Espace physique restant |  | **65 536 o** |

Les écritures de CLUT de base représentent 1 216 octets par chargement d’atlas. Les semaines remplacent des pages partagées, pas une allocation VRAM cumulative : W2 utilise 7 pages 8bpp, W3 8 pages plus la page de secours BF, W4/W5/W7 3 pages, W6 5 pages et WeekEnd 1 8 pages. La Freeplay superpose son animation DJ sur le slot 7; la page 8 sert successivement au logo/menu et à l’animation de mort. La CLUT 8bpp commune est à (0,496).

### SPU

Le VAGi musical utilise quatre voix, interleave 4 096 octets par canal et deux blocs de lecture. L’allocation SPU du double buffer est donc `4096×4×2 = 32 768` octets à partir de `0x1010`; la FIFO miroir en RAM est de 96 Kio. SFX gameplay : voix 4–7, zone à `0x10000`; SFX de menu : voix 8–10, banque de 269 056 octets à `0x22000`; Game Over : voix 11. Voix 12–23 disponibles. Capacité SPU physique : 512 Kio. Ce plan est lu dans les constantes et dans la configuration de streaming; aucune mesure de fragmentation SPU runtime n’est disponible.

## Chemins réellement codés en v136

1. **Démarrage → menu :** `main()` charge le paquet de base W1 (589 824 o lus sur CD, 589 824 o de pages uploadées, puis 1 216 o de CLUT), puis `load_menu_visuals()` relit la page logo W1 de 65 536 o et sa CLUT de 512 o. Le rendu du premier écran remplace ensuite cette page logo par la texture de menu empaquetée (65 536 o d’upload VRAM). La lecture du logo intermédiaire est donc écrasée avant utilisation.
2. **Ouverture Freeplay :** l’art Freeplay est uploadé depuis la mémoire de l’exécutable dans la page menu (65 536 o), plus jusqu’à quatre icônes 14×28 pixels à 4bpp (~3 136 o). L’animation DJ remplace le slot 7 avec 65 536 o depuis la ROM empaquetée; pas de lecture CD de scène. Les données des autres semaines ne sont pas lues.
3. **Lancement d’un morceau :** arrêt/libération du flux menu, lecture du chart arrondie au secteur, lecture/restauration de la page 7 DJ depuis W1 (65 536 o), libération de l’art menu, lecture du paquet de scène actif, puis seulement démarrage du VAGi et allocation du FIFO 96 Kio. Les charts restent indépendants des paquets de scènes.
4. **Retour Freeplay v136 :** arrêt du flux, libération du chart, restauration des pages de la semaine active, puis chargement complet de l’atlas W1 (589 824 o), lecture de la page logo W1 (65 536 o), overlay DJ, reprise du menu. La restauration de la semaine active est immédiatement écrasée par W1; la page logo est elle aussi remplacée par l’art Freeplay empaqueté. Les appels des chargeurs inactifs réécrivent également la CLUT de base plusieurs fois.
5. **Game Over → Retry v136 :** le Game Over change la CLUT partagée (512 o) et écrit les frames de mort dans une zone 40×96 de la page 8. Retry recharge ensuite le paquet complet de la semaine, bien que les pages actives soient conservées. Seule la CLUT doit être restaurée pour toutes les semaines; W3 a en plus placé la page BF de secours en page 8, que l’animation de mort écrase. Cette exception W3 requiert une lecture de cette page W1 et son upload.

## Volumes calculés par paquet

Les nombres de scène ci-dessous excluent le chart, identique avant/après, et séparent lecture CD et transfert VRAM. Une page 8bpp = 65 536 octets; une CLUT = 512 octets; les paquets de semaine stockent la palette dans un secteur CD de 2 048 octets.

| Paquet actif | Pages de scène à l’entrée | CD lu à l’entrée | VRAM pages + CLUT |
|---|---:|---:|---:|
| W1 (base déjà en place) | 0 | 0 | 0 |
| W2 | 7 | 460 800 o | 459 264 o |
| W3 (8 pages + sauvegarde BF W1) | 9 | 591 872 o | 590 336 o |
| W4 / W5 / W7 | 3 | 198 656 o | 197 120 o |
| W6 | 5 | 329 728 o | 328 192 o |
| WeekEnd 1 | 8 | 526 336 o | 524 800 o |

Les transitions ont été simplifiées dans le code, mais les gains chiffrés sont des calculs statiques :

| Transition | v136 | Version modifiée | Gain calculé |
|---|---|---|---|
| Démarrage / retour : logo W1 intermédiaire | 65 536 o CD + 65 536 o VRAM, puis remplacé par l’écran menu | aucun chargement logo; art menu uploadé directement avant dessin | −65 536 o CD et VRAM, −512 o CLUT |
| Entrée d’un morceau autre que W1 | 5–6 chargeurs inactifs écrivent la CLUT de base avant le paquet actif | seul le paquet actif est acquis | −2 560 à −3 072 o d’écritures CLUT |
| Retour Freeplay | restauration du paquet semaine, puis W1 complet + logo CD | W1 complet, destination Freeplay, sans étape de restauration semaine ni logo intermédiaire | −(pages de la semaine restaurée + 65 536) o CD/VRAM; −4 096 o d’écritures CLUT redondantes |
| Retry W2/W3/W4/W5/W6/W7/WEnd1 | paquet entier + palette; W3 inclut sa sauvegarde BF | palette seule; W3 relit aussi sa page BF de secours | −458 752 / 524 288 / 196 608 / 196 608 / 327 680 / 196 608 / 524 288 o CD et pages VRAM |

Pour une chanson W3, le Retry conserve une lecture/upload BF de secours de 65 536 o, car l’animation Game Over l’écrase en page 8. La palette de W1 est restaurée depuis les données statiques, sans lecture CD. Le volume chart reste `ceil(chart_bytes/2048)*2048`; la taille exacte varie selon le chart et est inchangée.

## Changement limité, propriétaires et limites

La transition Freeplay reçoit désormais directement l’atlas W1, sans restauration préalable des pages de la semaine. `load_menu_visuals()` marque la ressource menu prête sans lire le logo W1 inutile; l’art menu remplit la même page avant son premier dessin. `load_song_stage_visuals()` n’appelle plus les chargeurs inactifs : Freeplay a établi l’atlas W1 canonique et effacé les drapeaux d’ownership, donc seul le paquet de destination est chargé. Un marqueur `vram_scene_owner_stage` indique l’état de la région partagée (base, semaine active ou transition invalide). La restauration de Retry ne touche qu’à la CLUT et à la page BF W3 si nécessaire; les indicateurs de semaine restent valides.

Aucun convertisseur n’a été exécuté ou modifié. Les dimensions, palettes, charts, stems, compositions, animations, gameplay et timings restent inchangés. La durée réelle des transitions, le pic heap, l’absence de corruption sur plusieurs cycles, et le bon rendu après chaque palette n’ont pas été mesurés. La confirmation DuckStation appartient au test utilisateur à venir; aucune validation console réelle n’est revendiquée.

