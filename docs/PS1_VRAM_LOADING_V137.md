# Manifeste de build — v137b, audit de chargement

## Référence source et configuration

- Branche : `ps1-port`.
- Base de l’audit : v136, source `71274dc3441d9d4c6e4e9330ef3e504ca5bc22c1`, changement v136 `f3106b5b72d699b072a479f86925e2e68b405137`.
- Commit source v137 : `eb72b59b64531f4739a100d7b7e2abbd3307e7db`.
- Répertoire CMake distinct : `ps1/build/vram-loading-v137-cmake/`.
- Cache CMake archivé localement : `ps1/build/archive-v137-vram-loading/CMakeCache-v137.txt`; SHA-256 `AE1B98B818D03A689653F0204C005D76DC1C5DAEF633ABB1F1E46A286F7FDD52`.
- Configuration suivie : CMake 4.5, Ninja, PSn00bSDK 0.24, MIPS GCC 12.3, `CMAKE_BUILD_TYPE=Debug`, cible `mipsel-none-elf`; `FUNKIN_PS1_DIAGNOSTICS_DEFAULT=OFF`, `FUNKIN_PS1_ARROW_DIAGNOSTIC_DEFAULT=OFF`, toutes les sondes/judgement tests et le test HUD désactivés, `FUNKIN_PS1_SCENE_DEMO_DEFAULT=OFF`, marqueurs de démarrage avant/après BSS et dans `main()` désactivés, `FUNKIN_PS1_DAD_LANES_DEFAULT=ON`. Les chemins d’entrées converties et d’outils sont conservés dans le cache local archivé, pas dans Git.
- Dry-run final : compilation de `spu_probe.c`, édition de liens, génération de l’image disque. Aucun convertisseur ni générateur d’assets n’était prévu.
- Passe incrémentale finale : seul `spu_probe.c` recompilé, puis ELF et image disque régénérés.

## Résultats de compilation et ressources

- ELF SHA-256 : `33F9DB4E24D5769A1FB7028E01A757FB70EFCEB94CD5EA14BB61D2DE3B20B6CF`.
- ELF chargé calculé depuis les sections : 1 058 330 octets, soit 172 octets de moins que v136 (1 058 502). Ce n’est pas une mesure de RAM libre à l’exécution.
- 116 fichiers `.bin`/`.vag` convertis comparés avec v136 : aucun hash différent. Ils n’ont pas été reconvertis.
- BIN livré : `ps1/build/vram-loading-v137-cmake/delivery-v137b-memory-loading-rootfix/funkin-ps1-v137b-memory-loading.bin`, 338 509 248 octets, SHA-256 `9CD4415B05D2B21D2DFA22AC6FB47057A440B447448453ABB36CE00E56EA6444`.
- CUE livré : `ps1/build/vram-loading-v137-cmake/delivery-v137b-memory-loading-rootfix/funkin-ps1-v137b-memory-loading.cue`, SHA-256 `665C9369D112A9C57A9FDFCDA497170958F8464031FFCD941DBD943E510A3751`.
- Contrôle ISO : 117 entrées; `SYSTEM.CNF;1` puis `FUNKIN.EXE;1`; exécutable racine et ordre BIOS vérifiés. La règle de démarrage validée demeure inchangée.

Les chemins d’assets, d’audio et du SDK sont propres à cette machine et restent dans le `CMakeCache` ignoré; ils ne sont pas incorporés au dépôt. Les BIN/CUE antérieurs n’ont pas été écrasés.

## Portée et niveau de validation

Les changements de code et les volumes avant/après sont décrits dans [`PS1_VRAM_LOADING_AUDIT_V136.md`](PS1_VRAM_LOADING_AUDIT_V136.md). Les volumes CD/VRAM et l’occupation des sections sont des calculs statiques; le dépôt n’a pas de compteurs runtime pour le débit CD, les uploads GPU ou le pic heap. Compilation et vérification ISO réussies. **Aucun lancement de v137b dans DuckStation n’a encore été observé** et aucune validation console réelle n’est revendiquée. L’utilisateur doit charger le CUE et tester des cycles entre semaines, retour Freeplay et Game Over/Retry avant toute conclusion sur la corruption ou la stabilité.

