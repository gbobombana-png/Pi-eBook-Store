# BLOCKSIDE — Game Design Document (GDD)
**Version 1.0 — Mai 2026**
**Confidentiel — © 2025-2026 BOBO MBANA GAEL**

---

## TABLE DES MATIÈRES

1. Vue d'ensemble & Pitch
2. Concept & Univers
3. Personnages (11 héros jouables)
4. Districts de Blockside City (7 zones)
5. Mécaniques de gameplay
6. Système de construction
7. Véhicules
8. Customisation du personnage
9. Économie du jeu
10. Intégration Pi Network
11. Social, Factions & Crew Wars
12. Battle Pass & Progression
13. Interface utilisateur
14. Stack technique
15. Roadmap de développement
16. Modèle économique & Monétisation
17. Marché cible & Opportunité
18. Vision long terme

---

## 1. VUE D'ENSEMBLE & PITCH

**BLOCKSIDE** est un jeu urbain sandbox de nouvelle génération, développé nativement pour l'écosystème **Pi Network**. Les joueurs construisent des empires dans une ville néon futuriste, gèrent des districts, forment des crews, combattent pour le territoire — et gagnent de vrais **Pi Coins** en jouant.

### Pitch en une phrase
> *"GTA meets Monopoly meets Web3 — dans une ville néon où chaque bâtiment que tu construis te rapporte des Pi."*

### Chiffres clés
| Indicateur | Valeur |
|---|---|
| Plateforme cible principale | Pi Browser (mobile) |
| Plateforme secondaire | Android (Unity), Web |
| Personnages jouables | 11 |
| Districts | 7 |
| Type de jeu | Urban sandbox / idle RPG / social |
| Économie | Pi Network (Pi Coin) |
| Modèle | Free-to-play + Pi monetization |

---

## 2. CONCEPT & UNIVERS

### 2.1 L'univers BLOCKSIDE

Blockside City est une mégapole fictive futuriste aux accents urbains — néons violets et oranges, gratte-ciels de béton, ruelles underground, ports industriels. La ville est divisée en **7 districts**, chacun avec son identité, son économie et ses factions.

Le joueur arrive en tant que **Street Rookie** et doit bâtir son empire : acheter des terrains, construire des bâtiments, recruter un crew, dominer les districts et devenir la légende de Blockside City.

### 2.2 Piliers du design
- **Build** — Construis et améliore des bâtiments qui génèrent des revenus passifs
- **Fight** — Défends ton territoire et attaque les crews rivaux
- **Own** — Possède des actifs numériques ancrés dans Pi Network

### 2.3 Ambiance visuelle
- Palette : `#07070F` (fond nuit), `#FF6B1A` (orange néon), `#9B2FFF` (violet), `#FF2D78` (rose), `#FFD700` (or)
- Style : Cyberpunk urbain, street culture, néon-noir
- Typographies : Space Mono (chiffres), Sora (interface)
- Inspirations visuelles : Cyberpunk 2077, GTA VI, NBA 2K (personnages)

---

## 3. PERSONNAGES (11 HÉROS JOUABLES)

Chaque personnage a une identité forte, des stats uniques et une ability exclusive qui change le style de jeu.

### Stats système (0–10)
| Stat | Rôle |
|---|---|
| STREET | Maîtrise des rues et du réseau underground |
| BUILD | Vitesse et efficacité de construction |
| HACK | Accès aux marchés cachés et aux failles système |
| TRADE | Revenus commerciaux et négociation |
| FIGHT | Puissance en Crew Wars et défense territoire |

---

### ZAY — Street Rookie
- **Couleur :** Orange `#FF6B1A`
- **Tagline :** *From nothing to legend.*
- **Quote :** *"Les rues m'ont tout appris. Maintenant c'est moi qui enseigne."*
- **Stats :** STREET 9 · BUILD 5 · HACK 3 · TRADE 7 · FIGHT 6
- **Ability — Street Flow :** Chaque collecte consécutive augmente le multiplicateur de +5%
- **Bonus :** +20% revenus commerce
- **Profil :** Ambitieux, instinctif, loyal à son crew. Personnage de départ parfait.

---

### NIA — Hustler
- **Couleur :** Rose `#FF2D78`
- **Tagline :** *Every deal. Every corner. Every π.*
- **Quote :** *"Je ne dors pas. Je génère."*
- **Stats :** STREET 7 · BUILD 4 · HACK 6 · TRADE 9 · FIGHT 5
- **Ability — Hustle Mode :** +15% sur toutes les sources de revenus actifs
- **Bonus :** +20% négociation sur toutes les transactions
- **Profil :** Calculatrice, charismatique, imprévisible.

---

### KANE — Builder
- **Couleur :** Or `#FFD700`
- **Tagline :** *I don't just build blocks. I build empires.*
- **Quote :** *"Chaque brique posée est une promesse tenue."*
- **Stats :** STREET 4 · BUILD 10 · HACK 3 · TRADE 6 · FIGHT 5
- **Ability — Master Builder :** -20% coût construction + bâtiments génèrent +10% revenu
- **Bonus :** +15% revenus passifs sur tous les bâtiments
- **Profil :** Méthodique, patient, visionnaire.

---

### MALIK — Strategist
- **Couleur :** Vert `#4ADE80`
- **Tagline :** *The city is just a chessboard.*
- **Quote :** *"Tu joues pour gagner. Moi je joue pour dominer."*
- **Stats :** STREET 5 · BUILD 6 · HACK 7 · TRADE 7 · FIGHT 8
- **Ability — Grand Strategy :** +25% gains lors des District Wars et événements
- **Bonus :** +25% gains lors des événements stratégiques
- **Profil :** Froid, analytique, impitoyable.

---

### VEX — Hacker
- **Couleur :** Violet `#9B2FFF`
- **Tagline :** *The system is just a game I've already won.*
- **Quote :** *"Tout système a une faille. Moi je suis la faille."*
- **Stats :** STREET 4 · BUILD 4 · HACK 10 · TRADE 6 · FIGHT 5
- **Ability — Ghost Protocol :** -25% coût marché noir + accès aux bâtiments cachés
- **Bonus :** +20% gains Black Market
- **Profil :** Mystérieux, brillant, solitaire.

---

### RICO — Dealer *(11ème personnage)*
- **Couleur :** Teal `#00D4AA`
- **Tagline :** *Les bonnes affaires ne tombent pas du ciel, on les crée.*
- **Quote :** *"Je contrôle le marché. Le marché ne me contrôle pas."*
- **Stats :** STREET 6 · BUILD 4 · HACK 5 · TRADE 9 · FIGHT 4
- **Ability — Market King :** +15% profits trading + +10% revenus Black Market
- **Bonus :** +10% Pi Coins sur toutes les ventes et transactions
- **Profil :** Rusé, ambitieux, maître de la négociation underground.

---

### BRICK — Trader
- **Couleur :** Orange `#FF6B1A`
- **Tagline :** *Everything has a price. I set the price.*
- **Quote :** *"Le deal parfait n'existe pas. Jusqu'à ce que je le crée."*
- **Stats :** STREET 7 · BUILD 5 · HACK 4 · TRADE 10 · FIGHT 6
- **Ability — Broker's Edge :** +30% revenus commerce inter-districts
- **Profil :** Pragmatique, sociable, redoutable en négociation.

---

### LUNA — Drifter
- **Couleur :** Bleu `#2F9BFF`
- **Tagline :** *Blink and you'll miss her.*
- **Quote :** *"Je passe comme le vent. Et je prends tout au passage."*
- **Stats :** STREET 8 · BUILD 3 · HACK 7 · TRADE 5 · FIGHT 7
- **Ability — Drift Mode :** +20% vitesse collecte + cooldown réduit
- **Profil :** Libre, intuitive, insaisissable.

---

### KAEL — Investor
- **Couleur :** Or `#FFD700`
- **Tagline :** *Money makes money. Pi makes empires.*
- **Quote :** *"Je n'achète pas des bâtiments. J'achète le futur."*
- **Stats :** STREET 3 · BUILD 7 · HACK 5 · TRADE 9 · FIGHT 4
- **Ability — Compound Effect :** +35% sur tous les revenus passifs automatiques
- **Profil :** Élégant, calculateur, toujours en avance.

---

### RAZE — Enforcer
- **Couleur :** Rose `#FF2D78`
- **Tagline :** *Your territory is my territory now.*
- **Quote :** *"On ne négocie pas avec moi. On se soumet."*
- **Stats :** STREET 8 · BUILD 5 · HACK 2 · TRADE 4 · FIGHT 10
- **Ability — Iron Grip :** +40% défense territoire + dégâts en Crew Wars
- **Profil :** Brutal, loyal à son crew, impitoyable.

---

### SHADOW — Unknown
- **Couleur :** Violet `#9B2FFF`
- **Tagline :** *You don't find SHADOW. SHADOW finds you.*
- **Quote :** *"..."*
- **Stats :** STREET 7 · BUILD 7 · HACK 7 · TRADE 7 · FIGHT 7
- **Ability — Dark Matter :** Capacité inconnue — se débloque au Prestige 2
- **Profil :** Identité classifiée. Personnage secret à débloquer.

---

## 4. DISTRICTS DE BLOCKSIDE CITY (7 ZONES)

### LOWSIDE *(disponible dès le début)*
- **Vibe :** Underground street vibes
- **Atmosphère :** La rue ne dort jamais. Le béton sue. L'argent coule sous les néons cassés.
- **Couleurs :** Orange · Rose · Nuit profonde
- **Musique :** Trap 140 BPM · Bass lourd
- **Slots de construction :** 9
- **Événements exclusifs :** Street Race, Flash Mob, Underground Market

### NEON DISTRICT *(débloqué à $10K)*
- **Vibe :** Commerce lumineux, nuits infinies
- **Atmosphère :** Les enseignes ne s'éteignent jamais ici. L'argent circule aussi vite que la lumière.
- **Couleurs :** Violet · Cyan · Or
- **Musique :** Lo-fi hip hop · Néon jazz
- **Slots :** 12
- **Bâtiment rare :** Crypto Exchange

### INDUSTRIA *(débloqué à $50K)*
- **Vibe :** Béton, acier, production massive
- **Atmosphère :** Les machines ne dorment jamais. Si tu as la volonté de construire, Industria t'appartient.
- **Couleurs :** Gris acier · Orange industriel
- **Musique :** Industrial techno · Bass mécanique
- **Slots :** 16

### DOWNTOWN *(débloqué à $150K)*
- **Vibe :** Power business, gratte-ciels
- **Atmosphère :** Le vrai pouvoir se négocie ici. Chaque bureau est un trône.
- **Couleurs :** Bleu nuit · Or · Blanc
- **Musique :** Ambient corporate · Jazz moderne
- **Slots :** 20

### THE PIT *(débloqué à $500K)*
- **Vibe :** Underground combat, factions rivales
- **Atmosphère :** Ici les règles n'existent pas. Seuls les plus forts survivent.
- **Couleurs :** Rouge · Noir · Orange sang
- **Musique :** Drill · Bass agressive
- **Slots :** 14

### COASTLINE *(débloqué à $1M)*
- **Vibe :** Luxe, yachts, white collar crime
- **Atmosphère :** Le luxe cache toujours quelque chose. Bienvenue dans la face propre du crime.
- **Couleurs :** Blanc · Bleu mer · Or
- **Musique :** Yacht rock · Deep house
- **Slots :** 18

### HIGHLANDS *(débloqué au Prestige 1)*
- **Vibe :** Elite level, domination totale
- **Atmosphère :** Peu arrivent jusqu'ici. Ceux qui y sont n'en repartent jamais.
- **Couleurs :** Violet prestige · Or · Noir absolu
- **Musique :** Orchestral · Epic bass
- **Slots :** 24

---

## 5. MÉCANIQUES DE GAMEPLAY

### 5.1 Boucle de jeu principale
```
Collecte revenus → Achète bâtiments → Améliore bâtiments
→ Débloque nouveaux districts → Participe aux événements
→ Crew Wars → Prestige → Recommence à un niveau supérieur
```

### 5.2 Système de revenus
- Chaque bâtiment génère un revenu passif toutes les X secondes
- Le revenu s'accumule même hors connexion (offline income)
- La collecte déclenche des VFX, sons et le système de combo
- **×N COMBO** : collectes consécutives rapides donnent un multiplicateur temporaire

### 5.3 Rangs du joueur
| Rang | Revenus requis |
|---|---|
| Street Rookie | Départ |
| Hustler | $5,000 |
| Block Boss | $25,000 |
| District King | $100,000 |
| City Legend | $500,000 |
| BLOCKSIDE ELITE | $2,000,000 |

### 5.4 Système de Prestige
Après avoir atteint un certain niveau, le joueur peut "Prestige" :
- Remet les compteurs à zéro
- Donne un bonus permanent (+X% sur tout)
- Débloque des cosmétiques exclusifs et des titres
- Jusqu'à 5 niveaux de Prestige

### 5.5 Événements Live
- **Neon Concert** : revenus ×5 sur certains bâtiments pendant 3h
- **Blackout** : revenus doublés en Lowside pendant 1h
- **Gang War** : attaque de crew rival — défends ou perds des revenus
- **Flash Deal** : bâtiment rare disponible pendant 30 minutes
- **Pi Rain** : bonus de Pi Coins distribués aléatoirement aux actifs

---

## 6. SYSTÈME DE CONSTRUCTION

### 6.1 Types de bâtiments
| Catégorie | Exemples | Revenus |
|---|---|---|
| Commerce | Snack Shop, Boutique, Marché | Bas → Moyen |
| Services | Garage, Barbershop, Studio | Moyen |
| Entertainment | Club, Casino, Salle de concert | Élevé |
| Tech | Data Center, Crypto Exchange | Très élevé |
| Rare | Black Market, Tower, Helipad | Exceptionnel |

### 6.2 Phases de construction (Unity 3D)
1. **PLACE** — Choix de l'emplacement sur la grille
2. **BUILD** — Animation de construction (temps variable selon le bâtiment)
3. **UPGRADE** — Amélioration jusqu'au niveau 5 (chaque niveau × revenu)
4. **DEFEND** — Protection contre les raids de crews rivaux

### 6.3 Grilles par district
- Chaque district a une grille de slots (3×3 à 4×6)
- Certains slots ont des bonus de position (coin = +10%, centre = +5%)
- Les bâtiments adjacents peuvent créer des synergies

---

## 7. VÉHICULES

| Véhicule | Type | Bonus |
|---|---|---|
| Street Bike | Rapide, agile | +15% vitesse de collecte |
| Muscle Car | Puissant, intimidant | +10% revenus Lowside |
| Armored Truck | Défensif | +25% résistance aux raids |
| Speed Boat | Accès Coastline | +20% revenus maritimes |
| Attack Helicopter | Combat aérien | +30% efficacité Crew Wars |

Les véhicules sont des NFT visuels — ils ne changent pas le gameplay core mais donnent des bonus et du prestige social.

---

## 8. CUSTOMISATION DU PERSONNAGE

### Catégories de cosmétiques
- **Tenues** : Street, Business, Militaire, Luxury, Prestige
- **Chaussures** : Sneakers, Boots, Designer
- **Accessoires** : Chains, Montres, Lunettes, Casques
- **Skins de bâtiments** : Changent l'apparence 3D des constructions
- **Tags de rue** : Graffitis personnalisés sur le territoire
- **Plaques** : Numéro de joueur (ex: #23) sur le personnage

### Système de skins
- Skins communs (gratuits)
- Skins rares (Pi Coins)
- Skins épiques (Battle Pass)
- Skins légendaires (événements limités)
- Skins Prestige (exclusifs au rang Prestige)

---

## 9. ÉCONOMIE DU JEU

### 9.1 Monnaies en jeu
| Monnaie | Type | Utilisation |
|---|---|---|
| $ Blockside Cash | In-game (soft) | Construction, upgrades |
| ⭐ Réputation | In-game (XP) | Rang, déblocages |
| π Pi Coins | Réelle (crypto) | Premium items, NFT |

### 9.2 Sources de revenus pour le joueur
- Revenus passifs des bâtiments
- Victoires en Crew Wars
- Complétion de missions
- Événements live
- Trading inter-districts
- Battle Pass (récompenses Pi)

### 9.3 Sink économique (dépenses)
- Construction et upgrades de bâtiments
- Cosmétiques premium
- Entrée dans les événements spéciaux
- Accélération de timers (optionnel)
- NFT de territoire

---

## 10. INTÉGRATION PI NETWORK

### 10.1 Authentification
- Login via **Pi Browser** avec compte Pi Network
- Nom d'utilisateur Pi affiché dans le jeu
- UID Pi utilisé comme identifiant permanent

### 10.2 Paiements Pi
- Tous les achats premium se font en **Pi**
- Intégration via **Pi Payments SDK** (approve + complete flow)
- Paiements confirmés côté serveur (Node.js backend)
- Taux de conversion : défini selon le cours Pi au moment du lancement

### 10.3 NFT & Ownership sur Pi
- Les bâtiments premium peuvent devenir des **NFT Pi** (ownership réel)
- Les skins légendaires sont des actifs numériques transférables
- Le territoire conquis est lié au compte Pi du joueur

### 10.4 API Backend (Node.js)
- `POST /api/auth/login` — Authentification Pi
- `GET /api/auth/me` — Données joueur
- `POST /api/payments/approve` — Approbation paiement Pi
- `POST /api/payments/complete` — Finalisation paiement
- `GET/POST /api/save` — Sauvegarde cloud
- `GET /api/leaderboard/global` — Classement mondial
- `GET /api/events` — Événements live

---

## 11. SOCIAL, FACTIONS & CREW WARS

### 11.1 Crews
- Chaque joueur peut créer ou rejoindre un **Crew** (max 20 membres)
- Nom, logo et couleurs personnalisables
- Le Crew partage un territoire sur la carte

### 11.2 Crew Wars
- Attaques de territoire programmées (2× par jour)
- Système de défense : bâtiments fortifiés, gardes, pièges
- Victoire = revenus volés + points de faction
- Défaite = revenus réduits pendant 1h

### 11.3 Factions de la ville
- **Block City Rebels** : Faction rue, bonus Lowside
- **Black Crow** : Faction hacker, bonus tech
- **Purple Reign** : Faction luxe, bonus Coastline
- **Iron Fist** : Faction combat, bonus The Pit

### 11.4 Classements
- Classement global (revenus totaux)
- Classement par faction
- Classement par district
- Hall of Fame Prestige

---

## 12. BATTLE PASS & PROGRESSION

### Structure du Battle Pass
- **50 niveaux** par saison (1 saison = 30 jours)
- Récompenses gratuites tous les 5 niveaux
- Récompenses premium (Pi) tous les niveaux
- Récompenses exclusives aux niveaux 25 et 50

### Types de récompenses
- Cash Blockside
- Skins de bâtiments
- Tenues exclusives
- Véhicules
- Pi Coins (niveaux premium)
- Titre exclusif de saison

### XP Battle Pass
Gagné via : missions quotidiennes, collectes, constructions, Crew Wars, connexion quotidienne

---

## 13. INTERFACE UTILISATEUR

### Écrans principaux
| Écran | Contenu |
|---|---|
| Splash | Logo animé, chargement |
| Sélection personnage | Carousel 11 persos, stats, ability |
| Hub | Stats globales, événements, actions rapides |
| Ville | Carte des 7 districts, revenus en attente |
| District View | Grille de construction, bâtiments |
| Profil | Carte sociale, stats, skins, partage |
| Crew | Membres, territoire, Crew Wars |
| Boutique Pi | Items premium, cosmétiques |
| Missions | Quotidiennes & hebdomadaires |
| Leaderboard | Global, factions, districts |
| Battle Pass | Track 50 niveaux, progression |
| Garage | Véhicules débloqués |

### Design mobile-first
- Interface pensée pour une main (thumb-friendly)
- Gestures : swipe pour naviguer entre districts
- Dark mode permanent (fond #07070F)
- Effets : glow néon, particules, transitions fluides

---

## 14. STACK TECHNIQUE

### Frontend (Prototype web actuel)
- HTML5 / CSS3 / JavaScript vanilla
- Web Audio API (système sonore)
- Pi Network SDK v2.0
- Déployé sur GitHub Pages

### Frontend (Version finale)
- **Unity 6** — moteur 3D
- Cible : Android (APK) + Pi Browser WebGL
- Shaders : URP (Universal Render Pipeline)
- Optimisé mobile (60 FPS sur mid-range)

### Backend
- **Node.js / Express**
- **Helmet** (sécurité HTTP)
- **Rate limiting** (60 req/min)
- **CORS** configuré pour Pi Browser
- Base de données : MongoDB ou PostgreSQL
- Déployé sur **Render.com**

### Infrastructure
- Frontend statique : **GitHub Pages**
- Backend API : **Render.com** (free tier → upgrade)
- Assets : CDN (Cloudflare)
- Logs & monitoring : intégré Render

### Sécurité
- Tous les paiements Pi vérifiés côté serveur
- JWT pour les sessions
- Validation des données backend
- Sauvegarde chiffrée côté serveur

---

## 15. ROADMAP DE DÉVELOPPEMENT

### Phase 1 — Prototype Web ✅ (Mai 2026)
- [x] Interface complète mobile-first
- [x] 11 personnages avec stats et abilities
- [x] 7 districts avec système de construction
- [x] Économie de base (cash, revenus passifs)
- [x] Système sonore Web Audio API
- [x] Combo, Level Up, profil social
- [x] Battle Pass, Leaderboard, Événements
- [x] Déploiement GitHub Pages

### Phase 2 — Pi Network Integration (Juin 2026)
- [ ] Authentification Pi SDK
- [ ] Paiements Pi (approve/complete)
- [ ] Profil lié au compte Pi
- [ ] Sauvegarde cloud backend
- [ ] Enregistrement sur Pi Developer Portal

### Phase 3 — Unity 3D Alpha (T3 2026)
- [ ] Personnages 3D (11 modèles)
- [ ] Open world Lowside jouable
- [ ] Construction 3D en temps réel
- [ ] Véhicules de base (Bike + Car)
- [ ] Crew Wars alpha

### Phase 4 — Beta & Expansion (T4 2026)
- [ ] 7 districts complets
- [ ] Tous les véhicules
- [ ] Customisation complète
- [ ] NFT Pi integration
- [ ] Classements mondiaux
- [ ] Events live automatiques

### Phase 5 — Launch (2027)
- [ ] Launch officiel Pi Network
- [ ] Battle Pass Season 1
- [ ] Marketing dans l'écosystème Pi
- [ ] Mise à jour contenu mensuelle

---

## 16. MODÈLE ÉCONOMIQUE & MONÉTISATION

### Sources de revenus
| Source | Mécanisme | Estimation |
|---|---|---|
| Battle Pass Premium | 5π/saison | Récurrent mensuel |
| Cosmétiques | 0.5π – 50π par item | Ponctuel |
| Boost d'XP / accélérateurs | 0.1π – 1π | Ponctuel |
| NFT de territoire | 10π – 500π | Premium |
| Events exclusifs | 1π entrée | Événementiel |
| Skins Prestige | 25π – 100π | Rare |

### Modèle F2P équitable
- **100% du contenu gameplay** accessible gratuitement
- Les Pi achètent uniquement des cosmétiques et du confort (pas de pay-to-win)
- Les joueurs actifs peuvent gagner des récompenses Pi via les classements et events

### Projections (conservatrices)
| Utilisateurs actifs | ARPU mensuel | Revenu mensuel |
|---|---|---|
| 1,000 | 2π | 2,000π |
| 10,000 | 2π | 20,000π |
| 100,000 | 2π | 200,000π |

*Note : valeur Pi au moment de la rédaction non fixée — les projections sont en volume Pi.*

---

## 17. MARCHÉ CIBLE & OPPORTUNITÉ

### Marché Pi Network
- **47+ millions** de membres Pi Network actifs (2025)
- Très peu de jeux de qualité disponibles dans l'écosystème Pi
- Forte demande pour des applications utilisant Pi Coin
- Communauté jeune, technophile, engagée

### Positionnement
BLOCKSIDE est le **premier urban sandbox RPG** natif Pi Network avec :
- Graphismes 3D de qualité console
- Gameplay deep (construction + combat + social)
- Économie Pi réelle et équitable
- Personnages représentatifs et identifiables

### Concurrence
- Pas de concurrent direct dans l'espace Pi Network
- Concurrents indirects : Clash of Clans, GTA Online, NBA 2K (différentes plateformes)
- Avantage : premier arrivé sur Pi Network avec un jeu de cette qualité

---

## 18. VISION LONG TERME

### BLOCKSIDE comme plateforme
Au-delà du jeu, BLOCKSIDE vise à devenir une **plateforme sociale urbaine** dans l'écosystème Pi :
- Marché NFT interne (bâtiments, skins, véhicules)
- Économie joueur-à-joueur (trading de ressources)
- Système de sponsoring de Crew par des marques Pi
- Tournois esports avec prizepool en Pi

### Expansion univers
- **BLOCKSIDE Comics** : Histoires des 11 personnages
- **BLOCKSIDE Music** : Tracks exclusifs par artistes (liés aux événements)
- **BLOCKSIDE Merch** : Vêtements street culture avec QR codes Pi
- **BLOCKSIDE 2** : Suite avec nouvelles villes (Lagos, Tokyo, São Paulo)

### Impact social
BLOCKSIDE est conçu pour refléter la culture urbaine mondiale — des personnages diversifiés, des histoires authentiques, une économie qui récompense l'effort. Le jeu vise à prouver que Web3 peut être fun, accessible et équitable.

---

## INFORMATIONS LÉGALES

**Propriétaire :** BOBO MBANA GAEL
**Création :** 2025
**Tous droits réservés :** BLOCKSIDE™, les personnages, l'univers et les assets visuels sont la propriété exclusive de BOBO MBANA GAEL.

**Contact :** via GitHub — gbobombana-png

---

*Document confidentiel — ne pas distribuer sans autorisation écrite du propriétaire.*
*© 2025-2026 BOBO MBANA GAEL — BLOCKSIDE*
