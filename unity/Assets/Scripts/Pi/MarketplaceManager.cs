using UnityEngine;
using System;
using System.Collections.Generic;
using BLOCKSIDE.Core;

namespace BLOCKSIDE.Pi
{
    [Serializable]
    public class PremiumItem
    {
        public string id;
        public string displayName;
        public string emoji;
        public string description;
        public float piPrice;
        public string effectType; // x2_income, legendary_skin, battle_pass, extra_slot
    }

    /// <summary>
    /// Manages premium items purchasable with Pi Coins.
    /// Handles purchase flow, inventory, and applying item effects.
    /// </summary>
    public class MarketplaceManager : MonoBehaviour
    {
        #region Inspector
        [SerializeField] private List<PremiumItem> catalog = new List<PremiumItem>();
        #endregion

        #region State
        private HashSet<string> ownedItemIds = new HashSet<string>();
        private PremiumItem pendingPurchase;
        #endregion

        #region Events
        public static event Action<PremiumItem> OnItemPurchaseStarted;
        public static event Action<PremiumItem> OnItemPurchaseSuccess;
        public static event Action<string> OnItemPurchaseFailed;
        public static event Action<PremiumItem> OnItemEffectApplied;
        #endregion

        #region Init
        private void Awake()
        {
            if (catalog == null || catalog.Count == 0) InitDefaultCatalog();
            SubscribeToPaymentEvents();
        }

        private void OnDestroy()
        {
            PiNetworkManager.OnPaymentCompleted -= HandlePaymentResult;
            PiNetworkManager.OnPaymentError -= HandlePaymentError;
        }

        private void InitDefaultCatalog()
        {
            catalog = new List<PremiumItem>
            {
                new PremiumItem{id="vip",displayName="VIP Pass",emoji="💎",description="Revenus ×2 permanent",piPrice=1f,effectType="x2_income"},
                new PremiumItem{id="skin",displayName="Legendary Skin",emoji="👑",description="Skin exclusif cosmétique",piPrice=3f,effectType="legendary_skin"},
                new PremiumItem{id="battle",displayName="Battle Pass",emoji="⚔️",description="Missions hebdo + récompenses",piPrice=5f,effectType="battle_pass"},
                new PremiumItem{id="key",displayName="District Key",emoji="🗝️",description="Slot de construction supplémentaire",piPrice=2f,effectType="extra_slot"}
            };
        }

        private void SubscribeToPaymentEvents()
        {
            PiNetworkManager.OnPaymentCompleted += HandlePaymentResult;
            PiNetworkManager.OnPaymentError += HandlePaymentError;
        }

        public void LoadData(List<string> savedOwned)
        {
            ownedItemIds.Clear();
            if (savedOwned != null)
                foreach (var id in savedOwned) ownedItemIds.Add(id);
            ReapplyAllEffects();
        }

        public void Reset()
        {
            ownedItemIds.Clear();
        }
        #endregion

        #region Purchase Flow
        /// <summary>Starts the Pi payment flow for an item.</summary>
        public void PurchaseItem(string itemId)
        {
            if (IsOwned(itemId))
            {
                Debug.Log("[MarketplaceManager] Already owned: " + itemId);
                return;
            }
            var item = catalog.Find(x => x.id == itemId);
            if (item == null) { Debug.LogWarning("[MarketplaceManager] Unknown item: " + itemId); return; }

            pendingPurchase = item;
            OnItemPurchaseStarted?.Invoke(item);

            var piMgr = GameManager.Instance?.PiNetwork;
            if (piMgr == null) { HandlePaymentError("PiNetworkManager not found"); return; }

            piMgr.CreatePayment(new PiPaymentData
            {
                amount = item.piPrice,
                memo = "BLOCKSIDE - " + item.displayName,
                metadata = item.id
            }, result =>
            {
                if (result.success) HandlePaymentResult(result);
                else HandlePaymentError(result.error);
            });
        }

        private void HandlePaymentResult(PiPaymentResult result)
        {
            var item = catalog.Find(x => x.id == result.itemId);
            if (item == null) item = pendingPurchase;
            if (item == null) return;

            ownedItemIds.Add(item.id);
            ApplyEffect(item);
            GameManager.Instance?.SaveGame();
            OnItemPurchaseSuccess?.Invoke(item);
            Debug.Log("[MarketplaceManager] Item purchased: " + item.displayName);
        }

        private void HandlePaymentError(string error)
        {
            OnItemPurchaseFailed?.Invoke(error);
            Debug.LogWarning("[MarketplaceManager] Purchase failed: " + error);
        }
        #endregion

        #region Effects
        private void ApplyEffect(PremiumItem item)
        {
            switch (item.effectType)
            {
                case "x2_income":
                    GameManager.Instance?.Economy.ActivateVIP();
                    break;
                case "extra_slot":
                    GameManager.Instance?.Districts.AddExtraSlot();
                    break;
                case "legendary_skin":
                case "battle_pass":
                    // Cosmetic — handled by UI layer
                    break;
            }
            OnItemEffectApplied?.Invoke(item);
        }

        private void ReapplyAllEffects()
        {
            foreach (var id in ownedItemIds)
            {
                var item = catalog.Find(x => x.id == id);
                if (item != null) ApplyEffect(item);
            }
        }
        #endregion

        #region Queries
        public bool IsOwned(string itemId) => ownedItemIds.Contains(itemId);
        public List<string> GetOwnedItemIds() => new List<string>(ownedItemIds);
        public List<PremiumItem> GetCatalog() => new List<PremiumItem>(catalog);
        public PremiumItem GetItem(string id) => catalog.Find(x => x.id == id);
        #endregion
    }
}
