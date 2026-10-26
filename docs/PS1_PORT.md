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

### Résultat stéréo observé par l'utilisateur

L'utilisateur a ensuite confirmé un essai manuel DuckStation de 4 min 02 s sur l'image stéréo du commit `46dbb5d`: 0 underrun, 0 erreur CD et aucun problème signalé à l'écoute. Cela valide le test stéréo dans DuckStation pour cette durée. La dérive précise n'a pas été mesurée et aucune console réelle n'a été testée. Le test quatre canaux qui suit reste distinct et non validé.

### Prototype VAGi quatre canaux

Le lecteur [`stream.c`/`stream.h` de `sound/cdstream` PSn00bSDK 0.24](https://github.com/Lameguy64/PSn00bSDK/tree/v0.24/examples/sound/cdstream) prend réellement en charge un nombre configurable de canaux : `Stream_Init()` compte les bits de `channel_mask`, fixe `chunk_size = interleave × num_channels`, puis ses IRQ parcourent les canaux activés et transfèrent le bloc entrelacé. Le VAGi décrit le nombre de canaux et la taille d'interleave par canal. Le prototype utilise les canaux 0–3 du masque `0x0f`, ordonnés instrumental gauche, instrumental droite, voix gauche, voix droite. Il conserve un seul callback/flux de lecture CD et une seule horloge SPU pour les quatre canaux.

La nouvelle cible et le nouveau disque sont indépendants du test stéréo. Le fixture synthétique garde le clic/basse instrumental sur les canaux 0/1 et ajoute un motif tonal distinct sur 2/3, décalé d'un demi-temps. `CIRCLE` est le bouton de bascule; le probe ne touche qu'aux registres de volume des canaux voix (2/3), sans modifier leurs clés, l'adresse ou la position du flux. L'écran affiche la connexion, l'état appuyé/relâché de Circle, l'état des voix, la position audio, le tampon, les erreurs CD et les underruns.

La marge de mixage du fixture quatre canaux est volontaire : amplitude maximale instrumentale bornée à 0,42 pleine échelle par côté et voix à 0,14/0,12; borne conservatrice de la somme d'entrée d'environ 0,56 avant atténuation. Le volume initial des quatre voix est `0x2fff` (75 % de `0x3fff` nominal), avec les voix commutées entre ce niveau et zéro. Ce calcul de crête est un budget numérique conservateur, pas une mesure de sortie analogique ni une validation de clipping sur console.

Budgets pour 4 096 octets d'interleave, 43 008 Hz et 4 canaux : un chunk contient 16 384 octets et 7 168 échantillons par canal, soit 1/6 seconde; le double-buffer SPU prend 32 Kio, de `0x1010` à `0x9010`, et utilise 4 des 24 voix. Le ring buffer en RAM principale reste 96 Kio, soit environ une seconde à 98 304 octets/s; le seuil de remplissage de 24 secteurs vaut 48 Kio et le préchargement minimal seuil + un chunk vaut 64 Kio. Le lecteur peut demander jusqu'à 48 secteurs / 96 Kio en un read initial. Le débit encodé du stream est 98 304 octets/s, soit 48 secteurs de données/s; ces chiffres ne mesurent ni les seeks, ni la marge réelle du lecteur CD, ni le temps CPU. La fixture de 8 secondes attendue contient 48 chunks, 384 secteurs payload et 788 480 octets avec son secteur d'en-tête.

Le générateur préserve les niveaux et la sortie binaire du fixture stéréo; l'atténuation des niveaux ne s'applique qu'à la variante quatre canaux. Build depuis `ps1/` avec l'installation PSn00bSDK déjà décrite plus haut :

```powershell
$fixture4 = Join-Path $env:TEMP 'fnf-spu-4ch.vag'
python .\generate_spu_fixture.py $fixture4 --channels 4 --loop-beats 16
cmake --preset default -B .\build\spu-four-channel "-DFUNKIN_PS1_AUDIO_VAGI_4CH=$fixture4"
cmake --build .\build\spu-four-channel --target ps1-spu-4ch-disc
```

Test manuel court : ouvrir `build/spu-four-channel/funkin-ps1-spu-4ch-probe.cue` dans DuckStation. Vérifier le clic/basse instrumental et le motif vocal distinct; appuyer plusieurs fois sur Circle et confirmer que seules les voix se coupent/reviennent alors que le compteur `SAMPLES` continue. Laisser tourner plusieurs minutes et contrôler `CD ERRORS` et `UNDERRUNS` à zéro. Le résultat d'exécution doit être noté après observation; compilation seule ne valide pas la lecture quatre canaux. Aucun essai console réelle n'est effectué dans ce jalon.

Résultats de construction du prototype : la fixture 4ch générée hors dépôt fait 788 480 octets, 43 008 Hz, 4096 octets d'interleave, 48 chunks et 8 secondes (SHA-256 `97AD644498C8BEED1FC9C55B5A31A036CE88E11DF1237D3854409326F2A6E131`). L'image `build/spu-four-channel/` a été compilée avec GCC 12.3.0 / PSn00bSDK 0.24 : EXE 45 056 octets, BIN 1 314 768 octets (559 secteurs bruts), CUE 90 octets. Dans l'ISO, `STREAM.VAG` commence au LBA 46 (en-tête); le payload est LBA 47–430 et le premier read de 48 secteurs est LBA 47–94. Seuls les deux avertissements `-Wdiscarded-qualifiers` de `stream.c` externe apparaissent. Le code a été compilé, mais l'image quatre canaux n'a pas été exécutée.

Le chemin stéréo reste reproductible : la fixture stéréo régénérée a correspondu octet pour octet au VAGi de l'image de référence (SHA-256 `70F5E6818CEDABFC6A05CECD6C3AF00144D8B4F85CB2975C842D07E095B9DFD6`). La cible existante `ps1-spu-disc` a été reconfigurée et recompilée dans `build/spu-stereo-recheck/`; elle produit toujours une image de 863 184 octets. Ce re-build n'est pas une seconde observation d'exécution; la validation manuelle de 4 min 02 s rapportée plus haut est le résultat d'écoute stéréo.

### Résultat quatre canaux confirmé et premier morceau officiel

L'utilisateur a ensuite confirmé le test synthétique quatre canaux du commit `c89d519` dans DuckStation : 3 min 08 s, aucun underrun, aucune erreur CD, coupure et rétablissement des voix avec Circle fonctionnels. La dérive précise n'a pas été mesurée; aucune console réelle n'a été testée.

#### Fichiers et organisation Bopeebo

Le test utilise exclusivement la version classique des stems de Bopeebo présents dans le sous-module `assets` épinglé à `724eba9de9e76761d9cefd52169926bc51c760a5`. Les chemins sont `songs/bopeebo/Inst.ogg`, `Voices-bf.ogg` et `Voices-dad.ogg`; leurs blobs Git sont respectivement `593052bfcf9f4931d597cd912c96716581af5c29`, `5394f467230fada6114753615f79d2280f0e0f00` et `bfd1edf25670d418e8e633aaf1cb7c7f4edb9770`. Les trois sont des Vorbis stéréo, 44 100 Hz, 81,6 s. Le jeu lui-même résout les voix séparément pour le personnage joueur et l'adversaire dans [`Song.hx`](../source/funkin/play/song/Song.hx) (`buildPlayerVoiceList()` / `buildOpponentVoiceList()`). Ici, BF est le stem joueur et Dad celui de l'adversaire. Circle atténue BF uniquement; Dad continue à jouer. Ce test n'émule donc pas encore le mixage par note ou le comportement du gameplay.

La licence des ressources à cette révision indique « All rights reserved » et interdit leur redistribution publique sans autorisation. Seuls le code du convertisseur et les références de provenance sont suivis par Git : OGG, WAV PCM, VAGi, EXE, BIN et CUE demeurent hors du dépôt, dans `%TEMP%` ou dans un répertoire de build ignoré. La licence Apache-2.0 du code du jeu ne couvre pas ces ressources audio.

Les trois sources locales contrôlées sont des OGG Vorbis stéréo, 44 100 Hz et 81,600 s : `Inst.ogg` (939 552 octets, débit moyen calculé 92,1 kbit/s), `Voices-bf.ogg` (714 105 octets, 70,0 kbit/s) et `Voices-dad.ogg` (705 962 octets, 69,2 kbit/s). Les fichiers décodés sont alignés à l'origine et en durée. Le flux VAGi ordonne les canaux instrumental L/R, BF L/R, Dad L/R. Aucun stem n'est normalisé indépendamment. Un seul feeder garde les six canaux synchronisés. Le probe applique un gain commun (`0x2800`, 62,5 %) et Circle atténue BF seulement sans arrêter ni déplacer sa lecture.

La première conversion à 22 050 Hz était un choix conservateur de débit CD pour six canaux ADPCM, et non une limite du SPU ou de la PS1. Le SPU accepte des fréquences de lecture bien supérieures, et l'exemple `cdstream` de PSn00bSDK documente un flux jusqu'à 44,1 kHz. La variante 43 008 Hz permet en outre un chunk de 166,7 ms, soit exactement deux chunks par temps à 120 BPM avec l'interleave de 4096 octets. La fréquence doit néanmoins être vérifiée avec le pilote et le rendu sur l'émulateur puis sur console.

Le budget comparatif à interleave 4096 octets par canal est le suivant. Le double-buffer SPU est 48 Kio dans les deux variantes (`0x1010–0xD010`), utilise 6 des 24 voix et laisse 18 voix pour les effets; le ring buffer principal reste 96 Kio.

| Fréquence | Durée d'un chunk | Débit six canaux | Secteurs 2048 o/s | Couverture du ring 96 Kio |
|---|---:|---:|---:|---:|
| 22 050 Hz | 325,1 ms | 75 600 o/s | 36,9 | 1,30 s |
| 43 008 Hz | 166,7 ms | 147 456 o/s | 72 | 0,67 s |

Le CD en double vitesse transporte nominalement jusqu'à 150 secteurs de données/s; 43 008 Hz représente donc 48 % de ce débit brut. Le seuil de refill de 48 Kio plus un chunk de 24 Kio demande 72 Kio de préchargement. Ce budget rend la variante plausible en lecture séquentielle et laisse une marge de débit théorique, sans mesurer les seeks, interruptions, autres lectures CD ou les marges CPU/RAM sur console.

L'encodeur padde chaque stem jusqu'à une frontière commune de chunk puis ajoute trois chunks silencieux. Le lecteur VAGi désactive la boucle logicielle uniquement pour cette cible : arrivée au bout du fichier, il ne redemande pas le LBA initial. L'écran affiche le compteur SPU, un indicateur de battement dérivé de ce compteur, le tampon, les erreurs CD/underruns, l'état de la manette, l'état de Circle, BF muet/audible, Dad audible et `FINISHED`. Après 81,6 s, le compteur musical est plafonné et le lecteur arrête le SPU après deux chunks de garde, pendant la queue silencieuse; cela évite de vider le ring buffer à la dernière interruption. Le test reste un essai audio seulement : aucun chart, jugement, score, dialogue ou graphisme du jeu n'est intégré.

#### Reproduire le test

Depuis `ps1/`, avec PSn00bSDK 0.24, CMake, Ninja, Python 3 et FFmpeg installés comme dans la section Toolchain de [`README.md`](../ps1/README.md) :

```powershell
git submodule update --init assets
$song = '..\assets\songs\bopeebo'
$work = Join-Path $env:TEMP 'fnf-bopeebo-724eba9'
New-Item -ItemType Directory -Force $work | Out-Null
foreach ($stem in 'Inst', 'Voices-bf', 'Voices-dad') {
  ffmpeg -hide_banner -y -i "$song\$stem.ogg" -map 0:a:0 -ac 2 -ar 22050 -c:a pcm_s16le "$work\$stem-22050.wav"
}
python .\convert_bopeebo_to_vagi.py "$work\bopeebo.vag" `
  --instrumental "$work\Inst-22050.wav" `
  --player-voice "$work\Voices-bf-22050.wav" `
  --opponent-voice "$work\Voices-dad-22050.wav"
cmake --preset default -B .\build\bopeebo-audio-final "-DFUNKIN_PS1_AUDIO_VAGI_BOPEEBO=$work\bopeebo.vag"
cmake --build .\build\bopeebo-audio-final --target ps1-bopeebo-audio-disc
```

Ouvrir les deux images ignorées par Git, `build/bopeebo-audio-final/funkin-ps1-bopeebo-audio.cue` (22 050 Hz) et `build/bopeebo-audio-43008-final/funkin-ps1-bopeebo-audio.cue` (43 008 Hz), dans DuckStation pour comparer. Circle/L coupe/rétablit BF; Dad et l'instrumental doivent continuer. Laisser chaque morceau finir sans rebouclage et surveiller les compteurs. L'utilisateur a confirmé le test Bopeebo initial, y compris Circle avec la touche L de DuckStation, mais a jugé le son dégradé. La nouvelle image haute fréquence a été exécutée pendant les 81,6 s; le mute Circle/L de cette variante n'a pas été retesté.

#### Analyse de qualité et variante 43 008 Hz

L'analyse reproductible `ps1/analyze_bopeebo_audio.py` compare les PCM source, les PCM après rééchantillonnage et le VAGi décodé avec le décodeur ADPCM correspondant. Les SNR/RMSE ADPCM sont mesurés par rapport au PCM de même fréquence; le rééchantillonnage est évalué en reconvertissant vers 44,1 kHz et comparant au décodage source. Les chiffres ci-dessous sont des mesures numériques hors émulateur, pas une mesure de sortie analogique.

| Étape / comparaison | 22 050 Hz | 43 008 Hz |
|---|---:|---:|
| Mix PCM source 44,1 kHz : RMS / pic | 6 608,1 / 43 689 | 6 608,1 / 43 689 |
| Mix PCM à fréquence cible : RMS | 6 603,7 | 6 608,1 |
| Pic du mix PCM rééchantillonné | 42 132 | 43 270 |
| PCM rééchantillonné, aller-retour vs source 44,1 kHz (SNR) | 30,06 dB | 78,75 dB |
| Ancien encodeur ADPCM, erreur PCM→décodage (SNR) | 14,38 dB | 14,56 dB |
| Encodeur corrigé ADPCM, erreur PCM→décodage (SNR) | 28,38 dB | 35,08 dB |
| Encodeur corrigé, RMSE | 251,7 LSB | 116,5 LSB |
| Mix décodé ADPCM corrigé : RMS | 6 608,6 | 6 609,2 |
| Pic du mix décodé ADPCM corrigé | 42 772 | 43 194 |

L'analyse a isolé deux causes : le rééchantillonnage à 22 050 Hz enlève davantage de contenu aigu, et l'ancienne sélection du champ `shift` ADPCM choisissait une quantification trop grossière (le champ est inverse : une valeur plus élevée donne un pas plus fin). Le convertisseur choisit maintenant le pas le plus fin qui contient les résidus; la qualité numérique s'améliore nettement aux deux fréquences. Le rééchantillonneur 43 008 Hz utilise FFmpeg `aresample` avec filtre 64 taps, cutoff 0,97; la commande antérieure à 22 050 utilisait le rééchantillonneur SWR par défaut. L'analyse ne permet pas à elle seule de quantifier le rendu subjectif, les filtres matériels ou l'aliasing du SPU.

La somme des stems PCM à gain unitaire culmine à 43 689, au-dessus de la pleine échelle 16 bits, donc l'addition brute saturerait. Le probe garde les gains relatifs et applique un gain commun `0x2800` (62,5 %); après ADPCM corrigé, le pic observé est 26 734 à 22 050 Hz et 26 998 à 43 008 Hz, sans échantillons au-delà de ±32 767 (environ 1,7–1,8 dB de marge). Aucun limiteur ni normalisation individuelle n'est appliqué. Le niveau analogique reste à écouter.

Pour régénérer la variante haute fréquence, rééchantillonner chaque stem à 43 008 Hz avec un départ identique, `-ac 2 -ar 43008 -af aresample=43008:filter_size=64:phase_shift=10:linear_interp=0:cutoff=0.97 -c:a pcm_s16le`, puis lancer `convert_bopeebo_to_vagi.py ... --rate 43008`. Le compte exact est 3 509 453 images par canal (81,600005 s); configurer CMake avec `-DFUNKIN_PS1_AUDIO_SAMPLE_COUNT=3509453u`. Pour 22 050 Hz, conserver l'image A/B existante; elle n'est pas remplacée.

#### Résultat de compilation et exécution de cet essai

La version A/B de référence à 22 050 Hz est conservée hors Git : VAGi 6 268 928 octets, 255 chunks; BIN 7 608 720 octets, CUE 90 octets, SHA-256 `240EF6D1DFD0FA8694BCDEFF7CDF0F650CA5EF7817A7F93E59B6492734BBA902`. Elle correspond à l'ancienne quantification ADPCM et reste utile pour l'écoute comparative.

Cette première image a été exécutée dans DuckStation 0.1-8675 sur les 81,6 s; fin sans rebouclage, `UNDERRUNS 0`, `CD ERRORS 0`. L'utilisateur a confirmé le jalon Bopeebo et le mute BF avec Circle/L. Il a signalé une qualité sonore dégradée, ce qui a motivé la comparaison PCM/ADPCM ci-dessus.

La variante corrigée à 43 008 Hz a été recompilée et exécutée dans DuckStation 0.1-8675. Observations écran : 00:00.866 / 37 273 échantillons, 00:24.766 / 1 065 164, 00:58.699 / 2 524 569, puis 01:21.600 / 3 509 453 et `FINISHED (NO LOOP)`. Tous ces points montraient `UNDERRUNS 0` et `CD ERRORS 0`; ce n'est pas une mesure de dérive à une horloge externe. L'écoute A/B subjective et le mute Circle/L sur cette image corrigée restent à faire par l'utilisateur; aucune console réelle n'a été testée.

La variante corrigée 43 008 Hz est hors Git dans `build/bopeebo-audio-43008-final`: VAGi 12 118 016 octets, 493 chunks; BIN 14 326 032 octets, CUE 90 octets, SHA-256 `E288B8C1889BCC8DA248321DE32EC70C10BE50688849278F19E21FD8E2112C49`. Les deux images restent sous des dossiers distincts ignorés par Git. La compilation GCC 12.3.0 / PSn00bSDK 0.24 a réussi; les avertissements observés sont deux conversions `volatile` dans `stream.c` fourni par le SDK. Aucune écoute acoustique contrôlée n'a été faite par l'agent.

### Comparaison Bopeebo quatre canaux à 43 008 Hz, avec effets

L'utilisateur confirme maintenant subjectivement la qualité de la référence Bopeebo six canaux à 43 008 Hz et que son mute BF par Circle (`L` dans DuckStation) fonctionne. Cette image six canaux reste inchangée dans `ps1/build/bopeebo-audio-43008-final/` pour l'écoute A/B.

La nouvelle variante conserve les mêmes trois stems de l'assets épinglé, leur origine commune, leurs PCM 43 008 Hz et l'encodeur ADPCM corrigé. L'ordre VAGi est instrumental L/R, Dad mono, BF mono. Les stems de voix sont ramenés en mono par moyenne signée `(L+R)/2`, avec arrondi à l'entier le plus proche. L'analyse des PCM locaux donne Dad corrélation L/R `0,997517`, variation RMS `−0,005 dB`, crête 16 440; BF `0,994837`, `−0,011 dB`, crête 19 869. Les canaux sont donc très corrélés et cette moyenne ne montre pas d'annulation de phase mesurable; le niveau RMS change de moins de 0,02 dB. Aucun stem n'est normalisé seul.

Les quatre voies musicales partagent le volume `0x2800` (62,5 % de `0x3fff`). Dans la première build comparative (commit `fad4fde`), Dad était à gauche et BF à droite en largeur initiale 7/7. Après le retour utilisateur, la largeur initiale est 5/7. Les flèches gauche/droite règlent un paramètre de largeur de 0 à 7 en changeant seulement les volumes SPU : aucun réencodage n'est nécessaire. La loi de panoramique à puissance constante utilise les facteurs Q14 gauche/droite suivants, ensuite multipliés par le gain musical commun : `(0,707; 0,707)`, `(0,782; 0,624)`, `(0,847; 0,532)`, `(0,901; 0,434)`, `(0,944; 0,330)`, `(0,975; 0,223)`, `(0,994; 0,112)`, `(1; 0)`. Dad suit cette courbe de gauche vers le centre; BF en est le miroir. Circle (`L`) met à zéro seulement le volume BF, puis le restaure au même panoramique, sans arrêter son flux ni changer sa position. Le bouton Square (`J`) déclenche l'effet d'essai.

L'effet sonore synthétique est un bip ADPCM résident de 0,122 s, 1 536 octets et 22 050 Hz; le code est incorporé à l'EXE puis copié une seule fois en RAM SPU à `0x10000`. Quatre voix SPU dédiées (4–7) servent de pool à rotation pour les déclenchements rapprochés. La première implémentation utilisait un volume fixe `0x0800` par voix; le diagnostic ultérieur décrit plus bas plafonne maintenant la somme des volumes du pool à `0x1800` et réalloue ce budget selon le nombre de voix actives. L'analyse ADPCM mesure une crête décodée de 4 787 LSB. Avec le nouveau plafond, les quatre effets simultanés sont bornés à 1 796 LSB par sortie. La musique décodée et panoramiquée, au gain commun, culmine à 25 474/26 672 LSB L/R en largeur maximale; la marge numérique conservatrice est d'au moins 1,22 dB en sortie droite. Ce calcul vérifie le mix numérique du test, pas le niveau analogique ni les effets du matériel réel.

L'analyse reproductible du downmix et du mixage ADPCM est `ps1/analyze_bopeebo_4ch_audio.py`; elle décode les quatre voies VAGi et l'effet VAGp, évalue les panoramiques centré/intermédiaire/large, puis ajoute la borne de quatre effets. Pour ce probe :

| Ressource | Allocation mesurée ou configurée | Réserve / interprétation |
|---|---:|---|
| RAM principale : EXE chargé (code, données et échantillon source SFX) | 47 104 o | inclut les 1 536 o SFX encodés |
| RAM principale : BSS statique du linker | 7 456 o | inclut l'état SDK et la pile d'interruptions de 4 Kio |
| RAM principale : ring audio `malloc` | 98 304 o (96 Kio) | couvre 1,0 s à 98 304 o/s; cela consomme toujours ces 96 Kio, la durée de réserve n'est pas une économie de RAM |
| RAM principale : total suivi du probe | 152 864 o (149,3 Kio) | EXE + BSS + ring; n'inclut pas les réserves système et la pile d'exécution |
| RAM SPU : double tampon musical | 32 768 o (32 Kio) | quatre voies × 2 tampons × 4 096 o, `0x1010–0x9010` |
| RAM SPU : effet résident | 1 536 o | `0x10000`, préchargé avant le morceau |
| RAM SPU : réservé par ce probe / espace libre arithmétique | 34 304 / 489 984 o | 33,5 / 478,5 Kio sur 512 Kio; le jeu et le SDK auront leurs propres besoins |
| Voix SPU | 8 utilisées / 16 libres | 4 musique + 4 pool SFX sur 24; les 16 restantes sont une réserve de conception, pas une garantie du jeu complet |
| CD | 98 304 o/s = 48 secteurs de 2 048 o/s | 32 % du débit nominal 2× de 150 secteurs/s; seeks et lectures concurrentes non mesurés |

Le VAGi musical fait 8 079 360 octets. Son débit explique le tampon de 1 seconde; celui-ci coûte bien les 96 Kio indiqués. Le probe réserve aussi 32 Kio SPU de musique, plus l'effet. Ces chiffres sont spécifiques à cette scène de test. Ils ne budgètent pas les charts, personnages, animations, décors, interfaces et sons de gameplay; ils doivent donc rester séparés de toute affirmation sur la place disponible pour le jeu final. Les allocations CPU/heap et les réserves de l'OS devront être remesurées avec le port jouable.

La conversion, l'image et l'analyse se reproduisent depuis `ps1/` (PSn00bSDK 0.24, CMake, Ninja, FFmpeg et Python déjà installés comme décrit dans `ps1/README.md`). Les fichiers de stems et VAGi restent hors Git :

```powershell
$song = '..\assets\songs\bopeebo'
$work = Join-Path $env:TEMP 'fnf-bopeebo-724eba9'
New-Item -ItemType Directory -Force $work | Out-Null
foreach ($stem in 'Inst', 'Voices-bf', 'Voices-dad') {
  ffmpeg -hide_banner -y -i "$song\$stem.ogg" -map 0:a:0 -ac 2 `
    -af 'aresample=43008:filter_size=64:phase_shift=10:linear_interp=0:cutoff=0.97' `
    -c:a pcm_s16le "$work\$stem-43008.wav"
}
python .\convert_bopeebo_4ch_to_vagi.py "$work\bopeebo-43008-4ch.vag" `
  --instrumental "$work\Inst-43008.wav" `
  --player-voice "$work\Voices-bf-43008.wav" `
  --opponent-voice "$work\Voices-dad-43008.wav" --rate 43008
cmake --preset default -B .\build\bopeebo-audio-4ch-43008 `
  "-DFUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH=$work\bopeebo-43008-4ch.vag" `
  -DFUNKIN_PS1_AUDIO_4CH_SAMPLE_COUNT=3509453u
cmake --build .\build\bopeebo-audio-4ch-43008 --target ps1-bopeebo-audio-4ch-disc
python .\analyze_bopeebo_4ch_audio.py `
  --instrumental "$work\Inst-43008.wav" --dad "$work\Voices-dad-43008.wav" `
  --bf "$work\Voices-bf-43008.wav" --vagi "$work\bopeebo-43008-4ch.vag" `
  --sfx .\build\bopeebo-audio-4ch-43008\bopeebo_sfx.vag
```

Ouvrir `ps1/build/bopeebo-audio-4ch-43008/funkin-ps1-bopeebo-4ch-audio.cue` dans DuckStation pour l'essai A/B avec le CUE six canaux conservé ci-dessus. Confirmer instrumental stéréo, Dad à gauche, BF à droite; tester la largeur avec les flèches; appuyer sur `L` pour couper/rétablir BF; appuyer plusieurs fois rapidement sur `J` pour vérifier le pool d'effets; surveiller position audio, fin sans boucle, `UNDERRUNS` et `CD ERRORS`. La lecture observée par l'agent a atteint `FINISHED (NO LOOP)` à 01:21.600 avec compteur 3 509 453, 0 underrun et 0 erreur CD. L'écran affichait le tampon, le mute, la largeur, l'effet et son compteur. L'agent n'a pas confirmé à l'écoute la balance, n'a pas obtenu de validation de chaque bouton dans cette session et n'a pas mesuré de dérive. Le fonctionnement sonore de la variante quatre canaux et des effets reste à faire confirmer en essai A/B; seule la référence six canaux et le prototype quatre canaux synthétique précédent ont un retour subjectif utilisateur. Aucune console réelle n'a été testée.

Compilation PSn00bSDK 0.24 / GCC 12.3.0 réussie : EXE 47 104 octets, BIN `funkin-ps1-bopeebo-4ch-audio.bin` 9 690 240 octets, CUE 94 octets. Le BIN contient 4 120 secteurs MODE2/2352. Le CUE et BIN sont dans `ps1/build/bopeebo-audio-4ch-43008/`, ignoré par Git; aucune ressource audio officielle n'est ajoutée au dépôt.

### Retour utilisateur et diagnostic SFX

L'utilisateur préfère subjectivement cette variante quatre canaux, confirme le panoramique et le mute BF par Circle (`L`), demande une largeur initiale `5` et souhaite conserver ce réglage dans les futures options. Le probe démarre maintenant à `PAN WIDTH 5/7`; les flèches gardent le réglage pendant l'exécution, mais il n'est pas encore persisté. La persistance sera ajoutée avec le futur menu d'options. La configuration quatre canaux est le choix privilégié actuel; le six canaux demeure une référence A/B disponible.

Le retour sur l'ancien essai était que DuckStation détectait Square (`J`), mais qu'aucun son d'effet n'était audible. Le code affiche maintenant l'état Square appuyé et un compteur d'appuis distinct du nombre de déclenchements. Pour isoler le chemin audio, le même effet est automatiquement déclenché une fois après son préchargement, avant l'initialisation de la musique, puis quatre fois en rafale pendant le morceau à partir de 2 s. Les compteurs séparés distinguent les déclenchements automatiques et manuels, affichent le dernier canal et le nombre de voix actives; le diagnostic pré-musique montre aussi octets transférés, taille attendue, adresse SPU et retour de fin DMA. Cela permet de différencier l'entrée du contrôleur, la copie SPU, le lancement d'une voix et le masquage par la musique.

Les vérifications statiques de l'effet sont cohérentes avec l'exemple `vagsample` de PSn00bSDK 0.24 : VAGp mono, 22 050 Hz, payload de 1 536 octets (96 blocs ADPCM), quantité multiple de 64 et source C alignée sur 64 octets. L'adresse `0x10000` est alignée sur 64 et séparée de l'étendue musicale `0x1010–0x9010`. Le pitch est `getSPUSampleRate(22050)` (registre 4.12 `0x0800`); l'adresse du registre voix passe par `getSPUAddr()`. Les blocs non finaux ont le flag `0x00`; le dernier a `0x01` (fin sans boucle). Le décodeur de mesure accepte les cinq prédicteurs et les shifts ADPCM valides; la crête décodée reste 4 787 LSB. Les registres ADSR `0x00ff/0x0000`, le séquencement key-off → adresse/pitch/volumes/ADSR → key-on et le transfert DMA suivent le code d'exemple du SDK. Le programme exige que `SpuWrite()` retourne exactement 1 536 octets et que `SpuIsTransferCompleted(SPU_TRANSFER_WAIT)` confirme la fin avant de permettre le lancement. Les voix SFX 4–7 ne chevauchent pas les voix musicales 0–3 ni le tampon SPU. Ces vérifications de code et de fichier ne prouvent pas encore que le son est audible dans l'émulateur ou sur console.

Le volume des effets est géré par un plafond de pool plutôt que par une hausse générale : la somme des quatre volumes de voix actives ne dépasse pas `0x1800`. Une seule occurrence reçoit ce budget, deux en partagent la moitié, etc.; au maximum quatre sons simultanés reçoivent chacun `0x0600`. Le pool suit l'occupation par une échéance logicielle de neuf images, pas par lecture d'un indicateur matériel de voix active; il choisit une voix libre en rotation, ou arrête la plus ancienne si le pool est plein. Le volume musical reste inchangé. Avec une crête SFX de 4 787 LSB, la somme maximale d'effets est bornée à 1 796 LSB. À la largeur panoramique maximale, musique décodée plus cette borne laisse environ 1,22 dB de marge numérique; la marge est supérieure à la largeur initiale 5. La comparaison ne prédit pas le niveau analogique. L'analyse `ps1/analyze_bopeebo_4ch_audio.py` a été mise à jour pour refléter ce plafond dynamique.

Le BIN/CUE de diagnostic est compilé dans `ps1/build/bopeebo-audio-4ch-sfx-diagnostic/`, séparément des deux versions précédentes. CMake/GCC 12.3.0 et PSn00bSDK 0.24 ont compilé l'EXE et généré l'image MODE2/2352 de 4 121 secteurs; le BIN fait 9 692 592 octets et le CUE 94 octets. CMake a signalé des chemins d'objets proches de sa limite Windows; le SDK externe a aussi ses deux avertissements de qualification `volatile`. Aucun de ces avertissements n'a bloqué la compilation.

DuckStation n'a pas présenté de fenêtre pilotable dans la session d'observation : après lancement contrôlé, l'énumération Windows ne renvoyait que des fenêtres Explorer portant le nom DuckStation et aucun panneau de l'émulateur. Je n'ai donc pas observé cette nouvelle image, ni son écran de diagnostic, ni écouté ses déclenchements. **Le SFX n'est pas validé.** Pour l'essai manuel, ouvrir le nouveau CUE, écouter le déclenchement annoncé avant la musique, puis écouter la rafale automatique après 2 s; confirmer que `AUTO DURING` atteint `4/4` et que `UPLOAD` indique `1536/1536` avec transfert terminé. Ensuite appuyer sur `J` : `SQUARE PRESSES` et `SFX TRIGGERS MAN` doivent augmenter ensemble. Comparer le résultat pré-musique au résultat pendant Bopeebo, vérifier Circle/`L` et la largeur initiale `5/7`, puis surveiller les underruns et erreurs CD. En l'absence d'audio audible dès le test pré-musique, le problème est côté voix SPU/transfert/échantillon, pas le masquage par la musique. Aucun test console réelle n'a été réalisé.

### Résultat SFX confirmé et prototype jouable Bopeebo Normal

L'utilisateur confirme maintenant que le diagnostic du commit `7a6250c` fonctionne comme prévu, aussi bien pour les SFX automatiques que manuels. Le bip temporaire paraît un peu faible; conserver ce retour pour le mixage final, sans ouvrir un jalon audio dédié. La préférence reste quatre canaux, panoramique initial `5/7` réglable et mute BF Circle (`L`) fonctionnel. Les probes précédents restent reproductibles et inchangés.

#### Chart officiel et conversion

Le chart utilisé est le Normal de Bopeebo classique, `preload/data/songs/bopeebo/bopeebo-chart.json` dans `Funkin.assets` épinglé à `724eba9de9e76761d9cefd52169926bc51c760a5`. Le JSON officiel et les stems ne sont pas ajoutés à Git. `ps1/convert_bopeebo_chart.py` vérifie les données puis génère le tableau C dans le dossier de build ignoré. Il garde la propriété des lanes (`d=0..3` BF, `d=4..7` Dad), convertit `t` et `l` millisecondes en positions échantillon à 43 008 Hz, et calcule la table PBOT1 sans dépendance à la bibliothèque mathématique flottante du SDK freestanding.

La conversion observée compte 102 notes et 58 holds; aucune lane invalide, note dupliquée à même lane/instant ou superposition de holds sur une lane. Le dernier tail est à 3 280 435 samples (~76,28 s); le VAGi audio dure 3 509 453 samples (~81,6 s). Les notes Dad sont affichées et considérées jouées par le stem Dad, sans score joueur. Le convertisseur arrondit chaque temps au sample le plus proche, les demi-samples vers le haut.

#### Règles reprises et écarts provisoires

Le gameplay reprend le scoring PBOT1 de la référence `FunkinCrew/funkin` au commit `d05659bbdcf0d83073c900207cf410472afbbede`: Sick `≤45 ms`, Good `≤90`, Bad `≤135`, Shit `≤160`, Miss au-delà; score maximal 500 pour un écart strictement inférieur à 5 ms, sinon formule sigmoïde du moteur (`500 × (1 − 1/(1+exp(−0,080×(écart−54,99)))) + 9`, tronquée). Les fenêtres sont comparées en unités rationnelles d'échantillons; les tests aux bornes inclusives et immédiatement après chacune passent. Miss vaut −100 et ghost miss −10. Bad/Shit/Miss brisent le combo. Vie initiale 1,0/2,0; Sick +0,03, Good +0,015, Bad 0, Shit −0,02, Miss/ghost −0,08. Les holds donnent +250 score/s et +0,12 vie/s; drop avec plus de 160 ms restants coûte −125 score/s et aucune vie selon les constantes de cette version. Les valeurs de vie Q8 introduisent un faible arrondi.

Écarts actuellement provisoires : appariement d'une pression D-pad à la note BF la plus proche dans sa fenêtre; pas d'input buffering, réglage de latence, pause, jugement textuel par note ni bilan final; pas d'animations ou réactions personnages. Un miss BF coupe la voix BF jusqu'au prochain hit BF, en plus du mute utilisateur séparé. Une pression hors fenêtre applique le ghost miss par défaut. Le chart validé ne contient pas de holds simultanés sur une même lane; l'état runtime réserve donc une tenue active par lane. La vie à zéro arrête la musique, et Start relance seulement après fin/game over. Square reste déclencheur d'essai manuel; les SFX provisoires sont aussi joués pour miss, ghost miss et drop. Les lanes Dad ne sont pas jouables dans ce premier test.

Défilement, jugement, misses automatiques, score et holds sont pilotés par `Stream_GetSamplesPlayed()`, la même horloge SPU que la lecture. Le SDK ancre sa progression sur les interruptions SPU et interpole par VSync; le compteur n'est pas une position matérielle échantillon-exacte. Le rendu GPU suit les frames vidéo, sans piloter la musique ni les jugements. Huit pistes simples montrent BF à gauche et Dad à droite, avec têtes et segments de sustain. Aucun personnage, décor ou menu complet n'est inclus.

#### Validation et image compilée

Vérification hors cible du chart et des bornes de jugement : PASS; conversion générée : 102 notes / 58 holds. Compilation PSn00bSDK 0.24 / GCC 12.3.0 et image CD MODE2/2352 : PASS. Le CUE/BIN est dans `ps1/build/bopeebo-playable-normal-4ch/`; BIN 9 702 000 octets (4 125 secteurs), CUE 93 octets, EXE 57 344 octets. SHA-256 BIN `164232CFE6824822A30F4E83C20005F98F810A2109A6304098FE93113DDE4D83`. Le JSON chart et les fichiers audio officiels restent hors dépôt.

DuckStation est installé et sa fenêtre a été observée, mais le sélecteur de fichier n'a pas pu être piloté de manière fiable; cette image n'a donc pas été exécutée. **Le résultat concret est compilé, pas validé en émulateur.** Son, affichage GPU, entrée des quatre directions, hits/misses, holds, voix BF et redémarrage doivent encore être observés dans DuckStation. Aucun test console réelle.

#### Budget mémoire actualisé du probe jouable

`mipsel-none-elf-size`: text 52 308 o, data 2 186 o, BSS 12 936 o, total 67 430 o. EXE disque: 57 344 o. Le ring buffer audio reste une allocation heap de 98 304 o (96 Kio), donc le suivi `text+data+BSS+ring` est 165 734 o (161,85 Kio); il s'agit du test jouable seulement et n'inclut pas tous les besoins système ni le futur contenu. Le tableau constant du chart compte ~1,5 Kio et les états runtime des 102 notes ~102 o; le BSS accru comprend aussi les primitives GPU.

Le SPU garde quatre voix musicales et quatre voix de SFX : 32 768 o de buffers musicaux (`0x1010–0x9010`) + 1 536 o de SFX résident (`0x10000`), 34 304 o au total. Seize des 24 voix restent libres pour cette scène. Débit CD musical : 98 304 o/s, soit 48 secteurs/s (~32 % du débit nominal 2×); 96 Kio de ring équivalent à environ une seconde. Charts, personnages, animations, décors et menus complets restent à budgéter avant toute projection sur le jeu.

Reproduction depuis `ps1/` (stems/encodeur préparés hors Git selon la section précédente) :

```powershell
$chart = '..\assets\preload\data\songs\bopeebo\bopeebo-chart.json'
$vagi = Join-Path $env:TEMP 'fnf-bopeebo-quality\bopeebo-43008-4ch.vag'
cmake --preset default -B .\build\bopeebo-playable-normal-4ch `
  "-DFUNKIN_PS1_BOPEEBO_CHART_JSON=$chart" `
  "-DFUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH=$vagi"
cmake --build .\build\bopeebo-playable-normal-4ch --target ps1-bopeebo-playable-disc
```

Essai manuel : ouvrir le CUE, jouer les flèches à l'arrivée des notes BF, vérifier holds, score/combo/vie/hits/misses, SFX de faute, Circle/`L` mute BF, L1/R1 pan, Square/`J` SFX de test et Start après fin/game over. Contrôler les compteurs CD et underrun pendant toute la chanson. Le SFX provisoire est jugé un peu faible; ajuster avec le mixage final.

### Résultat SFX confirmé et prototype jouable Bopeebo Normal

L'utilisateur confirme que le diagnostic du commit `7a6250c` fonctionne, avec SFX automatiques et manuels. Le bip temporaire paraît un peu faible; garder le point pour le mixage final, sans rouvrir un jalon dédié au bip. La préférence reste quatre canaux, panoramique initial `5/7` réglable et mute BF avec Circle (`L`) fonctionnel. Les probes antérieurs restent reproductibles. Dans le jeu, L1/R1 règlent le panoramique afin que les quatre directions restent réservées aux lanes; la persistance du réglage attend le futur menu d'options.

#### Chart officiel

Le chart est le Normal de Bopeebo classique : `preload/data/songs/bopeebo/bopeebo-chart.json` depuis `Funkin.assets` à `724eba9de9e76761d9cefd52169926bc51c760a5`. Le JSON chart et les stems officiels ne sont pas commités. `ps1/convert_bopeebo_chart.py` valide les entrées, convertit `t`/`l` millisecondes en samples à 43 008 Hz et génère une table C dans le dossier de build ignoré. Les lanes `d=0..3` sont BF et `d=4..7` Dad.

Résultat de conversion : 102 notes, 58 holds, aucune lane invalide, aucun doublon même lane/même instant et aucun chevauchement de holds sur une même lane. Le dernier tail est à 3 280 435 samples (~76,28 s); le stream audio va à 3 509 453 samples (~81,6 s). Dad est visualisé et son stem couvre ses notes; aucune lane Dad n'est jouable. La conversion arrondit au sample le plus proche, demi-sample vers le haut.

#### Règles et différences provisoires

Le scoring reprend PBOT1 depuis `FunkinCrew/funkin` au commit `d05659bbdcf0d83073c900207cf410472afbbede`: Sick `≤45 ms`, Good `≤90`, Bad `≤135`, Shit `≤160`, puis Miss; score `500` si l'écart est strictement inférieur à 5 ms, sinon formule sigmoïde du moteur (pente `0,080`, centre `54,99 ms`, score tronqué). Les bornes sont comparées en unités rationnelles de samples. Contrôle des valeurs à 45/90/135/160 ms et juste au-delà : PASS. Miss vaut −100; ghost miss −10. Bad/Shit/Miss cassent le combo. Vie 1,0/2,0 au départ; Sick +0,03, Good +0,015, Bad 0, Shit −0,02, Miss/ghost −0,08. Les holds donnent +250 points/s et +0,12 vie/s; abandon avec plus de 160 ms restants applique −125 points/s et 0 de pénalité de vie selon les constantes de cette version. Le stockage de vie Q8 arrondit légèrement les gains.

Écarts de ce jalon : une pression D-pad prend la note BF la plus proche dans la fenêtre; pas d'input buffering, compensation de latence, pause, classement textuel de chaque note ni bilan final. Pas d'animations, scripts ou réactions personnages. Le miss BF coupe sa voix jusqu'au prochain hit BF; Circle mute reste un état séparé. Une pression hors fenêtre applique le ghost miss par défaut. Une tenue active par lane est gérée; le chart testé n'a aucun chevauchement de holds dans la même lane. Vie à zéro arrête le flux. Start redémarre proprement après fin ou game over, pas pendant le morceau. Square reste un déclencheur SFX de test; les fautes miss/ghost/drop utilisent également le SFX provisoire.

Le scroll, les misses, les jugements, le score et les holds utilisent `Stream_GetSamplesPlayed()` depuis l'horloge audio SPU. Le SDK ancre cette valeur sur les interruptions SPU puis interpole via VSync; ce n'est pas un read head exact par échantillon. Les frames ne pilotent que le rendu. Huit pistes simples rendent maintenant Dad à gauche et BF à droite, avec têtes de notes et segments de sustain; la propriété des lanes ne change pas. Pas de personnage, décor ni menu complet.

#### Compilation, exécution et mémoire

Vérification de conversion et limites de jugement : PASS. Compilation PSn00bSDK 0.24 / GCC 12.3.0 et génération de l'image MODE2/2352 : PASS. Le dossier distinct est `ps1/build/bopeebo-playable-normal-4ch/`; BIN 9 702 000 octets (4 125 secteurs), CUE 93 octets, EXE 57 344 octets. SHA-256 BIN `9030DA2D2E2BC0EB00707541754F2FDC41D03FD2BE633C3CEDBAE1EC1CECE88D`. Les ressources officielles restent hors Git.

DuckStation était présent, mais le sélecteur d'image n'a pas pu être piloté de manière fiable; le CUE n'a pas été exécuté. Le prototype est compilé, pas validé en émulateur. Affichage, audio, commandes, jugements, holds, mute après faute et redémarrage restent à observer. Aucune console réelle n'a été testée.

Budget mesuré par `mipsel-none-elf-size`: text 52 228 o, data 2 186 o, BSS 12 932 o, total 67 346 o. Ring audio en heap: 98 304 o (96 Kio), total suivi `text+data+BSS+ring`: 165 650 o (161,77 Kio). BSS inclut notamment les primitives GPU et l'état/stack du SDK; le tableau chart constant fait environ 1,5 Kio, les états de 102 notes environ 102 o. Le SPU réserve 32 768 o au double tampon musical et 1 536 o au SFX; 34 304 o sur 512 Kio. Quatre voix SPU musique + quatre SFX sont utilisées, 16 libres dans cette scène de test. Débit CD : 98 304 o/s, 48 secteurs/s, ~32 % du débit nominal 2×; 96 Kio représentent ~1 s de tampon. Ce budget n'inclut pas le contenu complet du jeu (charts futurs, personnages, animations, décors, menus, banques de SFX).

Reproduction depuis `ps1/` avec le VAGi quatre canaux déjà généré hors Git :

```powershell
$chart = '..\assets\preload\data\songs\bopeebo\bopeebo-chart.json'
$vagi = Join-Path $env:TEMP 'fnf-bopeebo-quality\bopeebo-43008-4ch.vag'
cmake --preset default -B .\build\bopeebo-playable-normal-4ch `
  "-DFUNKIN_PS1_BOPEEBO_CHART_JSON=$chart" `
  "-DFUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH=$vagi"
cmake --build .\build\bopeebo-playable-normal-4ch --target ps1-bopeebo-playable-disc
```

Essai manuel : ouvrir le CUE, jouer les quatre flèches, vérifier holds et score/combo/vie/hits/misses; écouter les SFX de faute, Circle/L pour le mute BF, L1/R1 pour le pan, Square/J pour le SFX manuel, puis Start après fin/game over. Surveiller CD errors et underruns jusqu'à la fin. Le SFX provisoire est jugé faible; régler lors du mixage final.

## Correction du relâchement anticipé des holds

Le retour utilisateur indique que les notes tenues semblaient jouables mais qu'un relâchement anticipé ne coupait pas la voix BF. La règle de référence épinglée à `d05659bbdcf0d83073c900207cf410472afbbede` est dans `Strumline.hx` et `PlayState.hx` : tout relâchement pendant un hold actif marque celui-ci manqué; le traitement de `PlayState` ne déclenche cependant la pénalité, le son de faute et le mute vocal que si le temps restant est strictement supérieur à `HOLD_DROP_PENALTY_THRESHOLD_MS` (160 ms). La pénalité originale est de −125 points par seconde restante. Les constantes de santé de drop sont à zéro dans cette révision. `goodNoteHit()` restaure la voix joueur lors de la prochaine note BF réussie.

Le probe vérifie désormais ce seuil en arithmétique entière d'échantillons (`remaining * 1000 > rate * 160`), sans arrondi en millisecondes. Une tenue atteignant sa fin est complétée avant de traiter un relâchement; un relâchement avec au plus 160 ms restants est toléré comme dans le chemin sans pénalité du moteur. Un drop effectif passe une seule fois par `game_hold_drop()` : combo cassé, pénalité −125 points/s au prorata du temps restant, BF réduit au silence et SFX provisoire joué une fois. La vie n'est pas déduite pour un drop, conformément aux constantes nulles de cette révision. Le flag de tenue active est ensuite effacé, ce qui empêche de répéter pénalité et SFX aux frames suivantes. La prochaine frappe BF réussie rétablit BF; Dad et l'instrumental restent indépendants. Le mute manuel Circle reste orthogonal et n'est pas annulé par cette récupération.

La présentation est maintenant Dad à gauche et BF à droite. Les notes gardent leur attribution officielle (chart lanes 0–3 BF, 4–7 Dad), leurs quatre pistes sont affichées dans l'ordre des lanes du chart et le D-pad continue à jouer BF avec les mêmes associations gauche/bas/haut/droite.

Vérification automatisée ciblée : `python ps1/test_bopeebo_hold_drop.py` couvre tenue terminée, relâchement avec plus de 160 ms, seuil exact à un taux de 43 kHz, ainsi que les échantillons immédiatement sous/au-dessus du seuil au taux de jeu réel 43 008 Hz, absence de répétition par frame, maintien des stems Dad/instrumental et rétablissement de BF après la frappe suivante. Ces tests de règles côté hôte ne remplacent pas l'observation de l'audio PS1.

La nouvelle image de correction est isolée dans `ps1/build/bopeebo-hold-release-fix/`. PSn00bSDK 0.24 / GCC 12.3.0 a compilé l'ELF et généré un BIN de 9 702 000 octets (4 125 secteurs MODE2/2352) et un CUE de 93 octets. ELF `text=52 472`, `data=2 186`, `BSS=12 936`, soit 67 594 octets; avec le ring audio 98 304, RAM suivie 165 898 octets (~162,01 Kio). Le budget SPU et CD reste celui du probe précédent : 34 304 octets SPU, 4 voix musique + 4 SFX, 16 voix libres, CD à 98 304 octets/s, tampon ~1 s. Le test ciblé hôte (`python ps1/test_bopeebo_hold_drop.py`) passe, 5 cas. **Aucun essai de ce nouveau disque dans DuckStation n'a été observé dans ce tour et aucune console réelle n'a été testée.**

## Première scène visuelle PS1 de Bopeebo

L'utilisateur valide manuellement le commit `01e84a0` dans DuckStation : le relâchement anticipé d'une tenue coupe BF, une réussite suivante rétablit sa voix, le mute manuel reste fonctionnel et Dad/BF sont placés correctement. Ce retour concerne le build de ce commit, pas le nouveau disque visuel ci-dessous.

### Ressources et conversion

Les ressources examinées viennent du sous-module officiel `Funkin.assets`, épinglé à `724eba9de9e76761d9cefd52169926bc51c760a5`. La semaine 1 référence `preload/data/stages/mainStage.json`; ses couches communes mesurent `stageback.png` 2560×1400 (12 564 octets), `stagefront.png` 2560×581 (115 485 octets) et `stagecurtains.png` 2560×1400 (118 886 octets). Les PNG sont réduits en 320×176 pour fond/rideaux et 320×56 pour le premier plan, sans interpolation bilinéaire, puis découpés en tuiles 256 pixels.

BF dispose de l'ancien atlas Sparrow complet `shared/images/characters/BOYFRIEND.png` (8192×4096, 3 394 386 octets) et XML. Le convertisseur en extrait deux images par animation idle, chant gauche/bas/haut/droite et miss dans ces quatre directions. Les JSON Animate modernes de Dad (`991×981`) et GF (`2064×1065`) décrivent des personnages en pièces riggées plutôt que des cellules Sparrow complètes. Les images `preload/images/storymenu/props/dad` et `gf`, bien que dotées de longues séquences idle, sont des masques rectangulaires pour l'interface du story menu, pas des sprites complets de personnage en jeu; un premier essai de recoloration a révélé des aplats rectangulaires dans DuckStation et a été abandonné.

Pour livrer une scène cohérente sans faussement présenter ces masques comme des personnages, la conversion dessine donc des silhouettes PS1 temporaires Dad et GF à partir de formes nettes et de leurs palettes caractéristiques. Dad a six poses simplifiées sélectionnées par les notes adverses et le tempo; GF alterne quatre poses de danse. Ce ne sont pas les poses officielles ni leurs animations directionnelles. L'extraction et le rendu des rigs Animate complets restent à faire. BF, ses chants et ses miss utilisent au contraire les images officielles de l'atlas historique. Le stageback et les rideaux sont derrière les personnages; stagefront puis les huit pistes, les récepteurs et les notes gardent les plans avant. Les personnages ne sont pas encore animés à partir des fautes Dad/GF; les réactions BF suivent les hits, les tenues, les ratés et le délai audio.

`ps1/convert_bopeebo_visuals.py` dépend de Python 3 et de FFmpeg fourni localement. Il lit le sous-module épinglé, applique un redimensionnement nearest-neighbor, réduit chaque groupe à une palette 4bpp RGB555 de 16 entrées (index 0 transparent), puis génère le header dans le répertoire de build. Ni les PNG officiels, ni l'header généré, ni le SDK ne sont ajoutés au dépôt. Les textures sont chargées une fois en VRAM avant `CdInit` et le démarrage du flux; aucune lecture CD graphique n'est faite pendant la chanson.

### Budgets mesurés et estimés

| Zone | Utilisé pour ce prototype | Réserve / précaution |
|---|---:|---|
| RAM principale, ELF `text+data+BSS` mesuré | 430 398 o (text 414 616, data 2 186, BSS 13 596) | Le text contient code, chart, SFX et 360 448 o de pages d'images compressées 4bpp. |
| Tampon audio principal | 98 304 o (96 Kio), alloué par le lecteur | Environ 1 s au débit de ce flux. |
| RAM suivie totale | 528 702 o (~516,3 Kio) | Sous-total ELF + ring; marge arithmétique jusqu'à 2 Mio : 1 568 450 o. La pile, les allocations internes SDK et le pic de conversion ne sont pas mesurés au runtime; le pic de conversion est côté PC, pas PS1. |
| VRAM | 307 200 o double framebuffer + 360 448 o de textures + 128 o palettes = 667 776 o | Sur 1 Mio, 380 800 o restent théoriquement avant polices, tables d'affichage et autres usages SDK; cette réserve doit être mesurée sur cible. |
| SPU | 32 768 o musique + 1 536 o SFX = 34 304 o | 4 voix streaming + 4 voix SFX utilisées, 16/24 voix restantes; budgets précédents conservés. |
| CD | 98 304 o/s, soit 48 secteurs/s | Tampon de 96 Kio ≈1 s; aucune lecture d'assets pendant le streaming. |

Ce budget concerne uniquement le probe jouable actuel. Les futurs charts, personnages/réseaux d'animations, décors, effets et menus consommeront la marge; l'exécutable n'a pas encore de mesure de heap/stack en fonctionnement ni de profiling GPU sur matériel. La réduction de pixels avant stockage économise ici réellement de la VRAM par rapport au RGBA source; charger les 360 448 octets de texture depuis le header statique consomme en revanche la même quantité de RAM principale, elle n'est pas économisée.

### Compilation et observation

Le nouveau build reproductible est `ps1/build/bopeebo-ps1-visuals/`; les entrées non versionnées sont le chart officiel JSON, le VAGi quatre canaux 43 008 Hz déjà généré et FFmpeg. Configuration Windows depuis la racine du dépôt, en fournissant les chemins locaux à CMake :

```powershell
$sdk = 'C:\toolchains\PSn00bSDK-0.24-win32'
$env:PSN00BSDK_LIBS = "$sdk\lib\libpsn00b"
cmake -S ps1 -B ps1/build/bopeebo-ps1-visuals -G Ninja `
  "-DCMAKE_MAKE_PROGRAM=$sdk/bin/ninja.exe" `
  "-DCMAKE_TOOLCHAIN_FILE=$env:PSN00BSDK_LIBS/cmake/sdk.cmake" `
  "-DPSN00BSDK_TC=$sdk" -DPSN00BSDK_TARGET=mipsel-none-elf `
  -DCMAKE_BUILD_TYPE=Debug `
  "-DFUNKIN_PS1_BOPEEBO_CHART_JSON=$env:TEMP/fnf-bopeebo-port/bopeebo-chart.json" `
  "-DFUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH=$env:TEMP/fnf-bopeebo-quality/bopeebo-43008-4ch.vag" `
  "-DFUNKIN_PS1_FFMPEG=C:/path/to/ffmpeg.exe"
cmake --build ps1/build/bopeebo-ps1-visuals --target ps1-bopeebo-playable-disc
```

PSn00bSDK 0.24 / GCC 12.3.0 compile et mkpsxiso ont terminé. L'ELF rapporte `text=414 616`, `data=2 186`, `BSS=13 596`; BIN 10 118 304 octets, CUE 93 octets, SHA-256 BIN `E791CE261F9C441EF6CCE04BDE11572F1E81480B38B374B6A614720B5278E2E4`. DuckStation 0.1-8675 a démarré l'image finale, affiché la scène à 320×240 et 60 IPS; la position audio a avancé et le programme est resté jusqu'à l'état de game over sans écran d'erreur. L'observation a duré environ 18 s et les diagnostics compacts étaient masqués; elle ne permet pas d'affirmer des compteurs CD/underrun nuls, une écoute concluante, les entrées, le mute, les holds, les SFX, le redémarrage ni la lecture entière de 81,6 s. La variante intermédiaire à aplats, elle aussi compilée, a affiché `CD ERR 0`, `UNDERRUN 0` et 60 IPS à environ 2,8 s, mais ces compteurs ne sont pas reportés comme mesure du BIN final.

Vérification hôte `python ps1/test_bopeebo_hold_drop.py` : 5 cas PASS après ajustement du test de source à la signature lane-aware; `git diff --check` : PASS. **Le nouveau jalon visuel n'est pas validé par l'utilisateur.** Le morceau entier, la lisibilité/animation pendant les notes, Circle, holds, SFX, erreurs CD/underruns, redémarrage et un essai console réelle restent à vérifier. Les assets et exécutables construits restent dans le sous-module ou le répertoire ignoré `ps1/build/`.

## Audit graphique et scène améliorée

Le retour utilisateur considère BF convaincant et le prototype prometteur, mais trop proche d'un rendu SNES; les textures réduites ne sont donc pas un plafond artistique. L'objectif reste une présentation PS1 soignée, avec des poses FNF lisibles, un décor reconnaissable, une caméra rythmée discrète et une interface plus fine. PaRappa sert de référence de mise en scène/finition, pas de style à copier. La validation précédente du gameplay et du son concernait le commit `01e84a0`; elle ne vaut pas validation de la présente scène.

### Ressources examinées et conversion

Le sous-module `Funkin.assets` reste épinglé à `724eba9de9e76761d9cefd52169926bc51c760a5`. Les ressources lues sont les rigs Animate `dad/Animation.json` (14 747 o), son atlas `spritemap1.json` (1 298 o, PNG 141 940 o en 991×981), `gf/Animation.json` (69 471 o) et son atlas (3 552 o, PNG 165 789 o en 2064×1065). Le renderer hôte `ps1/animate_preview.py` suit les instances et transformations des timelines Animate et découpe les symboles depuis les atlas : l'aperçu complet mesure 421×767 pour Dad et 697×635 pour GF. Le convertisseur échantillonne 6 poses de repos Dad et 2 images pour chacune des 4 directions; il prend 8 images de danse dans l'animation idle de GF. Ce sont de vraies poses des rigs officiels, mais les timings d'animation restent des échantillons choisis et ne reproduisent pas encore toutes les timelines/expressions du jeu.

BF reste extrait de l'atlas Sparrow officiel `BOYFRIEND.png` (8192×4096, 3 394 386 o; XML 68 461 o), avec 2 images pour chacune de 9 animations (repos, 4 chants, 4 ratés). Le décor semaine 1 est issu de `stageback.png` 2560×1400 (12 564 o), `stagecurtains.png` 2560×1400 (118 886 o) et `stagefront.png` 2560×581 (115 485 o). Fond et rideaux sont composités puis ramenés à 320×176 avec réduction area pour limiter l'aliasing; le premier plan devient 320×56. Les images de personnage sont ramenées à Dad 72×112, GF 128×120 et BF 64×96 avec nearest-neighbor pour garder des contours francs. La scène compose Dad à gauche, GF et ses enceintes au centre, BF à droite; le décor et les personnages passent derrière les huit pistes, récepteurs et notes. Les pistes Dad sont optionnellement masquées en solo par Triangle, sans retirer charts, données ni animations; l'affichage par défaut reste visible jusqu'à la décision sur la scène complète.

Les textures de décor, Dad et GF utilisent une palette commune 8bpp de 255 couleurs plus l'index 0 transparent; BF utilise une CLUT 4bpp distincte de 15 couleurs plus le transparent. La mesure RGB RMSE de la conversion est 0,95 pour décor/Dad/GF combinés, 1,14 pour Dad et 0,87 pour GF; les comparer au RMSE 8,53 obtenu en contraignant le décor à 15 couleurs. Cette métrique ne mesure ni la ressemblance perceptuelle ni les artefacts d'animation. Les couleurs sont quantifiées en RGB555 par le GPU PS1. Le stage est plus détaillé que la première version 4bpp; aucun filtrage bilinéaire n'est utilisé.

La caméra applique un zoom maximal d'environ 2,7 % au début de chaque battement et un déplacement horizontal de 5 pixels vers Dad ou BF pendant leurs sections vocales; fond, rideaux et avant-plan ont des facteurs de parallaxe distincts. Les pistes de notes restent fixes à l'écran pour préserver la lecture rythmique. C'est une impulsion et un recentrage rudimentaires, sans interpolation de transition; ils restent à évaluer pendant le morceau entier et pourront être assouplis si les notes deviennent moins lisibles. L'interface par défaut tient sur une ligne (temps et état Triangle); Select est prévu pour révéler diagnostic, score, combo, jugements, vie, voix et SFX. Sa bascule n'a pas été confirmée avec le clavier de cet essai DuckStation. Ce HUD de prototype n'est pas l'interface finale.

### Carte mémoire

Le build final charge 7 pages 8bpp (7 × 65 536 = 458 752 o) et 3 pages 4bpp (3 × 32 768 = 98 304 o), soit 557 056 o de textures. La table GPU contient désormais ces 10 pages. Une révision intermédiaire avait omis les trois coordonnées de page BF; DuckStation avait alors rendu BF en données corrompues. La revue d'adresses a aussi révélé que la ligne CLUT y=480 chevauchait les 16 dernières lignes du framebuffer inférieur (y=256..495). Le build v5 place les deux palettes aux lignes y=496..511, sous les deux framebuffers, et les textures à partir de x=384. Cette correction est visible dans la capture du build final : BF est entier et le bas du framebuffer n'est plus recouvert.

| Région | Occupation du build v5 | Nature de la mesure / marge |
|---|---:|---|
| RAM principale : ELF `text+data+BSS` | 628 570 o (`text=612 752`, `data=2 210`, `BSS=13 608`) | Mesuré par `mipsel-none-elf-size`; `text` contient environ 557 056 o de pages d'images statiques, ainsi que code, chart, lecteur et SFX. |
| Tampon CD→RAM | 98 304 o (96 Kio) | Alloué par le stream; durée environ 1 s au débit de 98 304 o/s. |
| RAM suivie | 726 874 o (~710,0 Kio) | ELF + ring; arithmétiquement 1 370 278 o de moins que 2 Mio, avant heap/stack/runtime SDK non mesurés. Ce n'est pas une mesure de pic mémoire. |
| VRAM : double framebuffer | 307 200 o | Deux buffers 320×240×16bpp aux lignes 0..239 et 256..495. |
| VRAM : textures préchargées | 557 056 o | Mesuré par nombre et profondeur des pages générées; pas d'accès CD visuel en cours de morceau. |
| VRAM : CLUT | 544 o | 256 + 16 entrées de 16 bits; placées dans la bande libre y=496..511. |
| VRAM : police / reste | 32 Kio réservés par estimation; ~151 008 o restent théoriquement | 32 Kio est une réservation de planification, pas une lecture du high-water mark. Restant calculé sur 1 Mio après framebuffers, textures, CLUT et cette réservation. Tables et contraintes SDK doivent être mesurées sur vraie cible. |
| SPU et CD | 34 304 o SPU; 4 voix stream + 4 SFX; 98 304 o/s CD | Valeurs de configuration existantes, inchangées par le jalon visuel. 16 voix SPU non affectées sur 24; aucun flux d'assets concurrent. |

Le budget de 557 056 o VRAM n'économise pas cette RAM principale : les mêmes pages sont présentes statiquement dans `text` afin de les précharger en VRAM. Le dimensionnement n'est pas celui du jeu final. Il reste à loger charts, personnages et toutes leurs animations, autres décors, menus, effets visuels et banques d'effets sonores. La conversion peut être affinée par chargement/déchargement par scène si le budget global l'exige, après mesure, sans remettre en cause l'audio par des lectures CD concurrentes non évaluées.

### Construction et vérification observée

Entrées du build : assets du sous-module épinglé, chart officiel Bopeebo Normal dans `%TEMP%\fnf-bopeebo-port\bopeebo-chart.json`, VAGi 4 canaux à 43 008 Hz dans `%TEMP%\fnf-bopeebo-quality\bopeebo-43008-4ch.vag`, Python 3 et FFmpeg 7.1.1. Le SDK, les sources et les ressources générées restent hors dépôt. Configuration/build Windows déjà utilisée pour le BIN/CUE v5 :

```powershell
$sdk = 'C:\toolchains\PSn00bSDK-0.24-win32'
$cmake = 'C:\toolchains\cmake-4.4.4-windows-x86_64'
$env:PSN00BSDK_LIBS = "$sdk\lib\libpsn00b"
$env:Path = "$sdk\bin;$cmake\bin;$env:Path"
$env:CMAKE_ROOT = "$cmake\share\cmake-4.4"
cmake -S ps1 -B ps1/build/bopeebo-visual-audit-v5 -G Ninja `
  "-DCMAKE_MAKE_PROGRAM=$sdk/bin/ninja.exe" `
  "-DCMAKE_TOOLCHAIN_FILE=$env:PSN00BSDK_LIBS/cmake/sdk.cmake" `
  -DPSN00BSDK_TC=$sdk -DPSN00BSDK_TARGET=mipsel-none-elf `
  -DCMAKE_BUILD_TYPE=Debug `
  "-DFUNKIN_PS1_BOPEEBO_CHART_JSON=$env:TEMP/fnf-bopeebo-port/bopeebo-chart.json" `
  "-DFUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH=$env:TEMP/fnf-bopeebo-quality/bopeebo-43008-4ch.vag" `
  '-DFUNKIN_PS1_FFMPEG=T:/Docker/MGTV Playlist Gen/ffmpeg-7.1.1-essentials_build/bin/ffmpeg.exe'
cmake --build ps1/build/bopeebo-visual-audit-v5 --target ps1-bopeebo-playable-disc
```

PSn00bSDK 0.24 / GCC 12.3.0 et mkpsxiso 2.03 ont compilé l'ELF et généré BIN/CUE : 10 346 448 octets (4 399 secteurs) et 93 octets, SHA-256 BIN `B751E80A7610BE06C566CF7983FFAD0128794A61D5EF94CA8706A34C77811971`. Avertissements restants : casts `volatile` dans `stream.c` du SDK lors de la compilation, et avertissements de chemin long/configuration portable CMake; pas d'erreur de compilation.

DuckStation 0.1-8675 a démarré v5 à 320×240. Pendant l'observation, l'émulateur affichait ~60 IPS; le compteur audio est passé de 00:07 à 00:18 sur deux observations, et la scène affichait BF/Dad/GF, les notes et un bas d'écran intact après déplacement des CLUT. L'exécution continue assez longtemps pour voir plusieurs états d'animation. **Ce n'est pas une mesure de fluidité garantie, une mesure de dérive audio, une validation de la chanson complète ou une acceptation utilisateur.** Le compteur diagnostics/CD n'a pas pu être activé via le clavier utilisé dans cette session; erreurs CD et underruns de v5 sont donc inconnus. Les contrôles, mute, notes tenues, SFX et redémarrage de ce nouveau BIN restent à rejouer; pas de test console réelle. Le build est compilé et exécuté dans l'émulateur, mais le jalon graphique reste à valider par l'utilisateur.

Après changements : `python ps1/test_bopeebo_hold_drop.py` — 5 tests de régression passent; `git diff --check` — PASS. Ces tests vérifient les règles de drop hold du code hôte et ne testent pas le rendu GPU.

## Interface de notes et composition v6

Le retour sur v5 la qualifie de présentation provisoire. Cette révision remplace le prototype de colonnes de notes par deux groupes de récepteurs isolés : Dad compact en haut à gauche et BF en bas, avec une structure de disposition par groupe conservant leurs états séparés pour le futur mode à deux joueurs. Triangle masque/affiche les lanes Dad sans supprimer leur chart, leur simulation autoplay ni leurs animations. Le réglage initial reste visible. Les commandes et règles de jugement demeurent dans le code existant et le défilement/jugements restent indexés sur `Stream_GetSamplesPlayed()`.

Les notes utilisent des flèches géométriques orientées, chacune avec sa couleur de lane et son contour sombre. Les récepteurs distinguent repos assombri, bouton maintenu et confirmation de jugement. Les tenues ont une tête fléchée, un corps et une terminaison; pendant une tenue joueur active, la portion déjà consommée est retirée du corps dessiné. Les frontières de clipping diffèrent par groupe pour garder les flux séparés. L'interface sobre présente portraits BF/Dad, score/combo et jauge de vie; les diagnostics (position audio, tampon, erreurs CD/underruns, état de manette, hits/misses/drops, voix et pan) peuvent démarrer masqués ou visibles via `FUNKIN_PS1_DIAGNOSTICS_DEFAULT`. HUD et pistes ne subissent pas les mouvements de caméra.

### Composition et qualité des textures

Le zoom rythmique discret, les mouvements horizontaux vers le chanteur et les facteurs de parallaxe du décor sont pilotés par la même horloge audio; les pistes et le HUD restent fixes. La scène resserrée conserve le stage et les enceintes, Dad à gauche, GF au centre et BF à droite. Les déplacements de caméra sont de quelques pixels et la marge/clipping maintient les notes à l'écran. Cette première impulsion reste volontairement modeste : le rendu n'est pas encore une présentation finale de type PaRappa/FNF.

Les conversions gardent décor, Dad et GF en 8bpp avec une palette partagée de 255 couleurs. L'audit RGB555 des images BF officielles à 64×96 a montré qu'une palette dédiée 8bpp améliore nettement les poses principales. Le v7 garde donc idle/chants BF en 8bpp (RMSE 3,99) et seulement les huit poses de faute en 4bpp (RMSE 17,88). Ces RMSE comparent les valeurs couleur après quantification, pas la perception, les contours, les détails géométriques ni les artefacts d'animation. La comparaison du rendu réel à 320×240 montre des silhouettes BF/Dad/GF nettes, mais le nearest-neighbor reste une adaptation d'images source et pas une finition pixel art. La 4bpp est désormais limitée aux fautes, non imposée à la scène entière.

Les captures de scène en ouverture sont `ps1/build/bopeebo-fnf-ui-off-v7/captures/dad-lanes-off.jpg` et `ps1/build/bopeebo-fnf-ui-v7/captures/dad-lanes-on.jpg`. Elles viennent de deux exécutions directes de DuckStation à 320×240; score −600 et −900 respectivement, donc phase et remplissage de vie proches, mais pas une comparaison contrôlée à la même image. La capture sans lanes provient d'une variante compilée avec Dad masqué au démarrage. Le code du toggle Triangle garde chart/autoplay/animations actifs, mais sa transition bouton n'a pas été testée dans cette session.

### Budgets mis à jour

Le build v7 et ses variantes de lanes/diagnostics ont les mêmes tailles de sections : text 684 756 o, data 2 234 o, BSS 13 644 o, soit 700 634 o; le ring CD→RAM de 98 304 o porte le sous-total suivi à 798 938 o (~780,2 Kio). `text` comprend les pages d'images, chart, SFX et code; les données de texture présentes en RAM principale ne sont pas économisées par le préchargement VRAM. Heap maximal, pile, allocations SDK et hautes eaux RAM n'ont pas été instrumentés.

La carte VRAM v9 comprend 307 200 o de double framebuffer, 622 592 o de textures (9 pages 8bpp + 1 page 4bpp), 1 056 o de trois CLUT (deux de 256 entrées et un de 16) et 32 Kio réservés à la police : total suivi/planifié 963 616 o, marge arithmétique 84 960 o sur 1 Mio. Les 8bpp sont dans les bandes libres à droite des framebuffers; la page 4bpp est dans le couloir x=320..383 à y=256, hors des buffers de 320 mots; les palettes sont réparties dans les lignes libres y=480 et y=496. Une première variante v6 plaçait à tort une CLUT sur le second framebuffer; v7 a corrigé cette collision. Le test de l'animation de faute a ensuite montré que `getTPage` quantifie le Y à 0/256 : le placement 4bpp à y=240 rendait un artefact. La v9 l'aligne à y=256; la validation statique du convertisseur vérifie désormais bornes et non-chevauchement des deux framebuffers, 10 pages, trois CLUT et réservation de police. Le résultat visuel de l'animation de faute sur la v9 reste à exécuter. Les 32 Kio de police restent une réservation et non un high-water mesuré. SPU et CD restent inchangés : 34 304 o alloués (32 768 musique + 1 536 SFX), 8 voix utilisées sur 24 (4 stream + pool 4 SFX), 16 voix libres; 98 304 o/s CD (48 secteurs/s), ring ~1 s. La marge doit loger les futurs charts, états/animations, personnages, décors, menus, travail temporaire et sons gameplay; ces valeurs ne sont pas le budget du jeu complet.

### Construction et observation de cette révision

Le disque de livraison compilé est `ps1/build/bopeebo-fnf-ui-v9/funkin-ps1-bopeebo-playable.cue` + `.bin` (10 428 768 o, 4 434 secteurs, SHA-256 BIN `E9F1368B166D1C39C1071195588A3B7D8B65425D425AC1D552134F2F8867262D`). La variante Dad masqué est compilée à part dans `ps1/build/bopeebo-fnf-ui-off-v9/` (SHA-256 BIN `A79C3F79AF6882E3CE6FD1EFA56EA47C345955D5BD364E59926132E5B051230A`). Une version v9 diagnostics-on n'a pas été construite; l'ancienne version diagnostic v7 ne reflète pas l'alignement y=256. Le v9 utilise PSn00bSDK 0.24/GCC 12.3.0, FFmpeg 7.1.1, Python 3.13/CMake 4.4/Ninja et mkpsxiso 2.03; chart Normal et VAGi 43 008 Hz officiels restent hors Git. Aucun asset ni SDK n'est versionné.

La build v7 a été exécutée dans DuckStation 0.1-8675; au début du morceau, scène, lanes, HUD et BF 8bpp sont apparus correctement à 320×240 et 60 IPS. La variante Dad masqué démarre aussi et ses récepteurs Dad sont absents. Pendant l'exécution sans commandes, l'animation de faute BF a affiché une bande erronée : diagnostic confirmé ensuite par l'alignement de texture page 4bpp à y=240, incompatible avec `getTPage`. La v9 corrige le placement à y=256 et compile, mais n'a pas été exécutée; la faute n'est pas déclarée réparée/validée en runtime. Les observations diagnostics antérieures sur une variante pré-v7 indiquaient Pad `ON`, tampon 32 768/98 304 à 00:10.166 puis 98 304/98 304 à 00:18.166, CD 0, U 0, 60 puis 59 IPS. Après 13 misses sans commande de jeu, la vie est arrivée à zéro et le code a arrêté le stream. Ce relevé bref ne concerne pas la v9, ne valide pas une lecture complète, une stabilité multi-minute ou une dérive. `PAD ON` prouve seulement la détection; aucune transition bouton n'a été validée dans cette exécution. L'audio n'a pas été évalué subjectivement. La validation audio et gameplay antérieure reste le retour utilisateur sur l'ancien commit; elle ne valide pas cette révision graphique. Aucun test console réelle.

Le CUE à essayer est `ps1/build/bopeebo-fnf-ui-v9/funkin-ps1-bopeebo-playable.cue`. Priorité de l'essai manuel : vérifier d'abord les poses de faute BF 4bpp après quelques misses, puis Triangle, quatre directions, hits/holds, mute Circle, SFX Square et redémarrage. Pour les compteurs CD/underruns, une build diagnostics-on doit être générée depuis le même cache/configuration avec `-DFUNKIN_PS1_DIAGNOSTICS_DEFAULT=ON`; elle recouvre le haut de scène et n'est pas le disque livrable. Lire ensuite la chanson entière, avec commandes, en surveillant les compteurs et la vie. La v9 n'a pas encore d'observation runtime, et le jalon visuel attend validation utilisateur.

## Official note art and character footing (v10)

The user’s v9 feedback is recorded as a validation of that version only: the arrow groups and controls were legible/functional and gameplay seemed broadly correct, while Dad’s legs were cut off and BF floated. It is not validation of this v10 rendering.

### Official assets and rendering changes

The playable build now converts the pinned “Funkin'” note style from `assets/preload/data/notestyles/funkin.json`: directional notes from `assets/shared/images/notes.png`, idle/press/confirm receptor animations from `noteStrumline.png`, and sustain body/end-cap slices from `assets/preload/images/NOTE_hold_assets.png`. Their XML metadata is used for atlas frame bounds. This replaces the prior hand-drawn arrows and rectangular holds. Directional note/receptor/hold textures use four small 4bpp pages with per-lane 15-color CLUTs; sampled colors and outlines are retained, but quantization remains visible and this is still a PS1 conversion, not the final art pass. Other principal scene art remains 8bpp. CMake now tracks all source files used by conversion as dependencies so a pinned asset change regenerates the packed header.

Dad and Girlfriend poses continue to be composed through their official Animate rigs and transformed frame bounds; BF uses its official Sparrow atlas rectangles and frame offsets. The stage foreground rail is drawn behind the characters. Dad/BF base positions are both adjusted by four canvas pixels as a shared floor anchor, keeping their soles on the same floor strip across the sampled pose set instead of shifting an individual pose. The selected pose samples and bounds are preserved, but exhaustive animation timeline coverage is not implemented. In DuckStation captures from the final candidate, both characters’ shoes are visible and touch the stage floor; this is a direct visual observation, not a console test.

### VRAM and runtime memory

The v10 VRAM map includes both 320×240 framebuffers (307,200 bytes), nine 8bpp texture pages (589,824 bytes), two 4bpp texture pages (65,536 bytes), four 15-entry CLUTs plus the existing three large CLUTs (1,184 bytes total), and the 32 KiB font reservation. The tracked total is 996,512 bytes of 1 MiB, leaving an arithmetic margin of 52,064 bytes. The validator checks page/CLUT bounds and overlap with both framebuffers. Texture pages, palette and font placements are reserved/packed; the 32 KiB font area is not an observed allocation high-water mark.

For the v10 ELF, `mipsel-none-elf-size` reports text 716,412 bytes, data 2,254 bytes, BSS 20,204 bytes (738,870 bytes combined). Text contains code and generated chart, SFX and visual data. Adding the 98,304-byte CD ring gives a tracked main-RAM subtotal of 837,174 bytes (~817.6 KiB); stack, SDK allocations, heap high-water and temporary graphics work were not measured. SPU remains 32,768 bytes for music plus 1,536 bytes for SFX, 8 of 24 voices in use with 16 free. The audio stream and CD throughput are unchanged from the validated four-channel design; no new competing CD reads were added. These are probe/milestone figures, not a complete game budget, and the remaining RAM/VRAM margin must still accommodate fuller character animation, charts, menus, effects and gameplay data.

### Build and runtime observation

The final candidate BIN/CUE is in the ignored, separate directory `ps1/build/bopeebo-official-assets-v10/`; BIN size is 10,464,048 bytes (4,449 sectors), SHA-256 `E6E578071C0CB5671F151A478C85A41F42709BB184E2452AAAE69C27EECEE6ED`. It was built with PSn00bSDK 0.24/GCC 12.3, CMake/Ninja and the pinned asset checkout. The generated art header and all build products remain outside Git. The manual DuckStation run of this candidate showed the 320×240 scene and a 60 IPS status readout. Captured images are in `ps1/build/bopeebo-official-assets-v10/captures/` (ignored): `idle.png` and `sing.png` show the composed scene and Dad singing pose, each with both characters’ feet visible. A miss capture is still missing: during these observations the gamepad continued producing successful hits/combo changes, so no miss frame was observed; I left the live controller state untouched. The brief runtime sampling does not establish full-song stability, exact miss/hold behavior, zero CD errors/underruns, audio quality, or synchronization drift. No real console was tested. The previously user-validated audio/gameplay results apply to earlier commits, not this visual revision.

This revision corrects the concrete problems from v9, but remains a staged visual prototype. Next, capture the miss pose from this exact image with the gamepad released, then test a whole song with diagnostic counters, all direction/receptor/hold transitions, camera extremes, mute, SFX and restart; collect user feedback before calling the art pass validated.

## Révision v13 — composition, caméra et transparence des notes

Le checkout `ps1-port` a été réconcilié avant ces changements : au départ, son arbre local avait le même SHA d’arbre que la tête distante de la PR #1 (`3a93df7` côté distant). Les changements locaux v10 n’ont donc pas été recopiés comme un second commit. Le retour utilisateur indique que la v10 n’est pas acceptée visuellement; cette v13 demeure un prototype de travail et n’est pas une validation esthétique finale.

Cette révision rapproche Dad et BF de GF, dessine GF puis Dad puis BF afin que les chanteurs passent devant les enceintes, et place l’avant-scène à y=150 avec une hauteur convertie de 73 pixels (au lieu de 56) pour conserver davantage le rapport de forme officiel du stage. L’emplacement s’inspire de `mainStage.json`; son adaptation en 4:3 reste une composition spécifique au port. Le rendu DuckStation présenté dans la capture montre les pieds et le raccord mur/sol, mais il ne couvre pas systématiquement toutes les poses ni les extrêmes de caméra.

La conversion du chart exporte désormais les événements officiels `FocusCamera`. La scène suit ces sections (Dad/BF) avec une interpolation smoothstep sur 550 ms et un déplacement configuré de ±18 pixels. Le zoom de pulsation et le déplacement de scène sont pilotés par `Stream_GetSamplesPlayed()`; HUD et notes restent ancrés à l’écran. La vidéo de 9,97 s montre le mouvement en jeu, sans marge noire découverte. La valeur ±18 est le paramètre du code, pas une mesure indépendante du déplacement à l’écran; aucune validation sur le morceau entier n’a été faite.

Les récepteurs sont maintenant découpés depuis leurs rectangles visibles de l’atlas Sparrow, plutôt que depuis leur grande toile logique avec offsets négatifs; ils sont rendus en 32×32, comme les flèches joueur. Les flèches, récepteurs, corps et terminaisons de tenues utilisent les atlas officiels épinglés. Le fond noir des notes venait de la conversion FFmpeg : le format RGBA était demandé à la sortie seulement, ce qui laissait certains filtres négocier un intermédiaire opaque. `format=rgba` est maintenant placé avant le recadrage/redimensionnement. Vérification du crop d’une flèche générée : 435 pixels transparents/semi-transparents et aucun pixel noir opaque; l’image source officielle comporte également des pixels transparents. Ce correctif est visible dans l’exécution v13. Les RMSE de flèche 4bpp mesurés par le convertisseur sont 8,63 gauche, 11,29 bas, 14,42 haut et 11,11 droite (valeurs RGB); ce sont des métriques de conversion, pas une validation subjective.

Le HUD de santé n’est qu’un affichage en deux zones opposées (Dad rouge à gauche, BF vert à droite, frontière mobile avec portraits). `health_q8`, ses gains/pertes, seuils et game over n’ont pas été changés. Les retours Sick/Good/Bad/Shit affichent brièvement le jugement déjà déterminé par le calcul en place; les fenêtres de jugement n’ont pas changé. Écart visuel explicite : ces textes utilisent la police système et les deux marqueurs de vie sont des petites images de frames personnages, pas les illustrations officielles de jugement et d’icônes HUD. Les trois états défavorable/équilibré/favorable n’ont pas été capturés comme une série de contrôle.

### Budget mesuré/estimé de v13

| Ressource | Utilisation suivie | Nature / réserve |
|---|---:|---|
| RAM principale ELF (`text+data+BSS`) | 739 494 o (`717 036 + 2 258 + 20 200`) | Mesuré avec `mipsel-none-elf-size`; contient notamment le code et les textures statiques. |
| Ring audio CD→RAM | 98 304 o | Configuration connue du lecteur; environ 1 s au débit 98 304 o/s. |
| Sous-total RAM suivi | 837 798 o (~818,2 Kio) | Somme ELF + ring, pas un high-water mark; heap, pile, allocations et runtime n’ont pas été mesurés. |
| VRAM totale PS1 | 1 048 576 o | Carte vérifiée par le convertisseur sans chevauchement avec framebuffer, texture pages, CLUT et réserve police. |
| Double framebuffer | 307 200 o | 320×240×16bpp ×2. |
| Pages de textures | 655 360 o | 9 pages 8bpp (589 824 o) et 2 pages 4bpp (65 536 o), préchargées. |
| CLUT | 1 184 o | Réservation des palettes générées. |
| Police réservée | 32 768 o | Réservation estimée, pas une mesure d’allocation effective. |
| Marge VRAM arithmétique | 52 064 o (~50,8 Kio) | 1 Mio moins les régions ci-dessus; marge limitée pour scènes et ressources supplémentaires. |
| SPU / CD | 34 304 o / 8 voix | 32 768 o musique + 1 536 o SFX; 4 voix musicales + pool de 4 SFX, 16 voix libres sur 24. Débit CD 98 304 o/s; pas de lecture concurrente de textures. |

Le chargement des textures dans la VRAM ne libère pas leur copie statique en RAM principale. Ce budget est celui du prototype audio/visuel et ne représente pas le jeu complet. Les charts, animations/scènes supplémentaires, menus et effets demanderont une mesure de pic et une nouvelle stratégie mémoire.

### Construction et vérifications de v13

Build PSn00bSDK 0.24 / GCC 12.3.0, CMake 4.4.4, Ninja, FFmpeg 7.1.1 et mkpsxiso 2.03. BIN/CUE compilés dans `ps1/build/bopeebo-scene-camera-ui-v13/`, hors Git : BIN 10 466 400 octets (4 450 secteurs), SHA-256 `11C9BB94C8A5B1ABD9C97ABFC51BD517CB7B99FDFFBA7BD0092666A700AD4119`. Entrées chart, assets officiels et VAGi restent hors dépôt; le SDK et ses bibliothèques propriétaires ne sont pas versionnés. Le fichier de capture réel est `ps1/build/bopeebo-scene-camera-ui-v13/captures/camera-follow-v13.mp4` (640×480, 30 fps, 9,97 s, vidéo seule) et son poster `camera-follow-v13.png`.

L’ELF v13 et l’image disque ont été compilés, puis l’image a été exécutée brièvement dans DuckStation 0.1-8675 à 320×240 (environ 59–60 IPS observées). La capture confirme la composition au repos/chant, le HUD, des notes et le mouvement de scène sur ce court extrait. Les cinq tests automatisés `test_bopeebo_hold_drop.py` passent, couvrant tenue complète, relâchement anticipé (pénalité unique), tolérance finale de 160 ms, récupération de voix à la réussite suivante et chemin C correspondant. `py_compile` des deux convertisseurs passe; `git diff --check` passe.

Ce constat n’est pas un essai complet : aucune chanson entière n’a été rejouée sur v13; aucun test de tous les boutons, mute Circle, SFX, reprise/redémarrage, compteurs CD/underrun ou comparaison audio n’a été effectué dans cette session; la manette n’a pas été validée sur cette image. La capture vidéo ne contient pas de son. Pas de test console réelle, pas de mesure de dérive audio, ni de mesure high-water RAM. Les validations utilisateur des builds précédents restent des retours sur ces commits, et ne sont pas transférées à v13.

Prochaine vérification : lancer le CUE v13 dans DuckStation avec diagnostics visibles, jouer tout Bopeebo en contrôlant les quatre directions, tenues, mute, SFX, Triangle et redémarrage, noter CD/underruns et écouter le mix; demander ensuite un retour utilisateur sur la lisibilité des flèches, ancrages et caméra. Répéter sur console réelle lorsque le matériel sera disponible.

Commande de reconstruction de v13 (après préparation des chemins locaux ci-dessous; les assets doivent être initialisés à la révision épinglée, le chart JSON, le VAGi et FFmpeg sont hors dépôt) :

```powershell
$sdk = 'C:\Users\Manau47\Documents\Codex\toolchains\PSn00bSDK-0.24-win32'
$cmake = 'C:\Users\Manau47\Documents\Codex\toolchains\cmake-4.4.4-windows-x86_64'
$env:PSN00BSDK_LIBS = "$sdk\lib\libpsn00b"
$env:Path = "$sdk\bin;$cmake\bin;$env:Path"
$env:CMAKE_ROOT = "$cmake\share\cmake-4.4"
cmake -S ps1 -B ps1/build/bopeebo-scene-camera-ui-v13 -G Ninja `
  "-DCMAKE_MAKE_PROGRAM=$sdk/bin/ninja.exe" `
  "-DCMAKE_TOOLCHAIN_FILE=$env:PSN00BSDK_LIBS/cmake/sdk.cmake" `
  -DPSN00BSDK_TC=$sdk -DPSN00BSDK_TARGET=mipsel-none-elf `
  -DCMAKE_BUILD_TYPE=Debug `
  "-DFUNKIN_PS1_ASSETS_DIR=$PWD/assets" `
  "-DFUNKIN_PS1_BOPEEBO_CHART_JSON=$env:TEMP/fnf-bopeebo-port/bopeebo-chart.json" `
  "-DFUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH=$env:TEMP/fnf-bopeebo-quality/bopeebo-43008-4ch.vag" `
  '-DFUNKIN_PS1_FFMPEG=T:/Docker/MGTV Playlist Gen/ffmpeg-7.1.1-essentials_build/bin/ffmpeg.exe'
cmake --build ps1/build/bopeebo-scene-camera-ui-v13 --target ps1-bopeebo-playable-disc
```

## Révision v15 — composition officielle et caméra de scène

La vidéo utilisateur du 25 octobre sert de référence de cadrage. La v13 ne reproduisait pas ses changements de focus de manière perceptible; cette révision remplace le déplacement de quelques pixels par un suivi de la caméra dans l’espace de scène. Le retour utilisateur sur v13 (« présentation provisoire ») reste applicable; **la v15 est un prototype exécuté, pas une validation visuelle finale**.

### Source de scène et adaptation 4:3

Le convertisseur lit `assets/preload/data/stages/mainStage.json` depuis le sous-module épinglé `724eba9de9e76761d9cefd52169926bc51c760a5`. Il réutilise les positions et offsets de caméra Dad `(335,885)/(150,-100)`, GF `(751.5,787)/(0,0)` et BF `(989.5,885)/(-100,-100)`, ainsi que l’ordre z (fond, GF, Dad, BF, avant-scène). Les coordonnées monde sont réduites au huitième pour la PS1, puis le décor officiel est précomposé à ses échelles d’origine dans une toile 352×192. La fenêtre n’est pas étirée : le point de vue est recentré et agrandi pour remplir le 320×240. Cette composition autorise Dad à sortir du cadre lorsque BF chante et BF à être rogné lors du focus Dad, comme dans la référence; elle ne promet pas de montrer tous les pieds/personnages à chaque image.

La scène convertie garde des proportions de sprite cohérentes : Dad 53×96, GF 87×79, BF 52×52, à partir des rectangles et dimensions logiques des rigs/atlas officiels. Le zoom base de caméra est adapté du `cameraZoom=1.1` officiel à un facteur Q8 de 640 (2,5×); le zoom d’impulsion atteint au plus 647/256 (~2,53×). Cette calibration PS1 est un choix de cadrage, pas le zoom littéral 1.1 de Flixel. Les sections officielles `FocusCamera` du chart commandent le focus : Dad à 0 ms, BF à 2 400 ms, Dad à 4 800 ms, puis alternance; transitions smoothstep de 600 ms (quatre temps au BPM 100). La pulsation et les transitions utilisent `Stream_GetSamplesPlayed()`. Notes et HUD sont tracés après la scène et restent en coordonnées écran.

Les pistes BF sont placées à y=194 (au lieu de 216) pour libérer de l’espace en bas; Dad garde son groupe compact en haut à gauche. Triangle masque les pistes Dad sans retirer leurs événements ni animations. Le HUD reprend l’icône officielle Dad/BF et la jauge de rapport de force; le texte `SCENE DEMO` apparaît seulement dans la build de démonstration. `Select` révèle/masque les diagnostics. La build jouable par défaut conserve score, santé, timings, fautes, mute et game over; la démo saute le jugement, le score, la santé et le game over et anime les poses depuis le chart. Elle n’est pas un second mode jouable.

### Cartes, budget et pertes visuelles

Les rendus v14/v15 préchargent 7 pages 8bpp et 2 pages 4bpp : 524 288 octets de texels. Les portraits BF/Dad et Sick/Good/Bad/Shit officiels partagent une page 4bpp avec leurs palettes; notes et états de récepteurs restent issus des atlas officiels. Le convertisseur vérifie les bornes et chevauchements des pages/CLUT avec framebuffers, palettes et zones réservées. La palette 4bpp des popups réduit certains dégradés/détails; les images 8bpp importantes restent à 255 couleurs indexées. Aucune méthode de pixel art n’est revendiquée : c’est un échantillonnage nearest-neighbor de sources officielles.

| Région | Occupation calculée / mesurée | Limite |
|---|---:|---|
| ELF `text+data+BSS` | 602 778 o (`580 324 + 2 262 + 20 192`), mesure `mipsel-none-elf-size` | Texte contient code et données visuelles/chart/SFX statiques. |
| Ring CD→RAM | 98 304 o (96 Kio) | Alloué par le lecteur; durée théorique ~1 s au débit VAGi courant. |
| RAM principale suivie | 701 082 o (~684.7 Kio) | Somme ELF + ring, pas un high-water mark; stack, heap, SDK/runtime et temporaires ne sont pas instrumentés. |
| Double framebuffer | 307 200 o | Deux images 320×240×16bpp. |
| Textures | 524 288 o | 7 pages 8bpp + 2 pages 4bpp, d’après la table générée. |
| CLUT | 1 216 o | Palettes générées et réservées. |
| Police réservée | 32 768 o | Estimation de planification, pas une allocation mesurée. |
| VRAM suivi et marge | 865 472 o utilisés; 183 104 o de marge arithmétique | Sur 1 Mio; la marge doit encore accueillir ressources/allocations futures. |
| SPU / voix | 34 304 o; 8/24 voix utilisées | 32 768 musique + 1 536 SFX; 16 voix libres. |
| Débit CD | 98 304 o/s | Quatre canaux à 43 008 Hz; pas de nouvelle lecture concurrente de graphismes. |

Le préchargement VRAM ne libère pas la copie statique des textures dans la RAM principale. Ces chiffres décrivent uniquement ce prototype, pas le jeu complet; charts de toutes les semaines, personnages animés complets, menus, scènes et SFX demanderont une nouvelle mesure.

### Build et observation DuckStation

Deux configurations ont compilé dans des répertoires distincts :

- `ps1/build/bopeebo-playable-v15/funkin-ps1-bopeebo-playable.cue` — mode normal, `FUNKIN_PS1_SCENE_DEMO_DEFAULT=OFF`, diagnostics masqués par défaut.
- `ps1/build/bopeebo-camera-demo-v15/funkin-ps1-bopeebo-playable.cue` — démo clairement étiquetée, mode normal de jugement désactivé, diagnostics masqués par défaut.

Les deux utilisent PSn00bSDK 0.24 / GCC 12.3, CMake 4.4.4, Ninja, Python 3.13, FFmpeg 7.1.1, le chart JSON et le VAGi 4 canaux à 43 008 Hz fournis localement. BIN/CUE, VAGi, assets convertis, captures et SDK restent dans les répertoires de build ignorés ou hors dépôt. Le BIN jouable v15 pèse 10 308 816 octets; son ELF mesure `text=580 324`, `data=2 262`, `BSS=20 192`. La compilation complète des cibles CMake passe après ajout du garde `TEST_PLAYABLE_BOPEEBO` autour de l’ouverture des polices; les avertissements persistants sont ceux de conversion `volatile` dans `stream.c` du SDK et des messages de configuration d’architecture/chemin de CMake portable.

La build démo v15 a démarré dans DuckStation 0.1-8675, rendu 320×240 logique et un statut ~60 FPS. L’enregistrement réel recadré à 640×480 (`ps1/build/bopeebo-camera-demo-v15/camera-transitions-v15.mp4`) montre Dad→BF puis BF→Dad; les captures fixes sont `camera-focus-dad-1.283s.png`, `camera-transition-dad-bf.png` (~2.766 s) et `camera-focus-bf-4.216s.png`. Ces temps sont ceux affichés par l’horloge du programme et sont reproductibles au redémarrage de la démo. La vidéo vient de la sortie DuckStation, recadrée depuis la capture de bureau; elle ne constitue pas une mesure de dérive.

**Observé dans cette exécution :** boot, affichage de scène, notes, focus et transitions dans les deux sens. **Non vérifié :** lecture sonore à l’écoute dans ce passage, compteurs CD/underrun (masqués pendant la capture), parcours complet, contrôles Triangle/Select/mute/notes/holds/SFX/restart sur cette révision, stabilité audio sur une chanson entière, mesure de dérive, validation visuelle utilisateur et exécution sur console réelle. Les validations précédentes de gameplay et d’audio restent des retours sur leurs commits respectifs et ne sont pas automatiquement transférées à cette révision.

Pour reproduire la configuration caméra, suivre les commandes de build de v13 ci-dessus et ajouter `-DFUNKIN_PS1_SCENE_DEMO_DEFAULT=ON -DFUNKIN_PS1_DIAGNOSTICS_DEFAULT=OFF`. Pour la build jouable, mettre `FUNKIN_PS1_SCENE_DEMO_DEFAULT=OFF`. `Select` est le contrôle documenté pour afficher les compteurs sur la démo; cette bascule reste à confirmer sur l’image v15.

## Révision v18 — portraits de vie et lisibilité CRT

La composition de scène, la caméra et les ancres v15 restent inchangées. Les règles de santé (valeur, pertes/gains, seuils et game over) ne changent pas.

### Portraits et ordre GPU

Les commandes du HUD sont soumises en ordre direct par `DrawPrim`: fond, remplissage et repère de la barre précèdent les portraits. La capture DuckStation de la build v18 montre les portraits Dad et BF au premier plan, au-dessus du remplissage. L'ordre du code était donc correct; le problème se trouvait dans le chemin texture/CLUT 4bpp utilisé par les petites icônes. La conversion v18 les place en 8bpp sur leur page préchargée et réutilise les palettes 8bpp des personnages (palette scène/Dad et palette BF). Ce choix utilise une page VRAM supplémentaire, mais évite une palette dédiée de 16 couleurs et n'ajoute aucune lecture CD concurrente.

Les portraits officiels sont extraits à 24×24. Le texte score/combo est en police SDK 8×8, à y=39 sous les portraits (fin y=37). Aucun contour ou flou artificiel n'a été ajouté. Les sources visuelles restent celles du sous-module officiel épinglé; les pixels générés ne sont pas commités.

### Zone sûre et mode vidéo

Le HUD est contenu dans x=16..303 et y=12..47. Les guides diagnostic donnent deux repères estimatifs: titre 95 % (x=8..311, y=6..233) et action 90 % (x=16..303, y=12..227). Ils sont dessinés seulement lorsque les diagnostics sont visibles; `Select` masque/réaffiche l'ensemble avec les compteurs. Une variante de diagnostic démarre avec ces repères actifs pour faciliter leur inspection, tandis que l'image jouable normale les masque.

Essai effectué dans DuckStation 0.1-8675 x64 avec le rendu D3D11. La barre d'état a indiqué le mode du jeu 320×240 et une cadence émulateur de 59–60 IPS pendant les observations. C'est une exécution en émulateur de classe 60 Hz; cela ne mesure pas la fréquence de sortie console ni les timings électriques NTSC. Aucun essai PAL, moniteur CRT ou console réelle n'a été réalisé. Les marges 95/90 sont des guides de composition, pas une certification d'overscan pour un téléviseur donné. La capture intégrée DuckStation a été exportée à 800×610; les PNG 320×240 fournis sont obtenus par recadrage 800×600 et réduction nearest-neighbor, sans interpolation, à partir de cette image de jeu.

### Mesures du prototype et livrables

| Ressource | v18 mesuré/calculé | Portée et limite |
|---|---:|---|
| ELF text+data+BSS | 668 650 o (`646 196 + 2 262 + 20 192`), `mipsel-none-elf-size` | Mesure du binaire jouable; contient code, tables visuelles/chart/SFX. |
| Ring CD→RAM | 98 304 o | Allocation configurée, hors pile/heap/SDK et allocations non instrumentées. |
| RAM principale suivie | 766 954 o (~749 Kio) | Somme ELF + ring; pas un maximum d'utilisation mesuré. |
| Double framebuffer | 307 200 o | 2×320×240×16bpp. |
| Textures | 589 824 o | 8 pages 8bpp + 2 pages 4bpp; comprend la page portraits additionnelle. |
| CLUT | 1 184 o | Palettes générées; les portraits réutilisent les palettes personnage. |
| Police réservée | 32 768 o | Réservation estimative du SDK. |
| VRAM suivie | 930 976 o utilisés; 117 600 o libres par calcul | 1 Mio total; les allocations runtime non déclarées restent à mesurer. |
| SPU / voix | 34 304 o; 8/24 voix | Inchangé: musique quatre canaux et pool SFX du prototype. |
| CD | 98 304 o/s | Flux quatre canaux à 43 008 Hz; pas de changement audio dans cette révision. |

Image jouable, hors Git: `ps1/build/bopeebo-crt-v18/funkin-ps1-bopeebo-playable.bin` et `.cue` (BIN 10 384 080 octets, 4 415 secteurs). Une seconde image `ps1/build/bopeebo-crt-v18-diagnostics/` démarre diagnostics et guides visibles. Captures 320×240: `ps1/build/bopeebo-crt-v18/captures/gameplay-native-320x240.png` et `safe-guides-native-320x240.png`; les captures source DuckStation 800×610 sont conservées dans le même dossier pour la traçabilité du recadrage.

Compilation PSn00bSDK 0.24/GCC MIPS réussie pour les deux variantes. Exécution DuckStation observée: scène, portraits devant la barre et guides titre/action visibles. Ce passage ne valide pas une écoute audio, la chanson entière, une stabilité audio prolongée, le rendu sur CRT/PAL, ni la console réelle. Les tests à refaire sur matériel comprennent la lisibilité selon l'overscan du téléviseur, niveaux/contrastes, scintillement des détails, cadence PAL/NTSC et stabilité audio/commandes.
## Révision v19 — plage de santé et ancrage des portraits

Retour utilisateur : l’affichage de santé de v18/v18bis paraissait borné et les portraits trop éloignés de la frontière. La logique de jeu (`health_q8`, gains/pertes, seuils et game over) reste inchangée.

Le défaut était dans la représentation : le vert utilisait `health_q8 * 62 / 512` sur une barre intérieure de 124 pixels, donc plafonnait à la moitié de sa largeur. v19 calcule désormais le vert sur toute la plage 0..124, arrondi et borné en affichage seulement. La frontière X vaut 222, 191, 160, 129 et 98 aux valeurs de santé 0, 25, 50, 75 et 100 %. Le rouge remplit le reste à gauche, le vert à droite. La ligne verticale blanche a été retirée : elle était ajoutée localement et n’est pas requise par la barre du moteur original; la frontière et les portraits la rendent lisible.

Le moteur original calcule les deux positions à partir du même point de barre et de `POSITION_OFFSET=26` sur une icône 150×150. Sur la barre PS1 de 124 pixels et les portraits 24×24, la transposition donne Dad à `frontière - 20` et BF à `frontière - 4`. Les deux sprites ont donc le même ancrage logique, chacun décalé de son côté comme dans `HealthIcon.updatePosition()`. Seuls les portraits sont bornés à la zone sûre horizontale x=16..280; cette protection ne réduit jamais la course du remplissage.

Les marges alpha des sources officielles ont été mesurées : Dad 150×150, dessin visible x=23..133/y=8..137; BF 300×150, frame idle x=1..138/y=33..114 et frame losing x=2..138/y=32..121. L’extraction garde ces canvases et les réduit sans flou, car leurs marges font partie de l’ancrage du moteur. Les anciens offsets de HUD ne tenaient pas compte de ces marges combinées à la moitié de course de la barre; ils créaient notamment un trou visible entre les dessins. Aucun offset par pose n’a été ajouté. Le fichier BF historique est une animation legacy à deux frames (idle/default et losing); v19 respecte le seuil losing original de 20 % (`health < 0,4` sur 2,0), mais ne peut pas distinguer l’état winning >80 % faute de frame winning distincte dans cet asset.

Le grand bandeau opaque du HUD normal a été supprimé pour rendre le décor/GF visibles. La barre conserve seulement son cadre étroit (132×16); le score a une petite bande sombre sous le texte (208×9), le temps de vérifier un contour de police matériel équivalent. Le panneau de diagnostics reste réservé à l’affichage diagnostic.

### Vérification visuelle déterministe

L’option CMake `FUNKIN_PS1_HEALTH_BAR_TEST_DEFAULT=ON` construit une image diagnostic distincte. Elle fixe l’affichage à 0, 25, 50, 75 et 100 % pendant dix secondes par valeur sur l’horloge audio, puis fait un balayage triangulaire 0→100→0 % sur 40 secondes. Elle ne modifie jamais `health_q8`. Avec `FUNKIN_PS1_SCENE_DEMO_DEFAULT=ON`, le gameplay reste en mode démo sans pénalité; le diagnostic compact montre simultanément santé réelle, santé affichée, X de frontière et X des deux sprites. Le contrôle attendu à 0/25/50/75/100 est respectivement `HP HUD 0/25/50/75/100`, frontières `222/191/160/129/98`, couleur rouge vers vert sans inversion, et portraits ancrés sur la même frontière. Les diagnostics démarrent visibles; Select les masque/affiche.

Sources alpha mesurées par décodage PNG; la compatibilité de ces portraits reste vérifiée dans l’émulateur, pas sur un téléviseur CRT. v19 conserve la composition v15 appréciée. L’overscan CRT, le mode PAL, les couleurs sur CRT et le comportement sur console réelle restent à valider.

### Résultat de compilation et exécution

Build normal compilé avec PSn00bSDK 0.24/GCC MIPS 12.3 et Ninja : ELF, BIN de 10 384 080 octets et CUE de 93 octets. Build visuel séparé avec `FUNKIN_PS1_HEALTH_BAR_TEST_DEFAULT=ON`, caméra démo et diagnostics : BIN de 10 379 376 octets, CUE de 93 octets. La variante de test garde la santé de gameplay à 50 % dans cet essai; la valeur affichée est une variable distincte.

Dans DuckStation 0.1-8675 x64, D3D11, le jeu a été observé à 320×240. Les diagnostics ont montré les cinq états suivants, tous avec `REAL 50%` : `DRAW 0% / EDGE X=222 / DAD X=202 / BF X=218`, puis `25% / 191 / 171 / 187`, `50% / 160 / 140 / 156`, `75% / 129 / 109 / 125` et `100% / 98 / 78 / 94`. Les captures confirment l’augmentation du vert de droite à gauche, la diminution du rouge, la frontière correspondant à la valeur et les portraits qui suivent la même frontière. À 100 %, le vert atteint le bord gauche prévu du remplissage; à 0 %, il n’en reste aucun. Un état du balayage observé à `DRAW 5% / EDGE X=216 / DAD X=196 / BF X=212` confirme le mouvement indépendant de `health_q8`. Les guides CRT restent visibles dans la build diagnostic; la scène et les sprites se déplacent derrière un HUD fixe.

Les captures PNG fournies ont été extraites des images DuckStation puis recadrées/réduites par nearest-neighbor à la résolution du jeu (320×240), sans interpolation. Fichiers : `health-0.png`, `health-25.png`, `health-50.png`, `health-75.png`, `health-100.png` et `health-moving.png`. Le disque diagnostic est sous `health-test/`; le disque jouable normal est à la racine du livrable. Les BIN/CUE ne sont pas ajoutés à Git.

Ce passage valide visuellement le calcul et l’ancrage dans l’émulateur, pas une mesure de dérive, une validation CRT/PAL ou une exécution sur console. Le résultat audio et gameplay des précédentes versions n’a pas été rejoué lors de ce test de HUD; aucun underrun audio pour cette variante n’est donc affirmé.

## Révision v20 — zone sûre Dad et cycles d’animation audio-clockés

La v19 reste en attente de validation utilisateur. Cette révision ne la considère pas validée sur la seule base de la démo.

### Zone sûre et scènes animées

Les guides diagnostiques restent estimatifs : le bleu/gris (`RGB 48,96,112`) encadre la zone titre 95 % (x=8..311, y=6..233); le vert (`RGB 96,160,128`) encadre la zone action 90 % (x=16..303, y=12..227). Le groupe Dad/autoplay a été décalé de 6 pixels vers l’intérieur : ses récepteurs et notes de 16 px commencent désormais à x=16, au bord de la zone action. Le même layout sert aux notes, tenues et flashes de confirmation; chart, ownership, timing et caméra ne changent pas.

Le convertisseur extrait les 14 étapes du timeline idle officiel de BF et n’en stocke qu’une fois les rasters identiques; la séquence conserve donc les répétitions et cadence d’origine. Dad utilise six poses du cycle de rig idle réparties sur la séquence de 12 images source, plus deux poses chantées par direction; le fit commun garde le sol et les offsets. GF alterne les séquences gauche/droite et utilise neuf poses extraites par côté. Chaque pose provient du rig officiel Week 1, qui inclut le mouvement des enceintes. Les chanteurs reviennent au cycle idle après la durée chant définie par le gameplay. Le beat, les impulsions, animations de repos/chant et événements caméra utilisent le compteur de samples audio et une table tempo Q16 continue; la conversion supporte les événements de changement BPM. Le chart Bopeebo épinglé n’a pas de changement de BPM, donc ce chemin est compilé mais le cas d’un changement effectif n’est pas observé sur le morceau.

Ces séquences sont des échantillons de poses rig sélectionnés, pas une lecture complète de tous les dessins intermédiaires, ni une validation utilisateur de finition. Elles gardent l’identité des rigs tout en limitant les pages chargées en 8bpp. Le tableau d’animation consomme 98 frames visuelles sur 11 pages (9×8bpp + 2×4bpp); le convertisseur vérifie toutes les pages, palettes, framebuffers et réserves dans la carte VRAM.

### Budget v20

| Ressource suivie | Estimation v20 | Portée |
|---|---:|---|
| ELF text + data + BSS | 734 698 o (`712 228 + 2 262 + 20 208`), mesuré avec `mipsel-none-elf-size` | Code et tables statiques; comparaison v19 `668 650 o`, soit +66 048 o. |
| Ring CD→RAM | 98 304 o | Allocation configurée, non high-water. |
| RAM suivie | 833 002 o (~813,5 Kio) | ELF + ring; pile, heap, allocations SDK et pics runtime non instrumentés. |
| Double framebuffer | 307 200 o | 2×320×240×16bpp. |
| Textures | 655 360 o | 9 pages 8bpp et 2 pages 4bpp; +65 536 o versus v19. |
| CLUT + police réservée | 1 216 + 32 768 o | Palettes mesurées dans les tables; police réservée par estimation. |
| VRAM suivie | 996 544 o utilisés; 52 032 o de marge arithmétique | 1 Mio total; les allocations runtime non décrites restent à confirmer. |
| SPU / voix | 34 304 o; 8/24 voix | Flux musical quatre canaux + pool SFX, configuration inchangée. |
| Débit CD | 98 304 o/s | Quatre canaux 43 008 Hz; aucune lecture CD graphique ajoutée. |

La hausse principale concerne les poses visuelles et le code de conversion/runtime. Ces valeurs décrivent le prototype Bopeebo, pas le jeu complet; le budget ne comprend pas de mesures de marge CPU ou de high-water RAM.

### Compilation, exécution et limites

Deux builds PSn00bSDK 0.24 / GCC MIPS 12.3 ont produit BIN/CUE séparés : `bopeebo-animation-v20-playable` (démo OFF) et `bopeebo-animation-v20` (démo caméra ON). Le build jouable produit un BIN de 10 459 344 octets (4 447 secteurs) et un CUE de 93 octets. Les données officielles, chart et VAGi 4 canaux à 43 008 Hz viennent de sous-modules épinglés ou de fichiers locaux temporaires; aucun SDK, asset généré ou source audio n’est inclus au dépôt.

La version démo a été chargée dans DuckStation 0.1-8675 x64, D3D11, sortie logique 320×240. L’émulateur affichait 58–60 IPS pendant les captures. La capture finale intégrée DuckStation dure 60,60 s (640×480, 59,82 fps, piste audio AAC) et montre la scène de la démo caméra. Elle commence à l’horloge musique 27,766 s, montre un autre état animé à 57,766 s et atteint l’état final autour de 81,6 s; les images à 2 et 30 s de la capture sont distinctes. Elle couvre un extrait continu jusque vers la fin du morceau, pas un parcours jouable depuis le début. Les animations et le rendu sont constatés dans cet extrait; aucun retour utilisateur ne valide encore v19 ou la présentation v20.

Restent à rejouer dans un test utilisateur : plusieurs cycles idle complets, Dad/GF/BF en chant et retour idle, pistes Dad visible/masquée, toute la chanson depuis le début, mute BF, tenues, SFX, redémarrage, compteurs CD/underrun et stabilité audio avec cette nouvelle scène. Le cas de changement BPM a été vérifié par conversion synthétique (100 BPM, puis 120 BPM à 60 s → 2 580 480 samples et beat Q16 6 553 600), mais pas exécuté dans DuckStation. Pas de mesure de dérive, d’essai sur CRT/PAL ni de validation console réelle. Référence visuelle examinée : `Screen_Recording_20261025_185817.mp4` (98,219 s, 1200×1080, 120 fps); les poses et compositions sont adaptées, pas une validation de parité visuelle. Les BIN/CUE et la vidéo sont hors Git sous `outputs/FNF-PS1-v20-final/` (mode jouable à la racine, caméra démo dans `camera-demo/`, capture `camera-transitions-v20.mp4`).

## Révision v21 — correction rouge et première navigation menu

Le retour utilisateur approuve globalement v20 et signale la perte du rouge des flèches droite. Le convertisseur réserve explicitement la teinte rouge officielle dans la CLUT 4bpp droite et vérifie le résultat RGB555 : 360 pixels rouges opaques de la note droite sont conservés. Les pixels sources des récepteurs au repos ne sont pas recolorés. Les mêmes assets directionnels sont utilisés par les groupes BF et Dad, les tenues et les confirmations. Cette vérification automatique couvre l’extraction/quantification; l’affichage des quatre directions dans DuckStation n’a pas été observé pour v21.

Le build ajoute un parcours prototype à la manette : Titre (Start) → menu principal (seule entrée active : Freeplay) → Freeplay (`Bopeebo — Normal`, seule entrée jouable) → jeu. Start ouvre une pause minimale; Croix reprend, Rond retourne au Freeplay; la fin du morceau retourne au Freeplay. Le convertisseur réutilise les ressources officielles épinglées du logo, du bouton Freeplay, du fond Freeplay Week 1 et des rigs BF/GF. Les interactions mobiles, achats, Newgrounds et liens web ne sont pas simulés. Story Mode, Options et Crédits ne sont pas rendus actifs. Le catalogue C utilise une entrée, extensible aux prochaines chansons/difficultés.

Cette étape reste incomplète sur trois demandes explicites : la musique et les sons de navigation des menus ne sont pas encore raccordés; les pages de textures menu et gameplay sont encore chargées ensemble au démarrage (elles partagent la page portraits sans accroître le nombre de pages), et ne sont donc pas libérées/réutilisées par écran; les labels utilisent la police SDK plutôt qu’une conversion des textes de menu officiels. Le build compile, mais aucun parcours ni transition répétée n’a été observé dans DuckStation, et aucune vidéo/capture v21 n’a été produite. L’automatisation UI de DuckStation a perdu la fenêtre après le redémarrage du processus; l’ancienne fenêtre affichait l’ancienne session, qui n’est pas une preuve d’exécution v21.

### Budgets mesurés / estimés par écran

Les allocations sont identiques sur les trois écrans de menu et le gameplay, car cette version ne fait pas encore de libération d’assets par écran. Les chiffres ELF proviennent de `mipsel-none-elf-size -A` sur le build final, et comprennent les tables visuelles statiques mais pas la pile, les allocations SDK/heap ni les pointes temporaires.

| Ressource | Titre / menu / Freeplay | Gameplay / pause | Nature |
|---|---:|---:|---|
| Code `.text` | 46 888 o | 46 888 o | mesuré |
| Données statiques `.rodata + .data + .sdata + .sbss + .bss` | 688 094 o | 688 094 o | mesuré; contient les 655 360 o de pages texture et les états |
| Ring de streaming CD→RAM | 98 304 o | 98 304 o | allocation configurée; présent même menu |
| RAM suivie code + statiques + ring | 833 286 o (~813,8 Kio) | 833 286 o (~813,8 Kio) | somme mesurée/configurée; pas un high-water |
| Framebuffers | 307 200 o | 307 200 o | 2×320×240×16bpp |
| Textures | 655 360 o | 655 360 o | 9×8bpp + 2×4bpp, logo/fond inclus dans pages existantes |
| CLUT + réserve police | 1 216 + 32 768 o | 1 216 + 32 768 o | tables mesurées + réserve SDK |
| VRAM suivie | 996 544 o / 1 Mio; marge arithmétique 52 032 o | idem | carte vérifiée par le convertisseur |
| SPU | 34 304 o; 8/24 voix | 34 304 o; 8/24 voix | tampon musical 32 Kio + SFX 1 536 o; allocation du prototype |
| Débit CD | 0 octet/s | ~98,3 Ko/s | menus silencieux; musique Bopeebo 4 canaux à 43 008 Hz en jeu |

Le chiffre statique `.rodata + .data + .sdata + .sbss + .bss` vaut 688 094 octets; il ne représente pas des allocations toutes indépendantes. Les textures sont encore embarquées dans le binaire/ROM et chargées ensemble en VRAM : aucune économie de RAM n’est revendiquée. Aucun effet de navigation officiel n’est joué au menu. Cette architecture est un jalon d’interaction, pas le découpage mémoire demandé pour la livraison finale.

### Compilation, exécution et vérifications restantes

Build final PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja dans `C:\Users\Manau47\Documents\Codex\ps1-build-v21-menu` : génération de la conversion, compile/link et image BIN/CUE réussis. Image 10 461 696 octets (4 448 secteurs), CUE 93 octets. Le build réutilise les ressources du sous-module assets à la révision épinglée; aucun SDK ni asset source/généré n’est ajouté au dépôt.

Seule validation automatique visuelle : contrôle du CLUT et du rouge avant compilation, plus vérification des chevauchements framebuffer/textures/palettes. Compilation réussie n’est pas exécution. Les quatre couleurs et états, le parcours menu, le mute, la fin de morceau, pause/reprise/retour, plusieurs cycles et les compteurs audio/CD restent à observer dans DuckStation. Aucune validation PAL/CRT ou console réelle. La vidéo utilisateur a servi à cadrer le flux; aucune nouvelle capture v21 n’a été obtenue.

## Révision v22 — CLUT droite isolée et premier menu audio

Base : `facbf1243875fe7e24819eff87d1879527f00584` sur `ps1-port`; assets épinglés à `724eba9de9e76761d9cefd52169926bc51c760a5`. Aucun changement de `main`.

### Flèches et carte GPU

Le défaut v21 comprenait des fragments, donc la perte de rouge seule ne suffisait pas à l’expliquer. L’asset épinglé `staticRight0001` se trouve à `(1628,0)`, taille `155×157`, non tourné; son crop source est propre. Le récepteur PS1 est en 4bpp sur la page UI 10, base VRAM `(320,256)`, UV `(32,96,32,32)`, CLUT droit `(256,480)`. La note droite rouge utilise maintenant sa CLUT séparée `(288,480)`, palette 8. Les états appui/confirmation/tenue gardent le CLUT officiel droit; Dad et BF empruntent le même chemin de rendu.

Le générateur valide les 101 rectangles : profondeur/page cohérentes, UV dans la page 256×256, pas de recouvrement entre frames packées ni entre pages, framebuffers, CLUT et réservation police. Il confirme 360 pixels rouges opaques après quantification RGB555. La carte comprend 9 pages 8bpp + 2 pages 4bpp (655 360 octets de textures VRAM). Ces contrôles sont statiques : le rendu GPU du récepteur droit et de ses états n’est pas observé en jeu sur ce build. La capture v21 n’est pas réputée corrigée.

### Menus et son

Le titre, le bouton Freeplay et le fond Freeplay utilisent les ressources officielles épinglées. `FreakyMenu.ogg` est converti en VAGi quatre canaux à 43 008 Hz et lu en boucle depuis `MENU.VAG`: les canaux 0/1 portent la stéréo, 2/3 sont ADPCM silencieux. `scrollMenu`, `confirmMenu` et `cancelMenu` deviennent des one-shots ADPCM mono dans une banque SPU de 40 448 octets, base `0x12000`, voix 8–10. Ce choix aligne le flux de menu sur le chemin quatre canaux utilisé par le gameplay.

La première variante deux canaux affichait `SPU STREAM ERROR / CODE 8` dans DuckStation, avec zéro erreur CD, après avoir tourné un moment. Cette observation est compatible avec un underrun SPU. La variante quatre canaux s’est ensuite maintenue sans écran d’erreur pendant plus de 140 secondes, donc au-delà de la boucle de la piste (112,953 s). C’est une observation de compteur d’erreurs par absence d’écran fatal, pas une mesure de débit ni une écoute acoustique; les compteurs runtime ne sont pas affichés au menu. Les transitions arrêtent/détruisent le flux courant, puis recherchent et préchargent le nouveau fichier. Le chemin prévu reste Titre → menu → Freeplay → Bopeebo Normal → Freeplay; aucun autre contenu n’est présenté comme jouable.

La page VRAM dédiée aux menus est chargée sur les écrans menu puis effacée par primitive GPU FILL à l’entrée du jeu, et rechargée au retour. Cela isole une page de 64 Kio en VRAM. Les octets source restent embarqués dans les sections statiques de l’exécutable en RAM : aucune économie RAM n’est revendiquée, et un chargement des ressources par CD avec tampon temporaire reste à implémenter. Les libellés gardent la police SDK : ce menu reste un prototype.

### Build et observation

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja : génération, compilation, lien et image BIN/CUE réussis. BIN final `23 268 336` octets (9 893 secteurs), CUE `93` octets; `MENU.VAG` `11 110 400` octets, 4 canaux, durée source `112,953 s`, bouclé. `mipsel-none-elf-size -A` donne `.text 47 968`, `.rodata 706 228`, `.data 2 112`, `.sdata 146`, `.sbss 324`, `.bss 19 880` octets. Le ring d’exécution est configuré à 98 304 octets en plus des sections statiques; pile, heap SDK et haute eau ne sont pas instrumentés. `.rodata` contient les pages graphiques et effets embarqués : ce n’est pas de la RAM libre. Le flux de menu consomme environ 196,6 Ko/s de données CD, soit 64 % du débit brut nominal 2× (307,2 Ko/s); tampons SPU de 32 Kio et quatre voix 0–3 actives, deux audibles. Ces valeurs sont calculées, pas mesurées sur console.

Le BIN quatre canaux a été inséré puis réinitialisé dans DuckStation 0.1-8675. Écran titre/logo/GF observé à 320×240, statut de 59–61 IPS. Le jeu est resté sur le titre pendant plus de 140 secondes sans afficher d’erreur SPU/CD, y compris à travers une boucle de la musique. Le clavier est configuré (`Return/K/J/I/L`), mais les appuis synthétisés dans cette session n’ont produit aucun événement de manette. Aucune navigation menu→jeu n’a donc été observée; le son n’a pas été écouté et aucun état de note/récepteur droite n’a été capturé. Aucun cycle répété, mesure de dérive ou vidéo du parcours.

| État | Résultat |
|---|---|
| Inspecté | Asset `staticRight0001`, champs page/UV/CLUT, carte VRAM, flux menu et conversions VAGi/VAGp. |
| Implémenté | Contrôles de packing, musique et sons menu, résidence VRAM des textures menu, démarrages/retours de flux. |
| Compilé | ELF et BIN/CUE produits avec succès. |
| Exécuté | Démarrage DuckStation, écran titre 320×240, plus de 140 s sans écran d’erreur sur VAGi 4 canaux, une boucle de piste. Une variante précédente deux canaux a montré CODE 8. |
| À vérifier | Écoute réelle de FreakyMenu et effets, note droite rouge et récepteur droit propres (repos/appui/confirmation/tenue, Dad/BF), les quatre directions, navigation et plusieurs transitions, diagnostics CD/underrun en affichage, dérive, console réelle. Ni la correction graphique, ni l’audio audible, ni le parcours menus ne sont déclarés validés. L’utilisateur a signalé en v22 que la note rouge droite avait disparu. |

## Révision v23 — correctif runtime de la flèche droite

La v22 n’est pas considérée validée. Les ressources épinglées et leur crop sont corrects : note droite `notes.xml`, UV d’atlas `(0,154,154,157)`, et 360 pixels rouges opaques conservés dans la texture convertie. Le défaut était dans le chemin GPU propre à la note : la note utilisait une CLUT indépendante à `(288,480)` tandis que les récepteurs/tenues droits utilisaient la CLUT de voie à `(256,480)`. Les données hors ligne étaient correctes, mais la note n’apparaissait pas dans DuckStation. La note utilise maintenant la CLUT droite commune; le rouge est réservé dans cette palette de 15 couleurs. Les récepteurs au repos restent gris. La RMSE droite mesurée par le convertisseur passe de 10,79 à 11,11 niveaux RGB555, soit +0,32; légère perte de quantification documentée, sans changement de format ou taille.

Select affiche une planche diagnostique dans le jeu : les notes, récepteurs au repos, états appuyé et confirmé, corps et terminaisons des tenues des quatre directions. Une option de build `FUNKIN_PS1_ARROW_DIAGNOSTIC_DEFAULT=ON` autolance Bopeebo et montre cette planche pendant le flux réel; elle est désactivée par défaut dans le jeu normal. Le rendu de la note et des récepteurs passe par les mêmes `draw_textured_frame`, tpage, UV et CLUT que les primitives du chart. Le contrôle du générateur couvre toujours 101 rectangles/page/profondeur/UV et la carte VRAM entière; textures: 9 pages 8bpp + 2 pages 4bpp, soit 655 360 octets.

### Compilation, exécution et budget

Build PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja dans `C:\Users\Manau47\Documents\Codex\ps1-build-v23-arrowdiag`, avec `FUNKIN_PS1_DIAGNOSTICS_DEFAULT=ON` et `FUNKIN_PS1_ARROW_DIAGNOSTIC_DEFAULT=ON` : BIN 23 268 336 octets, CUE 93 octets. Sections ELF mesurées par `mipsel-none-elf-size -A`: `.text 48 100`, `.rodata 706 164`, `.data 2 112`, `.sdata 142`, `.sbss 324`, `.bss 19 880` octets; ces sections totalisent 776 722 octets. Ring audio: 98 304 octets; total RAM statique + ring comptabilisé 875 026 octets, hors pile, heap et allocs SDK non instrumentés. VRAM suivie: 996 512 octets utilisés (double framebuffer 307 200, textures 655 360, palettes 1 184, police réservée 32 768), marge arithmétique 52 064 octets. SPU inchangé: 34 304 octets et 8/24 voix. Ce budget concerne la scène de test Bopeebo, pas le jeu complet.

Le nouveau BIN a été lancé dans DuckStation 0.1-8675 x64, D3D11, sortie de jeu 320×240 et 60 IPS affichés. Une capture du vrai flux montre la note droite rouge, les quatre voies/états de la planche et le récepteur droit gris au repos. À cette observation, diagnostics `CD 0`, `U 0`, `PAD ON`; il s’agit d’une observation courte (~14 s d’horloge musicale), pas d’un essai complet du morceau. PNG DuckStation d’origine 800×600 (viewport 320×240 agrandi par l’émulateur): `outputs/FNF-PS1-v23-right-note-fix/duckstation-arrow-diagnostic.png`; BIN/CUE dans le même dossier. L’image diagnostique masque une partie de la scène et n’est pas le HUD de jeu normal.

Compilation et image exécutées sont vérifiées; la correction de la note droite est visuellement observée dans DuckStation. L’input automatisé du poste n’a pas transmis les boutons, donc les quatre voies ne sont pas validées par des appuis manette, ni en contexte Dad/BF séparé. Il reste à vérifier une durée complète, les transitions menu↔jeu répétées, l’écoute audio, les compteurs CD/underrun sur tout le morceau, les menus fidèles, Game Over/retry, résultats réels, CRT/PAL et console. Ces autres écrans sont les jalons suivants; ils ne sont pas déclarés réalisés.
## v25 — jugements, fautes rapprochées et SFX officiels

Retour utilisateur : l’affichage normal et la flèche droite de v24 sont validés; les jugements n’apparaissent plus et la réaction de faute BF semble bloquée jusqu’à la fin de l’animation. Les règles de score, de santé, de fenêtres, de notes tenues et de déclenchement des événements restent inchangées.

Les retours Sick/Good/Bad/Shit restent pilotés par le résultat déjà calculé et l’horloge audio, apparaissent pendant 650 ms et sont dessinés après la scène et les notes, indépendamment de Select. Le tableau de primitives visuelles passe à 384 entrées pour réserver de la place au HUD au-delà du chart le plus chargé; diagnostics et guides CRT restent masqués au lancement. Select affiche les diagnostics et la planche de flèches; `FUNKIN_PS1_ARROW_DIAGNOSTIC_DEFAULT=ON` reste une configuration QA distincte, non utilisée pour le BIN normal. Cette correction est compilée, mais le popup n’a pas été observé visuellement dans le test v25c : elle n’est pas déclarée validée.

Chaque miss, ghost miss et drop effectif réinitialise immédiatement le chronomètre visuel de faute BF sur l’échantillon audio de cet événement, sans garde liée à la fin de l’animation précédente. Un hit suivant sélectionne l’animation de chant déjà prévue et rétablit la voix selon le comportement existant. La boucle chart conserve le traitement unique des drops de holds; aucun événement, SFX, miss ou pénalité additionnel n’est introduit. Si plusieurs fautes tombent dans la même mise à jour, elles sont parcourues dans l’ordre du chart : chaque événement conserve ses compteurs et son SFX existant, tandis que la dernière faute de cet ordre détermine la lane/pose BF visible jusqu’au prochain événement. Ce choix est déterministe.

Le bip de debug n’est plus raccordé au jeu jouable. Les événements de faute existants sélectionnent les trois ressources officielles épinglées `assets/shared/sounds/missnote1.ogg` à `missnote3.ogg`; le gameplay reprend la variation de source (choix aléatoire et gain 0,50–0,60 pour miss/drop, 0,10–0,20 pour ghost miss). Le convertisseur les passe en mono 22 050 Hz, ADPCM SPU mono-shot avec blocs 64 octets alignés; il ne normalise pas les échantillons. Le choix pseudo-aléatoire est reproductible. Le pool de quatre voix SFX (4–7) accepte les fautes rapprochées, coupe la voix dont l’échéance est la plus proche si le pool est plein, et plafonne la somme des volumes à `0x3000`. Les trois voix menu (8–10) partagent le bank resident; l’effet synthétique ne reste disponible que dans les probes.

| Ressource | Budget v25c |
|---|---:|
| Sections ELF suivies en RAM | 831 118 o (`.text`, `.rodata`, `.data`, `.sdata`, `.sbss`, `.bss`, métadonnées de chargement) |
| Ring audio en RAM | 98 304 o; total suivi avec sections 929 422 o, hors pile, heap et allocations SDK non instrumentées |
| VRAM suivie | 996 512 o / 1 048 576; pas de changement de pages/palettes par rapport à v23 |
| SPU | 32 768 o ring music + 87 552 o bank SFX = 120 320 o / 524 288 |
| Voix SPU réservées | 11/24 : 0–3 streaming, 4–7 fautes/effets, 8–10 navigation; 13 non réservées |
| CD | Bopeebo VAGi 98 304 o/s (48 secteurs/s), sans lectures SFX concurrentes; flux menu séparé hors gameplay |

La cible secondaire `ps1-bopeebo-audio-4ch-disc` compile de nouveau : `game_screen` est référencé uniquement dans la branche jouable; le probe audio conserve ses propres commandes et bip de diagnostic.

### Compilation et exécution observée

Build PSn00bSDK 0.24 / GCC MIPS 12.3 / CMake/Ninja : cible jouable et cible audio 4 canaux compilées et images générées. Le BIN jouable final fait 23 322 432 octets (9 916 secteurs MODE2/2352), CUE 93 octets; SHA-256 BIN `56178E50A0FF0D8CA24B7E3C9F2A39A2B22464565FCFA5D2880820E692227865`. Il est livré séparément dans `outputs/FNF-PS1-v25c-judgement-visibility/`.

Le CUE v25c a été chargé dans DuckStation 0.1-8675 x64, sortie logique 320×240. L’écran Freeplay normal s’est affiché sans diagnostics. Le compteur de l’émulateur a oscillé de 42 à 60 IPS pendant la capture. Le mapping clavier DuckStation indique Croix=K et D-pad=flèches, mais l’injection de touches de cette session n’a pas permis de confirmer une entrée de menu/jeu sur v25c. En conséquence, aucune apparition de jugement, faute rapprochée (même direction), récupération par hit, écoute des missnotes, stabilité audio/CD ou nombre d’underruns n’est revendiquée pour ce build. La correction des popups et de l’animation reste à confirmer par un essai reproductible avec commandes effectivement reçues. Console réelle non testée.

Le parcours menus fidèle, Game Over/retry, résultats statistiques, écoute A/B des sons et leur validation par l’utilisateur restent les jalons suivants; cette passe ne les remplace pas.

## v26 — chaîne de rendu des jugements et cible QA déterministe

Le retour utilisateur v25c confirme les fautes rapprochées et les missnotes officielles; les jugements restaient invisibles. Le pipeline est maintenant instrumenté de l’événement de note au GPU : `game_update()` classe les hits avec les seuils existants (Sick ≤45 ms, Good ≤90 ms, Bad ≤135 ms, Shit au-delà, dans la fenêtre de hit de 160 ms), mémorise le résultat et sa différence temporelle, puis fixe la durée à 650 ms exprimés dans les échantillons de l’horloge musicale. Les fautes, ghost misses et drops de tenue utilisent le même compteur d’échantillons et la fréquence effective du flux pour leur fenêtre d’affichage; ils ne relisent plus une horloge séparée pour calculer l’expiration.

Le rendu écran est indépendant de la caméra et s’effectue après la scène et les notes. Les quatre illustrations officielles sont dans la page 4bpp no 9, UV `(0,104,64,24)` Sick, `(64,104,51,20)` Good, `(115,104,42,21)` Bad et `(157,104,46,26)` Shit, avec CLUT palette 7 en `(272,480)`; le tpage correspond à la page VRAM `(320,0)`. L’upload 4bpp, les UV et la CLUT sont partagés par le chemin QA et le chemin normal. Le compteur `judgement_drawn` indique la soumission de la primitive (il ne prouve pas à lui seul le résultat à l’écran). La capacité du tableau des primitives visuelles passe de 384 à 512 pour garder de la marge dans les scènes denses.

La cible `FUNKIN_PS1_JUDGEMENT_VISUAL_TEST_DEFAULT=ON` est séparée du jeu normal, sans flux audio ni planche superposée. Elle simule quatre appuis sur les notes du chart épinglé avec offsets de 0, 60, 110 et 150 ms, appelle le même `game_update()` que le jeu puis `draw_gameplay()` et présente Sick/Good/Bad/Shit en boucle, sans manette. Son horloge d’échantillons synthétique avance au quart de vitesse : la fenêtre demeure 650 ms musicaux, ce qui ouvre une fenêtre de capture de 2,6 s. Cette cible QA ne change pas la durée du mode jouable. Les options d’autoplay et de test visuel sont OFF dans l’image normale; diagnostics et planche de flèches restent masqués au démarrage.

### Résultats observés

| Étape | Résultat |
|---|---|
| Inspecté | Seuils de `game_update`, stockage et expiration de `last_judgement`, branche screen-space, atlas officiel, indices de page/UV/profondeur, CLUT et chargement des pages après les ressources menu. |
| Implémenté | Unités d’expiration unifiées sur l’échantillon audio courant et la fréquence du flux; diagnostic d’expiration et de soumission GPU; cible QA no-input raccordée au calcul de jugement; 512 primitives visuelles. Réactions aux fautes et sons officiels conservés. |
| Compilé | Cibles jouable et audio secondaire avec PSn00bSDK 0.24 / GCC MIPS 12.3 / CMake-Ninja. Image normale avec diagnostics, planche et tests automatiques désactivés : BIN `23 320 080` octets (9 915 secteurs MODE2/2352), CUE 93 octets; SHA-256 `B6157AE825BE82E4C6B3F617E95561DD4BFFE5351602EAC6DD26A04AA8B2D51`. |
| Exécuté | La cible QA no-audio a tourné dans DuckStation 0.1-8675 x64/D3D11 à 320×240, environ 60 IPS. Les illustrations officielles sont visibles; labels Sick/Good/Bad/Shit et `DRAW` suit la fenêtre de 650 ms audio simulée. Capture de Sick sous `outputs/FNF-PS1-v26g-judgement-hitpath-qa/`. L’image normale a démarré, montré Freeplay puis le gameplay sans texte QA ni planche; capture sous `outputs/FNF-PS1-v26-normal-judgements/`. |
| À vérifier | Le jugement déclenché par une manette pendant le flux audio normal n’a pas été capturé sans ambiguïté. La QA appelle le vrai `game_update()` mais remplace le flux par une horloge synthétique et des appuis programmés. Le jeu normal a été vu en gameplay, sans popup dans la fenêtre de capture. Reste à confirmer les quatre popups sur une partie jouée, puis tester le morceau entier, les transitions répétées et les compteurs CD/underrun. Aucun résultat console réelle ni mesure de dérive. |

BIN/CUE QA et normal sont livrés dans des dossiers distincts sous `outputs/`, hors du commit Git. Les menus fidèles, Game Over/retry et résultats restent les jalons suivants.


## v27 — couche finale des jugements et inversion des tenues

Inspection du chemin complet : le poll manette détecte un front d’appui (bits PAD actifs bas), transmet `game_pressed` à `game_update()`, qui résout le hit, met à jour `last_judgement` et `judgement_until`, puis efface l’événement d’entrée à la fin de la mise à jour. Le même `samples` d’`Stream_GetSamplesPlayed()` alimente cette mise à jour et le rendu; l’expiration est de 650 ms à la fréquence effective du flux. `reset_game_state()` est appelé à l’entrée/redémarrage du morceau, pas à chaque frame. Les seuils de hit et l’horloge restent inchangés.

L’écart concret entre QA et jeu normal était l’ordre des couches : la QA terminait avec la passe scène/notes et sa légende, alors que le jeu normal dessinait ensuite le fond et les textes du HUD. Le popup était donc soumis plus tôt dans le jeu normal. Cette différence rendait le QA insuffisant pour valider l’image finale; elle ne prouve pas que le HUD masquait effectivement le popup dans la partie. La soumission est déplacée dans une passe screen-space après le HUD principal; le diagnostic `Select` affiche désormais `HITS`, le dernier front directionnel, le jugement, l’écart en ms, le temps restant et si la primitive de cette frame est soumise. Il reste à confirmer dans une partie jouée que cet ordre était la cause visible.

Les corps et terminaisons des notes tenues utilisent désormais des UV inversés horizontalement et verticalement (rotation 180°), uniquement pour ces deux éléments. Flèches, récepteurs, timings et règles de tenue gardent leur chemin inchangé.

| Étape | Résultat |
|---|---|
| Inspecté | Entrée PAD active bas → `game_pressed` → hit/résultat → durée samples → passes GPU; constantes de build QA et normale; pages/CLUT déjà chargées avant la transition menu→jeu. Aucune remise à zéro du jugement par frame n’existe dans le chemin étudié. |
| Implémenté | Popup après le HUD principal; instrumentation accessible avec Select, masquée au lancement normal; rotation 180° UV des corps et terminaisons de tenues. |
| Compilé | Cibles jeu normal et probe audio quatre canaux avec PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja; la cible QA visuelle avec `FUNKIN_PS1_JUDGEMENT_VISUAL_TEST_DEFAULT=ON` compile également. QA non exécutée après le changement. BIN normal 23 322 432 octets, CUE 93 octets; flags diagnostics, planche flèches, QA jugement et démo scène tous OFF. Fichiers sous `outputs/FNF-PS1-v27-judgement-final-layer/`. |
| Exécution | Pas observée dans DuckStation pour ce build. La tentative de contrôle UI de l’émulateur a été bloquée par l’accès Parsec; aucun screenshot récent ne prouve la correction runtime. |
| À vérifier | Hit manette dans le build normal avec Select pour lire `HITS/J/LEFT/DRAW`, visibilité du popup après HUD, quatre directions, tenues tournées, stabilité audio et non-régression des fautes rapprochées/sons officiels. Pas de test console réelle. |

Le résultat précédent demeure : v26 QA a montré les quatre illustrations; cela ne vaut pas validation du hit manette. Le BIN v27 est jouable par configuration et conserve les diagnostics masqués, mais la correction visuelle du hit normal reste en attente de confirmation d’exécution. Les menus fidèles, Game Over/retry et résultats restent ultérieurs.


## v28 — échelle des jugements et capuchon des tenues

L’utilisateur confirme que le jugement est désormais visible dans le build v27 et valide le reste de cette version, sous réserve de deux ajustements visuels. Le popup Sick/Good/Bad/Shit est réduit de 18 % par rapport à la taille v27, reste centré et conserve sa durée pilotée par l’horloge audio. Les données et règles de jugement ne changent pas.

La terminaison officielle de chaque tenue est maintenant dessinée à son extrémité haute, avant le corps. Le corps recouvre le capuchon de 4 px pour cacher le raccord; le flip UV 180° des textures reste appliqué. Cette retouche n’affecte ni les flèches/récepteurs, ni le chart, ni la logique de maintien.

Le BIN/CUE v28 est compilé avec diagnostics et cibles QA masqués par défaut : [BIN](../outputs/FNF-PS1-v28-judgement-hold-cap/funkin-ps1-bopeebo-playable.bin) · [CUE](../outputs/FNF-PS1-v28-judgement-hold-cap/funkin-ps1-bopeebo-playable.cue). La modification de source est vérifiée et compilée; DuckStation n’a pas été relancé pour cette passe, donc taille/raccord des jugements et orientation nouvelle des tenues restent à confirmer visuellement par l’utilisateur. Aucun test console réelle.


## v29 — points affichés près du jugement

Le popup affiche maintenant le delta de score réellement appliqué lors du dernier événement : valeur positive sur un hit, valeur négative pour miss/ghost miss/drop de tenue. Pour une tenue, la valeur affichée au jugement est le score de la tête; les points accumulés pendant son maintien restent attribués comme auparavant. Le total, la table de score, les pénalités et l’horloge du popup ne sont pas modifiés. Le nombre signé apparaît à droite du jugement, sans panneau.

Build jouable normal PSn00bSDK 0.24 / GCC MIPS 12.3 : [BIN](../outputs/FNF-PS1-v29-judgement-points/funkin-ps1-bopeebo-playable.bin) · [CUE](../outputs/FNF-PS1-v29-judgement-points/funkin-ps1-bopeebo-playable.cue). BIN 23 322 432 octets, CUE 93 octets, SHA-256 `A9EF856C58A68D2481819543401308594D1B0C8FCFCBB99E88C5BC244F0928E3`. Diagnostics, QA et scène démo désactivés par défaut. Compilation réussie. Cette nouvelle image n’a pas encore été observée dans DuckStation; proximité/lisibilité du nombre restent à confirmer à l’écran, puis à ajuster si besoin. Pas de validation console réelle.


## v30 — compteur de combo et score VCR

Clarification utilisateur : l’élément demandé près des jugements est le compteur de combo, pas le delta de points de la note. Le delta ajouté en v29 est retiré. À partir de 10 réussites consécutives, le build normal affiche les chiffres officiels de combo (au moins trois chiffres, unité à droite), près des jugements; l’affichage suit la fenêtre musicale d’environ deux temps plus 200 ms et est recalculé aux changements de tempo. Lors d’une rupture d’un combo d’au moins 10, `000` apparaît brièvement, comme dans `PopUpStuff`/`PlayState` épinglés. Aucun score, seuil de jugement, santé, combo ou autre règle de jeu ne change.

Le mot `COMBO` est retiré de la barre de score. Le score total reste calculé comme avant et est rendu à droite, au niveau de la barre de vie, avec les glyphes de la police bitmap officielle VCR (`Score:`, chiffres, virgule et signe moins). Le convertisseur prélève les régions de glyphes depuis l’atlas officiel et les chiffres officiels de combo; les petites textures utilisent un redimensionnement nearest-neighbor net. Ces ressources réemploient la page et CLUT popup existantes : carte suivie inchangée à 9 pages 8bpp + 2 pages 4bpp, soit 655 360 octets de textures VRAM recensées (hors framebuffers et palettes comptabilisées dans la carte globale du projet).

Build normal PSn00bSDK 0.24 / GCC MIPS 12.3 compilé avec diagnostics/QA masqués. BIN/CUE : `outputs/FNF-PS1-v30-combo-score/`. BIN 23 324 784 octets; SHA-256 `552F20EC65D5D896CA785902D384FDAAB87B498655CEC6272C3B2B5D4C1AD921`; CUE 93 octets. Compilation vérifiée; aucun essai d’affichage de cette nouvelle image dans DuckStation, aucune validation utilisateur de v30 et aucun essai sur console réelle ne sont revendiqués.

## v31 — réserve de primitives pour score et jugements

Le retour sur v30 (« score et jugement invisibles ») est cohérent avec le partage du tableau de 512 primitives texturées : le chemin score v30 soumettait deux quads par glyphe, puis le jugement et le combo passaient dans le même helper qui refuse silencieusement les appels après la limite. Le code source confirme ce risque de budget et le mauvais point de défaillance; aucun compteur v30 n’a cependant mesuré qu’une frame utilisateur avait réellement atteint 512, donc la saturation de cette session n’est pas affirmée comme observation.

v31 augmente le tableau à 640 primitives, limite la passe scène/notes à 608 et réserve ainsi 32 soumissions aux couches finales. Le score dessine chaque glyphe VCR une seule fois au lieu d’ajouter un quad d’ombre par caractère. Les diagnostics Select exposent maintenant le nombre de primitives du monde, le high-water, les rejets, les glyphes score effectivement soumis et l’état de soumission du jugement. Ils restent masqués par défaut. Gameplay, positionnement et timing des jugements ne changent pas. La réserve ajoute 5 120 octets au tableau RAM (estimation directe de la différence d’allocation statique); carte VRAM inchangée.

Build v31 compilé avec PSn00bSDK 0.24 / GCC MIPS 12.3; BIN 23 324 784 octets, CUE 93 octets, SHA-256 BIN `D0EA4FF0F23041FC7CBAC5D31269D42913A6EC2D41433CF1D9477DD66E42426B`. Fichiers dans `outputs/FNF-PS1-v31-hud-primitive-reserve/`. Pas encore observé dans DuckStation : le retour runtime du score/jugement et les compteurs de primitive restent à vérifier sur cette image. Console réelle non testée.

## v32 — score visible et lecture correcte du diagnostic de jugement

Le retour v31 confirme que la réserve GPU n’a pas rétabli le score à l’écran. La capture de diagnostic montre `HUD GLYPHS 14`, donc les primitives VCR étaient soumises, mais leur rendu n’est pas visible dans l’image fournie. v32 remplace l’affichage du score par le chemin bitmap `FntPrint/FntFlush`, déjà utilisé par les diagnostics visibles, dans une zone à droite de la barre de vie. La police est celle fournie par PSn00bSDK; l’extraction officielle VCR reste dans le pipeline de conversion mais n’est plus utilisée pour le score normal. C’est un compromis de rendu, pas une validation de son apparence.

La même capture indique `J 4 LEFT 0` et un dernier delta d’environ 1010 ms. Le popup de jugement dure 650 ms musicaux; il avait donc expiré avant cette capture. Cela explique l’absence du jugement sur cette image précise et ne justifie pas d’allonger sa durée. Il reste à capturer un hit normal dans les 650 ms pour confirmer visuellement son affichage sur le build courant.

Build v32 normal compilé avec diagnostics masqués au démarrage : BIN 23 322 432 octets, CUE 93 octets, SHA-256 `6C421D812E3AAF99E3535B7939B88C31A493F6E4D6D00E90ABC55B63457F4C0B`. Fichiers dans `outputs/FNF-PS1-v32-score-font-fallback/`. Pas encore exécuté/observé dans DuckStation; l’affichage score v32, un jugement dans sa fenêtre active et la validation utilisateur restent à confirmer. Console réelle non testée.

## v33 — score sous la barre et mouvement des popups

L’utilisateur confirme par capture que le score SDK de v32 et un popup de jugement sont visibles dans le jeu normal. Il signale que le score mord légèrement sur la barre de vie. v33 déplace donc la zone de score à (208,37), sous le cadre de vie (y=19..35), et borne sa largeur à 96 px dans la marge CRT droite. La valeur, la police, le calcul du score et les jugements ne changent pas.

Les PNG officiels de jugement et les chiffres officiels combo de assets/preload/images/ui/popup/funkin/ sont des dessins individuels, pas des atlas d’images animées. Leur animation originale est définie par code dans source/funkin/play/components/PopUpStuff.hx : vélocité verticale, accélération, délai de fondu et tween d’alpha. v33 reproduit un flottement vertical déterministe, une entrée légèrement réduite qui atteint sa taille normale, et un fondu final par modulation de couleur jusqu’au noir. Les chiffres combo ont leur propre mouvement et fondu. Le temps écoulé vient des échantillons audio; aucune règle de hit/combo n’est changée. Compromis : le fondu GPU assombrit les pixels opaques jusqu’au noir au lieu d’animer un alpha continu; la fenêtre de vie Sick/Good/Bad/Shit reste les 650 ms déjà utilisées, même si le code original retarde le fondu d’une durée de beat puis 200 ms.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 réussie. Nouveau BIN/CUE dans outputs/FNF-PS1-v33-popup-motion-score-layout/; BIN 23 324 784 octets, CUE 93 octets, SHA-256 97A8C06BF8D6DDBC1E46BDB62D55446B819A5103082BFE1A92CE3E993346910E. Pas encore exécuté dans DuckStation : l’emplacement du score, le mouvement/fondu des popups et la stabilité du jeu après ce changement restent à observer. La capture utilisateur valide seulement le score et le popup de v32; aucune console réelle n’a été testée.

## v34 — popup de jugement à pleine intensité

Retour utilisateur : le placement du score v33 est approuvé, mais le popup de jugement n’est plus visible. Le fondu RGB de v33 atteignait le noir durant les 200 dernières ms; comme le popup reste limité à 650 ms, cette modulation pouvait le rendre trop difficile à percevoir. v34 supprime uniquement le fondu du jugement : l’image officielle garde sa modulation normale pendant toute la fenêtre existante, avec le mouvement vertical et la petite entrée en taille conservés. Score, durée, jugement, combo et gameplay ne changent pas. Le combo conserve son animation séparée.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 réussie. BIN/CUE distincts dans outputs/FNF-PS1-v34-judgement-visible/; BIN 23 324 784 octets, CUE 93 octets, SHA-256 0628E2D4445D262FDB4FEA146FE51EDFFCE0F3A85C68009128E13CC3FBA5864A. Non exécuté dans DuckStation après le correctif; la capture fournie n’indique pas l’événement de hit ni son âge musical. La visibilité après un hit réel reste à confirmer dans cette build. Pas de test console réelle.

## v35 — fenêtre de popup alignée au moteur

La capture de diagnostic fournie ne permet pas de conclure que le renderer a raté le popup : LEFT 0 signifie que la fenêtre était déjà expirée. Correction de lecture des diagnostics : DMS est l’écart du hit (timing delta), pas l’âge écoulé depuis le popup. La durée fixe de 650 ms utilisée jusque-là était également plus courte que le code original PopUpStuff, qui retarde son fondu d’un beat puis 200 ms. v35 calcule donc la fenêtre par tempo au moment de l’événement : 60 000 / BPM + 200 ms; à 100 BPM sur Bopeebo, cela donne 800 ms. Le popup reste à pleine modulation et conserve son mouvement/entrée en taille; la durée est un paramètre d’affichage uniquement. Le combo conserve sa propre durée de deux beats + 200 ms.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 réussie. BIN/CUE dans outputs/FNF-PS1-v35-original-popup-window/; BIN 23 324 784 octets, CUE 93 octets, SHA-256 CDE7F9412F5A5DD4895FA6C293A165B21227FB094D8AF71ACDDA5E67DB988E2E. Pas encore exécuté dans DuckStation : l’apparition du jugement dans la fenêtre active reste à vérifier. Pas de console réelle.

## v36 — popups au-dessus du panneau de diagnostic

La capture utilisateur montre le panneau de diagnostic opaque recouvrant le centre du jeu. Le popup Sick/Good/Bad/Shit était soumis avant le flush de la police de diagnostic : Select activé, celle-ci le dessinait donc au-dessus. v36 déplace le rendu des popups après le flush; aucun jugement ou règle de gameplay ne change. La durée reste celle de v35 (un beat + 200 ms).

Build PSn00bSDK 0.24 / GCC MIPS 12.3 compilé : BIN 23 324 784 octets, CUE 93 octets, SHA-256 BIN `DA81B623983AFDC279DD31B0685DBCD4F18B9A6CB761C899BAD0FD2D64AD6B96`, sous `outputs/FNF-PS1-v36-popup-over-diagnostics/`. Le build corrigé n’a pas encore été exécuté dans DuckStation; vérifier les hits avec diagnostics actifs et masqués. Pas de validation console réelle.

## v37 — rendu fixe du jugement restauré

Retour utilisateur : les captures v36 ne montrent toujours pas le popup; le changement de couche seul n’a pas résolu le problème. v37 retire la transformation animée du jugement et restaure le placement fixe et l’échelle v32, précédemment observés visibles. La fenêtre v35 reste fondée sur l’horloge audio (un beat + 200 ms; 800 ms à 100 BPM). La logique de jugement et de score ne change pas; le combo garde son animation séparée.

Build local PSn00bSDK 0.24 / GCC MIPS 12.3 : BIN 23 324 784 octets, CUE 93 octets, SHA-256 BIN `788F1E29875B762F38F76ADF705627E5FD7920FBFF72E0A802BB78798D45D313`, sous `outputs/FNF-PS1-v37-stable-judgement-display/`. Exécution DuckStation de v37 non vérifiée; pas de validation console réelle.
