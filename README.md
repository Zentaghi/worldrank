# WorldRank — mise en ligne complète

## 1. Site (GitHub Pages)
Fichiers : `index.html`, `data.json` (+ `generate_data.py`, `schema.sql`).
Envoie-les dans un dépôt GitHub public, Settings → Pages → branche `main` / root.

## 2. Vraies données
`python3 generate_data.py` (ou via GitHub Actions) remplace `data.json` : tous les pays, ~23 catégories, noms FR/EN/ES.
« Pire passeport » : enregistre ton fichier sous le nom `passport.csv` à côté du script (colonnes `rank,country,visa_free_score`, noms anglais : le script les rapproche des pays et affiche ceux qu'il ne reconnaît pas).
Le mode Football utilise des données intégrées au jeu (approximatives, à vérifier).

## 3. Comptes + classement mondial (Supabase, gratuit)
1. supabase.com → New project. 2. SQL Editor → colle `schema.sql` → Run.
3. Settings → API : copie **Project URL** et **anon public key** dans `index.html` (`const SB_URL="…",SB_KEY="…"`).
4. Authentication → URL Configuration : Site URL = `https://TON-PSEUDO.github.io/worldrank/` (ajoute-la aussi dans Redirect URLs).
5. Authentication → Providers → **Google** : crée un « OAuth client » (Web) dans Google Cloud Console, redirect URI = celle affichée par Supabase, colle Client ID/Secret.
6. **Apple** : demande un compte Apple Developer payant (99 $/an) puis suit le guide Supabase « Login with Apple ». Tu peux lancer sans Apple au début.

Limite connue : les scores sont envoyés par le navigateur, donc un tricheur motivé peut les falsifier. Prochaine étape : vérifier les scores côté serveur en rejouant la graine du plateau.
