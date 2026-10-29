# Audit de récupération des builds PS1 v75/v76

Date de l’inventaire : 2026-10-30. Cet audit distingue les artefacts présents des sources exactes retrouvées. Il ne reconstitue pas un état historique absent.

## État sauvegardé

- Le snapshot des sources actuellement présentes dans le checkout a été publié sur `ps1-port` par le commit `fcd804095088fdeb0cdb34c0066c1f4595ffe7d2` (`Checkpoint PS1 source and v89 startup diagnostic`). C’est une sauvegarde de l’état courant, pas une restauration de v75 ou v76.
- Le checkout local reste sur `facbf1243875fe7e24819eff87d1879527f00584` et contient des modifications de travail. Il n’a pas été réinitialisé ni nettoyé.
- L’accès Git distant par `git fetch` a échoué faute d’identifiants Windows (`SEC_E_NO_CREDENTIALS`). L’état distant a été vérifié en lecture par l’API GitHub : branche `ps1-port` à `fcd8040`; PR #1 ouverte, brouillon, non fusionnée.
- Trente commits Git inaccessibles aux branches/ref existantes ont été rattachés à `refs/archive/ps1-recovery/<sha12>`. Un bundle local qui contient l’historique référencé a été créé et vérifié : `C:/Users/Manau47/Documents/Codex/work/Funkin-ps1-recovery-20261030.bundle` (4 613 229 octets).

## v75 et v76 : fichiers retrouvés, sources non retrouvées

| Build | Artefact retrouvé | Taille | SHA-256 |
|---|---|---:|---|
| v75 | `outputs/FNF-PS1-v75-week1-on-demand-week2-enhanced/funkin-ps1-bopeebo-playable.bin` | 98 666 400 | `6C09832B3BB2BABE77EA5411EFE83D5445AA34F189FBB5882C773A3DB1B760F6` |
| v75 | `outputs/FNF-PS1-v75-week1-on-demand-week2-enhanced/funkin-ps1-bopeebo-playable.cue` | 93 | `8579EEF0E6966AFD78659F364593E560C8384148E9258D14FA88B196A842B340` |
| v76 | `outputs/FNF-PS1-v76-week2-week3-loading/funkin-ps1-bopeebo-playable.bin` | 131 942 496 | `828489413342768586115C99AD5C1A6B82FC65F88800A17F16308A3BC9E08402` |
| v76 | `outputs/FNF-PS1-v76-week2-week3-loading/funkin-ps1-bopeebo-playable.cue` | 93 | identique au CUE v75 |

Les BIN/CUE existants n’ont pas été écrasés. Les sources exactes, un commit/tag par build et les configurations de compilation complètes de v75/v76 n’ont pas été retrouvés. Aucun commit local/distant ni reflog ne nomme ou ne correspond à ces versions; les 30 commits détachés recensés sont des itérations PS1 antérieures. Il n’y a pas de stash. Le dossier `ps1/build/freeplay-v76-week2-week3-loading` a été réutilisé et contient maintenant des sorties v78 : son cache ne prouve donc pas la configuration originale de v76. Les recherches ciblées dans `work/` et l’historique de session n’ont révélé aucune copie source exacte.

Le contenu des deux images reste comparable : `SYSTEM.CNF` identique, `FUNKIN.EXE` à LBA 25 dans les deux; l’exécutable embarqué diffère (v75 : 868 352 octets, PC `0x8001F910`, text `0xD3800`; v76 : 860 160 octets, PC `0x8001D864`, text `0xD1800`; champs BSS d’en-tête nuls). v76 ajoute W3SCENE (262 656 octets), neuf charts et les pistes de Week 3; les ressources communes Menu/Bopeebo/Weeks 1–2 comparées ont les mêmes hashes. Les premières données de Week 1 sont décalées d’environ 13 999 secteurs par l’ajout de ressources. Ces observations isolent les changements de contenu du disque, pas la cause du gel au démarrage : les sources/options v75/v76 exactes manquent toujours.

## Portée de récupération et prochaine procédure

- **Retrouvé exactement :** les quatre fichiers BIN/CUE et leurs empreintes; l’historique Git disponible; le snapshot actuel sauvegardé sur GitHub; les différences structurelles des images consignées ci-dessus.
- **Récupéré mais antérieur :** 30 commits détachés, conservés localement dans les refs d’archive et le bundle.
- **Non retrouvé :** sources et options de compilation correspondant précisément aux BIN v75/v76. Une reconstruction à partir de commits proches serait approximative et ne doit pas être appelée v75/v76.
- Pour chaque nouveau disque : commit source dédié sur `ps1-port`, configuration et références d’assets consignées, manifeste contenant version, commande de build, SHA-256 du BIN/CUE et résultat d’exécution. Si la publication GitHub échoue, garder le commit local et signaler explicitement l’échec. SDK, assets officiels et intermédiaires restent hors Git.

Ne pas commencer le test différentiel v75→v76 tant qu’une source exacte n’a pas été trouvée ou que l’utilisateur n’a pas choisi explicitement une reconstruction approximative à partir de l’état récupérable.

