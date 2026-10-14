# WorldRank – mise en ligne

1. `python3 generate_data.py` → crée `data.json` (tous les pays, 20 catégories, données World Bank).
   Le `data.json` fourni ici est une **démo** (68 pays, rangs approximatifs) : remplace-le.
2. Teste en local : `python3 -m http.server` puis ouvre http://localhost:8000
   (le jeu charge `data.json` automatiquement ; sans lui il utilise ses données de démo).
3. Mets `index.html` et `data.json` dans un dépôt GitHub → Settings → Pages → branche `main`.

Chaque partie tire 8 catégories parmi toutes celles du fichier et ne garde que les pays qui ont des données pour ces 8 catégories.
Ajouter une catégorie = ajouter une ligne `(nom, code World Bank)` dans `CATS` de `generate_data.py`.
