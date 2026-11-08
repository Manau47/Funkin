# Week 5 — premier relevé de composition (v175)

## Résultat

Le premier jet réglé dans l’éditeur v174 a été lu directement dans le scanner mémoire DuckStation, puis repris comme composition de démarrage pour la scène Christmas Mall. L’éditeur reste actif pour une seconde passe. Carré réinitialise maintenant le calque sélectionné à ces valeurs de départ. Evil Mall garde ses réglages neutres.

Les X/Y sont les unités de déplacement de l’éditeur dans l’espace de scène, pas des pixels écran. Les échelles sont les facteurs Q8 de l’éditeur (`256 = 100 %`). L’ordre des valeurs est l’enum `W5_EDIT_*`, pas nécessairement l’ordre visuel du panneau.

| Calque | X | Y | Échelle |
|---|---:|---:|---:|
| Fond | -60 | -45 | 75 % |
| Caméra | -25 | -20 | 100 % |
| Arbre | -30 | -30 | 100 % |
| Neige | +35 | 0 | 62,5 % |
| GF | -5 | 0 | 112,5 % |
| Adversaire (Dad) | 0 | 0 | 137,5 % |
| BF | +15 | -5 | 100 % |
| Foule supérieure | -80 | -55 | 137,5 % |
| Escalator | -115 | -80 | 150 % |
| Foule inférieure | -15 | -5 | 112,5 % |
| Santa | -5 | 0 | 112,5 % |

La variante Evil Mall était affichée dans la seconde rangée du tableau mémoire : tous ses déplacements restent à 0 et toutes ses échelles à 100 %.

## Caméra

Le code v174 suit déjà les ancrages édités de l’acteur ciblé : les déplacements de l’adversaire, de BF et de GF sont ajoutés à leurs cibles de focus respectives après le calcul du focus fluide. Le décalage indépendant relevé pour le calque Caméra (`-25/-20`, échelle `100 %`) est également conservé et s’applique ensuite à la projection de la scène. Cette passe reprend ces valeurs et ce chemin existant ; elle n’ajoute pas une seconde correction arbitraire à la caméra. Les cibles restent à observer dans DuckStation avec le nouveau placement.

## Source et build

- Base Git : branche `ps1-port`, commit `7057882fa4c481fb878de4cc27d3a827179f7ddd`, avec les modifications locales de l’éditeur v174.
- Changement v174→v175 limité à `ps1/spu_probe.c` : valeurs initiales Christmas Mall, valeurs de remise à zéro correspondantes. Pas de changement de règles de jeu, de scène Evil, d’animations, de charts ou d’audio.
- Options conservées : éditeur Week 5 ON, démo de scène ON, diagnostics de démarrage OFF, Dad lanes ON, probes QA OFF.
- PSn00bSDK 0.24 et GCC MIPS 12.3. Le dry-run incrémental ne planifiait que `spu_probe.c`, le `stream.c` du SDK, le lien et la création du disque. Aucune conversion d’asset/audio/chart.
- Compilation et création de l’image réussies ; deux avertissements `volatile` préexistants dans `stream.c` du SDK.
- Paquet `week5-scene.bin` réutilisé sans changement, SHA-256 `827FC943FC0429785B3C61C0CA4740E9812063498B1568D1AFFB34D1DFA85245`.
- `stream-playable.vag` réutilisé sans changement, SHA-256 `205EA3A13D2EBA739E250F4DA41AA44E5EABF78202EE0A1F81AB02B8647026D0`.
- BIN livré : SHA-256 `C50264FFB7CDD08848A7DFC1E981FCEAE5C7CFAB05E5F8F48B696DB759CD7D90`, 339 861 648 octets. CUE : `65A155397AB1B2F21B6525C8734953826EF9CD9384AD28DB7751C7CEE03EC126`.
- Le CUE référence le BIN du même dossier. Le répertoire racine ISO a été réordonné comme les builds PS1 précédemment préparés : `SYSTEM.CNF;1` entrée 1, `FUNKIN.EXE;1` entrée 2, avec EDC/ECC recalculés sur les secteurs touchés.

## État de validation

Le relevé source des valeurs a été observé dans le scanner mémoire DuckStation sur v174. v175 est compilé et son disque est produit. Le nouveau disque n’a pas encore été lancé dans DuckStation ; aucune validation de la composition ou de la caméra dans v175 n’est revendiquée, et aucune console réelle n’a été testée. L’escalator et la foule sont repris aux échelles définies par l’utilisateur, mais leur détail reste le point différé signalé pour une passe ultérieure.

## Reproduction et archive

Le snapshot exact (`spu_probe.c`, `CMakeLists.txt`, `CMakeCache.txt`, commande de build et diff v174→v175), l’ELF, le MAP et le `FUNKIN.EXE` sont dans `C:/Users/Manau47/Documents/Codex/week5-first-pass-v175-delivery/`. Le BIN/CUE v174 est conservé dans son dossier original et n’a pas été écrasé. Aucun SDK, asset source ou secret n’est copié dans le dépôt.
