// Stockage en mémoire pour le prototype — à remplacer par Firebase/MongoDB en production

const users    = new Map(); // piUid -> userData
const saves    = new Map(); // piUid -> gameState
const leaderboard = new Map();
const payments = new Map(); // paymentId -> paymentRecord
const auctions = new Map(); // auctionId -> auctionRecord
const mintedCounts = new Map(); // nftId -> count minted

export const PLATFORM_FEE = 0.10; // 10% sur chaque vente

export const NFT_MAX_SUPPLY = {
  nft_founder: 10,
  nft_legend:  5,
  nft_dragon:  3,
  nft_city:    1,
};

export const db = {
  // ── Utilisateurs ──────────────────────────────────────────────
  getUser(piUid) { return users.get(piUid) || null; },
  upsertUser(piUid, data) {
    const updated = { ...(users.get(piUid)||{}), ...data, piUid, updatedAt: Date.now() };
    users.set(piUid, updated);
    return updated;
  },

  // ── Cloud Save ────────────────────────────────────────────────
  getSave(piUid) { return saves.get(piUid) || null; },
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
    return [...leaderboard.values()].sort((a,b) => b.rep - a.rep).slice(0, limit);
  },
  getFactionBoard() {
    const factions = {};
    for (const e of leaderboard.values()) {
      if (!e.faction) continue;
      if (!factions[e.faction]) factions[e.faction] = { faction: e.faction, members: 0, totalRep: 0 };
      factions[e.faction].members++;
      factions[e.faction].totalRep += e.rep || 0;
    }
    return Object.values(factions).sort((a,b) => b.totalRep - a.totalRep);
  },

  // ── Paiements ────────────────────────────────────────────────
  savePayment(paymentId, record) {
    payments.set(paymentId, { ...record, createdAt: Date.now() });
  },
  getPayment(paymentId) { return payments.get(paymentId) || null; },
  markPaymentComplete(paymentId, txid) {
    const p = payments.get(paymentId);
    if (p) payments.set(paymentId, { ...p, txid, status: 'completed', completedAt: Date.now() });
  },

  // ── Supply NFT ────────────────────────────────────────────────
  getMintedCount(nftId) { return mintedCounts.get(nftId) || 0; },
  incrementMintedCount(nftId) { mintedCounts.set(nftId, (mintedCounts.get(nftId) || 0) + 1); },
  getAllSupply() {
    return Object.fromEntries(
      Object.entries(NFT_MAX_SUPPLY).map(([id, max]) => [id, { minted: mintedCounts.get(id) || 0, max }])
    );
  },

  // ── Enchères NFT ─────────────────────────────────────────────
  createAuction(sellerUid, { nftId, tokenId, nftName, nftEmoji, nftRarity, startPrice, durationHours, isCreatorDrop = false }) {
    const auctionId = `auction_${Date.now()}_${Math.random().toString(36).slice(2,8)}`;
    const endsAt = Date.now() + durationHours * 3600000;
    const record = {
      auctionId, sellerUid, nftId, tokenId, nftName, nftEmoji, nftRarity,
      startPrice, currentBid: 0, currentBidder: null, currentBidderName: null,
      bids: [], endsAt, status: 'active', createdAt: Date.now(), isCreatorDrop,
    };
    auctions.set(auctionId, record);
    return record;
  },
  getAuction(auctionId) { return auctions.get(auctionId) || null; },
  getActiveAuctions() {
    const now = Date.now();
    return [...auctions.values()]
      .filter(a => a.status === 'active' && a.endsAt > now)
      .sort((a,b) => a.endsAt - b.endsAt);
  },
  // Enchères terminées en attente de paiement du gagnant
  getEndedUnpaid(bidderUid) {
    const now = Date.now();
    return [...auctions.values()].filter(a =>
      a.status === 'active' && a.endsAt <= now &&
      a.currentBidder === bidderUid && a.currentBid > 0
    );
  },
  placeBid(auctionId, bidderUid, bidderName, amount) {
    const a = auctions.get(auctionId);
    if (!a) return { error: 'Enchère introuvable' };
    if (a.status !== 'active' || a.endsAt <= Date.now()) return { error: 'Enchère terminée' };
    if (a.sellerUid === bidderUid) return { error: 'Tu ne peux pas enchérir sur ton propre NFT' };
    const minBid = a.currentBid > 0 ? a.currentBid + 0.1 : a.startPrice;
    if (amount < minBid) return { error: `Offre minimum : π${minBid.toFixed(1)}` };
    a.bids.push({ bidderUid, bidderName, amount, at: Date.now() });
    a.currentBid = amount;
    a.currentBidder = bidderUid;
    a.currentBidderName = bidderName;
    auctions.set(auctionId, a);
    return { success: true, auction: a };
  },
  cancelAuction(auctionId, sellerUid) {
    const a = auctions.get(auctionId);
    if (!a || a.sellerUid !== sellerUid) return false;
    if (a.currentBid > 0) return false; // ne peut pas annuler si des offres existent
    auctions.set(auctionId, { ...a, status: 'cancelled', cancelledAt: Date.now() });
    return true;
  },
  markAuctionSold(auctionId, buyerUid, txid) {
    const a = auctions.get(auctionId);
    if (a) auctions.set(auctionId, { ...a, status: 'sold', buyerUid, txid, soldAt: Date.now() });
  },
};
