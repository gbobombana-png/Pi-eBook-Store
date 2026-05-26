import { Router } from 'express';
import { authMiddleware } from '../middleware/piAuth.js';
import { db, PLATFORM_FEE, NFT_MAX_SUPPLY } from '../db/store.js';

const router = Router();
const CREATOR_UID = '64585852-7e08-42ff-a02d-1f74152b2423';

// GET /nft/auctions — enchères actives + terminées non payées + supply info
router.get('/auctions', authMiddleware, (req, res) => {
  const active = db.getActiveAuctions().map(a => ({
    ...a,
    sellerUsername: db.getUser(a.sellerUid)?.username || 'Anonyme',
    timeLeft: Math.max(0, a.endsAt - Date.now()),
  }));
  const wonUnpaid = db.getEndedUnpaid(req.piUser.uid).map(a => ({
    ...a,
    sellerUsername: db.getUser(a.sellerUid)?.username || 'Anonyme',
    timeLeft: 0,
  }));
  const supply = db.getAllSupply();
  res.json({ auctions: active, wonUnpaid, supply });
});

// POST /nft/auction — créer une enchère
router.post('/auction', authMiddleware, (req, res) => {
  const { nftId, tokenId, nftName, nftEmoji, nftRarity, startPrice, durationHours } = req.body;
  if (!nftId || !startPrice || !durationHours) {
    return res.status(400).json({ error: 'Champs manquants' });
  }
  if (nftId === 'nft_origin') {
    return res.status(403).json({ error: 'Le NFT Origin est non transférable' });
  }
  if (![24, 48, 72].includes(Number(durationHours))) {
    return res.status(400).json({ error: 'Durée invalide (24, 48 ou 72h)' });
  }

  // Seul le créateur peut lancer un drop initial
  if (req.piUser.uid === CREATOR_UID) {
    const max = NFT_MAX_SUPPLY[nftId];
    if (!max) return res.status(400).json({ error: 'NFT inconnu' });
    const minted = db.getMintedCount(nftId);
    if (minted >= max) return res.status(400).json({ error: `Édition épuisée (${minted}/${max})` });
    const existing = db.getActiveAuctions().find(a => a.nftId === nftId && a.isCreatorDrop);
    if (existing) return res.status(409).json({ error: 'Un drop est déjà en cours pour ce NFT', auctionId: existing.auctionId });
    const auction = db.createAuction(req.piUser.uid, { nftId, tokenId: '', nftName, nftEmoji, nftRarity, startPrice: Number(startPrice), durationHours: Number(durationHours), isCreatorDrop: true });
    return res.json({ success: true, auction });
  }

  // Joueur lambda : doit posséder le NFT pour le remettre en vente
  if (!tokenId) return res.status(400).json({ error: 'tokenId requis pour une revente' });
  const save = db.getSave(req.piUser.uid);
  if (!save?.nftOwned?.find(n => n.nftId === nftId && n.tokenId === tokenId)) {
    return res.status(403).json({ error: 'Tu ne possèdes pas ce NFT' });
  }
  const existing = db.getActiveAuctions().find(a => a.sellerUid === req.piUser.uid && a.nftId === nftId);
  if (existing) return res.status(409).json({ error: 'Ce NFT est déjà aux enchères', auctionId: existing.auctionId });
  const auction = db.createAuction(req.piUser.uid, { nftId, tokenId, nftName, nftEmoji, nftRarity, startPrice: Number(startPrice), durationHours: Number(durationHours), isCreatorDrop: false });
  res.json({ success: true, auction });
});

// POST /nft/bid — placer une offre
router.post('/bid', authMiddleware, (req, res) => {
  const { auctionId, amount } = req.body;
  if (!auctionId || !amount) return res.status(400).json({ error: 'auctionId et amount requis' });
  const seller = db.getUser(req.piUser.uid);
  const result = db.placeBid(auctionId, req.piUser.uid, seller?.username || 'Anonyme', Number(amount));
  if (result.error) return res.status(400).json({ error: result.error });
  res.json(result);
});

// POST /nft/auction/cancel — annuler une enchère (seulement si 0 offres)
router.post('/auction/cancel', authMiddleware, (req, res) => {
  const { auctionId } = req.body;
  const ok = db.cancelAuction(auctionId, req.piUser.uid);
  if (!ok) return res.status(400).json({ error: 'Impossible d\'annuler (offres existantes ou non autorisé)' });
  res.json({ success: true });
});

// Résumé des frais pour info
router.get('/fees', (req, res) => {
  res.json({ platformFee: PLATFORM_FEE, sellerReceives: 1 - PLATFORM_FEE, neonRate: 1000 });
});

export default router;
