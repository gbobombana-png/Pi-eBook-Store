# BLOCKSIDE — Structure des Scènes Unity 6

## Ordre de chargement

```
BootstrapScene
    └── SceneBootstrap.cs — instancie les singletons (GameManager, Audio, Input, Notifs)
        └── charge SplashScene
```

## Scènes et contenu

### BootstrapScene
- Scène vide (aucun visuel)
- Contient uniquement : `SceneBootstrap` + canvas de chargement (barre de progression)
- Durée : ~0.5s

### SplashScene
- Logo BLOCKSIDE animé (Shader Graph — dégradé néon)
- Bouton **Connexion Pi Network** → `PiNetworkManager.Authenticate()`
- Bouton **Mode Démo** → `GameManager.LoginDemo()`
- Fond : particules canvas + orbes flou radial

### CharacterSelectScene
- Carousel horizontal de 5 personnages (ZAY, NOVA, BRICK, RAVEN, KAYO)
- Chaque card : modèle 3D low-poly + stats + bonus
- Bouton Jouer → `GameManager.NewGame(characterId, username)`

### HubScene  *(scène principale — la plus lourde)*
- **Managers actifs** : IncomeSystem, MissionManager, DailyRewards, LiveEventManager,
  WeatherManager, LeaderboardManager
- **UI Panels** : HUD, BottomNav, NotifPanel, PrestigeOverlay, DailyRewardModal
- **Navigation** vers : CityMapScene, Crew, PiMarket, Profile, Garage, Missions, BattlePass, Leaderboard

### CityMapScene
- Vue top-down isométrique de BLOCKSIDE City
- 5 districts cliquables (LOWSIDE, NEON MARKET, SKY DISTRICT, UNDERBLOCK, THE EDGE)
- Effets météo visuels (pluie, brouillard, tonnerre) via WeatherManager
- Chargement additif de DistrictScene au clic

### DistrictScene  *(chargement additif)*
- Grille de slots (3×3 à 4×4 selon le district)
- Placement et upgrade de bâtiments
- Collecte de revenus avec particules VFX
- BuildingPlacer + BuildingBase + IncomeSystem locaux

## Hiérarchie type (HubScene)

```
[HubScene]
├── [Managers]
│   ├── GameManager (DontDestroyOnLoad — déjà présent)
│   ├── IncomeTickSystem
│   ├── MissionManager
│   ├── WeatherManager
│   └── LiveEventManager
├── [Canvas — UI]
│   ├── HUD (argent, rep, bâtiments)
│   ├── BottomNavBar
│   ├── ActivityFeed
│   ├── Panels/
│   │   ├── CrewPanel
│   │   ├── MarketPanel
│   │   ├── ProfilePanel
│   │   ├── LeaderboardPanel
│   │   ├── PrestigeOverlay
│   │   ├── NotifPanel
│   │   └── DailyRewardModal
│   └── Modals/
│       ├── BuildModal
│       ├── BuildingDetailModal
│       └── PaymentModal
├── [City Preview]
│   ├── CityBackground (Quad + shader néon)
│   └── WeatherVFX (Rain, Fog, Lightning)
└── [Audio]
    └── AudioManager (musique ambiante + SFX)
```

## Paramètres Build Android

| Paramètre | Valeur |
|-----------|--------|
| minSdkVersion | API 24 (Android 7.0) |
| targetSdkVersion | API 34 (Android 14) |
| Architectures | ARM64 + ARMv7 |
| Backend | IL2CPP |
| Orientation | Portrait |
| FPS cible | 60 |
| Qualité | Medium (réglable dans options) |
| Bundle | AAB (Play Store) ou APK (direct) |
