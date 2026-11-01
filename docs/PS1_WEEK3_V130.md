# Week 3 v130 — relever le fond ville

## Modification

Le retour sur v129 indique que la ville paraît trop basse dans la composition. v130 relève uniquement les deux tuiles de la couche arrière de 8 unités monde, soit environ 12 pixels à l’écran avec le zoom de 1,5×. Le facteur de parallaxe reste 0,3. Le quai, le train, les personnages et la caméra ne bougent pas.

## Préservation et build

v128, référence stable précédente, et v129 restent conservées. Cette variante part des ressources préconverties v129, sans conversion d’assets. Les fichiers `week3-scene.bin` avant/après sont identiques (524800 octets, SHA-256 `886D0CED3C52B63C2CDEC752D59B78ADCE86894FDA4AFAD17F9F00AFF48B4AED`). Le build reconstruit le code, l’exécutable et le disque dans un nouveau dossier; les avertissements `volatile` viennent du code cdstream préexistant du SDK.

Image contrôlée : 117 fichiers, `SYSTEM.CNF;1` en premier et `FUNKIN.EXE;1` en second. BIN 338509248 octets, SHA-256 `9660E496BDAE906C7A3A41CE1921B2B9B7DA86391059296685CCF0BEB1AA3D99`. CUE SHA-256 `32F6069BC1FB3B5A563126E84749269BFE7818B2CD07DB2DB1799EAF1B87E597`.

## État du test

La compilation et la vérification du disque sont réussies. v130 n’a pas encore été lancée dans DuckStation ni sur console réelle. L’essai utilisateur doit confirmer que la ville est remontée à la bonne hauteur, sans déplacer le quai, sans faire réapparaître de vide et en conservant parallaxe, lumières, train et cheveux de GF. La v129 reste disponible pour comparer.
