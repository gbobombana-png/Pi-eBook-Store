import { Router } from 'express';

const router = Router();

// Événements live — en production, ceux-ci viendraient d'une BDD admin
const LIVE_EVENTS = [
  {
    id: 'black_market_night',
    emoji: '🔥',
    title: 'BLACK MARKET NIGHT',
    desc: 'Revenus ×3 dans Underblock',
    districtBonus: { district: 'underblock', multiplier: 3 },
    endsAt: Date.now() + 6120000, // 1h42
    color: '#FF2D78',
    active: true,
  },
  {
    id: 'district_wars',
    emoji: '⚔️',
    title: 'DISTRICT WARS',
    desc: 'Crew Wars — contrôle de The Edge',
    districtBonus: null,
    endsAt: Date.now() + 83700000, // 23h15
    color: '#FF6B1A',
    active: true,
  },
  {
    id: 'neon_concert',
    emoji: '🎵',
    title: 'NEON CONCERT',
    desc: 'Snack Shop rapporte ×5 ce soir',
    buildingBonus: { buildingId: 'snack', multiplier: 5 },
    endsAt: Date.now() + 11280000, // 3h08
    color: '#9B2FFF',
    active: true,
  },
  {
    id: 'city_blackout',
    emoji: '🌩️',
    title: 'CITY BLACKOUT',
    desc: 'Revenus doublés dans tous les districts',
    globalBonus: { multiplier: 2 },
    endsAt: Date.now() + 2700000, // 45min
    color: '#2F9BFF',
    active: true,
  },
];

// GET /events — liste des événements actifs
router.get('/', (req, res) => {
  const now = Date.now();
  const active = LIVE_EVENTS.filter(e => e.active && e.endsAt > now)
    .map(e => ({
      ...e,
      remainingMs: e.endsAt - now,
      remainingLabel: formatRemaining(e.endsAt - now),
    }));
  res.json({ events: active });
});

// GET /events/:id — détail d'un événement
router.get('/:id', (req, res) => {
  const ev = LIVE_EVENTS.find(e => e.id === req.params.id);
  if (!ev) return res.status(404).json({ error: 'Événement introuvable' });
  res.json({ event: { ...ev, remainingMs: Math.max(0, ev.endsAt - Date.now()) } });
});

function formatRemaining(ms) {
  if (ms <= 0) return 'Terminé';
  const h = Math.floor(ms / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  return h > 0 ? `${h}h ${m}min` : `${m}min`;
}

export default router;
