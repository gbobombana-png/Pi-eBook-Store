import { Router } from 'express';
import { authMiddleware } from '../middleware/piAuth.js';
import { db } from '../db/store.js';

const router = Router();

// Champs autorisés à synchroniser (évite l'injection de champs sensibles)
const ALLOWED_FIELDS = [
  'username', 'character', 'money', 'rep', 'crew', 'premiumOwned',
  'buildings', 'districts', 'totalEarned', 'totalBuildings', 'clickCount',
  'collectCount', 'upgradeCount', 'visitedDistricts', 'activities',
  'missions', 'missionsLastDailyReset', 'missionsLastWeeklyReset',
  'dailyReward', 'vehicles', 'tutorialDone', 'ownedSkins', 'activeSkin',
  'seasonPass', 'prestigeLevel', 'prestigeBonus', 'currentWeather',
  'achievements',
];

function sanitizeSave(raw) {
  const clean = {};
  for (const key of ALLOWED_FIELDS) {
    if (raw[key] !== undefined) clean[key] = raw[key];
  }
  return clean;
}

// GET /save — charge la sauvegarde cloud
router.get('/', authMiddleware, (req, res) => {
  const save = db.getSave(req.piUser.uid);
  if (!save) return res.json({ save: null }); // premier lancement
  res.json({ save });
});

// POST /save — pousse la sauvegarde locale vers le cloud
router.post('/', authMiddleware, (req, res) => {
  const incoming = req.body.gameState;
  if (!incoming || typeof incoming !== 'object') {
    return res.status(400).json({ error: 'gameState requis' });
  }

  // Résolution de conflits : on garde la version avec le plus de rep/argent
  const existing = db.getSave(req.piUser.uid);
  let toSave = sanitizeSave(incoming);

  if (existing) {
    const existingScore = (existing.rep || 0) + (existing.totalEarned || 0);
    const incomingScore = (incoming.rep || 0) + (incoming.totalEarned || 0);
    // Si la sauvegarde cloud est plus avancée, on refuse le recul (anti-triche basique)
    if (existingScore > incomingScore * 1.5) {
      return res.status(409).json({
        error: 'Conflit de sauvegarde : la version cloud est plus avancée',
        cloudSave: existing,
      });
    }
    // On fusionne les premiumOwned et ownedSkins pour ne rien perdre
    const mergedPremium = [...new Set([...(existing.premiumOwned || []), ...(incoming.premiumOwned || [])])];
    const mergedSkins   = [...new Set([...(existing.ownedSkins   || []), ...(incoming.ownedSkins   || [])])];
    toSave.premiumOwned = mergedPremium;
    toSave.ownedSkins   = mergedSkins;
  }

  const saved = db.upsertSave(req.piUser.uid, toSave);

  // Met à jour le classement
  db.updateLeaderboard(req.piUser.uid, {
    username:  toSave.username  || req.piUser.username,
    rep:       toSave.rep       || 0,
    buildings: toSave.totalBuildings || 0,
    prestige:  toSave.prestigeLevel  || 0,
    faction:   toSave.crew      || null,
  });

  res.json({ success: true, savedAt: saved.savedAt });
});

export default router;
