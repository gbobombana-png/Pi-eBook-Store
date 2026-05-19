// Stockage en mémoire pour le prototype — à remplacer par Firebase/MongoDB en production

const users = new Map();       // piUid -> userData
const saves = new Map();       // piUid -> gameState
const leaderboard = new Map(); // piUid -> { username, rep, buildings, prestige, faction, updatedAt }
const payments = new Map();    // paymentId -> paymentRecord

export const db = {
  // ── Utilisateurs ──────────────────────────────────────────────
  getUser(piUid) {
    return users.get(piUid) || null;
  },
  upsertUser(piUid, data) {
    const existing = users.get(piUid) || {};
    const updated = { ...existing, ...data, piUid, updatedAt: Date.now() };
    users.set(piUid, updated);
    return updated;
  },

  // ── Cloud Save ────────────────────────────────────────────────
  getSave(piUid) {
    return saves.get(piUid) || null;
  },
  upsertSave(piUid, gameState) {
    const record = { ...gameState, piUid, savedAt: Date.now() };
    saves.set(piUid, record);
    return record;
  },

  // ── Classement ────────────────────────────────────────────────
  updateLeaderboard(piUid, entry) {
    leaderboard.set(piUid, { ...entry, piUid, updatedAt: Date.now() });
  },
  getGlobalBoard(limit = 50) {
    return [...leaderboard.values()]
      .sort((a, b) => b.rep - a.rep)
      .slice(0, limit);
  },
  getFactionBoard() {
    const factions = {};
    for (const e of leaderboard.values()) {
      if (!e.faction) continue;
      if (!factions[e.faction]) factions[e.faction] = { faction: e.faction, members: 0, totalRep: 0 };
      factions[e.faction].members++;
      factions[e.faction].totalRep += e.rep || 0;
    }
    return Object.values(factions).sort((a, b) => b.totalRep - a.totalRep);
  },

  // ── Paiements ────────────────────────────────────────────────
  savePayment(paymentId, record) {
    payments.set(paymentId, { ...record, createdAt: Date.now() });
  },
  getPayment(paymentId) {
    return payments.get(paymentId) || null;
  },
  markPaymentComplete(paymentId, txid) {
    const p = payments.get(paymentId);
    if (p) payments.set(paymentId, { ...p, txid, status: 'completed', completedAt: Date.now() });
  },
};
