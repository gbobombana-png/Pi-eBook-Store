import { Router } from 'express';
import { db } from '../db/store.js';

const router = Router();

// Données mock pour étoffer le classement en prototype
const MOCK_ENTRIES = [
  { piUid:'mock1', username:'ALPHA_GOD',   rep:245820, buildings:67, prestige:3, faction:'rebel' },
  { piUid:'mock2', username:'NeonKing',    rep:198340, buildings:54, prestige:2, faction:'purple' },
  { piUid:'mock3', username:'ShadowBoss',  rep:156720, buildings:49, prestige:2, faction:'crow' },
  { piUid:'mock4', username:'StreetLord',  rep:98450,  buildings:38, prestige:1, faction:'rebel' },
  { piUid:'mock5', username:'CityMaster',  rep:76230,  buildings:31, prestige:1, faction:'purple' },
  { piUid:'mock6', username:'BlockKing',   rep:54180,  buildings:27, prestige:0, faction:'crow' },
  { piUid:'mock7', username:'NightRunner', rep:38920,  buildings:22, prestige:0, faction:'rebel' },
  { piUid:'mock8', username:'UrbanLord',   rep:25640,  buildings:18, prestige:0, faction:'purple' },
];

const MOCK_FACTIONS = [
  { faction:'rebel',  factionName:'REBEL CITY',    members:1247, totalRep:2847520, dominancePercent:52 },
  { faction:'crow',   factionName:'BLACK CROW',     members:892,  totalRep:1984320, dominancePercent:33 },
  { faction:'purple', factionName:'PURPLE NATION',  members:634,  totalRep:1256840, dominancePercent:15 },
];

// GET /leaderboard/global?limit=20 — top joueurs
router.get('/global', (req, res) => {
  const limit = Math.min(parseInt(req.query.limit) || 20, 100);

  // Fusionne les vrais joueurs avec les mocks (les vrais en premier si même uid)
  const real = db.getGlobalBoard(limit);
  const mockFiltered = MOCK_ENTRIES.filter(m => !real.find(r => r.username === m.username));
  const combined = [...real, ...mockFiltered]
    .sort((a, b) => b.rep - a.rep)
    .slice(0, limit)
    .map((e, i) => ({ ...e, rank: i + 1 }));

  res.json({ board: combined, total: combined.length });
});

// GET /leaderboard/factions — classement des factions
router.get('/factions', (req, res) => {
  const real = db.getFactionBoard();

  // Fusionne avec les mocks
  const merged = { ...Object.fromEntries(MOCK_FACTIONS.map(f => [f.faction, { ...f }])) };
  real.forEach(r => {
    if (merged[r.faction]) {
      merged[r.faction].members  += r.members  || 0;
      merged[r.faction].totalRep += r.totalRep || 0;
    } else {
      merged[r.faction] = r;
    }
  });

  const board = Object.values(merged)
    .sort((a, b) => b.totalRep - a.totalRep)
    .map((f, i) => ({ ...f, rank: i + 1 }));

  res.json({ board });
});

// GET /leaderboard/districts — classement par district
router.get('/districts', (req, res) => {
  res.json({
    board: [
      { district:'LOWSIDE',    icon:'🏚️', color:'#FF6B1A', leader:'ALPHA_GOD',  buildings:67, income:128400 },
      { district:'NEON MARKET',icon:'🌃', color:'#2F9BFF', leader:'NeonKing',   buildings:54, income:342800 },
      { district:'SKY DISTRICT',icon:'🏙️',color:'#9B2FFF', leader:'ShadowBoss', buildings:38, income:865000 },
      { district:'UNDERBLOCK', icon:'🌑', color:'#FF2D78', leader:'StreetLord', buildings:29, income:210500 },
      { district:'THE EDGE',   icon:'⚡', color:'#FFD700', leader:'CityMaster', buildings:21, income:480000 },
    ],
  });
});

export default router;
