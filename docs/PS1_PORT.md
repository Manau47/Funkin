# Adaptation PlayStation 1 — cadrage initial

## Objectif

Créer une adaptation non officielle au style PS1 marqué, en préservant autant que le matériel le permet les chansons, charts et difficultés, personnages, semaines, dialogues et modes du jeu. Le premier morceau jouable sera un jalon de validation audio, timing et gameplay, pas la limite du portage. Un mode local à deux joueurs viendra plus tard; les états d'entrée doivent donc rester distincts par joueur.

## Référence et état du dépôt

- Dépôt de travail : `Manau47/Funkin`, branche par défaut `main`.
- Référence du dépôt de travail et du dépôt original `FunkinCrew/funkin` lors de l'inspection : `d05659bbdcf0d83073c900207cf410472afbbede` (`main`). Cette référence doit rester le point de départ explicite des comparaisons du portage.
- La branche locale `ps1-port` a été créée à partir de ce commit. Aucune branche distante `ps1-port` n'existait à l'inspection.
- Aucun `AGENTS.md` n'a été trouvé. Les instructions de compilation du dépôt sont dans `docs/COMPILING.md` et couvrent le jeu Haxe/Flixel de bureau.

Les sous-modules `assets` et `art` sont déclarés dans `.gitmodules` et pointent respectivement vers `FunkinCrew/Funkin.assets` et `FunkinCrew/Funkin.art`. La méthode du dépôt est `git submodule update --init --recursive`. Les sous-modules n'ont pas été récupérés pour ce jalon. Leurs licences signalent que les ressources créatives sont propriétaires et ne peuvent pas être redistribuées publiquement sans autorisation. Le code du jeu est sous Apache-2.0 selon `LICENSE.md`; cette licence ne s'étend pas aux ressources des sous-modules. Garder cette séparation et les attributions lors de toute conversion.

## Réemploi et réécriture

Référence consultée à `source/funkin/Conductor.hx`, `source/funkin/util/GRhythmUtil.hx`, `source/funkin/util/Constants.hx`, `source/funkin/play/PlayState.hx`, `source/funkin/play/notes/Strumline.hx`, `source/funkin/data/song/SongData.hx` et `source/funkin/Highscore.hx`.

| Système original | Réutilisable comme données/règles | À réécrire côté PS1 |
| --- | --- | --- |
| Charts, BPM, changements de tempo, temps des notes, directions et longueurs des notes tenues | Format et contenu de charts, après conversion d'un sous-ensemble testé vers un format binaire compact | Chargeur, indexation mémoire, rendu et défilement des notes |
| Timing (`Conductor`) | Position musicale en millisecondes, BPM et calcul des pas/temps comme référence comportementale | Horloge basée sur VBlank et/ou position audio CD, latence d'entrée, pause/reprise et resynchronisation |
| Fenêtres de jugement | `GRhythmUtil` fixe la fenêtre générique à ±160 ms dans `Constants.HIT_WINDOW_MS`; implémenter des essais comparatifs avant de figer les fenêtres PS1 | Échantillonnage manette par frame, tri des frappes simultanées et évaluations/tallies |
| Notes maintenues | Durée, maintien jusqu'à la fin, pénalité à la perte, bonus continu (dans PlayState) | Détection d'appui/relâchement depuis masque de boutons actif-bas et visualisation de la tenue |
| Score, combo et vie | Barème et paramètres `Constants`/`Highscore` à porter en entiers et vérifier contre les résultats originaux | HUD et persistance, limités par mémoire et architecture de sauvegarde |
| Voix et erreurs | Le jeu distingue pistes vocales joueur/adversaire et resynchronise avec l'instrumental; `PlayState` réduit le volume vocal joueur sur un miss | Mix CD-DA ou séquence d'échantillons, stratégie de mémoire CD, synchronisation de pistes et règles de baisse/restauration des voix |

La logique de gameplay est une source de vérité, mais ses classes ne sont pas portables telles quelles : elles dépendent de Haxe, Flixel, du modèle d'acteurs/états et des systèmes de données et scripts. Le portage nécessitera des modules C/C++ dédiés pour le temps, le chart, l'état de chaque joueur, les jugements, le score/vie, l'audio et le rendu. Les éditeurs de charts, débogueurs, pipeline Haxe/Lime, intégrations Newgrounds/Discord, systèmes de mods et outils de bureau restent des outils de développement ou fonctions en ligne; ils ne sont pas requis par l'exécutable PS1. Le format et le contenu créés avec ces outils peuvent néanmoins être convertis et préservés.

## Chaîne choisie et premier résultat

Le fichier `Psxdev.zip` fourni (environ 419 Mo) contient des installateurs fragmentés CodeWarrior pour PlayStation et PsyQ, dont PsyQ 4.6. Ils n'ont pas été extraits ni exécutés. Une chaîne PSn00bSDK est retenue pour ce prototype : compilateur GCC MIPS, CMake et construction en ligne de commande, sans intégrer de SDK au dépôt. PSn00bSDK 0.24, CMake 4.4.4 et GCC 12.3.0 ont été installés hors du dépôt sous `Documents\Codex\toolchains`; l'archive GCC fournie séparément n'était pas nécessaire, PSn00bSDK incluant déjà cette version. CMake 4.4.4 portable a nécessité de définir `CMAKE_ROOT` vers son dossier `share/cmake-4.4`. C'est un choix de démarrage fondé sur la reproductibilité et l'outillage accessible, pas une preuve que chaque capacité audio, vidéo ou CD nécessaire à l'adaptation est déjà couverte. Il faudra valider séparément les limites de mémoire, l'accès audio CD, les contrôleurs, le média de livraison et les performances.

`ps1/` contient le banc d'essai d'affichage et de lecture de manette. L'architecture réserve un enregistrement d'état à chaque joueur; seul le premier contrôleur est affiché pour l'instant.

## Audio : options, test et choix en attente

PSn00bSDK 0.24 fournit plusieurs chemins : CD-DA stéréo PCM (lecture matérielle du disque), XA-ADPCM depuis les secteurs CD, et le streaming SPU ADPCM montré par son exemple `sound/cdstream`. Ce dernier lit un `.VAGi` depuis le CD vers un tampon circulaire en RAM, puis transfère des blocs vers la SPU; son pilote accepte un masque de canaux SPU et un callback de temps. La mesure `Stream_GetSamplesPlayed()` est ancrée aux interruptions SPU de début de bloc et interpolée entre elles; par défaut l'interpolation utilise `VSync`, mais le callback de minuterie peut être remplacé. Référence : [notes de version PSn00bSDK 0.24](https://github.com/Lameguy64/PSn00bSDK/releases/tag/v0.24) et [exemple officiel cdstream](https://github.com/Lameguy64/PSn00bSDK/tree/v0.24/examples/sound/cdstream).

Le programme facultatif `ps1/audio_probe.c` prend actuellement le chemin CD-DA et appelle `CdlGetlocP` pour lire la position relative de la piste par Subchannel Q. Le compteur de piste utilise les minutes/secondes/frames BCD du CD, avec 75 frames audio par seconde; le repère à 120 BPM est calculé depuis cette position disque et non depuis `VSync`. La commande est documentée comme valable sur les pistes CD-DA dans [`psxcd.h` de PSn00bSDK](https://github.com/Lameguy64/PSn00bSDK/blob/v0.24/libpsn00b/psxcd.h). Le test produit une image à deux pistes : exécutable de données et courte piste audio.

Le fixture actuel est un clic/basse synthétique de 12 secondes, 44,1 kHz stéréo et 120 BPM, généré par `ps1/generate_click_track.py` vers un chemin temporaire hors dépôt. Il permet de confronter le front sonore périodique au flash visuel, mais ne valide pas encore le mix, le tempo ni les voix d'un morceau FNF. L'image a été compilée; son exécution audio dans DuckStation et la mesure de dérive sur 12 secondes restent à faire dans cette session.

Pour préparer un vrai essai, le morceau retenu est **Bopeebo classique (semaine 1)**, à la révision de sous-module `FunkinCrew/funkin.assets` épinglée dans le dépôt (`724eba9de9e76761d9cefd52169926bc51c760a5`). Les sources de stems sont [`songs/bopeebo/Inst.ogg`](https://github.com/FunkinCrew/funkin.assets/blob/724eba9de9e76761d9cefd52169926bc51c760a5/songs/bopeebo/Inst.ogg) (blob `593052bfcf9f4931d597cd912c96716581af5c29`, 939 552 octets) et [`songs/bopeebo/Voices-bf.ogg`](https://github.com/FunkinCrew/funkin.assets/blob/724eba9de9e76761d9cefd52169926bc51c760a5/songs/bopeebo/Voices-bf.ogg) (blob `5394f467230fada6114753615f79d2280f0e0f00`, 714 105 octets); le stem adverse est `Voices-dad.ogg` (blob `bfd1edf25670d418e8e633aaf1cb7c7f4edb9770`, 705 962 octets). La licence de ce sous-module réserve tous les droits et interdit la redistribution publique de son contenu : [LICENSE.md](https://github.com/FunkinCrew/funkin.assets/blob/724eba9de9e76761d9cefd52169926bc51c760a5/LICENSE.md). Aucun de ces fichiers n'est ajouté au dépôt. Le téléchargement local des OGG n'a pas abouti dans cet environnement; il faudra fournir les stems localement ou rendre le téléchargement HTTPS disponible pour pouvoir encoder et écouter l'extrait.

Le moteur source sépare l'instrumental et les voix joueur/adversaire. Dans `PlayState.hx`, les voix joueur sont mises à zéro après un miss (autour de la ligne 3192 à la référence inspectée) et rétablies après une frappe réussie (autour de la ligne 3380). Un CD-DA stéréo mixé ne peut pas couper cette voix séparément.

**Décision de portage : partir sur le streaming SPU `.VAGi`** pour le premier prototype synchronisé. Il permet de contrôler les stems séparément et fournit une position en échantillons ancrée aux interruptions SPU. Le test CD-DA reste un comparatif de diagnostic, pas la voie retenue pour le jeu. Le jalon actuel vérifie un stream stéréo; il ne valide pas encore le stream quatre canaux, l'atténuation réelle des voix, les underruns ou le budget mémoire final. Le pilote `cdstream` fourni avec PSn00bSDK n'autorise qu'un flux actif à la fois, mais ce flux peut occuper plusieurs canaux SPU via un VAGi interleavé. L'essai du jeu devra encoder instrumental et voix joueur dans un même stream multicanal pour les piloter indépendamment, puis mesurer les coûts CD, RAM et SPU. Les sources de streaming du SDK restent dans l'installation locale; aucune copie du SDK ni donnée audio de test n'est versionnée.

## Prochaines étapes

1. Tester chaque touche, maintien, relâchement, simultanéité et reconnexion avec une manette active; l'écran de diagnostic montre maintenant le masque de fronts et les frames de maintien.
2. Exécuter le disque de streaming SPU VAGi dans DuckStation, vérifier le son, la position en échantillons, les erreurs CD et les underruns; répéter sur console si du matériel est disponible.
3. Obtenir localement les stems Bopeebo épinglés, vérifier le chart/BPM et convertir un court extrait sans ajouter les ressources propriétaires au dépôt.
4. Mesurer sur le stream SPU `.VAGi` quatre canaux l'usage RAM, CD et SPU, les underruns et l'atténuation après miss; garder CD-DA/XA comme options de comparaison si une contrainte apparaît.
5. Implémenter un prototype jouable avec quatre voies, judgement, notes tenues, score/vie et synchronisation instrumentale/voix; comparer au jeu de référence.
6. Évaluer les graphismes PS1, les scènes, personnages et dialogues, puis préserver progressivement semaines et modes compatibles.
7. Ajouter et tester les contrôleurs et états de gameplay du second joueur dans une étape séparée.

## Résultats de cette étape

- Inspecté : dépôt propre sur `main`, consignes de compilation, modules de gameplay ciblés, sous-modules et licences; contenu de l'archive inventorié sans exécution.
- Implémenté : branche locale `ps1-port`, projet C PS1 isolé, preset CMake reproductible, configuration d'image de disque et notes de portage.
- Compilé : `cmake --preset default` puis `cmake --build --preset default` ont réussi avec PSn00bSDK 0.24; image CD `.bin` de 381 024 octets et fichier `.cue` produits. La dernière compilation n'a émis aucun avertissement.
- Exécuté/testé : `funkin-ps1-probe.cue` a démarré dans DuckStation 0.1-8675 (build `g3ea26cc91`). L'image du programme s'affiche en 320×240; DuckStation a rapporté 60 IPS pour le jeu et la vidéo. Le port 1 est indiqué connecté, type de pad numérique `0x04`, et l'état inactif des boutons est affiché. Une pression maintenue n'a pas été confirmée dans cette vérification.
- Corrigé après inspection visuelle : texte de pied de page raccourci pour rester dans la zone visible; la nouvelle image compile et affiche entièrement ce texte dans l'émulateur.
- À vérifier : état affiché pendant l'appui sur un bouton, fonctionnement sur console réelle, synchronisation audio, lecture d'une chanson et budget mémoire du jeu. La réussite dans DuckStation valide ce test technique limité, pas le jeu complet.

## Résultats du jalon entrées/audio

- Réconcilié le checkout local et son index avec le commit distant `88a9198252a90d428076f715f649255efa9c8863`; la branche `ps1-port` est propre à ce commit, sans second commit des modifications déjà présentes.
- Implémenté : le test manette indique maintenant nombre de boutons enfoncés, fronts actifs-bas pressés/relâchés et frames maintenues; la connexion initiale et une reconnexion ne créent pas de front artificiel.
- Implémenté : image audio facultative avec CUE piste de données + piste CD-DA, horloge de position via `CdlGetlocP`/Subchannel Q et pulse visuel 120 BPM. WAV de test synthétique généré hors dépôt par Python.
- Compilé : configuration CMake et build PSn00bSDK 0.24 ont produit `funkin-ps1-audio-probe.bin` (2 855 328 octets) et `.cue`, en plus de l'image d'entrée; aucune ressource OGG officielle n'est dans le dépôt.
- Exécuté/mesuré : la nouvelle image n'a pas pu être observée dans DuckStation pendant ce passage; il n'y a donc aucun résultat attestant du son entendu, du rythme visuel ni de dérive mesurée. Les états ON des boutons, les fronts et la reconnexion n'ont pas non plus été validés en émulateur.
- À vérifier : tester les touches avec une manette utilisable dans l'émulateur; le probe CD-DA précédent n'a pas été validé à l'écoute; obtenir les stems localement pour l'essai Bopeebo, puis répéter sur console réelle.

## Décision SPU et probe de streaming

- Décision : le chemin audio du portage part sur le streaming ADPCM VAGi vers la SPU, afin de pouvoir gérer instrumental et voix joueur séparément. CD-DA reste disponible comme comparaison de lecture et d'horloge disque.
- Implémenté : `ps1/spu_probe.c` recherche `STREAM.VAG` sur le disque, alimente le pilote `sound/cdstream` livré avec l'installation PSn00bSDK 0.24 et affiche `Stream_GetSamplesPlayed()`, l'heure calculée depuis la fréquence d'échantillonnage et le repère à 120 BPM. Le compteur est ancré aux IRQ de blocs SPU et interpolé par le timer VSync du pilote; il ne dérive donc pas par simple accumulation d'images, mais l'interpolation demeure de résolution frame entre IRQ audio.
- Compilé : `ps1-spu-disc` a été construit avec le `STREAM.VAG` stéréo d'exemple fourni par PSn00bSDK hors dépôt. L'image de test fait 5 741 232 octets. La compilation a produit deux avertissements `-Wdiscarded-qualifiers` dans `stream.c` fourni par le SDK; `spu_probe.c` s'est compilé sans avertissement.
- Exécuté/mesuré : DuckStation a été lancé avec l'image, mais le processus n'a exposé aucune fenêtre à cette session et a été arrêté. Aucun affichage, son, pulse, compteur, underrun ou dérive n'a donc été observé/mesuré.
- À vérifier : ouvrir `build/funkin-ps1-spu-probe.cue` dans DuckStation, vérifier lecture stéréo, position audio et compteurs d'underrun/erreurs CD sur toute la durée, puis répéter sur console réelle. Tester ensuite un VAGi à quatre canaux issu des stems officiels Bopeebo et mesurer leur atténuation indépendante.

## Audit SPU et fixture stéréo

### Audit du lecteur PSn00bSDK 0.24

Le code source installé de l'exemple `sound/cdstream` a été inspecté dans `stream.c/.h`; il n'est pas copié dans le dépôt. `Stream_GetSamplesPlayed()` combine `play_time` et une interpolation entre le dernier IRQ de bloc SPU et l'instant courant. À chaque IRQ sans underrun, `play_time` avance de `interleave / 16 * 28` échantillons par canal, puis le pilote mémorise le timer. Le timer par défaut est `VSync(-1)` et sa fréquence vaut 60 Hz en NTSC ou 50 Hz en PAL: l'interpolation est donc quantifiée par frame, même si l'ancre vient du bloc audio SPU. Le compteur garde sa monotonie lorsque le lecteur CD boucle les secteurs; il n'est pas une position circulaire.

Le chemin underrun de l'IRQ appelle le callback et réactive l'interruption sans incrémenter `play_time` ni modifier `last_updated`. Après cet événement, l'interpolation de temps continue depuis l'ancre précédente et n'est plus une mesure crédible du son effectivement joué. Le probe incrémente un compteur puis arrête le test avec une erreur explicite. Le chemin de lecture CD vérifie `CdControl`/`CdRead`, examine les retours négatifs de `CdReadSync(1)`, consigne `CdlDiskError` et limite à 600 VBlanks l'attente de l'en-tête et du préchargement; un disque absent ou mal formé n'attend plus indéfiniment.

Le VAGi est un en-tête de 48 octets au début d'un secteur de 2048 octets, suivi de tranches ADPCM alternées par canal et complétées au dernier secteur. Le parseur accepte seulement le format VAGi v0x20, le stéréo du premier jalon, un interleave multiple de 2048 et de 16 octets, une taille de canal multiple de 16, un taux de 4–44,1 kHz, et un payload calculé qui tient dans la taille ISO réelle. Pour l'interleave 4096 du fixture, une tranche canal contient 256 blocs ADPCM de 16 octets et produit 7 168 échantillons. Le buffer circulaire RAM fait 98 304 octets; le lecteur demande un remplissage à partir de 49 152 octets libres (24 secteurs). Le double-buffer SPU du test stéréo occupe 16 384 octets de `0x1010` à `0x5010`, très en deçà des 512 Kio de RAM SPU. `Stream_Init()` utilise toutefois un `assert(malloc(...))` dans la bibliothèque SDK; l'application peut borner les paramètres et les allocations attendues, mais ne peut pas récupérer proprement d'un échec de cet `malloc` sans adapter le pilote.

Les codes d'échec affichés sont: 1 fichier introuvable, 2 lecture d'en-tête, 3 format ou bornes VAGi, 4 commande CD, 5 lecture CD, 6 expiration du préchargement, 7 démarrage du stream, 8 underrun. Les compteurs runtime d'erreurs CD et d'underrun sont affichés tant que le test reste valide.

### Fixture généré et disponibilité de l'essai

`ps1/generate_spu_fixture.py` génère hors dépôt un clic/basse ADPCM synthétique de 8 secondes, 16 temps à 120 BPM, 43 008 Hz, interleave 4096, 2 canaux et 48 blocs de stream. Chaque temps dure exactement 21 504 échantillons (3 blocs); la boucle de 16 temps correspond exactement à 48 blocs. Ce signal n'utilise aucun asset FNF ni ressource SDK. Le fixture généré pendant ce passage fait 395 264 octets; le programme C compilé fait 40 960 octets et l'image BIN/CUE fait 858 480 octets/86 octets.

DuckStation 0.1-8675 est installé et démarre avec son interface. Plusieurs essais de lancement CLI n'ont pas chargé le disque; depuis l'interface, la boîte native « Choisir une Image Disque » apparaît, mais l'outil de contrôle ne permet pas de cibler cette fenêtre modale séparée. Le BIN/CUE a donc été produit après fermeture de l'émulateur, mais **n'a pas été exécuté**. Aucun son entendu, pulse observé, compteur, boucle, compteur d'erreurs ou underrun n'est rapporté. Aucune dérive n'a été mesurée, et le jalon SPU n'est pas validé. Les essais multi-minutes ne sont pas faits.

Pour permettre un essai manuel: lancer DuckStation, choisir `Système → Démarrer le fichier…`, ouvrir `ps1/build/funkin-ps1-spu-probe.cue`, puis écouter le clic stéréo et confirmer que `AUDIO`/`SAMPLES` avancent, que le repère clignote à 120 BPM et que le son reboucle à 8 secondes tandis que le compteur reste croissant. Laisser tourner au moins trois minutes, noter le nombre d'échantillons et de battements au début et à la fin, puis comparer clics audibles et repères aux deux extrémités. Noter séparément le constat visuel et la dérive calculée; tout compteur CD ou underrun non nul invalide l'essai.

Le probe entrées n'a détecté jusqu'ici que la présence d'une manette numérique et affiché ses valeurs inactives. Les directions, boutons de façade, Start, appuis/maintien/relâchement, simultanéité et déconnexion/reconnexion restent à vérifier en lançant `ps1/build/funkin-ps1-probe.cue` et en lisant les masques/frames d'état à l'écran.

Le test quatre canaux n'a pas été construit, conformément à la dépendance demandée envers la validation stéréo. Estimation à 43 008 Hz et interleave 4096: 4 canaux × 4096 octets × double-buffer = 32 Kio de SPU (`0x1010–0x9010`), 4 voix sur 24 utilisées, 96 Kio de RAM principale couvrant environ une seconde, payload CD d'environ 98,3 ko/s (48 secteurs de 2048 octets/s), laissant 20 voix SPU pour les effets. Ces budgets sont des calculs de capacité, pas des mesures de performance. Après validation stéréo, générer quatre canaux entrelacés instrumental G/D et voix G/D; atténuer les voix uniquement par leur volume SPU sans relâcher leurs clés, et comparer la position des deux paires pendant la coupure/restauration. Aucun gameplay, Bopeebo ou asset officiel n'est inclus dans cette étape.

### Correction après le premier essai manuel

Retour utilisateur dans DuckStation: `SPU STREAM ERROR`, code 6, `CD ERRORS 0`, `UNDERRUNS 0`. Le code 6 correspond au délai de préchargement, donc la lecture n'avait pas encore démarré et les zéros d'underrun étaient attendus. La cause a été confirmée: la lecture d'en-tête appelle `CdReadCallback(0)`, mais aucune lecture de flux ne réinstallait `cd_read_handler`. Le tampon restait donc vide et `read_pending` n'était jamais libéré par callback.

Correction: la fonction de lecture de flux initialise les diagnostics et `read_pending`, installe `CdReadCallback(cd_read_handler)`, puis appelle `CdRead`. Le callback ne crédite les secteurs et n'appelle `Stream_Feed()` que pour `CdlComplete`; `CdlDiskError` et tout événement inattendu marquent la lecture en erreur sans fournir de données au tampon. Les retours immédiats de `CdRead` et les résultats négatifs de `CdReadSync` libèrent également l'état en attente. En cas de timeout, une annulation CD est demandée et sondée pendant au plus 120 frames; le code n'attend pas indéfiniment. Les erreurs affichent maintenant la taille du tampon, l'état pending, les secteurs demandés/reçus et les callbacks reçus/réussis/échoués.

La condition de démarrage reste `buffer.length >= 24 secteurs + 1 chunk`, soit 57 344 octets pour le fixture; le buffer circulaire offre 98 304 octets. La première lecture peut fournir 48 secteurs (98 304 octets); sur un callback de fin réussi, le préchargement dépasse donc la condition. Cette atteignabilité est démontrée par les tailles et la logique, mais le comportement à l'exécution reste à confirmer avec le nouvel essai.

Compilation après correction: `funkin-ps1-spu-probe.exe` 43 008 octets, BIN 860 832 octets, CUE 86 octets, dans `ps1/build/spu-retry/` pour contourner le verrou du premier disque qui est encore ouvert dans DuckStation. Le build a réussi; les deux avertissements `-Wdiscarded-qualifiers` proviennent du `stream.c` externe de PSn00bSDK. Cette image corrigée **n'a pas été exécutée**. En attente d'un nouvel essai manuel; ni l'audio stéréo, ni la durée multi-minute, ni la dérive ne sont validés. Aucun test quatre canaux n'a été démarré.

### Correction du contrat callback après le deuxième essai manuel

Le rapport suivant de DuckStation était `CODE 5`, `CD ERRORS 1`, `BUFFER 0 / 98304`, `READ PENDING 0`, `SECTORS REQ 48`, `CALLBACKS 1 / OK 0 / ERR 0`, `SECTORS RX 0`. Il confirme qu'un callback arrivait mais qu'aucune donnée n'était fournie au stream. La comparaison avec PSn00bSDK 0.24 a révélé l'incompatibilité: `libpsn00b/psxcd/cdread.c` appelle le callback enregistré avec l'interruption du dernier secteur, `CdlDataReady` (valeur numérique 1), après copie des secteurs demandés dans le tampon destination. L'implémentation ne convertit pas la réussite de `CdRead()` en `CdlComplete`. Elle transmet `CdlDiskError` en cas d'erreur disque. Le feeder de `examples/sound/cdstream/main.c` ignore de la même façon seulement `CdlDiskError` avant `Stream_Feed()`.

Dans PSn00bSDK 0.24, `CdRead()` retourne 1 lorsque la lecture asynchrone a démarré et 0 lorsqu'elle n'a pas démarré (y compris lorsqu'une autre lecture est encore active); cette valeur n'est pas un nombre de secteurs lus. `CdReadSync(1, result)` interroge la lecture: une valeur positive indique le nombre de secteurs toujours en attente, 0 indique qu'il n'en reste aucun, -1 une erreur d'expiration/nouvelles tentatives, et -2 une opération interrompue. En mode 1, cette implémentation ne remplit pas le pointeur de résultat. Une fois la lecture terminée, `CdReadSync(0, result)` retourne 0 en cas de commande complète, -1 en cas d'échec ou -2 en cas d'interruption; le buffer reçoit alors les octets de réponse de `CdSync(0, result)`.

Le callback accepte maintenant `CdlDataReady` comme fin réussie et fournit exactement `secteurs demandés × 2048` octets seulement pour cet événement. Une erreur disque ou un événement inattendu ne fournit aucune donnée. `read_pending` est libéré par callback terminal, démarrage refusé, résultat terminal de synchronisation ou traitement borné d'expiration/annulation. Le compteur `read_errors` augmente une seule fois par lecture échouée, avec une cause conservée. L'écran d'erreur ajoute l'événement numérique, les quatre octets du payload de callback, le dernier retour de `CdRead`, le dernier retour et les octets de réponse de `CdReadSync`, ainsi que le code et le nom de la cause.

L'ancienne image rapportée lors de l'essai avait `STREAM.VAG` à l'extent LBA 45. Dans la nouvelle image inspectée après compilation, le fichier a son extent en LBA 46 et une taille de 395 264 octets; le LBA 46 contient l'en-tête VAGi et le payload de 192 secteurs va du LBA 47 au LBA 238 inclus. La première lecture de 48 secteurs demande donc les LBA 47–94 inclus, dans le payload et dans l'image actuelle de 367 secteurs bruts. `read_ctx.start_lba = CdPosToInt(file.pos) + 1` pointe bien au premier secteur payload. Aucun dépassement de l'étendue du fichier ou de l'image n'est observé.

La nouvelle source est compilée séparément sous `ps1/build/spu-contract-fix/`; le BIN produit fait 863 184 octets (367 secteurs bruts) et le CUE 86 octets. La compilation GCC 12.3.0 / PSn00bSDK 0.24 a réussi; les deux seuls avertissements sont des suppressions de `volatile` dans le `stream.c` externe du SDK. Cette image n'a pas été relancée dans DuckStation après la correction. Le décalage de contrat callback est corrigé dans le code, mais le préchargement, la lecture SPU, la boucle et la synchronisation attendent encore une observation manuelle. Ce jalon reste stéréo; aucun test quatre canaux n'a commencé.

