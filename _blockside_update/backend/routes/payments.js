import { Router } from 'express';
import { authMiddleware } from '../middleware/piAuth.js';
import { db, PLATFORM_FEE } from '../db/store.js';

const router = Router();
const PI_API_BASE = process.env.PI_API_BASE || 'https://api.minepi.com/v2';
const PI_API_KEY  = process.env.PI_API_KEY  || '';

// Effets des items Pi sur l'état du joueur
const ITEM_EFFECTS = {
  vip:         (save) => { save.premiumOwned = [...new Set([...(save.premiumOwned||[]), 'vip'])]; },
  skin:        (save) => { save.premiumOwned = [...new Set([...(save.premiumOwned||[]), 'skin'])]; },
  battle:      (save) => { save.premiumOwned = [...new Set([...(save.premiumOwned||[]), 'battle'])]; },
  key:         (save) => { save.premiumOwned = [...new Set([...(save.premiumOwned||[]), 'key'])]; },
  s2_pass:     (save) => {
    save.premiumOwned = [...new Set([...(save.premiumOwned||[]), 's2_pass'])];
    save.seasonPass = true;
    save.ownedSkins = [...new Set([...(save.ownedSkins||['default']), 'neon'])];
  },
  gold_boost:  (save) => { save.premiumOwned = [...new Set([...(save.premiumOwned||[]), 'gold_boost'])]; save.goldBoostUntil = Date.now() + 86400000; },
  city_key:    (save) => {
    save.premiumOwned = [...new Set([...(save.premiumOwned||[]), 'city_key'])];
    // Débloque tous les districts
    if (save.districts) Object.keys(save.districts).forEach(k => { save.districts[k].unlocked = true; });
  },
  neon_skin_pack: (save) => {
    save.ownedSkins = [...new Set([...(save.ownedSkins||['default']), 'neon', 'void', 'fire'])];
  },
  neon_100:  (save) => { save.neonBalance = (save.neonBalance || 0) + 100; },
  neon_500:  (save) => { save.neonBalance = (save.neonBalance || 0) + 550; },
  neon_1500: (save) => { save.neonBalance = (save.neonBalance || 0) + 1800; },
  neon_5000: (save) => { save.neonBalance = (save.neonBalance || 0) + 7500; },
  nft_founder: (save, uid, txid) => {
    if (!save.nftOwned) save.nftOwned = [];
    if (!save.nftOwned.find(n => n.nftId === 'nft_founder')) {
      const tokenId = `BLK-NFT-FOUNDER-${uid.slice(0,6).toUpperCase()}-${txid.slice(-8).toUpperCase()}`;
      save.nftOwned.push({ nftId: 'nft_founder', tokenId, mintedAt: Date.now(), txid });
    }
  },
  nft_legend: (save, uid, txid) => {
    if (!save.nftOwned) save.nftOwned = [];
    if (!save.nftOwned.find(n => n.nftId === 'nft_legend')) {
      const tokenId = `BLK-NFT-LEGEND-${uid.slice(0,6).toUpperCase()}-${txid.slice(-8).toUpperCase()}`;
      save.nftOwned.push({ nftId: 'nft_legend', tokenId, mintedAt: Date.now(), txid });
    }
  },
  nft_dragon: (save, uid, txid) => {
    if (!save.nftOwned) save.nftOwned = [];
    if (!save.nftOwned.find(n => n.nftId === 'nft_dragon')) {
      const tokenId = `BLK-NFT-DRAGON-${uid.slice(0,6).toUpperCase()}-${txid.slice(-8).toUpperCase()}`;
      save.nftOwned.push({ nftId: 'nft_dragon', tokenId, mintedAt: Date.now(), txid });
      save.ownedSkins = [...new Set([...(save.ownedSkins||['default']), 'dragon'])];
    }
  },
  nft_city: (save, uid, txid) => {
    if (!save.nftOwned) save.nftOwned = [];
    if (!save.nftOwned.find(n => n.nftId === 'nft_city')) {
      const tokenId = `BLK-NFT-CITY-${uid.slice(0,6).toUpperCase()}-${txid.slice(-8).toUpperCase()}`;
      save.nftOwned.push({ nftId: 'nft_city', tokenId, mintedAt: Date.now(), txid });
    }
  },
};

// POST /payments/approve — appelé côté client (onReadyForServerApproval)
router.post('/approve', authMiddleware, async (req, res) => {
  const { paymentId, itemId } = req.body;
  if (!paymentId || !itemId) {
    return res.status(400).json({ error: 'paymentId et itemId requis' });
  }

  try {
    const piRes = await fetch(`${PI_API_BASE}/payments/${paymentId}/approve`, {
      method: 'POST',
      headers: {
        Authorization: `Key ${PI_API_KEY}`,
        'Content-Type': 'application/json',
      },
    });

    const piData = await piRes.json();
    if (!piRes.ok) return res.status(piRes.status).json({ error: 'Erreur approbation Pi', detail: piData });

    // Enregistre le paiement en attente
    db.savePayment(paymentId, {
      piUid: req.piUser.uid,
      itemId,
      status: 'approved',
      amount: piData.amount,
    });

    res.json({ approved: true, payment: piData });
  } catch (err) {
    console.error('[payments/approve]', err.message);
    res.status(500).json({ error: 'Erreur serveur' });
  }
});

// POST /payments/complete — appelé côté client (onReadyForServerCompletion)
router.post('/complete', authMiddleware, async (req, res) => {
  const { paymentId, txid } = req.body;
  if (!paymentId || !txid) {
    return res.status(400).json({ error: 'paymentId et txid requis' });
  }

  // Vérifie que le paiement appartient bien au joueur connecté
  const record = db.getPayment(paymentId);
  if (!record) return res.status(404).json({ error: 'Paiement introuvable' });
  if (record.piUid !== req.piUser.uid) return res.status(403).json({ error: 'Paiement non autorisé' });
  if (record.status === 'completed') return res.json({ completed: true, alreadyDone: true });

  try {
    const piRes = await fetch(`${PI_API_BASE}/payments/${paymentId}/complete`, {
      method: 'POST',
      headers: {
        Authorization: `Key ${PI_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ txid }),
    });

    const piData = await piRes.json();
    if (!piRes.ok) return res.status(piRes.status).json({ error: 'Erreur complétion Pi', detail: piData });

    // Marque le paiement comme complété
    db.markPaymentComplete(paymentId, txid);

    // Paiement d'enchère NFT gagnée
    if (record.itemId && record.itemId.startsWith('nft_auction_')) {
      const auctionId = record.itemId.replace('nft_auction_', '');
      const auction = db.getAuction(auctionId);
      if (!auction) return res.status(404).json({ error: 'Enchère introuvable' });
      if (auction.status === 'sold') return res.json({ completed: true, alreadyDone: true });
      if (auction.currentBidder !== req.piUser.uid) return res.status(403).json({ error: 'Tu n\'es pas le gagnant de cette enchère' });

      const buyerSave = db.getSave(req.piUser.uid) || {};
      if (!buyerSave.nftOwned) buyerSave.nftOwned = [];

      // Règle : 1 seul NFT de chaque type par joueur
      if (buyerSave.nftOwned.find(n => n.nftId === auction.nftId)) {
        return res.status(400).json({ error: 'Tu possèdes déjà ce NFT — 1 exemplaire maximum par joueur' });
      }

      if (auction.isCreatorDrop) {
        // DROP CRÉATEUR : mint fresh — le NFT n'existait pas encore
        const tokenId = `BLK-NFT-${auction.nftId.replace('nft_','').toUpperCase()}-${req.piUser.uid.slice(0,6).toUpperCase()}-${txid.slice(-8).toUpperCase()}`;
        buyerSave.nftOwned.push({ nftId: auction.nftId, tokenId, mintedAt: Date.now(), txid });
        if (auction.nftId === 'nft_dragon') {
          buyerSave.ownedSkins = [...new Set([...(buyerSave.ownedSkins||['default']), 'dragon'])];
        }
        db.upsertSave(req.piUser.uid, buyerSave);
        db.incrementMintedCount(auction.nftId);
        db.markAuctionSold(auctionId, req.piUser.uid, txid);
        return res.json({ completed: true, auction: true, creatorDrop: true, nftId: auction.nftId, tokenId, finalPrice: auction.currentBid });
      }

      // REVENTE P2P : transfert depuis le vendeur
      const sellerSave = db.getSave(auction.sellerUid) || {};
      const nftIndex = (sellerSave.nftOwned||[]).findIndex(n => n.nftId === auction.nftId && n.tokenId === auction.tokenId);
      if (nftIndex !== -1) {
        const [nftRecord] = sellerSave.nftOwned.splice(nftIndex, 1);
        buyerSave.nftOwned.push({ ...nftRecord, listed: false, listingPrice: 0, auctionId: null, boughtAt: Date.now(), boughtFrom: auction.sellerUid });
        db.upsertSave(auction.sellerUid, sellerSave);
      }
      db.upsertSave(req.piUser.uid, buyerSave);

      // Créditer le vendeur (90% en NEON, plateforme garde 10%)
      const sellerShare = 1 - PLATFORM_FEE;
      const sellerNeon = Math.floor(auction.currentBid * 1000 * sellerShare);
      const sellerSaveForCredit = db.getSave(auction.sellerUid) || {};
      sellerSaveForCredit.neonBalance = (sellerSaveForCredit.neonBalance || 0) + sellerNeon;
      db.upsertSave(auction.sellerUid, sellerSaveForCredit);

      db.markAuctionSold(auctionId, req.piUser.uid, txid);
      return res.json({ completed: true, auction: true, nftId: auction.nftId, finalPrice: auction.currentBid, sellerNeon, platformFee: PLATFORM_FEE });
    }

    // Item standard
    const save = db.getSave(req.piUser.uid) || {};
    const applyEffect = ITEM_EFFECTS[record.itemId];
    if (applyEffect) applyEffect(save, req.piUser.uid, txid);
    db.upsertSave(req.piUser.uid, save);

    res.json({ completed: true, payment: piData, itemApplied: record.itemId });
  } catch (err) {
    console.error('[payments/complete]', err.message);
    res.status(500).json({ error: 'Erreur serveur' });
  }
});

// GET /payments/:paymentId — vérifie le statut d'un paiement
router.get('/:paymentId', authMiddleware, (req, res) => {
  const record = db.getPayment(req.params.paymentId);
  if (!record || record.piUid !== req.piUser.uid) {
    return res.status(404).json({ error: 'Paiement introuvable' });
  }
  res.json({ payment: record });
});

export default router;
