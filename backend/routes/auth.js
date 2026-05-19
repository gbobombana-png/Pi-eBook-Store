import { Router } from 'express';
import { authMiddleware } from '../middleware/piAuth.js';
import { db } from '../db/store.js';

const router = Router();

// POST /auth/login — authentifie le joueur via Pi SDK et crée/met à jour son profil
router.post('/login', authMiddleware, (req, res) => {
  const { uid, username } = req.piUser;

  const user = db.upsertUser(uid, {
    username,
    lastLogin: Date.now(),
  });

  // Met à jour le classement avec les données de base
  db.updateLeaderboard(uid, {
    username,
    rep: 0,
    buildings: 0,
    prestige: 0,
    faction: null,
  });

  res.json({
    success: true,
    user: {
      piUid: user.piUid,
      username: user.username,
      lastLogin: user.lastLogin,
    },
  });
});

// GET /auth/me — récupère le profil du joueur connecté
router.get('/me', authMiddleware, (req, res) => {
  const user = db.getUser(req.piUser.uid);
  if (!user) return res.status(404).json({ error: 'Joueur non trouvé — fais /auth/login d\'abord' });
  res.json({ user });
});

export default router;
