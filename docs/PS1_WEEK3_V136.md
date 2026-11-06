# Week 3 v136 — réinitialiser les textures au retour Freeplay

## Défaut signalé

Après un retour au Freeplay puis le lancement d’un autre morceau, la scène apparaît fortement corrompue (capture utilisateur du 1er novembre 2026). Les notes et le HUD restent reconnaissables tandis que les textures de scène montrent des couleurs/pixels incohérents.

## Analyse et correction

Les scènes partagent les pages de texture et une CLUT 8bpp. Les pages 0–7 sont réutilisées par les packages de semaine; la page 7 est aussi prêtée au DJ Freeplay. Le chemin de retour déchargeait les packages selon des indicateurs `*_visuals_loaded`, puis rendait page 7 au DJ et rechargeait le fond Freeplay. Cette gestion par propriété partielle n’établissait pas un état de base complet et vérifiable de l’atlas partagé.

v136 ajoute au retour Freeplay un rechargement complet de l’atlas/palettes de base Bopeebo depuis `W1SCENE.BIN`, après le déchargement de la scène. Les indicateurs de location des packages semaine sont alors remis à `false`; l’entrée suivante recharge les pages du morceau sélectionné depuis son package. Le DJ Freeplay et son écran sont restaurés ensuite. Aucun asset, chart, son ou transform graphique n’est modifié par ce correctif.

L’inspection identifie une faiblesse possible de restauration de l’état VRAM partagé, mais le lien causal avec la corruption reste à confirmer par l’essai après un cycle Freeplay → morceau → Freeplay → morceau. Le rechargement complet de l’atlas de base en v136 est une remise à zéro conservatrice pour ce test, pas une nécessité de conserver les assets de toutes les pistes en VRAM ni l’architecture mémoire finale. Les palettes peuvent être chargées avec le paquet de scène; la pression principale porte sur les pages de texture qui doivent coexister avec les framebuffers et les éléments communs.

## Build

Build distinct `ps1/build/week3-v136-vram-reset-cmake/`, PSn00bSDK 0.24 / GCC MIPS 12.3 / CMake / Ninja. Le dry-run du disque jouable ne prévoyait que compilation/link et création ISO; les assets convertis ont été réutilisés via les répertoires préconvertis. `W3SCENE.BIN` est identique à v135 (524800 octets, SHA-256 `886D0CED3C52B63C2CDEC752D59B78ADCE86894FDA4AFAD17F9F00AFF48B4AED`).

ISO après réordonnancement : 117 fichiers, `SYSTEM.CNF;1` en premier et `FUNKIN.EXE;1` en deuxième, 338509248 octets. BIN SHA-256 `15A53475CC050D60B884D5A5B8572AD41F3788A185BF38406C51C859E61BCE1B`; CUE SHA-256 `054E3A25865253AB5009649E5F3607BA382DFF8811DB8B4882B2A3828F7B22A4`. Livraison : `ps1/build/week3-v136-vram-reset-cmake/delivery-v136-rootfix/`.

## Vérification

Compilation et contrôles statiques ISO réussis. v136 n’a pas été exécutée dans DuckStation par l’agent; la scène après le cycle de transition attend le test utilisateur. Aucun résultat console réelle n’est revendiqué. Le build v135 est conservé sans modification.
