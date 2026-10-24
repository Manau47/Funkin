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

Le fichier `Psxdev.zip` fourni (environ 419 Mo) contient des installateurs fragmentés CodeWarrior pour PlayStation et PsyQ, dont PsyQ 4.6. Ils n'ont pas été extraits ni exécutés. Une chaîne PSn00bSDK est retenue pour ce prototype : compilateur GCC MIPS, CMake et construction en ligne de commande, sans intégrer de SDK au dépôt. C'est un choix de démarrage fondé sur la reproductibilité et l'outillage accessible, pas une preuve que chaque capacité audio, vidéo ou CD nécessaire à l'adaptation est déjà couverte. Il faudra valider séparément les limites de mémoire, l'accès audio CD, les contrôleurs, le média de livraison et les performances.

`ps1/` contient le banc d'essai d'affichage et de lecture de manette. L'architecture réserve un enregistrement d'état à chaque joueur; seul le premier contrôleur est affiché pour l'instant.

## Prochaines étapes

1. Installer PSn00bSDK, CMake et Ninja hors du dépôt, compiler `ps1/` et démarrer l'image cue/bin dans un émulateur.
2. Vérifier la détection, la polarité active-bas des boutons et la fluidité vidéo dans l'émulateur, puis sur console si du matériel est disponible.
3. Choisir un morceau et difficulté représentatifs; définir un format de chart compilé et mesurer le budget RAM, CD et audio.
4. Implémenter un prototype jouable avec quatre voies, judgement, notes tenues, score/vie et synchronisation instrumentale/voix; comparer au jeu de référence.
5. Évaluer les graphismes PS1, les scènes, personnages et dialogues, puis préserver progressivement semaines et modes compatibles.
6. Ajouter et tester les contrôleurs et états de gameplay du second joueur dans une étape séparée.

## Résultats de cette étape

- Inspecté : dépôt propre sur `main`, consignes de compilation, modules de gameplay ciblés, sous-modules et licences; contenu de l'archive inventorié sans exécution.
- Implémenté : branche locale `ps1-port`, projet C PS1 isolé, preset CMake reproductible, configuration d'image de disque et notes de portage.
- Compilé : non. CMake/Ninja et le SDK ne sont pas installés dans l'environnement courant.
- Exécuté/testé : aucun émulateur PS1 détecté; donc aucune validation d'exécution ou de manette.
- À vérifier : compilation réelle, format de l'image produite, rendu/lecture de manette en émulateur puis console, et compatibilité audio/mémoire du jeu.
