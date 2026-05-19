import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import { rateLimit } from 'express-rate-limit';

import authRoutes       from './routes/auth.js';
import paymentsRoutes   from './routes/payments.js';
import saveRoutes       from './routes/savegame.js';
import leaderboardRoutes from './routes/leaderboard.js';
import eventsRoutes     from './routes/events.js';

const app  = express();
const PORT = process.env.PORT || 3001;

// ── Sécurité de base ──────────────────────────────────────────
app.use(helmet());

const defaultOrigins = 'http://localhost:3000,http://localhost:5173,http://127.0.0.1:5500,https://gbobombana-png.github.io';
const allowedOrigins = (process.env.ALLOWED_ORIGINS || defaultOrigins).split(',').map(o => o.trim());
app.use(cors({
  origin: (origin, cb) => {
    if (!origin || allowedOrigins.includes(origin)) return cb(null, true);
    cb(new Error(`CORS bloqué : origine non autorisée — ${origin}`));
  },
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'x-demo-uid', 'x-demo-username'],
}));

app.use(express.json({ limit: '256kb' }));

// ── Rate limiting ─────────────────────────────────────────────
const apiLimiter = rateLimit({
  windowMs: 60 * 1000,   // 1 minute
  max: 60,               // 60 requêtes/min par IP
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Trop de requêtes — réessaie dans 1 minute' },
});

const saveLimiter = rateLimit({
  windowMs: 30 * 1000,   // 30 secondes
  max: 5,                // max 5 sauvegardes/30s
  message: { error: 'Sauvegarde trop fréquente — attends 30 secondes' },
});

// ── Routes ────────────────────────────────────────────────────
app.use('/api', apiLimiter);
app.use('/api/auth',        authRoutes);
app.use('/api/payments',    paymentsRoutes);
app.use('/api/save',        saveLimiter, saveRoutes);
app.use('/api/leaderboard', leaderboardRoutes);
app.use('/api/events',      eventsRoutes);

// ── Healthcheck ───────────────────────────────────────────────
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'BLOCKSIDE Backend',
    version: '1.0.0',
    env: process.env.NODE_ENV || 'development',
    uptime: Math.floor(process.uptime()) + 's',
  });
});

// ── 404 & erreurs globales ────────────────────────────────────
app.use((req, res) => {
  res.status(404).json({ error: `Route introuvable : ${req.method} ${req.path}` });
});

app.use((err, req, res, _next) => {
  console.error('[Erreur serveur]', err.message);
  res.status(500).json({ error: 'Erreur interne du serveur' });
});

// ── Démarrage ─────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`\n🏙️  BLOCKSIDE Backend — Port ${PORT}`);
  console.log(`   Environnement : ${process.env.NODE_ENV || 'development'}`);
  console.log(`   Routes actives :`);
  console.log(`     POST /api/auth/login`);
  console.log(`     GET  /api/auth/me`);
  console.log(`     POST /api/payments/approve`);
  console.log(`     POST /api/payments/complete`);
  console.log(`     GET  /api/save       POST /api/save`);
  console.log(`     GET  /api/leaderboard/global`);
  console.log(`     GET  /api/leaderboard/factions`);
  console.log(`     GET  /api/leaderboard/districts`);
  console.log(`     GET  /api/events\n`);
});
