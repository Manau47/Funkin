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

L’hypothèse initiale de saturation du tableau était erronée pour le run fourni. La capture v31 montre 253/640 primitives, WORLD 35, HIGH 55 et DROP 0 : la réserve de 32 n’était pas consommée. Elle montre également 14 glyphes VCR soumis sans rendu visible. La cause de l’absence du score est donc ailleurs; aucun diagnostic de palette/commande GPU ne l’a encore isolée.

v31 augmente le tableau à 640 primitives, limite la passe scène/notes à 608 et réserve ainsi 32 soumissions aux couches finales. Le score dessine chaque glyphe VCR une seule fois au lieu d’ajouter un quad d’ombre par caractère. Les diagnostics Select exposent maintenant le nombre de primitives du monde, le high-water, les rejets, les glyphes score effectivement soumis et l’état de soumission du jugement. Ils restent masqués par défaut. Gameplay, positionnement et timing des jugements ne changent pas. La réserve ajoute 5 120 octets au tableau RAM (estimation directe de la différence d’allocation statique); carte VRAM inchangée.

Build v31 compilé avec PSn00bSDK 0.24 / GCC MIPS 12.3; BIN 23 324 784 octets, CUE 93 octets, SHA-256 BIN `D0EA4FF0F23041FC7CBAC5D31269D42913A6EC2D41433CF1D9477DD66E42426B`. Fichiers dans `outputs/FNF-PS1-v31-hud-primitive-reserve/`. Pas encore observé dans DuckStation : le retour runtime du score/jugement et les compteurs de primitive restent à vérifier sur cette image. Console réelle non testée.

## v32 — score visible et lecture correcte du diagnostic de jugement

Le retour v31 confirme que la réserve GPU n’a pas rétabli le score à l’écran. La capture de diagnostic montre `HUD GLYPHS 14`, donc les primitives VCR étaient soumises, mais leur rendu n’est pas visible dans l’image fournie. v32 remplace l’affichage du score par le chemin bitmap `FntPrint/FntFlush`, déjà utilisé par les diagnostics visibles, dans une zone à droite de la barre de vie. La police est celle fournie par PSn00bSDK; l’extraction officielle VCR reste dans le pipeline de conversion mais n’est plus utilisée pour le score normal. C’est un compromis de rendu, pas une validation de son apparence.

La même capture indique `J 4 LEFT 0` et un dernier delta d’environ 1010 ms. Le popup de jugement dure 650 ms musicaux; il avait donc expiré avant cette capture. Cela explique l’absence du jugement sur cette image précise et ne justifie pas d’allonger sa durée. Il reste à capturer un hit normal dans les 650 ms pour confirmer visuellement son affichage sur le build courant.

Build v32 normal compilé avec diagnostics masqués au démarrage : BIN 23 322 432 octets, CUE 93 octets, SHA-256 `6C421D812E3AAF99E3535B7939B88C31A493F6E4D6D00E90ABC55B63457F4C0B`. Fichiers dans `outputs/FNF-PS1-v32-score-font-fallback/`. Pas encore exécuté/observé dans DuckStation; l’affichage score v32, un jugement dans sa fenêtre active et la validation utilisateur restent à confirmer. Console réelle non testée.

## v33 — score sous la barre et mouvement des popups

L’utilisateur confirme par capture que le score SDK de v32 et un popup de jugement sont visibles dans le jeu normal. Il signale que le score mord légèrement sur la barre de vie. v33 déplace donc la zone de score à `(208,37)`, sous le cadre de vie (`y=19..35`), et borne sa largeur à 96 px dans la marge CRT droite. La valeur, la police, le calcul du score et les jugements ne changent pas.

Les PNG officiels de jugement et les chiffres officiels combo de `assets/preload/images/ui/popup/funkin/` sont des dessins individuels, pas des atlas d’images animées. Leur animation originale est définie par code dans `source/funkin/play/components/PopUpStuff.hx`: vélocité verticale, accélération, délai de fondu et tween d’alpha. v33 reproduit un flottement vertical déterministe, une entrée légèrement réduite qui atteint sa taille normale, et un fondu final par modulation de couleur jusqu’au noir. Les chiffres combo ont leur propre mouvement et fondu. Le temps écoulé vient des échantillons audio; aucune règle de hit/combo n’est changée. Compromis : le fondu GPU assombrit les pixels opaques au lieu d’animer un alpha continu; la fenêtre de vie Sick/Good/Bad/Shit reste les 650 ms déjà utilisées, même si le code original retarde le fondu d’une durée de beat puis 200 ms.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 réussie. Nouveau BIN/CUE dans `outputs/FNF-PS1-v33-popup-motion-score-layout/`; BIN 23 324 784 octets, CUE 93 octets, SHA-256 `97A8C06BF8D6DDBC1E46BDB62D55446B819A5103082BFE1A92CE3E993346910E`. Pas encore exécuté dans DuckStation : l’emplacement du score, le mouvement/fondu des popups et la stabilité du jeu après ce changement restent à observer. La capture utilisateur valide seulement le score et le popup de v32; aucune console réelle n’a été testée.

## v34 — popup de jugement à pleine intensité

Retour utilisateur : le placement du score v33 est approuvé, mais le popup de jugement n’est plus visible. Le fondu RGB de v33 atteignait le noir durant les 200 dernières ms; comme le popup reste limité à 650 ms, cette modulation pouvait le rendre trop difficile à percevoir. v34 supprime uniquement le fondu du jugement : l’image officielle garde sa modulation normale pendant toute la fenêtre existante, avec le mouvement vertical et la petite entrée en taille conservés. Score, durée, jugement, combo et gameplay ne changent pas. Le combo conserve son animation séparée.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 réussie. BIN/CUE distincts dans `outputs/FNF-PS1-v34-judgement-visible/`; BIN 23 324 784 octets, CUE 93 octets, SHA-256 `0628E2D4445D262FDB4FEA146FE51EDFFCE0F3A85C68009128E13CC3FBA5864A`. Non exécuté dans DuckStation après le correctif; la capture fournie n’indique pas l’événement de hit ni son âge musical. La visibilité après un hit réel reste à confirmer dans cette build. Pas de test console réelle.

## v35 — fenêtre de popup alignée au moteur

La capture de diagnostic fournie ne permet pas de conclure que le renderer a raté le popup : `LEFT 0` signifie que la fenêtre était déjà expirée. Correction de lecture des diagnostics : `DMS` est l’écart du hit (timing delta), pas l’âge écoulé depuis le popup. La durée fixe de 650 ms utilisée jusque-là était également plus courte que le code original `PopUpStuff`, qui retarde son fondu d’un beat puis 200 ms. v35 calcule donc la fenêtre par tempo au moment de l’événement : `60 000 / BPM + 200 ms`; à 100 BPM sur Bopeebo, cela donne 800 ms. Le popup reste à pleine modulation et conserve son mouvement/entrée en taille; la durée est un paramètre d’affichage uniquement. Le combo conserve sa propre durée de deux beats + 200 ms.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 réussie. BIN/CUE dans `outputs/FNF-PS1-v35-original-popup-window/`; BIN 23 324 784 octets, CUE 93 octets, SHA-256 `CDE7F9412F5A5DD4895FA6C293A165B21227FB094D8AF71ACDDA5E67DB988E2E`. Pas encore exécuté dans DuckStation : l’apparition du jugement dans la fenêtre active reste à vérifier. Pas de console réelle.

## v36 — popups au-dessus du panneau de diagnostic

La nouvelle capture utilisateur montre que le panneau de diagnostic opaque recouvre presque toute la zone de jeu. Le rendu soumettait Sick/Good/Bad/Shit avant `FntFlush(diagnostics_font_id)`, donc le panneau était dessiné par-dessus les jugements lorsque Select activait les diagnostics. v36 conserve l’événement, la fenêtre de v35 et les règles de jugement, mais dessine les popups après le flush des diagnostics. Le panneau ne peut ainsi plus les masquer.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 réussie : BIN 23 324 784 octets, CUE 93 octets, SHA-256 BIN `DA81B623983AFDC279DD31B0685DBCD4F18B9A6CB761C899BAD0FD2D64AD6B96`. Fichiers dans `outputs/FNF-PS1-v36-popup-over-diagnostics/`. La capture qui a permis d’identifier le recouvrement n’est pas une preuve que le correctif v36 a été exécuté. Il reste à vérifier un hit dans DuckStation avec Select activé puis désactivé. Aucune validation console réelle.

## v37 — rendu fixe du jugement restauré

Retour utilisateur : les captures v36 ne montrent toujours pas le popup. Le correctif d’ordre des calques seul n’a donc pas résolu le problème. v37 retire la transformation animée propre au popup (mouvement/variation d’échelle) et revient au placement fixe et à l’échelle v32, auparavant observés visibles. La fenêtre audio v35 (un beat + 200 ms; 800 ms à 100 BPM) et les données de jugement restent inchangées. Le combo garde son animation séparée. Ce build doit encore être observé sur un hit réel; aucune validation n’est revendiquée.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 réussie : BIN 23 324 784 octets, CUE 93 octets, SHA-256 BIN `788F1E29875B762F38F76ADF705627E5FD7920FBFF72E0A802BB78798D45D313`. Le CUE v37 démarre dans DuckStation 0.1-8675 x64 et atteint l’écran titre; la fenêtre indique 60 IPS. La progression vers Bopeebo n’a pas été testée : aucune entrée Start utilisable n’était disponible dans cette session, donc le popup n’a pas été observé en jeu. Pas de validation console réelle.

## v38 — fenêtre de jugement étendue et diagnostic en millisecondes

Retour utilisateur : v37 n’affiche toujours pas de popup. La capture de diagnostic indique `J DRAW 0` à l’instant capturé; cette valeur était en outre retardée d’une image puisqu’elle était imprimée avant le rendu courant. Pour rendre le popup moins facile à manquer, v38 conserve l’image fixe v32 mais étend sa fenêtre d’affichage, uniquement visuelle, à deux beats + 200 ms (1,4 s à 100 BPM). La ligne `LEFT` du diagnostic est maintenant exprimée en millisecondes. Aucun score, jugement, timing, santé, SFX ou événement de gameplay ne change.

Build PSn00bSDK 0.24 / GCC MIPS 12.3 compilé : BIN 23 324 784 octets, CUE 93 octets, SHA-256 BIN `1515C1287F52FC0A36A06750745BF27261FC122445265316DFBB2BAB60A1030F`, dans `outputs/FNF-PS1-v38-longer-judgement-window/`. Exécution et visibilité en gameplay non vérifiées; test DuckStation requis. Aucun test console réelle.

## v39 — trace du popup sur le chemin de jeu normal

Le nouveau traçage confirme que `J DRAW` était lu avant l’appel de rendu de l’image courante; ce zéro ne permettait donc pas de conclure que la primitive avait échoué. La QA isolée et le jeu normal utilisent les mêmes pages d’assets (jugements sur la page 4bpp 9, CLUT popup dédiée) et le même helper GPU. L’écran normal appelle bien `game_update()` avant `draw_gameplay()` puis `draw_judgement_popup()`. La page popup est chargée par `load_bopeebo_visuals()` et n’est pas la page menu libérée à l’entrée du morceau. Ces vérifications éliminent le timer, la page menu et une absence évidente d’appel comme causes établies; elles ne prouvent toujours pas que le hit manette laisse l’état actif jusqu’au rendu, ni que DuckStation affiche la primitive.

v39 garde le mode jouable normal, masque les diagnostics au démarrage et remplace la métrique trompeuse par `J LAST a/s Fnn`: résultat mémorisé du dernier rendu de popup (`a` = tentative, `s` = primitive soumise), avec numéro de frame. Il s’agit d’un diagnostic de soumission GPU, pas d’une preuve de pixels visibles. La durée visuelle v38 est conservée pour ne pas changer plusieurs variables en même temps. Il faut capturer un hit manuel avec Select activé puis désactivé; interpréter `LEFT` (état actif) et `J LAST` ensemble. Aucun correctif visuel n’est déclaré avant cette observation.

Build v39 compilé avec PSn00bSDK 0.24 / GCC MIPS 12.3 : BIN 23 324 784 octets, CUE 93 octets, SHA-256 `F4F97A9301F656E7DD1C44EE0C98348B16DF22C932FD965A3DA2CB3A3B388CB6`, fichiers sous `outputs/FNF-PS1-v39-judgement-render-trace/`. Le démarrage et le hit manuel de cette image ne sont pas observés dans DuckStation. Aucun test console réelle.

## v40 — trace persistante du hit, sans correction de rendu

L’utilisateur rapporte que son essai rapide de v39 ne montre aucune différence fonctionnelle. Comparaison du code de la popup avec v32 (`0f597bd375a326867c0879d7fc5061316738b88b`) : même sélection des quatre frames officielles, même géométrie fixe (164 % des dimensions source, centrée à y=57), même helper texturé/tpage/CLUT et même ordre score → jugement → combo lorsque les diagnostics sont cachés. La durée du code courant est plus longue que celle de v32 (deux beats + 200 ms contre 650 ms); elle ne peut pas expliquer un popup absent par expiration trop courte. L’ordre autour du texte de diagnostic diffère uniquement quand Select est actif. Aucune différence responsable de l’absence en jeu normal n’est donc établie; ce jalon ne change ni le popup, ni le gameplay, ni sa durée.

Le build de diagnostic conserve le dernier hit réussi jusqu’au suivant et mémorise son jugement, son numéro de frame, ses échantillons musicaux, son expiration et la géométrie/atlas calculés. À chaque image pendant laquelle la popup est active, il mémorise aussi l’instant, le numéro de frame, la tentative de rendu et le retour de soumission du helper GPU. Select ouvre seulement cinq lignes transparentes de trace; la planche de flèches et les guides CRT restent absents de ce chemin et aucune entrée n’est automatisée. Le mode normal sans Select est inchangé.

BIN/CUE de diagnostic compilés avec PSn00bSDK 0.24 / GCC MIPS 12.3, dans `outputs/FNF-PS1-v40-hit-trace/`; BIN 23 324 784 octets, CUE 93 octets, SHA-256 `08277D82CD456CB0B32EA24E4D6922CE1204595FB38D10AE1B8FA83BC62E728E`. Compilation et génération de l’image réussies. Le processus DuckStation a été lancé, mais aucune fenêtre de l’émulateur n’est exposée au contrôle UI dans cette session; parcours menu → morceau et hit n’ont donc pas été observés. L’image v40 est une sonde de diagnostic, pas un correctif et n’a pas été poussée ni commitée. Pour le test, lancer le CUE, Start → Croix pour ouvrir Freeplay → Croix sur Bopeebo; jouer des notes manuellement, puis Select pour lire la trace persistante. Rester en Select ne désactive pas les commandes de jeu.

## v41 — isolation du chemin GPU du jugement

La vidéo utilisateur `2026-10-26 18-35-00.mkv` montre vers 35 s `SHIT ACTIVE`, tentative/commande envoyée et géométrie non vide, sans illustration clairement visible. Le code-source de v32 (`0f597bd375a326867c0879d7fc5061316738b88b`) confirme la même frame SHIT à `(122,57)`, `75×43`, UV `(157,104)`, dimensions source `46×26`. Le helper texturé de v32 et celui du build actuel sont identiques : `POLY_FT4`, modulation RGB `(128,128,128)`, tpage via `getTPage(0,0,320,0)`, CLUT `(272,480)`, puis `DrawPrim`.

La ressource convertie place SHIT sur la page logique 9; page VRAM `(320,0)`, frame `(u=157,v=104,w=46,h=26)`. Correction de la note précédente : la page logique 9 est chargée depuis `bopeebo_visual_pages4[0]` (les 9 pages 8bpp précèdent les pages 4bpp), pas `[1]`. Sa palette popup 7 occupe `(272,480)`. L’atlas de la bonne page contient 570 texels non transparents sur les 1 196 du rectangle SHIT; la CLUT contient 15 entrées non nulles, avec l’index 0 transparent. Le nombre 385 précédemment attribué au popup concernait une autre page et était erroné. Ces valeurs sont établies par les données converties, pas par lecture de la VRAM runtime.

La valeur `SUB1` de v40 ne prouve pas que des pixels sont visibles. Elle signifiait que le helper a accepté la primitive et appelé `DrawPrim`. La désassemblage PSn00bSDK 0.24 montre que `DrawPrim` attend la fin GPU précédente et lance une primitive via les registres DMA; il ne l’ajoute pas à une ordering table et ne retourne pas de preuve de visibilité écran. La frame vidéo montre en outre que le panneau Select v40, placé à y=49–89, se superpose à la zone du jugement y=57–100. Cette superposition n’existait pas dans la capture v32 validée avec diagnostics masqués et rend la frame v40 insuffisante pour isoler la texture.

La cible temporaire v41 remplace seulement le quad texturé du jugement par un rectangle jaune opaque aux mêmes `(x,y,w,h)` et au même point d’émission. La durée et les règles ne changent pas; aucune touche n’est injectée. Le panneau Select est descendu à y=104, sous la zone du popup. Dans cette cible probe, la première tentative lit aussi par `StoreImage` les 12 mots × 26 lignes correspondant aux 46×26 texels 4bpp et les 16 mots de CLUT; elle affiche le nombre de texels non transparents, la correspondance CLUT et le retour de `DrawSync`. Ce readback vérifie le contenu VRAM; seul le rectangle effectivement visible peut confirmer le résultat de sortie GPU. L’option CMake `FUNKIN_PS1_JUDGEMENT_SOLID_PROBE_DEFAULT` reste OFF par défaut.

BIN/CUE v41 compilés avec PSn00bSDK 0.24 / GCC MIPS 12.3 sous `outputs/FNF-PS1-v41-solid-judgement-probe/`; BIN 23 324 784 octets, CUE 97 octets, SHA-256 `AA3C33D5B8F4B47B1B8C8F43235DBD51694AA5550E8827DB4D066BA5AD2E1113`. La configuration CMake a ensuite été rétablie avec la sonde désactivée. DuckStation n’a pas exposé de fenêtre contrôlable; le test rectangle et le readback runtime n’ont donc pas été exécutés. Aucun correctif visuel n’est commité ou publié avant ce résultat; console réelle non testée.

### Retour et analyse du freeze v41

L’utilisateur rapporte que v41 se fige dès la première note. Le rectangle n’a donc pas été observé. Le readback était effectivement dans `draw_judgement_popup()` sur la frame du premier hit, avant le remplacement par le rectangle : deux `StoreImage()` suivis de `DrawSync(0)` dans le chemin critique de rendu.

Les paramètres statiques ne montrent pas de débordement : texture lue depuis `(x=359,y=104)`, `12×26` mots VRAM (312 mots 16 bits = 624 octets), dans un tampon `uint32_t[156]` aligné sur 4 octets; CLUT `(272,480)`, `16×1` mots (32 octets), dans `uint32_t[8]`. Ces rectangles restent dans la VRAM et les tampons sont assez grands. Le SDK PSn00b 0.24 implémente `StoreImage()` par une opération asynchrone de queue GPU; `DrawSync(0)` attend que la queue et le GPU soient au repos. L’appel intervient dans le frontend normal, après `game_update()` et pendant `draw_judgement_popup()`, pas dans une callback IRQ. Le freeze est donc corrélé à cette lecture/synchronisation bloquante au hit; le v41 ne permet pas de départager un blocage de `StoreImage()` d’une attente `DrawSync()` dans ce contexte. L’alignement et les dimensions ne sont pas la cause évidente.

## v42 — rectangle seul, sans lecture VRAM

La sonde v42 conserve la composition normale, les commandes manuelles et le rectangle jaune aux coordonnées du jugement, mais retire tous les appels `StoreImage()` et le `DrawSync()` ajouté pour leur lecture. Le panneau indique explicitement `PROBE SOLID RECT ONLY - VRAM READ OFF`. La première observation répondra seulement si le rectangle, émis par `DrawPrim()` au même endroit que le popup, est visible sans blocage. Une éventuelle sonde VRAM sera un jalon séparé, déclenché ultérieurement à un moment sûr hors du traitement du hit.

BIN/CUE v42 compilés avec PSn00bSDK 0.24 / GCC MIPS 12.3, dans `outputs/FNF-PS1-v42-solid-rect-only/`; BIN 23 324 784 octets, CUE 91 octets, SHA-256 `E1299FB3EC99756164D641A21E65854A91BA21DB5C22991F2D7241A53DD15082`. Retour utilisateur après exécution : le rectangle apparaît après les hits, Select activé ou masqué, et le jeu continue après la première note. C’est une validation utilisateur du rectangle F4, pas du rendu texturé du jugement. CMake est restauré avec la sonde de rectangle désactivée par défaut. Aucun changement aux règles de gameplay ou au placement du score validé; le popup n’est pas déclaré corrigé. Pas de test console réelle.

## v43 — primitive FT4 de référence, sans readback VRAM

Retour utilisateur sur v42 : le rectangle jaune apparaît après les hits, avec Select affiché ou masqué, et le jeu continue après la première note. Cela confirme l’emplacement écran et le chemin de commande F4 dans le flux normal. Cela ne teste pas le fetch texture/CLUT. Aucun changement n’est apporté au jugement, à sa durée, au gameplay ou au placement du score.

Comparaison du code : la sonde v42 initialise un `POLY_F4` via `setPolyF4`, renseigne RGB/XY/WH, puis appelle `DrawPrim`. Le jugement utilise `POLY_FT4` via `setPolyFT4`, modulation RGB `128/128/128`, quatre XY, UV inclusifs `u..u+w-1` et `v..v+h-1`, `tpage=getTPage(depth,0,pageX,pageY)`, CLUT issue de la palette de la frame, puis le même `DrawPrim`. Les deux sont soumis immédiatement au GPU depuis `draw_judgement_popup()`; aucun tableau de primitives de jeu n’est présenté comme une confirmation d’exécution GPU. Le helper FT4 retourne vrai après validation des limites et appel `DrawPrim`, ce qui ne prouve pas à lui seul que les texels ont été visibles. La comparaison v32 reprise ici vient de l’analyse consignée en v40/v41 (helper FT4, géométrie et état visuel identiques); l’objet du commit v32 n’est pas présent dans la base Git locale actuelle, donc ce jalon ne prétend pas refaire un `git diff` de cette révision.

Pour isoler le chemin texturé en jeu normal, v43 conserve menu, chart, entrées manuelles, emplacement `(122,57)` pour le cas SHIT, dimensions d’affichage `75×43`, durée et ordre de dessin. Pendant la fenêtre d’un jugement, elle affiche à cet emplacement l’image connue `VIS_BF_MISS_LEFT_0` étirée au même rectangle, via le même helper FT4; le jugement calculé reste dans la trace. Cette image est page logique 9, profondeur 4bpp, VRAM `(320,0)`, UV `(0,0,52,52)`, palette 1 / CLUT `(256,496)`. Elle partage donc la page chargée avec SHIT, mais change UV et CLUT : si elle apparaît, le chemin FT4/page/CLUT fonctionne et l’écart restant est propre aux données ou paramètres de la frame de jugement; si elle n’apparaît pas alors que v42 affiche son F4, l’investigation reste sur le chemin texturé/état GPU.

La lecture VRAM et `StoreImage` sont absents; le freeze v41 ne doit pas être reproduit par cette sonde. Le panneau Select affiche les métadonnées du frame FT4 de référence et reste sous la zone du popup. L’option de sonde est une configuration de diagnostic dédiée; elle n’est pas activée par défaut dans la cible normale. Les tests de traces statiques corrigent l’index page4 expliqué ci-dessus. La cible a été compilée avec `FUNKIN_PS1_JUDGEMENT_TEXTURE_PROBE_DEFAULT=ON`, sonde rectangle OFF.

Build propre PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja dans `C:\Users\Manau47\Documents\Codex\ps1-build-v43` : génération des données et compilation/link réussis, puis ISO BIN/CUE générée (23 324 784 octets, 9 917 secteurs; CUE 97 octets). Deux avertissements de qualification `volatile` proviennent de `stream.c` du SDK et ne bloquent pas le build. SHA-256 BIN `8E49534CD996405983F5E43A8BB244BEF191FF28DB9E49E368D681D765BD0016`, livrée dans `outputs/FNF-PS1-v43-ft4-known-frame-probe/`. Retour utilisateur avec captures : l’image BF de sonde apparaît dans le parcours normal, Select masqué puis visible, avec `SHIT ACTIVE` et la trace FT4. Cela confirme que le chemin texturé peut afficher la page logique 9 et la CLUT BF connue; l’apparence étirée de l’image dans le rectangle de jugement est uniquement la sonde. Le popup lui-même n’est pas validé. Console réelle non testée.

## v44 — UV du jugement avec CLUT BF connue

La sonde FT4 v43 est apparue en jeu normal. Le prochain essai garde le frame et les UV du résultat réel (Sick/Good/Bad/Shit), mais force uniquement la CLUT connue de v43 `(256,496)` au lieu de la CLUT popup 7 `(272,480)`. Position, échelle, primitive FT4, durée, règles, score, audio et commandes restent inchangés; Select reste facultatif et aucune planche/autocommande/readback VRAM n’est ajoutée.

Interprétation prévue : si le dessin du jugement apparaît avec la CLUT BF, ses UV et texels sont exploitables et la CLUT popup devient la différence principale; s’il reste absent, l’écart n’est pas limité à la CLUT 7 et il faudra examiner les UV/source/paramètres propres au frame. Ce résultat doit être observé avant toute correction ou réintroduction des animations.

Build PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja : compilation/link et génération BIN/CUE réussies (23 324 784 octets, 9 917 secteurs). Deux avertissements non bloquants sur le qualificatif `volatile` dans `stream.c` du SDK. BIN SHA-256 `4B8E38A0640700B60B29BBE72CDDF164BA6BAC63C94CDC53048CC99859BEC101`, fichier `outputs/FNF-PS1-v44-judgement-uv-bfclut-probe/`. Retour utilisateur avec captures : le jugement apparaît avec des couleurs différentes quand la CLUT BF remplace la CLUT popup. Cela valide les UV/texels du jugement et la voie FT4; la palette popup ou son chargement devient la différence à isoler. La capture ne valide pas la palette d’origine ni le popup final. Pas de test console réelle.

## v45 — UV connus avec CLUT popup

Retour utilisateur sur v44 : le jugement reste visible avec la CLUT BF connue mais affiche des couleurs différentes. v45 garde les texels/UV BF MISS LEFT qui sont apparus en v43, et ne change que la CLUT pour la CLUT popup `(272,480)`. La trace attendue est `PG9 D4 VRAM320,0 UV0,0 52x52 CL272,480`. Aucun readback VRAM, aucune modification de santé, jugement, combo, score, timing ou audio.

Interprétation : si le frame BF apparaît sous cette CLUT, le fetch et l’adresse de CLUT popup fonctionnent; ses entrées/quantification restent suspectes pour le graphisme popup. Si le frame disparaît, le problème est dans l’adresse, le contenu uploadé ou l’état GPU associé à cette CLUT. Ce test croisé complète v44 avant de toucher au rendu normal.

Build PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja : compilation/link et génération BIN/CUE réussies (23 324 784 octets, 9 917 secteurs); avertissements SDK `volatile` non bloquants. BIN SHA-256 `4A8B3E91912E64D84B56F31672D7379AE51895EB6F66ABFDA324D8688A328D0C`, fichiers sous `outputs/FNF-PS1-v45-known-uv-popup-clut-probe/`. Retour utilisateur : le frame BF connu disparaît sous la CLUT popup. Croisé avec v44 (jugement visible sous CLUT BF), cela réduit le défaut au chargement/adressage ou au contenu de cette CLUT; v45 seule ne distingue pas encore les deux. Aucune correction déclarée. Console réelle non testée.

## v46 — palette popup relocalisée à l’adresse BF connue

Le dernier probe conserve les texels/UV du jugement et la palette popup générée, mais charge ces mêmes 16 couleurs à `(256,496)`, adresse de CLUT BF déjà observée fonctionnelle, puis la sélectionne dans le FT4. Cette passe change uniquement la résidence/adresse GPU de la palette; dans cette image de test, elle remplace la CLUT BF des poses de faute. La trace doit afficher le jugement actif, ses UV d’origine et `CL256,496`.

Si le jugement apparaît, les valeurs générées de la palette popup sont utilisables et l’adresse/upload original `(272,480)` est impliqué. S’il reste absent, le contenu ou l’indexation/quantification de la palette devient la cause la plus probable. Aucun readback VRAM, aucune modification de gameplay, des règles, du score, du timing ou de l’audio.

Build PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja : compilation/link et image BIN/CUE réussies (23 324 784 octets, 9 917 secteurs); avertissements SDK `volatile` non bloquants. BIN SHA-256 `572E8F93A5FFB1F6A0E6ACF698BA8732962F7F98C43B36A05F4A1B8ED6ED17E7`, fichiers dans `outputs/FNF-PS1-v46-popup-palette-relocated-probe/`. Retour utilisateur avec captures : le jugement réel apparaît lorsque palette et CLUT sont déplacées à `(256,496)`. Cela valide les données/indices de palette popup; le défaut est attribuable à la résidence/adresse originale `(272,480)` ou à son interaction GPU. Aucune correction normal publiée. Console réelle non testée.

## v47 — CLUT popup dans le slot libre `(288,480)`

La v46 confirme que les couleurs extraites sont utilisables lorsqu’elles sont chargées à `(256,496)`, mais cet emplacement est occupé en jeu normal par la CLUT des poses de faute BF. v47 reprend le jugement réel et sa palette popup inchangée dans le slot adjacent libre `(288,480)`, avec les poses BF gardées à leur CLUT existante. Seuls l’adresse de chargement et le CLUT référencé par le FT4 changent. Select doit indiquer la CLUT `(288,480)`; aucune lecture VRAM n’est faite.

Si le popup apparaît, ce slot permet un correctif ciblé qui préserve les couleurs BF. S’il n’apparaît pas, la v46 `(256,496)` reste le seul placement runtime confirmé, et il faudra déplacer séparément la palette BF avant de pouvoir le garder sans conflit. Ce probe n’est pas encore observé en émulateur.

Build PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja : compilation/link et image BIN/CUE réussies (23 324 784 octets, 9 917 secteurs); avertissements SDK `volatile` non bloquants. BIN SHA-256 `0877679B592BF49AD37DBB0E4AB70D440EC8CDA593556461D21913F2B7F05DFE`, fichiers dans `outputs/FNF-PS1-v47-popup-clut-free-slot-probe/`. Retour utilisateur : le popup reste visible au slot libre `(288,480)`. Avec v45 absent à `(272,480)` et v46 visible à `(256,496)`, l’échec est isolé au slot original, malgré l’absence de chevauchement statique détectée dans la carte VRAM. Pas de validation console réelle.

## v48 — correction normale du slot CLUT popup

Le rendu de jugement standard charge maintenant la palette popup à `(288,480)` et `set_visual_clut()` sélectionne le même slot. Le convertisseur vérifie désormais ce rectangle dans la carte VRAM complète : il est adjacent aux palettes existantes, sans chevauchement avec la framebuffer, les pages texture ou les autres CLUT. La palette des fautes BF reste à `(256,496)`. Les probes, planche de flèches, diagnostics de démarrage et guides CRT sont tous OFF. Le popup reste fixe comme pendant les essais v47; ses animations ne sont pas encore réintroduites pour ne pas ajouter un changement simultané.

Build normal PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja : conversion VRAM, compilation/link et génération BIN/CUE réussies; image 23 324 784 octets, 9 917 secteurs, SHA-256 `7F08A6777808EFD240B936130E89487DF8F47562C8C9428AEE7EF89E4FFD7C68`, sous `outputs/FNF-PS1-v48-popup-clut-slot-fix/`. Avertissements non bloquants du `stream.c` SDK sur le qualificatif `volatile`. Retour utilisateur : v48 n’affiche aucun popup. Le test v47 ne suffit donc pas à valider la voie normale; sa voie de primitive forçait `setClut` et effectuait une seconde `LoadImage` sur le slot popup. La cause se situe encore entre la sélection effective de CLUT et la résidence/charge GPU, et v48 n’est pas validée. Audio, gameplay, score, règles et placement restent inchangés; aucune validation console réelle.

## v49 — voie normale avec CLUT explicite

v49 conserve le slot popup unique `(288,480)` et son chargement une seule fois, comme v48. La primitive de jugement appelle maintenant le même `draw_textured_frame_with_clut(...,288,480)` explicite que la sonde v47, sans remplacer l’image du jugement, sans double chargement, et sans panneau QA au démarrage. Cela isole le sélecteur CLUT générique de la primitive FT4. Si le popup apparaît, la sélection via `set_visual_clut()` est en cause; si non, il faut rechercher la différence de chargement/résidence ou d’ordre dans le flux normal.

Build normal PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja : compilation/link et BIN/CUE réussis (23 324 784 octets, 9 917 secteurs), SHA-256 `96C6F94B028EE421E83E385C1B64DDC4574B365B0B9A7B968F4657E5C1260BD1`, sous `outputs/FNF-PS1-v49-explicit-popup-clut/`. Diagnostics et remplacement visuel sont OFF par défaut. Compilation confirmée, exécution DuckStation encore requise; ni popup ni animations ne sont déclarés corrigés par ce build. Pas de test console réelle.

Retour utilisateur sur v49 : toujours aucun popup malgré le `setClut(288,480)` explicite. Inspection du contrat PSn00bSDK 0.24 (`doc/drawing_queue.md`) : `LoadImage()` enqueue une DrawOp asynchrone et la file GPU ne contient que 16 opérations. `load_bopeebo_visuals()` soumettait 18 transferts avant son seul `DrawSync()` : 8 pages 8bpp gameplay (la page menu étant exclue), 2 pages 4bpp, puis 8 palettes. La CLUT popup était le 18e transfert. Les retours visuels (v47 double chargement visible, v48/v49 single chargement invisible) concordent avec la file saturée et une palette pas résidente; l’adresse seule et le setter seul ne suffisent pas. Il s’agit de la cause concrète identifiée; v50 ajoute des barrières entre groupes de transferts.

## v50 — synchronisation des transferts VRAM

Le chargeur purge d’abord la file GPU, soumet 10 pages de textures, attend la fin avec `DrawSync(0)`, puis soumet 8 palettes et attend de nouveau. La file reste donc sous la limite SDK de 16. Le popup conserve le CLUT `(288,480)`; le rendu reprend le sélecteur normal `set_visual_clut()`. Tous les probes et diagnostics de démarrage sont désactivés. Cette correction teste en jeu normal la résidence réelle de la palette.

Build PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja : compilation/link et génération BIN/CUE réussies, 23 324 784 octets / 9 917 secteurs, SHA-256 `BD728D80BA3FE4B1A8DF2A8AB75D552C29BB0E24B3716E635F5B86357304B614`, dans `outputs/FNF-PS1-v50-gpu-upload-queue-fix/`. L’utilisateur a ensuite confirmé que le popup est revenu dans v50 en jeu normal. Pas de validation console réelle; règles du jeu, timing et audio inchangés.

## v51 — mouvement audio-clock des jugements

Le popup conserve son asset officiel, sa taille et son point de départ visibles en v50. Il flotte maintenant selon une trajectoire verticale balistique pilotée par les échantillons audio; une variation déterministe entre jugements rend le mouvement reproductible. Le déplacement horizontal reste léger. Les coordonnées restent bornées à l’écran. La fenêtre v50 (deux beats plus 200 ms) et le remplacement du popup au prochain événement restent inchangés. Aucun hit, pénalité, fenêtre de jugement, score, santé ou mix audio n’est modifié.

La référence officielle `source/funkin/play/components/PopUpStuff.hx` anime les jugements avec une vitesse verticale aléatoire, une accélération gravitationnelle, une faible dérive horizontale et un fondu alpha après un beat. Le port reprend le flottement et la dérive, avec paramètres réduits pour la résolution PS1. Le fondu alpha Flixel n’est pas reproduit dans cette passe afin de préserver la lisibilité à pleine modulation; la durée de deux beats + 200 ms est conservée pour permettre l’observation, même si le jeu source amorce son fondu après un beat. Les combos gardent leur animation séparée.

Build PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja compilé et image disque générée : BIN 23 334 192 octets, CUE 97 octets, SHA-256 BIN `272533E70C1F6207AFA30BF2AFC4C256B83E8399A77956F6CAA2FB73E6F03856`, fichiers dans `outputs/FNF-PS1-v51-animated-judgements/`. Diagnostics, test QA, planche de flèches, scène démo et guides CRT sont OFF au démarrage. L’utilisateur a confirmé que les popups animés sont visibles dans v51. Aucun test console réelle. L’essai suivant vérifie la taille et le mouvement coordonné de v52.

## v52 — taille réduite et mouvement partagé des popups

La vidéo utilisateur `2026-10-27 16-02-14.mkv` a été examinée à partir de 56 s. Le jugement passe de 164 % à 131 % de sa taille source (réduction d’environ 20 % une fois l’entrée terminée). La taille des chiffres du combo n’a pas changé. Une fonction de mouvement commune applique maintenant au jugement et au combo la même trajectoire verticale audio-clock et la même entrée d’échelle de 100 ms; leurs positions d’ancrage et leurs durées restent séparées. La dérive horizontale propre au jugement a été retirée. Aucun changement de gameplay, de santé, de score, de timing, de palette ou d’audio.

Build PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja : compilation/link et BIN/CUE réussis, BIN 23 334 192 octets, CUE 95 octets, SHA-256 BIN `02A52D5D4E44A4874AA405E23C875903CE2E374B0A6DE49B0DFE81748C380125`, dans `outputs/FNF-PS1-v52-matched-popup-motion/`. Diagnostics et planches restent masqués au démarrage. Compilation confirmée; v52 n’a pas encore été exécutée ou validée visuellement. La validation utilisateur précédente porte sur la visibilité et les animations de v51. Aucun test console réelle. À vérifier dans DuckStation : lisibilité du jugement réduit et trajectoire commune avec le combo à partir de 10 hits consécutifs.

## Validation v52 et audit menus / fin de partie

L’utilisateur confirme maintenant v52 dans DuckStation : les popups de jugement et de combo sont visibles, animés et à la taille souhaitée. Il identifie le chargement des palettes VRAM comme cause de leur disparition et demande de conserver les synchronisations ajoutées au chargeur. Les `DrawSync(0)` entre chargement des pages et chargement des CLUT sont conservés. Cette validation utilisateur ne mesure pas la dérive audio et ne couvre pas la console réelle.

Lecture du code de la révision épinglée : `TitleState.hx` utilise le logo animé, la danse de GF, le rythme et `FreakyMenu`; `MainMenuState.hx` présente Story Mode, Freeplay, options et crédits avec navigation, sélection et sons. La référence fournie montre aussi cette composition et ses transitions. Pour le port, seuls les parcours réellement implémentés sont actifs : titre, menu principal puis Freeplay avec Bopeebo Normal. Les autres morceaux/difficultés restent absents du catalogue jouable.

La base PS1 précédente avait déjà ce parcours côté état et boutons, ainsi que la musique FreakyMenu en VAGi quatre canaux et les sons officiels scroll/confirm/cancel chargés en SPU. Son rendu restait une maquette textuelle : une seule entrée Freeplay, arrière-plans convertis et danse de GF; pas encore de sélection de catalogue complète ni d’écran d’options/crédits. Les trois compositions 256×192 sont quantifiées dans le jeu de couleurs partagé et chargées l’une à la fois dans la page menu déjà réservée. Carte VRAM inchangée (9 pages 8bpp, 2 pages 4bpp, framebuffers et CLUT compris). Le menu occupe 192 KiB supplémentaires de données constantes en RAM principale (3 pages × 64 KiB); l’ELF map place la fin des données statiques/BSS vers `0x80110220`, soit environ 1.06 MiB depuis le début d’exécution `0x80010000`, avant allocations dynamiques et pile. Le BIN/CUE reste chargé depuis le CD; les ressources graphiques officielles et les fichiers de conversion ne sont pas ajoutés au dépôt.

`GameOverSubState.hx` contient la séquence officielle BF `firstDeath` → `deathLoop`, l’attente avant acceptation des commandes, les musiques `gameOverStart`/`gameOver`, `fnf_loss_sfx`, puis l’animation `deathConfirm` et `gameOverEnd`; Croix relance, Rond revient. Les sources locales contiennent aussi les rigs BF death et les fichiers audio officiels. Le port courant n’a pas encore d’état Game Over : la santé à zéro renvoie immédiatement en Freeplay, comme une fin de morceau. Il faut séparer ces raisons de sortie avant d’ajouter retry, charger l’animation BF depuis les ressources de scène, ajouter l’audio correspondant et vérifier le stop/restart du flux CD/SPU.

`PlayState.hx`, `Scoring.hx` et `ResultState.hx` montrent que les résultats utilisent le vrai tally (Sick/Good/Bad/Shit, ratés, notes totales, combo maximal, score) et calculent un rang; l’écran anime ensuite BF, les classements et lance la musique selon le rang. Le port garde score, combo courant, ratés et hits, mais ne mémorise pas encore les compteurs par jugement, le combo maximal ni un bilan de réussite. Le résultat du morceau ne doit donc pas être simulé. La prochaine étape devra ajouter ces compteurs à la logique existante, les réinitialiser au retry, calculer seulement les statistiques/rangs dont les règles source sont portées et présenter explicitement les écarts.

## v53-v54 — premier parcours visuel de menus

v53 ajoute les arrière-plans officiels `menuBG`/`freeplayBGweek1-bf`, le logo, la danse de GF et le bouton Freeplay officiel; la musique et les sons de navigation restent sur le chemin existant. Les menus et le gameplay n’occupent pas simultanément leur page de textures. Le titre v53 a été observé dans DuckStation à 320×240 et environ 59–60 IPS; une capture ultérieure montre l’écran Freeplay. La navigation complète jusqu’au jeu, le son menu, le chargement du morceau et le retour ne sont pas établis par ces observations.

v54 extrait les trois images officielles de l’animation `freeplay selected` et les fait défiler au menu principal sur la page menu déjà chargée. L’écran Freeplay ne réutilise plus le grand mot-symbole Freeplay comme titre de chanson; il affiche `BOPEEBO / NORMAL` et les commandes. Aucun contenu supplémentaire n’est activé. Cette version compile avec PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja et génère un BIN de 23 559 984 octets (10 017 secteurs), CUE de 91 octets, SHA-256 `56A2E494E242E964BCB484267A144FB500C2CA80466DBF4F603F9C771D3DA161`, dans `outputs/FNF-PS1-v54-menu-freeplay/`. Les diagnostics restent masqués au démarrage. v54 n’a pas été chargée dans DuckStation dans cette passe; elle n’est pas déclarée testée ni validée. Aucun essai console réelle.

## v55 — menus rapprochés de la référence et premier Game Over

Cette passe répond aux retours que le menu v54 était trop éloigné de la source et qu’aucun écran de mort n’existait. Le menu principal utilise le fond jaune officiel et les quatre animations de libellés officielles Story Mode, Freeplay, Merch et Credits; seule l’entrée Freeplay conduit à un écran actif. La sélection Freeplay reprend ses trois poses officielles animées. Le titre conserve le logo, GF animée, FreakyMenu et les sons officiels de navigation. Freeplay est recomposé en bande jaune sur panneau noir, avec des poses officielles BF/Dad/GF détourées, Week 1, Bopeebo/Normal et commandes. Cette scène s’inspire de la composition vidéo 4:3 sans importer d’assets d’une autre révision. Les textures sont préchargées dans les pages menu existantes, puis réutilisées; aucun groupe de textures menu ne reste chargé avec le gameplay.

À santé nulle, le jeu entre maintenant dans un état Game Over séparé de la fin normale du morceau. La scène noire affiche 22 poses échantillonnées depuis le rig officiel BF Death (intro, boucle et confirmation), en conservant son ancrage commun. Elle joue `fnf_loss_sfx`, puis `gameOver.ogg` après l’intro; Croix lance `gameOverEnd.ogg`, l’animation de confirmation et un compte 3–2–1 avant de repartir du début; Rond revient en Freeplay. Le catalogue reste limité à Bopeebo Normal. Les fichiers `gameOverStart.ogg` et les sons/images officiels du compte initial ne sont pas présents au chemin attendu dans cette révision locale : le compte 3–2–1 est donc une adaptation textuelle provisoire. La fin normale du morceau revient encore au Freeplay; l’écran de résultats, les rangs et statistiques restent à faire.

Les trois écrans utilisent la page VRAM menu existante et ses mêmes coordonnées; aucune page ni CLUT supplémentaire n’est ajoutée. Les poses Game Over occupent 22 × 80 × 96 = 168 960 octets de données ROM/RAM statiques, en plus des trois images menu (192 KiB) et des trois images d’animation Freeplay (13 824 octets); la page Game Over remplace le menu à l’exécution. La carte VRAM reste 9 pages 8bpp + 2 pages 4bpp (640 KiB), framebuffers 300 KiB et CLUT/font dans les zones déjà vérifiées. L’image exécutable fait 1 251 328 octets; `size` rapporte 1 245 076 octets text, 2 310 data et 38 764 BSS (1 286 150 octets cumulés). Sur 2 MiB de RAM, cela laisse environ 792 KiB avant l’allocation runtime de 96 KiB du tampon CD; environ 696 KiB restent ensuite pour pile et autres besoins dynamiques. C’est une estimation basée sur les sections ELF, pas un relevé de l’allocation pendant l’exécution.

Audio : les flux musique menu, morceau et Game Over sont lus l’un après l’autre par le même flux CD/SPU à 43 008 Hz; aucune musique ne reste active en parallèle. Le tampon CD principal reste 96 KiB. Le tampon SPU VAGi à 4 canaux occupe 32 KiB à partir de `0x1010` (interleave 4 096 × 4 canaux × 2); le bank résident de sons menu, fautes et perte occupe 139 008 octets de `0x22000` à `0x43F00`. Les voix 0–3 sont pour la musique, 4–7 pour SFX de jeu, 8–10 pour menu et 11 pour le son de perte; 12–23 restent disponibles. Le débit CD et l’absence d’underrun durant les changements d’écran ne sont pas encore observés sur cette version.

Le build a été compilé et l’image disque générée avec PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja. BIN 29 011 920 octets, 12 335 secteurs; CUE 93 octets; SHA-256 BIN `E32183E5B53ADD5159DDD5F2EE1CEBAF685AE5E95C5FECBCEE16DEC78CB95871`. Les diagnostics de flèches, journaux et guides CRT sont désactivés par défaut. L’image n’a pas été exécutée dans DuckStation dans cette passe : ni le rendu runtime, ni la musique, ni le parcours de mort/retry ne sont déclarés validés. Aucun test console réelle. Le BIN/CUE est fourni dans `outputs/FNF-PS1-v55-menu-gameover/` pour que l’utilisateur le charge manuellement; l’interaction avec DuckStation attend sa confirmation.

### Étapes après l’essai utilisateur

1. L’utilisateur charge le CUE v55 et confirme que DuckStation l’a ouvert. Ensuite seulement, poursuivre l’essai ensemble au clavier visuel : titre → menu principal → Freeplay → Bopeebo, puis provoquer Game Over, attendre, vérifier Croix retry avec reset/count-in et Rond retour Freeplay. Refaire les transitions pour surveiller audio/CD et corruption de textures.
2. Corriger tout écart visuel ou de commandes à partir de l’observation réelle, sans confondre compilation et validation utilisateur.
3. Construire l’écran résultats en mémorisant les vrais jugements, ratés, score et combo maximal pendant la partie; n’afficher aucun résultat de réussite après Game Over.
4. Continuer la réconciliation distante avant commit/push : `git fetch origin ps1-port` échoue actuellement avec `SEC_E_NO_CREDENTIALS`; l’historique distant de la PR #1 est en avance et structurellement divergent. Aucun commit en doublon, push ou fusion n’a été fait.

## v56 — correction du cadrage des menus

Retour utilisateur sur v55 : le parcours semblait s’arrêter à Freeplay; le titre était à retravailler, le fond du menu principal paraissait étiré, Freeplay reprenait une disposition de Story Mode et Game Over restait une base provisoire. Cette passe ne modifie aucune logique de navigation, de gameplay ni d’audio.

- Le menu principal garde sa composition à quatre entrées, mais `menuBG.png` est maintenant cadré par recadrage central (« cover ») au ratio 4:3 au lieu d’être déformé.
- Le titre repart d’un fond sombre, avec le logo officiel à sa proportion source, GF en danse officielle au premier plan et l’invite `PRESS START TO BEGIN`.
- Freeplay possède son propre fond officiel de la semaine 1. L’image complète est contenue dans le cadre 4:3 sans étirement, avec bandes sombres discrètes en haut/bas; une capsule officielle sélectionnée, le badge officiel Normal, `BOPEEBO` et la commande de lancement identifient la sélection de chanson. Bopeebo Normal reste le seul choix actif.
- Game Over conserve les phases et contrôles déjà en place, mais l’animation officielle BF death est agrandie de 80×96 à 118×142 pixels d’écran pour mieux occuper le cadre. Les transitions, le retry et le retour Freeplay ne changent pas.

Les compositions restent trois bitmaps 256×192 chargés tour à tour dans la page menu existante : aucun changement de carte VRAM, de nombre de CLUT, de pages chargées simultanément ou de budget SPU. Les trois bitmaps sont toujours 192 KiB de données statiques; les animations BF death gardent leur stockage existant. Le résultat `size` du nouvel ELF est text 1,245,128, data 2,314 et BSS 38,768 octets (1,286,210 octets cumulés), soit +52 octets cumulés par rapport au relevé v55. Cette mesure de sections ne représente pas le pic RAM pendant l’exécution. Le VAGi, le tampon CD, les volumes et l’ordonnancement des flux sont inchangés.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja et génération ISO réussies. BIN 29,011,920 octets (12,335 secteurs), CUE 89 octets; SHA-256 du BIN `FB67A7933A87D7660A2FBAC2DFCB33A2F80837E6C8D750020594FE08441FA1F3`. Fichiers sous `outputs/FNF-PS1-v56-menu-layout/`. Cette version n’a pas été exécutée dans DuckStation : le nouveau cadrage, la navigation jusqu’au démarrage de Bopeebo, le son menu et l’écran Game Over restent à vérifier par l’utilisateur. Aucun test console réelle. Diagnostics masqués au démarrage.

Les modifications v55 déjà présentes dans le checkout restent non commitées avec ce travail; aucun commit en double n’a été créé. La PR #1 n’est pas actualisée depuis ce checkout : le dernier état distant connu est divergent et le fetch authentifié échouait (`SEC_E_NO_CREDENTIALS`). Ne pas pousser avant une nouvelle lecture/réconciliation de la tête distante.

## v57 — essai intégré du libellé Options

L’utilisateur a validé le deuxième concept « OPTIONS » et demande le traitement visuel normal du menu : inactif noir à contour blanc, sélectionné blanc à contour noir avec animation. Le PNG validé reste sous `outputs/menu-options-concept-v2.png` et n’est pas ajouté à Git. Le convertisseur crée ses deux états depuis ce visuel; il n’utilise l’image officielle `options.png` que comme solution de repli si le PNG local est absent.

Le menu principal n’affiche plus « Merch ». Le nouveau libellé remplace cet emplacement. L’état sélectionné reprend le rythme des `AtlasMenuItem` source (24 images/s) avec trois phases de pulsation centrées. Dans ce build d’essai, `Square` (`J` dans DuckStation) bascule uniquement l’aperçu visuel Options; le lancement existant reste `Cross` (`K`) vers Freeplay, car le menu de réglages n’est pas encore implémenté. Ce raccourci sert à comparer idle/sélectionné et n’ajoute pas une fonction Options fictive. Les autres états du menu et le jeu restent inchangés.

Les états Options et Freeplay utilisent la bande libre de la page menu existante, en deux moitiés de 128 pixels; les trois bitmaps menu et le nombre de pages VRAM ne changent pas. La table ajoute 13,824 octets pour les trois images 128×36 (idle Freeplay, idle Options et sélection Options). Le nouvel ELF rapporte text 1,259,684, data 2,326 et BSS 38,772 octets, soit 1,300,782 octets de sections cumulées, +14,632 par rapport à v56. Ce chiffre n’inclut pas le tampon audio de 96 KiB, la pile ni les allocations runtime. VRAM inchangée : 9 pages 8bpp + 2 pages 4bpp, framebuffers et palettes compris; audio, streaming, chart, score et timings inchangés.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja et génération BIN/CUE réussies. BIN 29,028,384 octets (12,342 secteurs), CUE 95 octets; SHA-256 BIN `68FEC884CA097DCCD18101A1F1A8784136C48D29A461DF3F52245A46ACB23130`, dans `outputs/FNF-PS1-v57-options-menu-test/`. Cette image n’a pas été exécutée dans DuckStation : l’apparence des deux états, l’animation, puis l’absence de régression au lancement de Bopeebo attendent l’essai utilisateur. Les diagnostics restent masqués par défaut. Les sources avant intégration sont sauvegardées hors Git sous `work/before-options-menu-integration/`.

### Synchronisation du dépôt

Comparaison GitHub du checkout `facbf124` avec la tête distante de la PR (`ee18a7f1`) : la branche distante est en avance de 63 commits. Plusieurs fichiers, dont `spu_probe.c` et `PS1_PORT.md`, diffèrent de façon structurelle; ce n’est pas un simple commit local manquant. Le `git fetch origin ps1-port` échoue sous Windows avec `SEC_E_NO_CREDENTIALS`. Je n’ai donc pas réécrit la tête distante avec l’état local. La PR #1 reste ouverte et brouillon, sans fusion; son code distant n’inclut pas ce BIN v54. Reprendre la publication après rétablissement d’un fetch authentifié et fusion/rebase des versions divergentes, puis pousser un unique commit intégré.

## v58 — navigation du menu principal et contour Options ralenti

Après l’essai utilisateur de v57, les quatre entrées étaient visuellement désalignées, l’animation Options trop rapide et les flèches directionnelles ne naviguaient pas dans le menu. v58 place Story Mode, Freeplay, Options et Credits dans quatre lignes centrées de même boîte source (128×36), avec un espacement régulier; le footer reste sous les libellés. Le PNG Options approuvé reste hors Git. Son texte blanc sélectionné ne change plus de taille ni de position : seule la bordure noire varie d’un pixel, lentement (une pose toutes les 18 images menu, environ 3,3 images/s). Les autres entrées utilisent leurs états idle/selected et leurs trois images officielles.

Haut/Bas parcourt les quatre entrées en boucle; Freeplay est sélectionné au démarrage. Croix ouvre uniquement Freeplay, les autres entrées restent sans destination fonctionnelle. En changeant de ligne, le menu restaure son fond de base avant d’effacer la nouvelle ligne sélectionnée, afin de ne pas laisser les anciennes lignes sélectionnées vides. Une copie de sauvegarde pré-v58 est conservée sous `work/before-menu-navigation-adjustments/`.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 / CMake 4.4.4 / Ninja réussie. La conversion confirme 9 pages 8bpp + 2 pages 4bpp, sans page VRAM supplémentaire; les 4 lignes de restauration utilisent la même page menu. Les données statiques liées au menu augmentent d’environ 46 Kio dans l’ELF par rapport aux métriques v57 (4 animations sélectionnées × 3 poses, moins l’ancien stockage d’essai, plus les quatre patches de fond). ELF : text 1 305 716, data 2 338, BSS 38 768 octets. BIN 29 080 128 octets, SHA-256 `05E15EC03F315A7268CDA38007B5B1B3D0FA78204E51D4867380844F8797D6E8`; CUE 93 octets. Fichiers : [BIN](../outputs/FNF-PS1-v58-menu-navigation/funkin-ps1-bopeebo-playable.bin) · [CUE](../outputs/FNF-PS1-v58-menu-navigation/funkin-ps1-bopeebo-playable.cue).

Le build conserve le parcours titre → menu principal → Freeplay → Bopeebo Normal, ainsi que l’audio et le gameplay déjà validés; les diagnostics restent masqués au démarrage. Compilation et génération de disque seulement : v58 n’a pas été exécutée dans DuckStation dans cette passe et attend l’essai utilisateur. Aucun test console réelle. Le checkout reste sur `ps1-port` sans nouveau commit ni publication de cette version non vérifiée.

## v59 — composition de menu calée sur la référence

La vidéo `Screen_Recording_20261026_000232.mp4` montre les libellés centrés selon l’espacement de `MainMenuState.hx` (160px logiques) et leurs dimensions d’atlas propres. v59 transpose ces centres au format 320×240 depuis la fenêtre 675px de la référence : Story Mode, Freeplay, Options et Credits sont centrés autour de y=35, 92, 149 et 206. Chaque texte garde une taille et un ratio propres; Story Mode sélectionné retrouve une présence plus grande, et le footer a été retiré pour ne pas couvrir Credits. La sélection initiale revient à Story Mode comme dans le code original.

Les images idle/selected de Story Mode, Freeplay et Credits viennent des atlas épinglés et utilisent leur cadence sélectionnée de 24 images/s. Le mot-symbole Options approuvé est conservé à la place de Merch. Son contour blanc idle et son contour noir sélectionné ont maintenant une épaisseur proche des labels dessinés à la main; son remplissage blanc reste fixe et le contour pulse entre deux épaisseurs sur les trois poses sélectionnées au même rythme que les autres entrées. Haut/Bas parcourt les quatre entrées; Croix ne lance que Freeplay. Story Mode, Options et Credits restent sans destination dans le port actuel.

Les quatre patches servant à effacer la ligne sélectionnée ont des dimensions propres à chaque label et sont rechargés dans la page menu existante. La carte VRAM reste 9 pages 8bpp + 2 pages 4bpp; aucune texture ni lecture CD supplémentaire n’est ajoutée. Le header généré fait 3 997 934 octets; ELF : text 1 310 536, data 2 346, BSS 38 768 octets. BIN 29 087 184 octets, SHA-256 `B4D318B21A42CC34E74BBD74CD16BBEF418673D263B9500FF8C37ADE8FE115AB`; CUE 93 octets : [BIN](../outputs/FNF-PS1-v59-options-match-menu/funkin-ps1-bopeebo-playable.bin) · [CUE](../outputs/FNF-PS1-v59-options-match-menu/funkin-ps1-bopeebo-playable.cue).

Compilation et création BIN/CUE réussies; `py_compile` et `git diff --check` passent. Pas d’exécution DuckStation dans cette passe, donc le cadrage et l’animation restent à confirmer par l’utilisateur. Diagnostics masqués au démarrage; aucun test console réelle. La version v58 et les sources de sauvegarde restent disponibles pour retour arrière.

Mise à jour du retour utilisateur sur v59 : l’utilisateur rapporte un gel lors de la sélection/navigation. Aucun diagnostic du freeze n’a été capturé, donc sa cause exacte n’est pas établie. La refonte des dimensions et des zones d’effacement introduite en v59 est retirée dans v60; la disposition v58 est restaurée comme demandé.

## v60 — retour à la disposition v58 et contour Options renforcé

v60 reprend la disposition compacte que l’utilisateur préfère : quatre rangées alignées dans des boîtes 128×36, rendues dans des sprites 160×45 aux positions de v58. La navigation Haut/Bas et Freeplay sélectionné par défaut sont conservés. Les changements v59 de tailles/positions variables et de patches de restauration spécifiques à chaque label sont retirés. Cela réduit le menu aux primitives et uploads de la disposition précédente; le freeze observé en v59 doit encore être retesté, sa cause n’ayant pas été isolée.

Le contour blanc de l’état idle d’Options est épaissi d’un pixel via une dilation propre à cet état. Le contour sélectionné, son animation, le remplissage, les timings et les autres labels gardent la géométrie v58. Aucun réglage de gameplay, d’audio ou de transitions n’a été modifié. Les conversions restent reproductibles; la source raster OPTIONS approuvée reste hors Git.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 / CMake 4.4.4 / Ninja réussie; BIN/CUE générés. Conversion : 9 pages 8bpp + 2 pages 4bpp, carte VRAM sans chevauchement, header 3 980 264 octets. ELF : text 1 305 640, data 2 338, BSS 38 768 octets. BIN 29 080 128 octets, SHA-256 `A38708CBBAA1BBF6C5E1463B3292FD2A8D2E6E235DF845AA761CC5F47ACE35E`; CUE 93 octets : [BIN](../outputs/FNF-PS1-v60-menu-nav-outline/funkin-ps1-bopeebo-playable.bin) · [CUE](../outputs/FNF-PS1-v60-menu-nav-outline/funkin-ps1-bopeebo-playable.cue).

L’utilisateur a ensuite chargé v60 dans DuckStation et confirmé que le menu fonctionne sans gel lors de la navigation. Cette validation couvre le parcours de menu essayé; elle ne valide pas encore v61 ni la console réelle. Aucun commit ni push effectué.

## v61 — Options légèrement réduit et contours animés

À la demande de l’utilisateur après validation du menu v60, le lettrage Options est réduit légèrement : la largeur maximale passe de 120 à 116 px (−3,3 %) et la hauteur de 32 à 31 px (−3,1 %), en gardant le ratio et le centrage dans sa boîte. Les autres éléments et la disposition validée restent identiques.

L’animation sélectionnée conserve le remplissage blanc fixe et redessine uniquement le contour noir sur trois images. Les contours varient subtilement en épaisseur horizontale/verticale (rayons 2×2, 3×2, 2×3 px); le cycle utilise le même index de trois images et la même cadence que Story Mode, Freeplay et Credits. Cela remplace l’ancien décalage horizontal uniforme du contour, qui ne ressemblait pas à l’animation des autres lignes. Le chargement et l’affichage gardent la page VRAM et le mécanisme v60; aucun changement de navigation, gameplay ou audio.

Conversion Python : `py_compile` réussi et `git diff --check` propre. Build PSn00bSDK 0.24 / GCC MIPS 12.3 / CMake 4.4.4 / Ninja réussi. La vérification VRAM reste à 9 pages 8bpp + 2 pages 4bpp, sans chevauchement; aucun espace supplémentaire n’est consommé. ELF : text 1 305 640, data 2 338, BSS 38 768 octets. BIN 29 080 128 octets, SHA-256 `BE581F5A9BFD297F855A8417D007BC21C87958ED2B806FBB6FEFDE2C09D41371`; CUE 93 octets : [BIN](../outputs/FNF-PS1-v61-options-animation/funkin-ps1-bopeebo-playable.bin) · [CUE](../outputs/FNF-PS1-v61-options-animation/funkin-ps1-bopeebo-playable.cue).

v61 est compilé mais pas encore exécuté dans DuckStation; la taille et l’animation restent à évaluer par l’utilisateur. Diagnostics masqués par défaut. Pas de test console réelle, aucun commit ni push effectué.

## v62 — contour noir plus large et animé avec irrégularités

Retour utilisateur sur v61 : la taille et l’aspect général sont meilleurs; le contour de sélection doit être un peu plus large et son mouvement moins régulier. v62 élargit le trait noir d’un pixel source autour du lettrage blanc fixe. Le bord extérieur varie légèrement par groupes de pixels selon un motif déterministe différent sur chacune des trois images; le noyau du contour reste continu afin de conserver la lisibilité.

La sélection d’image Options suit maintenant une courte séquence pseudo-aléatoire de 16 pas, mise à jour toutes les quatre images menu, avec répétitions irrégulières. Cela casse l’alternance lisse et répétitive tout en réutilisant les trois images générées et le même chargeur VRAM. Les autres libellés gardent leur cadence inchangée. La disposition v60, la taille Options v61, les commandes, l’audio et le gameplay restent inchangés.

Build PSn00bSDK 0.24 / GCC MIPS 12.3 / CMake 4.4.4 / Ninja réussi. La conversion confirme 9 pages 8bpp + 2 pages 4bpp et aucun chevauchement VRAM; pas de page supplémentaire. BIN 29 080 128 octets, SHA-256 `4107ABA3BC73BFCB57A7291435625A8D4C15C207EBFA216337A304F3EFFAF0ED`; CUE 93 octets : [BIN](../outputs/FNF-PS1-v62-options-contour-noise/funkin-ps1-bopeebo-playable.bin) · [CUE](../outputs/FNF-PS1-v62-options-contour-noise/funkin-ps1-bopeebo-playable.cue).

Compilation et conversion Python (`py_compile`, `git diff --check`) réussies. v62 n’a pas encore été exécuté dans DuckStation; largeur du contour et effet de bruit attendent la validation de l’utilisateur. Diagnostics masqués au démarrage. Aucun test console réelle; aucun commit ni push.

## v63 — catalogue Week 1 et Tutorial

Le menu Freeplay contient maintenant les quatre morceaux réellement convertis depuis le checkout d’assets épinglé : Tutorial, Bopeebo, Fresh et Dadbattle. Haut/Bas choisit le morceau; Gauche/Droite choisit Easy, Normal ou Hard; Croix lance la sélection et Rond revient au menu principal. Bopeebo Normal reste le choix initial. Erect et Nightmare sont indiqués comme réservés, sans choix jouable.

Les charts des trois difficultés sont convertis en temps d’échantillons à 43 008 Hz. Le catalogue conserve les tenues, tempos et événements FocusCamera présents dans les JSON officiels. Le Tutorial garde BF comme joueur et GF comme adversaire, avec ses quatre poses de chant et son portrait; les trois morceaux de Week 1 gardent Dad. La scène commune reste celle du prototype PS1. Les règles de gameplay validées ne changent pas.

Les sources OGG de chaque morceau sont converties à 43 008 Hz avec une origine commune en quatre canaux VAGi : instrumental L/R, voix adversaire mono, voix BF mono. Les voix mono sont la moyenne gauche/droite, sans normalisation indépendante. Circle coupe uniquement BF. Les nouveaux flux se chargent depuis le CD un par un; aucun extrait officiel ni fichier généré n’est ajouté au dépôt. Les fichiers intermédiaires et VAGi sont sous `ps1/build/` (ignoré par Git).

| Morceau | Opposant | Échantillons | Durée | Chart Easy / Normal / Hard |
| --- | --- | ---: | ---: | ---: |
| Tutorial | GF | 2 890 137 | 67,2 s | 55 / 55 / 71 notes |
| Bopeebo | Dad | 3 509 453 | 81,6 s | 88 / 102 / 124 notes |
| Fresh | Dad | 3 612 672 | 84,0 s | 169 / 210 / 267 notes |
| Dadbattle | Dad | 3 843 243 | 89,4 s | 144 / 263 / 327 notes |

Le catalogue compilé fait 62 768 octets et contient au plus 327 notes par chart. La conversion graphique reste à 9 pages 8bpp et 2 pages 4bpp, framebuffers et CLUT inclus (655 360 octets de textures); l’icône GF est rangée dans la page popup 4bpp existante, sans page VRAM supplémentaire. L’ELF mesure 1 573 020 octets sur disque; sections résidentes `.text + .rodata + .data + .sdata + .sbss + .bss` : 1 361 610 octets. Le lecteur conserve son FIFO CD/SPU de 96 Kio alloué dans le heap; marge estimée avant stack et allocations ponctuelles : environ 494 Kio dans les 1,875 Mio accessibles au programme. Les VAGi des trois nouveaux morceaux occupent 23 828 480 octets sur le CD. Le débit VAGi reste à environ 96 Kio/s pour les quatre canaux et le tampon garde environ une seconde de réserve; aucun chargement CD concurrent n’a été ajouté.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 / CMake 4.4.4 / Ninja et génération BIN/CUE réussies. BIN 56 462 112 octets, SHA-256 `9B1B62B74CE3B758B24E2FAF68A354F92CCD42EB176A1992D120D7DEC48FCA39`; CUE 93 octets : [BIN v63](../outputs/FNF-PS1-v63-week1-songs/funkin-ps1-bopeebo-playable.bin) · [CUE v63](../outputs/FNF-PS1-v63-week1-songs/funkin-ps1-bopeebo-playable.cue).

v63 n’a pas été exécuté dans DuckStation dans cette passe. Les quatre charts et nouveaux sons sont convertis et compilés, pas validés à l’écoute ni joués en émulateur. Essai demandé : titre → Freeplay → vérifier chaque morceau et ses trois difficultés, en particulier Tutorial/GF et Dadbattle Hard, puis retour au menu. Mute BF et les mécaniques précédemment validées doivent aussi être recontrôlés. Aucun test console réelle. Aucun commit ni push effectué.

Assets de référence : sous-module `assets` à `724eba9de9e76761d9cefd52169926bc51c760a5`.

## v64 — Tutorial en premier et Freeplay réorganisé

Retour utilisateur après v63 : les quatre morceaux sont considérés bons; correction demandée, Tutorial doit être le premier choix, et Freeplay doit mieux reprendre la référence vidéo du 26 octobre. Le catalogue place maintenant Tutorial, Bopeebo, Fresh, Dadbattle dans cet ordre. La sélection initiale et celle au retour au menu pointent donc vers Tutorial Normal. Haut/Bas parcourt ces quatre morceaux; Gauche/Droite reste limité à Easy, Normal et Hard. Les touches Circle/Croix gardent leur action existante. Erect et Nightmare ne sont pas sélectionnables.

L’écran Freeplay reprend les éléments visibles dans la référence : illustration officielle de BF au DJ à gauche, fond officiel Week 1 à droite, quatre entrées en liste avec la capsule officielle de sélection, difficulté, pochette Volume 1 et commandes à la manette. Il est composé à 256×192 puis affiché en 320×240 sans étirer la source. Trois poses du rig Animate officiel `freeplay-boyfriend` alternent dans le menu. La capsule suit la sélection et est rechargée dans la bande inutilisée au bas de la page VRAM menu; la liste de quatre titres reste affichée. Aucun doublon de décor par chanson, page VRAM gameplay ou lecture CD concurrente n’est ajouté. Les poses partagent le CLUT menu afin de ne pas répéter les mêmes couleurs dans l’échantillonnage de la palette gameplay.


La ligne `BEST 000000` représente l’absence de sauvegarde de meilleur score dans cette version; aucun record n’est enregistré. Le prompt tactile de changement de DJ et les choix Erect/Nightmare ne sont pas simulés. Les contrôles restent Haut/Bas chanson, Gauche/Droite difficulté, Croix jouer, Rond retour. Le test visuel des proportions du DJ, du contraste des lignes, de la pochette, des changements de difficulté et des quatre sélections reste à faire dans DuckStation; la compilation seule ne valide pas ce nouvel écran. La validation précédente des quatre morceaux est un retour utilisateur, mais leur réordonnancement et le nouvel écran n’ont pas encore été essayés ensemble. Pas de test console réelle.

Build v64 : PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja / CMake réussi. L’exécutable ne signale plus de dépassement RAM. Sections résidentes `.text + .rodata + .data + .sdata + .sbss + .bss` : 1 496 762 octets, dont 38 944 octets de BSS; le FIFO CD/SPU reste de 96 Kio. Il reste environ 371 014 octets (362 Kio) dans l’estimation de 1,875 Mio avant stack et allocations ponctuelles. Carte VRAM inchangée : 9 pages 8bpp + 2 pages 4bpp, framebuffers et CLUT compris (655 360 octets de textures); la capsule utilise une bande de staging existante. La table de charts fait 62 768 octets. Le BIN est de 56 617 344 octets, SHA-256 `CB4CAE489E96D65AC96D46A85F35CE19227C1843970424461B3350E45359C9E3`; CUE 93 octets : [BIN v64](../outputs/FNF-PS1-v64-tutorial-first-freeplay/funkin-ps1-bopeebo-playable.bin) · [CUE v64](../outputs/FNF-PS1-v64-tutorial-first-freeplay/funkin-ps1-bopeebo-playable.cue).

La génération des charts/VAGi, la conversion des assets et la compilation BIN/CUE ont réussi. v64 n’a pas encore été exécuté dans DuckStation. À vérifier par l’utilisateur : l’écran Freeplay comparé à la vidéo, Tutorial en première ligne et le morceau lancé avec Croix, les sélections des trois autres titres, Easy/Normal/Hard, retour menu et stabilité audio. Aucun test console réelle; aucune fusion ou publication PR dans cette passe.

## v65 — correctif du crash à l’ouverture de Freeplay

Retour utilisateur sur v64 : le jeu plante au moment d’ouvrir Freeplay. L’écart concret par rapport à la version auparavant fonctionnelle est que v64 ouvre quatre régions texte PSn00bSDK supplémentaires (une par chanson) puis les vide chacune chaque frame. Le code ne contrôlait pas l’échec éventuel de `FntOpen`; cette allocation est donc une cause plausible du crash, mais sans dump ni observation instrumentée elle n’est pas confirmée comme cause unique.

v65 retire ces quatre ouvertures supplémentaires et utilise une seule région déjà prévue pour imprimer la liste des quatre titres. Le nombre de régions texte ouvertes revient à celui du build précédent. L’ordre Tutorial, Bopeebo, Fresh, Dadbattle, le cadrage Freeplay, la capsule sélectionnable et le chargement VRAM sont conservés. Aucun changement de gameplay ou d’audio.

Build PSn00bSDK 0.24 / GCC MIPS 12.3 réussi, BIN de 56 617 344 octets. Le correctif n’a pas été observé dans DuckStation : le chargement de Freeplay, la navigation et l’absence de crash restent à confirmer. Si v65 plante encore, le prochain essai doit désactiver temporairement le chargement/dessin de la capsule pour isoler le chemin VRAM. Aucun test console réelle.

## v66 — Freeplay composé et catalogue parcourable

Le Freeplay est maintenant intégré au build jouable sur `ps1-port`. La composition approuvée est adaptée à 320×240 : séparation oblique jaune plus large vers le bas, inscriptions officielles recolorées en trois familles nettement distinctes (jaune clair, jaune-orangé et orange), et illustration Week 1 recadrée sur Dad. Le recadrage source 430×322 vers 256×192 conserve le rapport 4:3, garde le visage et le micro de Dad dans le cadre et exclut Girlfriend du fond. BF apparaît au DJ avec une pose officielle fixe.

Chaque ligne est composée de sa capsule officielle sélectionnée ou inactive, d’une icône pixel officielle, du titre dans la cavité intérieure et d’un état `LOCKED` à droite pour les chansons indisponibles. Les icônes font 28×28 pixels, soit +16,7 % par rapport aux boîtes 24×24 antérieures; leur placement vertical et leur chevauchement léger avec la capsule sont calculés d’après les limites alpha propres à chaque sprite. La liste suit l’ordre du catalogue sans rebouclage : Tutorial, Bopeebo, Fresh, Dadbattle, puis le catalogue classique parcourable. Seules les quatre premières entrées lancent un morceau; confirmer les autres ne lance rien. Haut/Bas parcourt les titres, Gauche/Droite change Easy/Normal/Hard, Croix lance un titre disponible et Rond revient au menu.

Le score et le pourcentage de réussite du bandeau viennent des résultats calculés à la fin d’une chanson jouée. Le pourcentage reprend une complétion de type moteur original : notes joueur Sick/Good moins ratés et drops de tenues, divisée par les notes joueur du chart et bornée à 0–100. Ces records sont conservés uniquement en RAM pendant la session; aucune sauvegarde sur carte mémoire n’est implémentée. Les autres entrées n’ont pas de record et montrent des tirets. Le gameplay et les flux audio existants ne sont pas modifiés; aucun flux CD concurrent ni asset de gameplay de catalogue verrouillé n’est ajouté. Diagnostics masqués au démarrage.

La page VRAM reste à 9 textures 8bpp et 2 textures 4bpp, framebuffers et CLUT compris, sans chevauchement (655 360 octets). Les deux capsules et l’alphabet officiel occupent la bande inférieure de la page menu déjà réservée; les quatre icônes visibles sont transférées depuis les données du programme lors du défilement, sans lecture CD ni page VRAM supplémentaire. Les tableaux générés d’icônes représentent 8 624 octets; les textures du jeu et du menu partagent les allocations déjà comptées. `size` sur l’ELF donne `.text 1 332 232`, `.data 2 350`, `.bss 38 992` octets, soit 1 373 574 octets au total pour ces segments; cette mesure ne réserve pas la pile ni le tampon audio alloué à l’exécution. Le flux garde son tampon CD de 96 Kio et son organisation SPU quatre canaux. Le BIN fait 56 476 224 octets, SHA-256 `6CD671A66958FF28F592768881C0B42130FD9C8E874AF5C5683874B719F678E4`; CUE 93 octets : [BIN v66](../outputs/FNF-PS1-freeplay-v66/funkin-ps1-bopeebo-playable.bin) · [CUE v66](../outputs/FNF-PS1-freeplay-v66/funkin-ps1-bopeebo-playable.cue).

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 / CMake 4.4.4 / Ninja réussie; conversion des graphiques, des charts/audio et création BIN/CUE réussies. `git diff --check` passe. Le build n’a pas été lancé dans DuckStation dans cette passe : aucun comportement de navigation, d’ouverture, de lancement ou de retour n’est donc validé par exécution. L’utilisateur doit charger le CUE et essayer Titre → Menu → Freeplay, parcourir jusqu’aux entrées verrouillées, lancer Tutorial/Bopeebo/Fresh/Dadbattle dans les difficultés voulues et vérifier retour/menu/audio. BF DJ est un dessin officiel statique dans v66; son animation officielle reste différée. Aucun test console réelle, aucun commit, push ou fusion.

## v67 — correction d’intégration Freeplay après la capture v66

La capture v66 fournie par l’utilisateur a été comparée à la maquette de référence fixe `outputs/FNF-PS1-freeplay-mockup-v5/freeplay-tutorial-selected-320x240.png`. Trois différences visibles avaient une cause concrète dans l’intégration : les titres provenaient de l’atlas `letterStuff` réduit en glyphes 5×7 plutôt que de la police VCR de la maquette; la difficulté était imprimée avec la police BIOS (`FntPrint("< NORMAL >")`) au lieu des images officielles; et le fond Week 1 était un crop top-left de 430×322, qui agrandissait Dad par rapport au mockup. Les titres jouables n’utilisaient en outre que 58 px de cavité, tandis que la maquette leur en réserve 89 px.

v67 conserve la composition et les dimensions d’interface de la maquette, sans ajout d’animation. Les titres sont rasterisés depuis `assets/fonts/vcr-bold.ttf` en cellules séparées de 6×8; chaque primitive ne lit que les 5×7 pixels d’encre, avec un pas de 6 px. Le titre jouable dispose de 89 px; les entrées verrouillées disposent de 59 px et gardent le badge dans son compartiment. La difficulté utilise `freeplayeasy.png`, `freeplaynormal.png` ou `freeplayhard.png`, plus une frame de `freeplaySelector.xml`; les éléments sont réduits et posés selon les coordonnées de la maquette. Une bande de 76×24 pixels est transférée dans la page Freeplay à la sélection d’une difficulté, sans page VRAM additionnelle. Les primitives de titre utilisent toujours la page 8bpp menu/CLUT8, avec UV calculées par indice et pas de 6×8.

Le fond source `freeplayBGweek1-bf.png` mesure 821×516. Il est réduit proportionnellement à 306×192 puis panoramiqué à x=25 dans la texture 256×192 : GF reste au-delà du bord droit, Dad garde son rapport d’aspect, et l’ancien agrandissement par crop est supprimé. BF DJ reste à 82×90 dans la texture, soit environ 103×113 à l’écran 320×240; le placement du DJ, la liste en arc, les capsules et la navigation restent ceux du mockup approuvé et des ajustements demandés ensuite.

La vérification du convertisseur contrôle maintenant explicitement les cellules VCR, les deux capsules, les quatre slots d’icônes et leurs limites sur la page; elle contrôle aussi que les sélecteurs et le label restent dans la bande uploadée. Les 124 rectangles du reste des atlas gardent leurs contrôles de profondeur, UV et recouvrement. La bande de difficulté occupe 912 mots (1 824 octets) par variante en ROM, soit 5 472 octets pour Easy/Normal/Hard; elle réutilise la page menu déjà chargée. Carte VRAM inchangée : 9 pages 8bpp + 2 pages 4bpp, framebuffers et CLUT compris, 655 360 octets de textures. ELF `size` : `.text 1 346 544`, `.data 2 406`, `.bss 39 060`, total 1 388 010 octets. Sur la même estimation de 1,875 Mio utilisée précédemment, il reste arithmétiquement 578 070 octets avant pile et allocations temporaires/audio; ce n’est pas une mesure du pic RAM.

Build reproductible dans `ps1/build/freeplay-v67-menu-match/`, cible `ps1-bopeebo-playable-disc`, avec les mêmes entrées locales chart/VAGi et FFmpeg que v66. Conversion et contrôles de page passent; compilation PSn00bSDK 0.24 / GCC MIPS 12.3, édition de l’ELF et création BIN/CUE réussies. Le BIN fait 56 492 688 octets, SHA-256 `7B8E735342194361E478CA2E6501F2FDF24E1DADB6766B0D6A2E50752D50DDD4`; CUE 93 octets : [BIN v67](../outputs/FNF-PS1-v67-freeplay-reference-match/funkin-ps1-bopeebo-playable.bin) · [CUE v67](../outputs/FNF-PS1-v67-freeplay-reference-match/funkin-ps1-bopeebo-playable.cue).

**Non vérifié dans DuckStation :** le nouveau disque n’a pas encore été lancé; aucune capture framebuffer 320×240 du build v67 n’est donc disponible, et aucune visibilité finale des titres/du label n’est revendiquée. L’utilisateur doit charger ce CUE; après sa confirmation, la capture native et la comparaison côte à côte seront faites dans l’émulateur avec Tutorial sélectionné. Les parcours menu→morceau, changement Easy/Normal/Hard, retour, audio, autres entrées LOCKED et essais console réelle restent à vérifier. Diagnostics compilés masqués au démarrage; aucun changement de gameplay ni d’audio, et BF DJ reste en pose fixe.

## v68 — isolation du gel à l’ouverture de Freeplay

Retour utilisateur sur v67 : DuckStation se fige immédiatement en entrant dans Freeplay. La seule opération graphique ajoutée spécifiquement à cette entrée était le transfert `LoadImage` partiel de la bande 76×24 pour la difficulté, après chargement du fond et des icônes. Ses dimensions et son adresse VRAM semblaient valides à l’inspection, donc sa responsabilité n’était pas prouvée; elle constitue toutefois une différence isolable du chemin v66. v68 retire complètement ce transfert partiel. Easy, Normal et Hard sont chacun composés en amont dans une page 256×256 complète; le changement de difficulté choisit cette page et réutilise le chargement plein écran déjà employé par les autres écrans menu. Les icônes gardent leur transfert existant. Aucun changement de gameplay, d’audio ou de commandes.

Coût : deux copies complètes de page menu supplémentaires sont stockées dans l’exécutable, soit 131 072 octets de ROM/RAM statique en plus que v67; une seule page est chargée en VRAM à la fois. La carte VRAM reste à 9 pages 8bpp + 2 pages 4bpp, 655 360 octets de textures. ELF `size` : `.text 1 471 968`, `.data 2 402`, `.bss 39 060`, total 1 513 430 octets. Sur l’enveloppe de 1,875 Mio utilisée comme estimation, il reste 452 650 octets pour pile et allocations à l’exécution; cette enveloppe ne remplace pas une mesure de pic RAM et doit être surveillée sur le parcours audio/menu.

PSn00bSDK 0.24 / GCC MIPS 12.3 a compilé l’ELF et mkpsxiso a produit le disque. Le BIN fait 56 636 160 octets, SHA-256 `3D32C00BC8FFB30576232671474051883D9CD4CB0A54257BD3DEC85CBE659936`; CUE 93 octets : [BIN v68](../outputs/FNF-PS1-v68-freeplay-no-partial-vram-load/funkin-ps1-bopeebo-playable.bin) · [CUE v68](../outputs/FNF-PS1-v68-freeplay-no-partial-vram-load/funkin-ps1-bopeebo-playable.cue). Conversion : contrôles de page et UV réussis; `git diff --check` passe.

**Observation rapportée après livraison :** l’utilisateur confirme que v68 est fonctionnelle et que Freeplay s’ouvre; cette confirmation écarte le gel immédiat observé en v67 dans son essai. Les trois difficultés, toutes les sélections et les cycles complets n’ont pas été couverts par ce seul retour. Aucun test console réelle. Diagnostics masqués au démarrage.

### Retour après livraison

L’utilisateur confirme ensuite que v68 est fonctionnelle et que Freeplay s’ouvre. Cette confirmation valide l’ouverture du menu dans son essai, pas encore chaque difficulté, tous les morceaux ni les transitions complètes.

## v69 — lisibilité des titres et marge haute Freeplay

À partir de la capture utilisateur de v68, le texte des chansons était trop petit et le bandeau `FREEPLAY` / meilleur score touchait la limite supérieure visible. Les capsules, leur arc, les portraits, l’illustration et les commandes restent inchangés. Les titres utilisent maintenant des glyphes VCR rasterisés en cellules 6×9 au lieu de 6×8, dessinés en 6×8 avec un espacement de 7 px et un gris clair renforcé. La cavité conserve assez de largeur pour Tutorial, Dadbattle et les libellés verrouillés. Le libellé FREEPLAY est descendu de 7 px dans la texture de menu, le fond sombre du bandeau a été étendu jusqu’à y=27, et le texte BEST est descendu de y=6 à y=15; la difficulté reste dégagée sous le bandeau.

La compilation PSn00bSDK 0.24 / GCC 12.3 a réussi. La conversion a vérifié les limites du nouvel atlas 48×36, l’absence de chevauchement avec les icônes et les UV des 26 lettres. VRAM reste à 655 360 octets de textures (9 pages 8bpp et 2 pages 4bpp); la RAM résidente mesurée est identique à v68 : 1 513 430 octets (text 1 471 968, data 2 402, bss 39 060). Le disque fait 56 636 160 octets.

[BIN v69](../outputs/FNF-PS1-v69-freeplay-title-legibility/funkin-ps1-bopeebo-playable.bin) · [CUE v69](../outputs/FNF-PS1-v69-freeplay-title-legibility/funkin-ps1-bopeebo-playable.cue). BIN : 56 636 160 octets; SHA-256 `8D21E87D50B9DE524F52984D91B33E2E5115EAD6A18F8A6E652782A3B0D5B9E8`. Les changements n’ont pas encore été observés dans DuckStation; charger le disque et vérifier la marge haute, la lisibilité des quatre noms disponibles et le libellé LOCKED. Aucune validation console réelle n’est revendiquée. Gameplay, audio et navigation n’ont pas été modifiés.

### Retour utilisateur

Après livraison, l’utilisateur indique que v69 est parfaite et demande de passer aux animations du menu. Ce retour valide visuellement les titres agrandis et la marge haute dans son essai DuckStation.

## v70 — animation officielle BF DJ dans Freeplay

Le rig Animate officiel `assets/preload/images/freeplay/freeplay-boyfriend` fournit les repères `Intro` (frames source 0–16) et `Idle` (17–30). Le convertisseur échantillonne neuf frames d’intro et sept d’idle à 12 images/s, puis les normalise sur un sol commun dans une zone 82×90. À l’entrée dans Freeplay, l’intro est jouée une fois, suivie de la boucle idle. Le temps de l’animation suit les frames UI; le lancement du morceau reste immédiat, sans délai ajouté. Les animations officielles confirm, fist-pump et easter-egg ne sont pas encore intégrées; les danses de GF au titre et les animations de sélection du menu principal restent présentes.

La pose fixe du DJ a été retirée des fonds Freeplay. Chaque pose convertie est recomposée opaque sur le fond décoratif de la même zone, puis chargée au changement d’image dans la fenêtre texture `(10,96)` de la page menu déjà active. Cela préserve les pixels jaunes/décor derrière les zones transparentes du rig. La page UI, les capsules, les icônes et les UV restent dans la carte VRAM existante : 9 pages 8bpp + 2 pages 4bpp, 655 360 octets de textures, aucun nouveau bloc VRAM. Un upload de 7 380 octets est fait quand l’image change; le débit moyen prévu à 12 fps est d’environ 88,6 Ko/s sur le bus GPU. Ce coût n’a pas été mesuré sur console.

L’animation occupe 118 080 octets de tableaux résidents (16 poses × 82 × 90 × 1 octet). La génération n’échantillonne que trois poses transparentes pour la palette partagée afin de ne pas pondérer 16 fois le fond jaune; RMSE mesurée par le convertisseur : DJ 4,89, Dad/GF combinés 4,71/4,43 RGB, contre 4,94/4,53 dans v69. L’ELF mesure 1 631 938 octets résidents (text 1 590 468, data 2 406, bss 39 064), soit 334 142 octets sous l’enveloppe RAM de 1,875 Mio. Après le tampon audio de 96 Kio, la marge arithmétique est d’environ 230 Kio pour pile et allocations runtime; leur haut niveau n’est pas mesuré. La mémoire SPU et l’audio CD restent inchangés.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 réussie; vérification de la palette, de l’ancrage commun, de la zone opaque de remplacement et de la carte VRAM réussie. Le BIN fait 56 772 576 octets, SHA-256 `7EF053B73524ECEC7D3284D2C27BE7DBBEE919FBEE6DDB9521B3AF772260C32D`; CUE 93 octets : [BIN v70](../outputs/FNF-PS1-v70-freeplay-dj-animation/funkin-ps1-bopeebo-playable.bin) · [CUE v70](../outputs/FNF-PS1-v70-freeplay-dj-animation/funkin-ps1-bopeebo-playable.cue). Ce build n’a pas été exécuté dans DuckStation. L’entrée Freeplay, le cycle intro→idle, l’absence de trous dans le fond et la stabilité de FreakyMenu pendant les mises à jour restent à confirmer par l’utilisateur. Pas de test console réelle.

### Retour utilisateur sur v70

L’utilisateur rapporte que le jeu se fige immédiatement à l’ouverture de Freeplay. La cause n’est pas encore confirmée. L’écart v70 propre à ce jalon est le transfert partiel de l’image BF vers la page menu à chaque nouvelle pose (82×90 pixels, environ 7,4 Kio, à 12 fps). v71 retire ce chemin critique; le nouvel essai devra confirmer si c’était bien la source du gel.

## v71 — atlas BF DJ et transferts VRAM hors animation

Les 16 poses officielles restent dans la même zone et suivent toujours l’intro puis l’idle à 12 images/s. Elles sont maintenant packées en trois pages 8bpp complètes. À l’entrée de Freeplay, le programme charge ces trois pages par transferts complets, synchronisés et regroupés, puis dessine chaque pose avec la voie texturée ordinaire. Aucun `LoadImage` n’est appelé lors du changement de pose. Les pages 8bpp 5 à 7, temporairement utilisées pour l’atlas pendant les menus, sont restaurées depuis les données d’origine avant le lancement d’une chanson. Les menus et le gameplay ne nécessitent donc pas simultanément les mêmes pages. Cette correction est une hypothèse isolée à tester; elle ne constitue pas encore une confirmation que le gel est résolu.

La carte VRAM reste à 9 pages 8bpp + 2 pages 4bpp (655 360 octets de textures), framebuffers et palettes compris. ELF `size` : `.text 1 669 408`, `.data 2 406`, `.bss 39 064`, total 1 710 878 octets. Sous l’enveloppe arithmétique de 1,875 Mio, il reste 255 202 octets; après le tampon audio de 96 Kio, environ 153 Kio restent pour pile et allocations runtime. Ce n’est pas une mesure du pic RAM. Les trois pages d’atlas occupent 196 608 octets de mémoire résidente, soit 78 528 octets de plus que les tableaux d’images v70.

La conversion et ses contrôles d’UV, profondeur, pages et recouvrement ont réussi; le convertisseur signale 140 rectangles sans chevauchement et 3 pages DJ complètes. Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 et création BIN/CUE réussies. BIN 56 864 304 octets, SHA-256 `C7FA7B5646D7BE45872EC3E0335300ED43C80B86C08EA144893A4852577FFB47`; CUE 93 octets : [BIN v71](../outputs/FNF-PS1-v71-freeplay-dj-atlas/funkin-ps1-bopeebo-playable.bin) · [CUE v71](../outputs/FNF-PS1-v71-freeplay-dj-atlas/funkin-ps1-bopeebo-playable.cue).

**Retour utilisateur après livraison :** Freeplay est fonctionnel dans son essai, donc l’ouverture sans gel est observée; le DJ est toutefois beaucoup trop petit. Ce retour ne valide pas les lancements de morceaux ni toutes les transitions. Je n’ai pas lancé l’émulateur. Aucun test console réelle.

## v72 — BF DJ Freeplay agrandi

La capture v71 montre que le rig officiel n’occupait qu’environ 31×38 pixels dans sa pose idle à l’intérieur d’un cadre opaque de 82×90. Le convertisseur conserve maintenant les poses du rig avec transparence et les recadre sur leur emprise horizontale commune de 31×90, tout en gardant l’ancrage au sol. Le rendu PS1 affiche ce sprite à 1,75× (environ 54×157 pour le rectangle texturé), à x=10, y=31; son bas reste à y=188, et le titre Freeplay est dégagé. Le fond jaune reste une couche distincte, les capsules sont dessinées par-dessus le DJ. Le filtrage reste nearest-neighbor du GPU PS1; aucun lissage n’est ajouté.

Les poses tiennent dans une seule page d’atlas 8bpp temporaire, restaurée avant le gameplay. La carte VRAM complète est inchangée : 9 pages 8bpp + 2 pages 4bpp, 655 360 octets de textures. Le tableau DJ occupe 65 536 octets résidents (contre 196 608 en v71). ELF `size` : `.text 1 538 332`, `.data 2 406`, `.bss 39 064`, total 1 579 802 octets. Sous l’enveloppe de 1,875 Mio, la marge arithmétique est de 386 278 octets; après le tampon audio de 96 Kio, environ 281 Kio restent pour pile/runtime. Cette marge n’est pas une mesure du pic RAM.

La conversion a contrôlé l’emprise des 16 poses, leur transparence, les UV et leur placement dans une page; compilation PSn00bSDK 0.24 / GCC MIPS 12.3 et génération BIN/CUE réussies. BIN 56 713 776 octets, SHA-256 `FF58C6E961E610F217D169E712489F193CAD1B479A5DD5E56756A59288116130`; CUE 93 octets : [BIN v72](../outputs/FNF-PS1-v72-freeplay-dj-size/funkin-ps1-bopeebo-playable.bin) · [CUE v72](../outputs/FNF-PS1-v72-freeplay-dj-size/funkin-ps1-bopeebo-playable.cue).

**À essayer dans DuckStation :** taille du DJ pendant plusieurs poses de l’intro et de l’idle, lisibilité du bandeau, absence de recouvrement gênant des capsules, puis lancement d’un morceau pour contrôler la restauration des textures et l’audio. Je n’ai pas exécuté ce build. Aucun test console réelle.
## v73 — première adaptation jouable de la Week 2

La base reste la v72/v71 de Freeplay; la taille du DJ, signalée comme encore incorrecte, est volontairement laissée inchangée. Le catalogue ajoute **Spookeez**, **South** et **Monster** après Tutorial, Bopeebo, Fresh et Dadbattle. Les trois difficultés officielles Easy/Normal/Hard sont converties depuis la révision d’assets épinglée `724eba9de9e76761d9cefd52169926bc51c760a5`. Les entrées du catalogue qui ne correspondent pas à ces sept chansons restent verrouillées et ne chargent pas de gameplay.

Pour chaque titre, le convertisseur reprend l’instrumental et les stems de voix `Voices-bf` + `Voices-spooky` (Spookeez/South) ou `Voices-bf` + `Voices-monster` (Monster). Le flux reste à 4 canaux et 43 008 Hz : instrumental L/R, adversaire mono, BF mono. Les sources de voix OGG ne finissent pas toutes au même échantillon; le générateur conserve le début commun à l’échantillon zéro, prend la durée du stem le plus long et complète les autres par du silence en fin de piste. Cela évite de décaler les voix et rend la fin du flux commune. Les charts, notes tenues, événements FocusCamera et changements de BPM restent à l’horloge audio.

La scène reprend l’image officielle `halloween_bg` et le fichier `spookyMansion.json`. Les snapshots de Spooky Kids proviennent de son atlas Sparrow; Monster est échantillonné depuis son rig Animate. Les quatre directions de chant existent pour les deux adversaires; l’idle Spooky alterne deux poses officielles de danse et Monster alterne Idle/Idle Hold. GF et BF réutilisent leurs animations existantes. Cette première passe conserve l’arrière-plan statique : l’éclair/flash, le tremblement et la séquence complète de frames Idle/Sing des rigs restent à intégrer après l’essai de scène et de synchronisation. Le cadrage est reconstitué dans l’espace monde divisé par huit à partir des coordonnées de scène officielles; des ajustements de position et d’échelle peuvent encore être nécessaires dans DuckStation.

Les données de scène occupent **3 pages 8bpp complètes** en RAM programme (196 608 octets) et une palette de 512 octets. En jeu, ces images remplacent temporairement les pages gameplay 0–2 et la palette 8bpp principale; le chargement Menu → Week 2 → Menu restaure/réapplique les palettes au bon moment. La carte VRAM reste celle de la base : **9 pages 8bpp + 2 pages 4bpp, 655 360 octets de textures**, framebuffers et palette comprises; pas de lecture CD supplémentaire pendant la musique. Les sections résidentes relevées avec `mipsel-none-elf-size -A` sont `.text + .rodata + .data + .sdata + .sbss + .bss = 1 817 142 octets`. Sous le plafond de calcul projet de 1 966 080 octets, la marge est d’environ 148 938 octets avant allocation du tampon de streaming de 96 Kio, pile et autres allocations temporaires; le jeu est plus serré en RAM qu’avant et cette marge reste à mesurer en exécution.

Le build v73 a compilé avec PSn00bSDK 0.24/GCC MIPS 12.3. L’image BIN fait 98 482 944 octets et contient les sept flux jouables, la musique de menu et les pistes Game Over. BIN/CUE sont dans `outputs/FNF-PS1-v73-week2-adaptation/`. **Le build n’a pas été lancé dans DuckStation par Codex** : la navigation vers les trois nouveaux titres, leur lecture complète, les transitions et le retour Freeplay sont à essayer par l’utilisateur. La v72 DJ, l’audio et le gameplay Week 1 ne sont pas revalidés par cette compilation; aucun test console réelle n’est revendiqué.

## v74 — charts et scène Week 2 chargés depuis le CD

Suite à la préférence de chargement par morceau, les 21 charts (7 chansons × Easy/Normal/Hard) sont des fichiers `.BIN` 8.3 sur le CD. `Ps1Song` contient des chemins de chart au lieu de tableaux C résidents. À la confirmation d’un morceau jouable, la musique du menu est arrêtée, le chart choisi est lu et vérifié (`FNC1`, quantités de notes/tempos/caméra, durée audio, tailles des structures), puis conservé en RAM pendant la partie et une éventuelle reprise. Il est libéré au retour au Freeplay. Les chansons verrouillées ne chargent pas de chart ni de ressources de jeu.

Les trois pages graphiques Week 2 et leur palette résident dans `W2SCENE.BIN` (197 120 octets). Le chargeur transfère une page de 65 536 octets à la fois vers la VRAM, réutilise le tampon pour la page suivante, puis lit la palette dans un secteur séparé. L’audio ne démarre qu’après ces lectures; aucun accès CD d’asset ne concurrence le streaming. Le callback d’asset garde `refill_length=0`, donc ne transmet pas ces octets à `Stream_Feed`. Au retour au menu, les pages et la palette Week 1 sont restaurées. Les textures de jeu Week 1 et les données des menus restent toutefois intégrées à l’exécutable : ce premier déplacement est partiel, conçu pour accueillir de futurs packages de scènes plus lourds.

### Mesures de mémoire

`mipsel-none-elf-size -A` : `.text 69 632`, `.rodata 1 448 636`, `.data 2 112`, `.sdata 282`, `.sbss 444`, `.bss 38 816`; total résident **1 559 922 octets**, contre 1 817 142 en v73, soit **257 220 octets économisés**. Sur l’enveloppe arithmétique projet de 1 966 080 octets, la marge avant allocations est 406 158 octets. En gameplay, le tampon audio de 96 Kio et le chart sélectionné (moins de 8 Kio pour les charts générés ici) laissent autour de **302 Kio** avant pile/autres allocations. Le staging visuel de 65 536 octets est utilisé avant de créer le tampon musical; il n’est pas simultané avec celui-ci. Ce sont des estimations à partir de l’ELF et des tailles d’allocations, pas une mesure du pic RAM sur console.

La VRAM reste à 9 pages 8bpp + 2 pages 4bpp = 655 360 octets de textures, avec les framebuffers/CLUT selon la carte existante. Les quatre voix musicales et le tampon streaming de 96 Kio ne changent pas; les voix SFX/menu gardent leurs allocations existantes. Le chargement de scène se fait avant la musique. La durée réelle des lectures n’a pas été mesurée; l’utilisateur accepte une attente visible comme partie de l’expérience PS1.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 réussie; ISO avec 21 charts et fichiers audio séparés, scène Week 2 et pistes menu/Game Over. BIN 98 515 872 octets, SHA-256 `3CC40FDE39F126858511E598BFE326A51E85D5F3ADD04634E8F3C11CE3F14A6D`; CUE 93 octets : [BIN v74](../outputs/FNF-PS1-v74-independent-song-loading/funkin-ps1-bopeebo-playable.bin) · [CUE v74](../outputs/FNF-PS1-v74-independent-song-loading/funkin-ps1-bopeebo-playable.cue). Aucun test DuckStation ou console réelle n’a été observé par Codex; l’essai utilisateur doit vérifier le démarrage d’un morceau Week 1, d’un morceau Week 2, les difficultés, retry et retour au Freeplay.

**Retour utilisateur après livraison :** v74 est maintenant confirmé fonctionnel dans DuckStation. Cette confirmation sert de base au jalon suivant; elle ne vaut pas validation de v75.

## v75 — scènes Week 1 à la demande et scène Week 2 enrichie

Les pages de texture de gameplay Week 1 ne sont plus des tableaux résidents dans l’ELF. Elles sont regroupées dans `W1SCENE.BIN` (655 360 octets : 9 pages 8bpp et 2 pages 4bpp, même carte VRAM), puis chargées vers la VRAM avec un tampon temporaire de 65 536 octets au démarrage ou lors de la restauration après Week 2. Les petits atlas/pages UI des menus et les poses DJ nécessaires à Freeplay restent des ressources distinctes; la page de logo de menu et les pages BF DJ requises par Freeplay sont relues depuis le paquet de scène quand leur zone VRAM est réutilisée. Les transferts sont synchronisés avant libération du tampon. Les charts et audio restent indépendants et ne sont chargés que pour le titre choisi.

Week 2 a été régénérée à partir des ressources officielles épinglées : décor porté à environ 362×256 pixels PS1 sans étirement (recadrage vertical explicite), sprites Spooky Kids de 72×84, quatre poses officielles d’idle et deux poses par direction de chant; deux poses de danse GF sont incluses dans l’atlas Week 2 afin de garder leur palette correcte. La scène occupe cinq pages 8bpp (deux décor, trois personnages) plus une CLUT de 512 octets : 328 192 octets au total dans `W2SCENE.BIN`. Elle réutilise temporairement les pages VRAM 0, 1, 2, 3 et 8 et la CLUT principale; le retour au menu/à Week 1 restaure les pages Week 1 depuis `W1SCENE.BIN` et sa palette. Cela augmente le chargement à l’entrée de Week 2, sans lecture d’assets concurrente avec la musique. La carte VRAM totale ne change pas : 9 pages 8bpp et 2 pages 4bpp, framebuffers et CLUT compris.

### Mesures et limites

`mipsel-none-elf-size -A` sur l’ELF v75 : `.text 70 384`, `.rodata 793 340`, `.data 2 112`, `.sdata 302`, `.sbss 444`, `.bss 38 816`; somme des sections résidentes **905 398 octets**. Par rapport au plafond de calcul projet de 1 966 080 octets, il reste arithmétiquement 1 060 682 octets avant les allocations dynamiques. Après le tampon audio de 96 Kio, environ 962 378 octets restent pour pile, chart sélectionné et autres allocations; le staging visuel maximal de 64 Kio est utilisé pendant les chargements, avant le streaming musical. Ce sont des budgets calculés, pas une mesure de pic en exécution. Les textures des deux scènes occupent toujours 655 360 octets en VRAM; le contenu Week 2 est paginé depuis le CD et n’augmente donc pas cette carte.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 et création BIN/CUE réussies. BIN 98 666 400 octets, SHA-256 `6C09832B3BB2BABE77EA5411EFE83D5445AA34F189FBB5882C773A3DB1B760F6`; CUE 93 octets, SHA-256 `8579EEF0E6966AFD78659F364593E560C8384148E9258D14FA88B196A842B340` : [BIN v75](../outputs/FNF-PS1-v75-week1-on-demand-week2-enhanced/funkin-ps1-bopeebo-playable.bin) · [CUE v75](../outputs/FNF-PS1-v75-week1-on-demand-week2-enhanced/funkin-ps1-bopeebo-playable.cue). L’utilisateur confirme v75 validée dans DuckStation. Aucun test console réelle.

**Retour utilisateur v75 :** l’utilisateur confirme la validation dans DuckStation. Aucun test console réelle.

## v76 — cadrage Week 2, première Week 3 et transitions de chargement

La capture d’essai v75 signalait le décor Week 2 absent et Monster coupé. Le rendu réutilisait le zoom Week 1 pour tous les stages. Le convertisseur lit maintenant `cameraZoom` dans les données officielles et le transforme avec le même calibrage que Week 1 (`cameraZoom 1.1` → Q8 640). Spooky Mansion utilise Q8 582 (≈2,27×) et Philly Train Q8 640 (2,5×), au lieu des facteurs erronés Q8 256/282.

Le catalogue ajoute Pico, Philly Nice et Blammed, avec charts Easy/Normal/Hard, stems officiels à 43 008 Hz et attribution Pico. La scène Philly est composée depuis les couches officielles de `phillyTrain.json` et les PNG du ciel, de la ville, des lumières, de l’arrière-plan du train et de la rue. Le rig officiel fournit idle et chants de Pico; deux poses de danse GF et l’icône Pico sont incluses. Le train mobile, ses lumières animées et les effets propres à la scène restent différés : ce n’est pas encore une adaptation complète de la Week 3.

Les scènes sont des paquets CD chargés à l’entrée d’un morceau, une page de 64 Kio à la fois. Week 2 : cinq pages 8bpp + CLUT, 328 192 octets. Week 3 : quatre pages 8bpp + CLUT, 262 656 octets. Les semaines réutilisent les mêmes pages VRAM; le contenu de l’autre semaine est restauré au retour Freeplay. Une carte de chargement statique est dessinée dans les deux framebuffers avant les lectures bloquantes d’entrée en jeu, retour Freeplay et relance. La musique ne démarre qu’après lecture du chart et de la scène. Le tampon de streaming audio reste à 96 Kio.

Sections ELF résidentes : 897 242 octets. Sous l’enveloppe de calcul projet de 1 966 080 octets, après le tampon audio de 96 Kio, il reste environ 973 Kio avant le tampon CD (64 Kio), le chart sélectionné, la pile et allocations runtime. Le pic RAM n’est pas mesuré. VRAM générée : 9 pages 8bpp + 2 pages 4bpp, 655 360 octets de textures; le convertisseur vérifie aussi les limites de pages et la carte des framebuffers/CLUTs.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 et création du disque réussies. BIN : 131 942 496 octets, SHA-256 `828489413342768586115C99AD5C1A6B82FC65F88800A17F16308A3BC9E08402` : [BIN v76](../outputs/FNF-PS1-v76-week2-week3-loading/funkin-ps1-bopeebo-playable.bin) · [CUE v76](../outputs/FNF-PS1-v76-week2-week3-loading/funkin-ps1-bopeebo-playable.cue). Diagnostics masqués au démarrage. Build non exécuté dans DuckStation et non validé par l’utilisateur. Essai attendu : Spookeez/South/Monster, retour puis relance; Pico/Philly Nice/Blammed aux trois difficultés; vérifier scène, cadrage Monster, audio et transitions. Aucun test console réelle.

## v77 — démarrage visible et scènes proches du programme

**Retour utilisateur v76 :** le jeu reste bloqué sur le logo PlayStation. L’audit de l’image ISO a montré que `W1SCENE.BIN`, requis au démarrage, commençait au LBA 53 257 (environ 104 Mio dans le disque), après les longs fichiers audio. `main()` attendait plusieurs lectures synchrones de cette scène avant le premier rendu, laissant l’écran BIOS visible pendant le chargement.

v77 déplace `W1SCENE.BIN`, `W2SCENE.BIN` et `W3SCENE.BIN` immédiatement après `FUNKIN.EXE`; `W1SCENE.BIN` commence maintenant au LBA 446. Le programme dessine également « LOADING GAME » dans les deux framebuffers avant l’initialisation audio/CD et les lectures de scène. Cette correction vise la longue attente de démarrage; seul l’essai utilisateur peut confirmer le comportement sur DuckStation.

BIN compilé : 131 944 848 octets, SHA-256 `EFA64D323CF86F3D74FEFBB957A8A509244B1AE2CE36A8A9494AD8E0F67D32D` : [BIN v77](../outputs/FNF-PS1-v77-startup-loading-fix/funkin-ps1-bopeebo-playable.bin) · [CUE v77](../outputs/FNF-PS1-v77-startup-loading-fix/funkin-ps1-bopeebo-playable.cue). Sections ELF résidentes : 897 298 octets. La compilation, la création du disque et l’inspection des entrées ISO/boot sont réussies. **Pas d’exécution DuckStation ni de validation console réelle.** Charger v77 et confirmer si le logo cède la place à « LOADING GAME », puis au titre et au Freeplay.

## v78 — repère GPU au tout début du programme

L’utilisateur a rapporté que v77 reste elle aussi sur le logo Sony. Le premier écran de chargement n’ayant pas été observé, v78 ajoute un repère plus tôt : après `ResetGraph`, elle soumet un remplissage GPU uni, attend `DrawSync`, active l’affichage et fait un `VSync`, avant d’appeler `FntLoad`, d’initialiser le CD/SPU ou de charger une scène. Cette sonde ne lit aucune VRAM et ne change pas les règles ou le rendu du gameplay. L’image ISO conserve les fichiers de scène en tête du disque (W1 au LBA 446).

Compilation PSn00bSDK 0.24 réussie. BIN : 131 944 848 octets, SHA-256 `54411573BB187CBC6E626B9604006CCE37AE4A3020F268EE5AEDF344F1553AC2`. `git diff --check` est propre. [BIN v78](../outputs/FNF-PS1-v78-early-boot-marker/funkin-ps1-bopeebo-playable.bin) · [CUE v78](../outputs/FNF-PS1-v78-early-boot-marker/funkin-ps1-bopeebo-playable.cue).

**Essai utilisateur nécessaire :** charger le CUE v78. Si le logo Sony reste affiché, l’exécution n’a probablement pas atteint le repère placé dans `init_video`; si l’écran devient bleu-noir sans texte, l’amorçage et le GPU fonctionnent mais le blocage précède/est dans l’initialisation des polices; si « LOADING GAME » apparaît, le démarrage est franchi et l’étape suivante pourra isoler le chargement de ressources. Aucun de ces résultats n’est encore observé par Codex; v78 n’a pas été lancée dans DuckStation ni sur console réelle.

## v79 — sonde minimale de démarrage PS-X EXE

L’utilisateur signale que v78 reste sur le logo Sony sans montrer son repère GPU. Audit direct des ISO v75/v78 : les deux contiennent `SYSTEM.CNF` avec `BOOT=cdrom:\FUNKIN.EXE;1`, `TCB=4`, `EVENT=10`, `STACK=801FFFF0`; `FUNKIN.EXE` se trouve au LBA 25 dans les deux disques. Les deux en-têtes commencent par `PS-X EXE`, chargent à `0x80010000`, ont GP `0` et des champs PS-X `memfill address/size` nuls. Entrée/taille déclarée : v75 `PC=0x8001F910`, `0xD3800` octets, fin `0x800E3800`; v78 `PC=0x8001D8B8`, `0xD2000` octets, fin `0x800E2000`. La pile vient de `SYSTEM.CNF`, identique. L’en-tête PS-X ne donne pas l’extrémité BSS pour ces deux exécutables (memfill nul); l’ELF v78 disponible indique `.bss` finissant à `0x800EB1A0`, toujours sous la pile. L’ELF v75 n’est pas conservé dans le workspace, donc sa fin BSS exacte ne peut pas être mesurée à partir de l’ISO seul.

La cible disque v78 embarque bien exactement l’exécutable produit par sa compilation (comparaison octet par octet après extraction ISO). Son en-tête et son adresse d’entrée concordent avec l’ELF. L’absence d’écran après cette version indique que le chargement d’une scène n’explique pas à lui seul le blocage; l’emplacement des scènes n’a pas été modifié pour v79.

v79 est un disque de diagnostic séparé, produit avec le même PSn00bSDK 0.24, GCC MIPS 12.3, fonction CMake `psn00bsdk_add_executable` et `psn00bsdk_add_cd_image`, ainsi que le même `SYSTEM.CNF`. Il ne contient que `SYSTEM.CNF` et un `FUNKIN.EXE` de 10 240 octets. Le programme appelle `ResetGraph`, définit le framebuffer 320×240, soumet un seul remplissage GPU bleu, attend `DrawSync`, active l’affichage puis reste dans `VSync`. Pas de polices, manette, CD, SPU, assets, gameplay ni lecture VRAM. Son ELF a `PC=0x80011664`, plage fichier `0x80010000–0x80012000`, fin BSS `0x80012BFC`; `STACK=801FFFF0`. L’exécutable extrait de l’ISO est identique au fichier `.exe` compilé.

BIN v79 : 369 264 octets, SHA-256 `33DAF8B8C6FA417191038F3DEEA087A0C9F1C22C4735D2E48D3081C131F6E809`. [BIN v79](../outputs/FNF-PS1-v79-minimal-boot-probe/funkin-ps1-boot-probe.bin) · [CUE v79](../outputs/FNF-PS1-v79-minimal-boot-probe/funkin-ps1-boot-probe.cue).

**Essai DuckStation utilisateur en attente.** Une image bleue confirme le démarrage EXE et le GPU avec la chaîne disque commune; un logo Sony persistant oriente le diagnostic vers le démarrage/chargement du disque ou une configuration d’émulateur. Après le résultat, les initialisations seront réintroduites par petites étapes. Aucun essai émulateur par Codex et aucun essai console réelle.

## v80 — checkpoints persistants du démarrage

La v79 fonctionnelle sert de base. L’examen des exécutables confirme que v79 et v78 utilisent le même CRT PSn00bSDK : `_start` installe `$gp` puis saute à `_start_inner`; celui-ci efface `.sbss`/`.bss` jusqu’à `_end`, initialise le heap sous `0x801FFFF8`, parcourt la liste `.ctors` en ordre inverse, puis appelle `main`. Les deux listes `.ctors` contiennent uniquement leur compteur nul et le terminateur (aucun constructeur). La v78 a une BSS de 39 152 octets (`0x800E1850–0x800EB1A0`); la v79 minimale en a environ 4,5 Kio (`0x80011A5C–0x80012BFC`). La v80 porte la BSS à 39 640 octets (`0x800157FC–0x8001F2D4`), proche de celle du jeu, et vérifie qu’un octet en fin de cette zone a bien été remis à zéro avant d’afficher le premier repère. Les étapes CRT pré-main sont donc comparées statiquement et la sonde teste désormais le même ordre de grandeur de BSS; aucun écran pré-main n’est revendiqué.

La v80 émet un aplat de couleur persistant avant et après chaque étape, sans assets et sans lecture CD. Après le premier repère (écran bleu, indiquant que le CRT a appelé `main`, que `ResetGraph` est revenu et que l’environnement GPU est installé), les couleurs signalent le point atteint : bleu vif = avant `FntLoad`; vert = après `FntLoad`; jaune = avant les six `FntOpen`; cyan = après; violet = avant le rendu du petit texte de chargement; rouge sombre = après son flush GPU; orange = avant `SpuInit`; rouge = après; blanc = avant la remise à zéro des 24 voix; rose = après; vert clair = avant `CdInit`; brun = après; bleu moyen = avant l’initialisation manette; bleu ciel = après; vert sombre = toutes les étapes incluses sont revenues. Si le programme se bloque dans une étape, la couleur « avant » correspondante reste affichée. Les appels CD s’arrêtent à `CdInit` : aucune recherche de fichier, lecture de secteur ou scène n’est effectuée. Les paramètres de réinitialisation SPU correspondent maintenant au jeu (`DUMMY_BLOCK_ADDR=0x1000`).

Le CUE v80 contient seulement `SYSTEM.CNF` et `FUNKIN.EXE`; l’exécutable extrait de l’ISO est identique au `.exe` compilé. Taille BIN : 385 728 octets; SHA-256 `48AAB9F563692BEE9BAC0409C4162D820C18C26BAD5F11AFA4713C49BE51B1A7`. Compilation PSn00bSDK 0.24 réussie; aucune exécution DuckStation par Codex. [BIN v80](../outputs/FNF-PS1-v80-startup-stage-checkpoints/funkin-ps1-startup-stage-probe.bin) · [CUE v80](../outputs/FNF-PS1-v80-startup-stage-checkpoints/funkin-ps1-startup-stage-probe.cue).

**Essai utilisateur requis :** indique la couleur stable observée. Si le logo Sony reste, le blocage se situe avant le premier repère (CRT/BSS/heap/constructeurs, `main`, ou initialisation GPU initiale); si une couleur d’étape reste, on connaît la dernière frontière franchie et on isolera cette seule routine ensuite. La v75 et la sonde v79 restent inchangées. Aucun test console réelle.

## v81 — repère de commande CD initiale

L’utilisateur a fourni une capture v80 dont la couleur correspond au vert sombre final (valeur programmée 20/140/100, capture mesurée autour de 30/150/110). Cela confirme que la sonde a dépassé le CRT et est revenue de toutes les étapes incluses en v80, jusqu’à `CdInit` et l’initialisation PAD. v81 repart de cette sonde, ajoute uniquement la commande `CdControlB(CdlPause, 0, 0)` utilisée par le jeu, puis se fige sur un repère persistant : bleu marine = juste avant la commande; jaune-orangé = retour 1 (succès); rose-rouge = retour autre que 1. Aucun `CdSearchFile`, `CdRead`, asset ou scène n’est introduit. Pas de changement gameplay.

Compilation PSn00bSDK 0.24 réussie. Le CUE reste une image de diagnostic à deux fichiers (`SYSTEM.CNF`, `FUNKIN.EXE`). BIN : 388 080 octets; SHA-256 `FBCCD38F2DFD740CB50066ACD4D6196D9831C455D6017037E4AF9C6CA5BBFE20`. [BIN v81](../outputs/FNF-PS1-v81-cd-pause-checkpoint/funkin-ps1-startup-stage-probe.bin) · [CUE v81](../outputs/FNF-PS1-v81-cd-pause-checkpoint/funkin-ps1-startup-stage-probe.cue).

**Essai DuckStation utilisateur en attente :** le jaune-orangé signifie que cette étape a réussi; le bleu marine persistant situe le blocage dans `CdControlB`; le rose-rouge est un retour d’erreur sans blocage. Après confirmation du jaune-orangé, l’étape suivante isolera la première recherche/lecture CD avant d’ajouter le chargement des scènes. Aucun essai console réelle.

## v82 — allocation de staging et recherche `W1SCENE.BIN`

L’utilisateur a confirmé le repère jaune-orangé v81 : `CdControlB(CdlPause)` retourne 1. v82 ajoute uniquement les premières opérations de `load_bopeebo_visuals` après cette commande : allouer un tampon d’une page (65 536 octets), puis exécuter `CdSearchFile("\\W1SCENE.BIN")` et vérifier que la taille retournée est 655 360 octets. L’allocation est libérée après la recherche. Le disque contient le fichier W1SCENE réel pour permettre la recherche, mais la sonde n’appelle ni `CdSetloc`, ni `CdRead`, ni `LoadImage` : aucun secteur de scène n’est transféré en RAM ou VRAM.

Repères après le succès CdlPause : orange = avant l’allocation; cyan = allocation réussie; bleu marine = avant `CdSearchFile`; rose-rouge = fichier introuvable; jaune-orangé = fichier trouvé avec taille inattendue; vert = trouvé à la taille attendue; blanc = tampon libéré et sonde terminée. Ces couleurs restent affichées en cas d’arrêt à l’étape correspondante.

Compilation PSn00bSDK 0.24 réussie, sans avertissement C dans cette cible. L’ISO contient `SYSTEM.CNF`, `FUNKIN.EXE` et `W1SCENE.BIN`; le fichier extrait de l’ISO correspond exactement au `.exe` compilé, et le fichier de scène mesure 655 360 octets. BIN : 1 147 776 octets; SHA-256 `93BAF61444FF80672582D76D5A2BF36B718395D778D88FE36A7E9D4844B90DDA`. [BIN v82](../outputs/FNF-PS1-v82-allocation-file-search/funkin-ps1-startup-stage-probe.bin) · [CUE v82](../outputs/FNF-PS1-v82-allocation-file-search/funkin-ps1-startup-stage-probe.cue).

**Résultat utilisateur :** la v82 reste blanche, ce qui confirme que l’allocation, `CdSearchFile` et la taille attendue ont été franchies. Aucun secteur n’a encore été lu. Aucun essai console réelle.

## v83 — conversion de position et `CdSetloc`

La v83 repart de la sonde v82 et ajoute seulement la conversion de l’adresse du fichier trouvée par `CdSearchFile` (`CdPosToInt` puis `CdIntToPos`) et l’appel `CdControl(CdlSetloc)`. Repères persistants : violet avant conversion, cyan après conversion, bleu marine avant `CdSetloc`, rose-rouge si la commande retourne une erreur, vert si elle réussit, puis blanc après libération du tampon. Le disque inclut le vrai `W1SCENE.BIN` pour retrouver son adresse, mais la sonde **n’appelle pas `CdRead` et ne transfère aucun secteur**.

Compilation PSn00bSDK 0.24 réussie. BIN : 1 150 128 octets, SHA-256 `A5E07A3922D2954781B37F8C38D8E6B193DECF94E0B13D32D720628596B9287B` : [BIN v83](../outputs/FNF-PS1-v83-cd-setloc-checkpoint/funkin-ps1-startup-stage-probe.bin) · [CUE v83](../outputs/FNF-PS1-v83-cd-setloc-checkpoint/funkin-ps1-startup-stage-probe.cue). `git diff --check` est propre. **Résultat utilisateur :** le blanc confirme que `CdSetloc` a réussi et que le tampon a été libéré. Aucun secteur n’a été lu; aucune console réelle testée.

## v84 — lecture synchrone bornée d’un secteur

Après le succès v83, la v84 ajoute une seule lecture de 2048 octets depuis le début de `W1SCENE.BIN`, dans le tampon de staging aligné déjà alloué. Le test désactive explicitement tout callback et utilise `CdRead(1, ..., CdlModeSpeed)`, puis interroge `CdReadSync(1, status)` à chaque VSync pendant au plus 300 images. Le secteur reste en RAM; aucune page n’est envoyée à la VRAM, aucun rendu ni gameplay n’est chargé. Pour vérifier que la lecture a livré le bon contenu, la sonde calcule le CRC-32 des 2048 octets et le compare à `0x569EEEF7`, relevé sur le premier secteur du `W1SCENE.BIN` généré pour cette image. En cas de timeout, elle annule la lecture et attend l’arrêt du lecteur avant de libérer le tampon.

Repères : bleu marine avant `CdRead`; rouge si la lecture ne démarre pas; cyan si elle démarre; magenta si `CdReadSync` renvoie une erreur/annulation; jaune-orangé si le délai de polling expire; orange si la lecture finit mais le CRC ne correspond pas; blanc si le secteur est lu et son CRC correspond. Le callback n’est pas testé dans cette version et reste une étape séparée.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja et création BIN/CUE réussies. BIN : 1 150 128 octets, SHA-256 `740D476B32306D579BEC5C046993640A259E8B579FAD66599A3308EEF0372226` : [BIN v84](../outputs/FNF-PS1-v84-cd-read-first-sector/funkin-ps1-startup-stage-probe.bin) · [CUE v84](../outputs/FNF-PS1-v84-cd-read-first-sector/funkin-ps1-startup-stage-probe.cue). **Résultat utilisateur :** blanc stable, ce qui confirme que la lecture d’un secteur et son CRC ont réussi. Aucun transfert VRAM ni test console réelle.

## v85 — callback de lecture CD

La v85 repart du chemin confirmé en v84 et ajoute un callback autour de la lecture d’un seul secteur. Le callback ne fait que mémoriser le nombre d’appels, l’événement reçu et les quatre premiers octets de réponse; `CdReadSync(1, status)` reste interrogé pour borner l’attente à 300 images. L’image attend un callback unique avec `CdlDataReady` (valeur enum 1, observée auparavant), un pointeur de réponse non nul et le même CRC-32 `0x569EEEF7`. Le commentaire de l’en-tête `CdReadCallback` du SDK 0.24 décrit pourtant `CdlComplete`/`CdlDiskError`; cette sonde tranche le comportement effectif du callback de `CdRead` sur le parcours utilisé. Aucun transfert VRAM, audio ou gameplay n’est effectué. Repères : violet avant l’enregistrement du callback; bleu marine avant `CdRead`; rouge si le démarrage échoue; cyan si démarré; magenta si `CdReadSync` rapporte erreur/annulation; jaune-orangé au timeout; orange si le nombre de callbacks n’est pas 1; violet clair si l’événement diffère; bleu si le payload est nul; rouge vif si le CRC diffère; blanc si callback unique, événement attendu, payload et CRC passent. Le timeout annule la lecture et attend l’arrêt du lecteur avant de libérer le tampon.

Build PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja réussi. BIN : 1 150 128 octets, SHA-256 `156B7043630F6E9142906B04D9B180D1FAB92C9318F45BD50D5A6FBC334EA3CB` : [BIN v85](../outputs/FNF-PS1-v85-cd-read-callback/funkin-ps1-startup-stage-probe.bin) · [CUE v85](../outputs/FNF-PS1-v85-cd-read-callback/funkin-ps1-startup-stage-probe.cue). **Résultat utilisateur :** bleu stable, donc un callback a été reçu avec l’événement attendu `CdlDataReady` (1), mais son pointeur payload était nul. La v85 s’arrête avant le contrôle CRC dans ce cas; la lecture avec callback n’est donc pas encore validée par contenu. Aucun test console réelle.

## v86 — distinguer payload nul et résultat de lecture

La v85 a atteint le repère bleu : callback unique et événement attendu, payload nul. La v86 retire le pointeur payload comme condition d’échec, conserve le nombre d’appels et l’événement, puis vérifie effectivement le CRC-32 du secteur en RAM. Elle différencie le succès avec payload non nul (blanc) du succès avec payload nul (vert). Les autres couleurs continuent à séparer échec de démarrage, erreur/timeout, callback absent/multiple, événement inattendu et CRC incorrect. Aucun secteur supplémentaire ni transfert VRAM n’est ajouté.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja réussie. BIN : 1 150 128 octets, SHA-256 `E460EC4F2A6668CF2F2C0C696CDD35C60EB35E3DDF801692C25F85F404D0FD63` : [BIN v86](../outputs/FNF-PS1-v86-cd-read-null-payload-check/funkin-ps1-startup-stage-probe.bin) · [CUE v86](../outputs/FNF-PS1-v86-cd-read-null-payload-check/funkin-ps1-startup-stage-probe.cue). **Résultat utilisateur :** vert. Le callback unique a donc fourni `CdlDataReady`, et le secteur lu malgré le payload callback nul correspond au CRC attendu. Aucun transfert VRAM ni test console réelle.

## v87 — lecture d’une page de scène de 32 secteurs

Après le résultat vert v86, v87 augmente la lecture d’un secteur à une page 8bpp complète (32 secteurs, 65 536 octets) dans le même tampon aligné. Elle réutilise `CdSetloc`, `CdRead`, un callback unique `CdlDataReady` et le polling `CdReadSync(1)` borné, puis vérifie le CRC-32 `0xA3BEABD8` calculé sur les premiers 65 536 octets de `W1SCENE.BIN`. Le payload callback peut rester nul; dans ce cas, vert indique callback et page conformes, blanc indique payload non nul et CRC conforme. Aucun `LoadImage` ni transfert VRAM. Cette sonde teste un bloc de même taille qu’une page du chargeur, sans encore parcourir les onze pages.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja et BIN/CUE réussis. BIN : 1 150 128 octets, SHA-256 `9C11E7B7B5BA6530DA14B608A82053C646291E74363CA7E1D591455FB3E7638E` : [BIN v87](../outputs/FNF-PS1-v87-cd-read-one-scene-page/funkin-ps1-startup-stage-probe.bin) · [CUE v87](../outputs/FNF-PS1-v87-cd-read-one-scene-page/funkin-ps1-startup-stage-probe.cue). **Résultat utilisateur :** vert confirme le callback et le CRC de la première page de 32 secteurs, avec payload callback nul. Aucun transfert VRAM ni test console réelle.

## v88 — lecture séquentielle complète de `W1SCENE.BIN`

v88 lit les 320 secteurs du paquet (655 360 octets) en 11 blocs correspondant à la géométrie réelle : neuf pages 8bpp de 32 secteurs et deux pages 4bpp de 16 secteurs. Le même tampon RAM de 65 536 octets est réutilisé pour chaque bloc; les commandes `CdSetloc`/`CdRead`, callback unique `CdlDataReady` et polling borné sont vérifiés à chaque étape. Un CRC-32 continu compare le fichier reconstitué à `0xF32FB433`. Aucun transfert VRAM n’est fait. Vert = tout le fichier et les callbacks sont corrects avec payload nul; blanc = tous les payloads sont présents et le CRC passe. Les couleurs d’échec distinguent commande de position, démarrage, sync/timeout, callback et CRC.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja et création BIN/CUE réussies. BIN : 1 150 128 octets, SHA-256 `849D0E9EA5ACBA251B3F03890D40D0B4C765E1E6F4A9871CDC6D4C8FB75DA6BE` : [BIN v88](../outputs/FNF-PS1-v88-read-full-week1-scene/funkin-ps1-startup-stage-probe.bin) · [CUE v88](../outputs/FNF-PS1-v88-read-full-week1-scene/funkin-ps1-startup-stage-probe.cue). **Résultat utilisateur : vert**, confirmant la lecture des 320 secteurs, les onze blocs, callbacks et CRC avec payloads callback nuls. Aucun transfert VRAM ni test console réelle.

## v89 — première page de scène transférée et dessinée

Après la confirmation verte v88, v89 isole la première page de scène 8bpp. Elle relit 32 secteurs dans le tampon de 64 Kio, valide le callback unique `CdlDataReady` et le CRC `0xA3BEABD8`, transfère l’image vers `(384,0)` avec une zone VRAM de 128×256 mots, puis charge la CLUT 8bpp officielle à `(0,496)`. `DrawSync(0)` précède et suit les transferts. La sonde soumet ensuite un quad texturé couvrant 320×240 avec UV 0–255 × 0–191, page `getTPage(1,0,384,0)` et cette CLUT. Un petit carré vert est dessiné ensuite pour distinguer le quad visible d’une simple primitive présente dans le code. Les couleurs d’étape restent visibles si l’exécution s’arrête avant le rendu final. Aucun gameplay, musique ou autre page n’est chargé.

Compilation et création BIN/CUE PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja réussies. BIN : 1 150 128 octets, SHA-256 `7E474DDAAB0C79555737DFDDA6627446DBD4DB50A07E209FF74B13EF1B282BFC` : [BIN v89](../outputs/FNF-PS1-v89-first-scene-vram-upload/funkin-ps1-startup-stage-probe.bin) · [CUE v89](../outputs/FNF-PS1-v89-first-scene-vram-upload/funkin-ps1-startup-stage-probe.cue). **À essayer par l’utilisateur dans DuckStation** : Codex n’a pas observé le rendu ni la stabilité dans l’émulateur. Aucun test console réelle.

## Audit v75 → v76 — artefacts comparés, sources historiques manquantes

Les deux BIN/CUE sont disponibles et ont été parcourus comme disques MODE2/2352. Leurs ISO ont le même `SYSTEM.CNF` (boot `cdrom:\FUNKIN.EXE;1`, pile `801FFFF0`), et l’exécutable au LBA 25 dans les deux cas. Les en-têtes PS-X annoncent `load=0x80010000`; leurs champs BSS/memfill sont nuls. v75 embarque un EXE de 868 352 octets (PC `0x8001F910`, texte `0xD3800`), v76 un EXE de 860 160 octets (PC `0x8001D864`, texte `0xD1800`). Sans les ELF historiques, ces en-têtes ne suffisent pas à comparer la fin BSS, le heap ou les constructeurs avant le premier repère GPU.

Les contenus communs de menus, flux Bopeebo, charts Week 1/2 et paquets W1/W2 ont des hashes identiques. v76 ajoute les pistes et neuf charts de Pico/Philly Nice/Blammed, plus `W3SCENE.BIN` (262 656 octets). Le BIN passe de 98 666 400 octets (v75, SHA-256 `6C09832B3BB2BABE77EA5411EFE83D5445AA34F189FBB5882C773A3DB1B760F6`) à 131 942 496 octets (v76, SHA-256 `828489413342768586115C99AD5C1A6B82FC65F88800A17F16308A3BC9E08402`). À cause du contenu ajouté avant les scènes dans l’ordre ISO, W1 se déplace de LBA 39 258 à 53 257, et W2 de LBA 39 097 à 53 096. Les notes v76 indiquent aussi des données de cadrage par stage, une scène Philly en couches, et une carte de chargement dessinée avant les lectures synchrones. Le total ELF documenté diminue pourtant (905 398 → 897 242 octets); tampon audio déclaré inchangé à 96 Kio.

La reconstruction exacte **n’est pas possible avec les fichiers disponibles** : le dépôt est au commit `facbf12` avec les changements postérieurs non engagés; aucun snapshot source/ELF/map/CMakeCache v75 n’a été trouvé. Le dossier nommé `ps1/build/freeplay-v76-week2-week3-loading` a été réutilisé : son BIN actuel est le v78 connu (SHA-256 `54411573BB187CBC6E626B9604006CCE37AE4A3020F268EE5AEDF344F1553AC2`) et son EXE ne correspond pas à celui de l’ISO v76. Son cache de configuration contient des réglages diagnostics OFF et des chemins d’assets/temporaires, mais ne représente plus la compilation v76. Le cache v75 manque également. Les références de source d’assets disponibles pointent vers le sous-module épinglé `assets` `724eba9de9e76761d9cefd52169926bc51c760a5`.

Le déplacement des scènes a déjà été tenté dans v77 et le logo est resté bloqué; v78 n’a pas montré son marqueur GPU précoce. Ces builds ont changé plusieurs éléments ensemble. **Aucune différence n’est donc attribuée comme cause.** Pour le prochain test causal dans le véritable exécutable, il faut retrouver les sources et configurations de build v75/v76 (ou un commit/worktree exact pour chacun); alors un unique groupe pourra être retiré/réintroduit avec marqueurs autour de ses étapes, sans changer les autres paramètres. La sonde v89 reste indépendante et ne prouve rien sur cette régression.

## Week 4 — première intégration à essayer (v100, 2026-10-30)

La branche ajoute trois morceaux au catalogue Freeplay : Satin Panties, High et M.I.L.F, chacun avec Easy/Normal/Hard. Les charts sont convertis depuis les assets épinglés. Les morceaux sont chargés indépendamment; le contenu Week 4 n’est pas gardé simultanément avec les autres scènes. Les entrées Week 4 sélectionnent Mom, Girlfriend et la scène correspondante.

Chaque morceau utilise un flux VAGi quatre canaux à 43 008 Hz : instrumental L/R, Mom mono et BF mono. Circle garde la coupure indépendante de BF. Le paquet de scène converti utilise trois pages 8bpp (196 608 octets) et une CLUT de 512 octets, en réutilisant les emplacements de textures gameplay existants. Le chargement a un tampon de staging temporaire de 65 536 octets, libéré après l’upload; le ring audio reste à 96 Kio et aucun chargement CD de scène n’est lancé en parallèle de la musique.

Compromis de cette première passe : décor statique et assemblé pour la PS1, avec un sous-ensemble de poses officielles de Mom et GF. Les voitures/henchmen et leurs animations ne sont pas encore intégrés. M.I.L.F Hard contient 674 notes; la capacité a été augmentée pour le chart le plus dense sans changer les règles de gameplay.

Build v100 : snapshot source local `adfa621` sur `ps1-port` (parent `facbf1243875fe7e24819eff87d1879527f00584`); `fb3fde6` ne contient que du nettoyage d’espaces/blancs après compilation. Le BIN a été produit depuis le contenu de `adfa621`. Assets épinglés à `724eba9de9e76761d9cefd52169926bc51c760a5`. PSn00bSDK 0.24, GCC MIPS 12.3, CMake 4.5 et Ninja. Le chemin de build a réutilisé les ressources converties de v90 et le paquet Week 4; le dry-run n’a montré que compilation C, édition de liens et fabrication de l’image disque, sans reconversion W1–W3 ni réencodage audio.

BIN : 169 296 960 octets, SHA-256 `7083695845D2726FFBC446D5892446DF571CFF499EFC716B8AD1453C9C3B8AFE`. CUE : 89 octets, SHA-256 `564DFCEE24E84C9F680CF4A1F43AC09E5DE64B56C9363CA7D183B09081602890`. `SYSTEM.CNF` a été réordonné en première entrée du répertoire ISO; l’exécutable `FUNKIN.EXE` est présent, signature PS-X EXE, entrée `0x8001DEB4`, chargement `0x80010000`.

Bilan mémoire statique : `.text + .data + .bss` = 899 514 octets; ring audio 96 Kio; staging scène 64 Kio temporaire. Le pic comptabilisé estimé est d’environ 1,07 Mio sur 2 Mio, mais ce n’est pas une mesure réelle du pic RAM et n’inclut pas précisément toutes les allocations/stack transitoires. Les pages scène occupent 196 608 octets VRAM réutilisés; CLUT 512 octets. Le double tampon musical SPU existant reste à 16 Kio.

**Validation :** l’utilisateur confirme maintenant que v100 est parfaite et stable après ses essais DuckStation. Pas de mesure de dérive audio ni de test console réelle.

## Week 5 — premier build jouable à essayer (v101, 2026-10-30)

Le catalogue ajoute Cocoa, Eggnog et Winter Horrorland avec leurs charts officiels Easy/Normal/Hard. Les trois pistes VAGi sont à 43 008 Hz, avec instrumental stéréo, voix BF et voix opposées (Parents pour Cocoa/Eggnog, Monster pour Winter Horrorland). Circle continue de couper BF seul. Le chargement sélectionne un morceau à la fois; ses flux restent lus depuis le CD. Les variantes Erect/Pico de Week 5 ne sont pas incluses.

La scène utilise des ressources officielles de Noël et du Mall, converties en trois pages 8bpp réutilisant les pages gameplay existantes (deux pages de décor, une page d’animations). Mom/Dad, Monster et GF Christmas ont des poses chant/repos ou danse converties depuis les rigs épinglés. Le décor reste statique dans cette première intégration, Santa utilise une pose fixe, et BF conserve le sprite existant : aucun sprite BF Christmas n’est présent dans la révision d’assets épinglée. Les sprites Mom/Dad/Monster/GF sont ramenés à 64×64; leur taille et leur ancrage en jeu restent à confirmer par l’utilisateur.

Ressources et mémoire : paquet scène 197 120 octets sur disque (3 × 65 536 octets + CLUT 512 octets); transfert par page avec tampon RAM temporaire de 65 536 octets, libéré après chargement. Le ring audio demeure à 96 Kio. Le chart maximal reste celui de M.I.L.F Hard (674 notes); les charts Week 5 comptent 279–458 notes. `.text + .data + .bss` de l’ELF v101 : 901 742 octets. Ces allocations sont statiques ou calculées; le pic RAM complet n’a pas été mesuré. Les trois pages et leur palette remplacent le contenu des mêmes emplacements VRAM employés par les autres scènes, puis sont restaurées au retour au Freeplay. Quatre canaux SPU musicaux et les voix réservées aux effets restent inchangés.

Build séparé : `ps1/build/week5-v101`; CUE destiné au test utilisateur : `ps1/build/week5-v101/delivery/funkin-ps1-week5-test-v101.cue`. BIN : 208 262 544 octets, SHA-256 `658FBED595201177D1931FB14DFB84FFDBF1056963FC7125CC5AE68ED073AF12`. CUE SHA-256 `0D2E7C2829827366B413FF6B7D31A4245934F123C06DAE6E8FD532FCC41494D7`. Le disque contient 74 fichiers; l’ISO a `SYSTEM.CNF` comme première entrée de fichier, et l’exécutable extrait correspond à l’EXE compilé. L’en-tête PS-X EXE déclare PC `0x8001E5B0`, chargement `0x80010000`, texte `0xD3000`. Les diagnostics sont désactivés par défaut.

La génération a réutilisé les ressources v90 et Week 4 déjà converties, ainsi que les VAGi Week 5 préproduits; le dry-run n’a planifié que compilation, édition de liens et image disque. Deux avertissements `volatile` viennent du `stream.c` externe de PSn00bSDK 0.24. Compilation et contrôles ISO/statique réussis. Le CUE n’a pas encore été exécuté dans DuckStation par Codex : parcours Freeplay, choix des trois morceaux/difficultés, animation, son, mute BF, transitions et stabilité sont à vérifier avec l’utilisateur. Pas de test console réelle.

## Week 6 — premier build jouable à essayer (v103, 2026-10-30)

Ajoute les trois chansons classiques Week 6 au Freeplay : Senpai, Roses et Thorns, chacune avec charts Easy/Normal/Hard. Les neuf charts proviennent de la révision d’assets épinglée `724eba9de9e76761d9cefd52169926bc51c760a5`. Les pistes VAGi synchronisées à 43 008 Hz contiennent instrumental L/R, BF mono et voix opposée mono; Circle conserve le mute BF. Les autres entrées du catalogue ne changent pas.

La scène utilise les décors officiels de l’école normale et maléfique, Senpai/Senpai angry/Spirit, BF pixel, GF pixel, icônes et flèches/récepteurs pixel officiels. La scène est préconvertie en cinq pages 8bpp et chargée sur demande. Ce premier rendu reste un compromis : décor composé et statique, sélection d’une pose par direction plutôt qu’animation complète des rigs, deux poses rythmiques de GF et corps de tenues en barres colorées bordées. Les décors animés, les animations complètes et les terminaisons pixel officielles des tenues restent à améliorer.

Les pages graphiques W6 remplacent cinq emplacements VRAM gameplay partagés (320 Kio) et une CLUT de 512 octets; elles sont restaurées au retour au Freeplay ou à la relance. Le chargement utilise un tampon temporaire de 64 Kio. Le ring audio reste à 96 Kio, le double tampon SPU à 16 Kio et les quatre voix de streaming ainsi que le pool SFX existant sont inchangés. L’ELF v103 occupe 904 910 octets en `.text + .data + .bss`; le pic RAM complet n’a pas été mesuré. Les trois pistes occupent 29 054 976 octets au total; le débit CD moyen de streaming est d’environ 99 kB/s par morceau. Aucun chargement de scène n’est concurrent avec le streaming musical. `W6SCENE.BIN` fait 328 192 octets, SHA-256 `251B525DCB437314A4ABB269B1D324AD8C48E5169035590209B4CDF2157AC730`.

Source identifiable : commit `ee0bbd668eead59b1e77d06a0b3ab5a63e69b823` sur `ps1-port`, parent Week 5 `e396110b6569a89263b5687c50750e3e62636d3a`. Build distinct `ps1/build/week6-v103`; paquet converti conservé dans `ps1/build/week6-assets-v102`. Le plan Ninja après réutilisation des ressources W1–W5 et du paquet W6 préconverti ne contient que deux compilations C, l’édition de liens et la création ISO. Deux avertissements de qualification `volatile` proviennent de `stream.c` du SDK.

BIN : 242 070 192 octets, SHA-256 `B70F551664AEBA18EA80F38DE0E9ACF37E65F162BB2D7F6BF80A123345B5411B`. CUE : SHA-256 `926B6307DD0A57E894F2E7C83EFB0F70822BFC8C4E78DC3F7EC8E26A4BAAC25F`. Le répertoire ISO contient 87 fichiers et commence par `SYSTEM.CNF`; l’EXE extrait est identique à l’exécutable compilé. Les overlays de diagnostic sont masqués par défaut.

**À vérifier par l’utilisateur dans DuckStation :** entrée Freeplay, lancement Normal/Easy/Hard de chaque morceau, audio/voix, charts et tenue, mute BF, retour au Freeplay et relance. Compilation et contrôle statique réussis; aucune exécution en émulateur ni validation utilisateur v103 n’est revendiquée. Aucun test console réelle.

## Week 7 — premier build d’essai (v104, 2026-10-30)

Ajoute Ugh, Guns et Stress au Freeplay, chacune avec les charts classiques Easy, Normal et Hard issus du sous-module `assets` épinglé à `724eba9de9e76761d9cefd52169926bc51c760a5`. Les flux VAGi gardent le format musical du port : 43 008 Hz, instrumental L/R, voix BF mono et voix Tankman mono. Circle continue de couper BF uniquement. Les variantes Pico/Erect et leurs présentations spécifiques restent hors catalogue jouable.

La première scène Week 7 est produite à la demande depuis un paquet séparé de trois pages 8bpp et une CLUT : deux pages de décor Battlefield et une page d’acteurs. Elle utilise les couches officielles de Week 7, les rigs Tankman et BF, les deux premières poses de danse de GF Tankmen extraites de son atlas Sparrow officiel, et les icônes Tankman/BF. Le décor est fixe; les chants utilisent un petit sous-ensemble de poses et GF alterne ses deux poses au rythme. Les fumées, tanks/vehicules animés, caméra et animations complètes ne sont pas encore portés : ce build est une base jouable à examiner, pas un rendu final.

Le chart le plus dense est Stress Hard à 905 notes; la capacité statique est donc 905. Les neuf charts font 72 288 octets ensemble. Les trois flux font 34 691 072 octets au total (Ugh 8 570 880; Guns 13 862 912; Stress 12 257 280), environ 99 kB/s chacun en moyenne. Ils sont chargés/streamés morceau par morceau; l’ensemble du catalogue n’est pas conservé en RAM.

Budgets : l’ELF mesure `.text + .data + .bss = 907 114` octets, soit +2 204 par rapport à v103. La capacité d’état de notes passe de 674 à 905 octets (+231). Le ring d’audio existant fait 96 Kio; une seule chart est chargée (max 11 080 octets); le transfert de scène utilise temporairement un tampon de 64 Kio, libéré après chargement. Estimation indicative d’environ 1,08 Mio pour ces postes et l’image ELF, hors pile, fragmentation et allocations runtime non comptabilisées; aucun pic RAM n’a été mesuré à l’exécution. En VRAM, trois pages remplacées/réutilisées (192 Kio) et la CLUT partagée (512 octets); aucun chargement de scène ne concurrence le stream. Le double tampon musique SPU de 16 Kio et les voix réservées au streaming/SFX restent inchangés.

Build distinct `ps1/build/week7-v104`; paquet officiel converti conservé dans `ps1/build/week7-assets-v104`. Le dry-run annonçait seulement la compilation de `spu_probe.c`, l’édition de liens et l’image disque. PSn00bSDK 0.24, GCC MIPS 12.3, CMake 4.5, Ninja; aucune bibliothèque SDK propriétaire ni ressource officielle n’est ajoutée au dépôt. Le BIN livré est construit à partir du contenu v104 puis réordonné dans un dossier séparé afin que `SYSTEM.CNF` soit la première entrée racine; aucun fichier précédent n’a été remplacé. L’ISO contient 100 fichiers; `FUNKIN.EXE` extrait est byte-identique à l’exécutable lié et porte une signature PS-X EXE valide.

Manifeste détaillé et hashes : [docs/PS1_WEEK7_V104.md](PS1_WEEK7_V104.md). Les sources du build sont identifiées par le commit local v104 `505e6038eb0a685afd725b450d5050417c7a3aa6`; les fichiers convertis et le disque restent sous `ps1/build/` et sont ignorés par Git.

**État :** compilation réussie et vérifications statiques du CUE/ISO/exécutable réussies. La scène, le parcours Freeplay, les neuf charts, les voix, le mute, la fin/reprise et la stabilité n’ont pas été observés dans DuckStation pour v104. Aucun test console réelle. L’essai manuel utilisateur est requis avant de considérer Week 7 validée.

## WeekEnd 1 classique — premier build d’essai v105b

Ajoute Darnell, Lit Up, 2Hot et Blazin, Easy/Normal/Hard, hors Pico Erect et Spaghetti. Les quatre entrées Freeplay existantes deviennent jouables. Charts : timings, lanes, holds, tempo et focus chart encodés; les notes de combat custom de Blazin ne sont pas portées comme mécaniques spécifiques. Audio quatre canaux VAGi à 43 008 Hz; Circle coupe la voix Pico sur les trois premiers morceaux; Blazin n’a pas de voix dans les assets épinglés. Décors statiques et poses partielles issus des assets officiels.

Build compilé et contrôlé statiquement, non testé dans DuckStation. Le BIN contient 117 fichiers, `SYSTEM.CNF` en première entrée, et l’exécutable extrait correspond au linker. Voir [le manifeste v105b](PS1_WEEKEND1_V105.md) pour le CUE, les hashes, les budgets et les limites connues.

## Week 2 — cadrage 4:3 et GF calée sur l’audio (v106, essai)

Les captures actuelles montraient les chanteurs rognés et peu de décor. La composition Week 2 utilisait le zoom Q8 582 (2,27×) en 320×240. Ce build réduit uniquement le zoom de scène à Q8 384 (1,5×) afin d’inclure davantage du décor et les personnages autour de GF. Les positions et profondeurs restent celles du stage officiel `spookyMansion.json`; charts, caméra événementielle, rendu des notes, santé, audio et commandes ne changent pas.

Toutes les scènes jouées sélectionnent déjà la danse de GF depuis l’horloge audio et la carte de tempo du chart, y compris les variations de BPM de Monster. L’écran titre utilisait cependant un compteur de frames à 100 BPM. Il utilise maintenant `Stream_GetSamplesPlayed()` et le BPM 102 de `freakyMenu-metadata.json` pour séquencer les mêmes poses échantillonnées. Le rythme du contour des options reste séparé de l’animation de GF.

Seul `spu_probe.c` a été recompilé. Le dry-run annonçait deux objets C, le lien puis l’image disque. Aucun asset, chart, stem, décor ni scène n’a été reconverti. Les paquets Week 1–3 du build v90 sont réutilisés avec les mêmes SHA-256; la carte VRAM, la mémoire SPU et les flux CD sont inchangés. Le total ELF `.text/.rodata/.data/.sdata/.sbss/.bss` est 922 442 octets. Le CUE distinct utilise une copie ISO réordonnée pour avoir `SYSTEM.CNF` puis `FUNKIN.EXE` comme deux premières entrées racine; le BIN généré brut est conservé.

**État :** compilé et contrôlé statiquement, essai manuel DuckStation en attente. Aucun rendu v106 n’a encore été observé par Codex ou validé par l’utilisateur, et aucune console réelle n’a été testée. Voir le [manifeste v106](PS1_WEEK2_V106.md) pour le chemin du CUE, les hashes et les détails de compilation.
