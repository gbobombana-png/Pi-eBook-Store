using System;
using System.Collections.Generic;
using UnityEngine;

namespace BLOCKSIDE
{
    /// <summary>Type of item rewarded at a Battle Pass tier.</summary>
    public enum TierRewardType
    {
        Money,
        Item,
        Skin,
        Building
    }

    [Serializable]
    public class TierReward
    {
        /// <summary>0-based tier index (0 = tier 1, 49 = tier 50).</summary>
        public int tier;
        public TierRewardType rewardType;
        public int moneyAmount;
        public string itemId;
        /// <summary>True = premium pass required to claim this tier.</summary>
        public bool premiumOnly;
    }

    [Serializable]
    public class SeasonData
    {
        public int seasonNumber;
        public string seasonName;
        /// <summary>Duration in days.</summary>
        public int durationDays;
        /// <summary>Unix timestamp (seconds) when season ends.</summary>
        public long endTimestampSec;
    }

    /// <summary>
    /// Manages the current season and Battle Pass progression.
    /// 50 tiers, driven by season XP.
    /// Premium pass unlocks premium-only tier rewards (Pi purchase).
    /// </summary>
    public class SeasonSystem : MonoBehaviour
    {
        // ─── Singleton ────────────────────────────────────────────────────────────
        public static SeasonSystem Instance { get; private set; }

        // ─── Inspector ────────────────────────────────────────────────────────────
        [SerializeField] private int xpPerTier = 1000;

        // ─── Persistence Keys ─────────────────────────────────────────────────────
        private const string KeyXP         = "blockside_season_xp";
        private const string KeySeason     = "blockside_season_data";
        private const string KeyPremium    = "blockside_season_premium";
        private const string KeyClaimed    = "blockside_season_claimed";

        // ─── Runtime State ────────────────────────────────────────────────────────
        private int _seasonXP;
        private bool _isPremiumPass;
        private HashSet<int> _claimedTiers = new HashSet<int>();
        private SeasonData _currentSeason;

        // ─── Unity Lifecycle ──────────────────────────────────────────────────────
        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
            LoadState();
            InitSeason();
        }

        // ─── Season Initialisation ────────────────────────────────────────────────
        private void InitSeason()
        {
            if (_currentSeason == null)
            {
                _currentSeason = new SeasonData
                {
                    seasonNumber = 1,
                    seasonName   = "Neon Genesis",
                    durationDays = 30,
                    endTimestampSec = DateTimeOffset.UtcNow.ToUnixTimeSeconds() + 30 * 86400L
                };
                SaveState();
            }
        }

        // ─── Battle Pass Tier Table ───────────────────────────────────────────────
        private TierReward GetTierReward(int tier)
        {
            // Pattern: every 5 tiers is a milestone
            if (tier % 10 == 9)  // tiers 9,19,29,39,49 — premium milestones
                return new TierReward { tier=tier, rewardType=TierRewardType.Skin, premiumOnly=true, itemId=$"skin_t{tier+1}" };
            if (tier % 5 == 4)   // tiers 4,14,24,34,44 — money milestones
                return new TierReward { tier=tier, rewardType=TierRewardType.Money, moneyAmount=(tier+1)*200 };
            if (tier == 49)      // tier 50 — legendary building
                return new TierReward { tier=tier, rewardType=TierRewardType.Building, premiumOnly=false, itemId="legendary_hq" };

            return new TierReward { tier=tier, rewardType=TierRewardType.Money, moneyAmount=(tier+1)*50 };
        }

        // ─── Public API ───────────────────────────────────────────────────────────

        /// <summary>Returns the current SeasonData.</summary>
        public SeasonData GetCurrentSeason() => _currentSeason;

        /// <summary>Returns the player's current 0-based tier (0 = not started, max 49).</summary>
        public int GetCurrentTier() => Mathf.Min(_seasonXP / xpPerTier, 49);

        /// <summary>Returns the total accumulated season XP.</summary>
        public int GetSeasonXP() => _seasonXP;

        /// <summary>Returns XP required for the next tier (progress within current tier).</summary>
        public int GetXPInCurrentTier() => _seasonXP % xpPerTier;

        /// <summary>Returns whether the player owns the Premium Battle Pass.</summary>
        public bool IsPremiumPass => _isPremiumPass;

        /// <summary>
        /// Adds season XP and potentially advances the tier.
        /// </summary>
        public void AddSeasonXP(int amount)
        {
            int oldTier = GetCurrentTier();
            _seasonXP += Mathf.Max(0, amount);
            int newTier = GetCurrentTier();
            SaveState();

            for (int t = oldTier + 1; t <= newTier && t <= 49; t++)
                Debug.Log($"[SeasonSystem] Tier {t + 1} unlocked!");
        }

        /// <summary>
        /// Claims the reward for a specific tier.
        /// Returns false if already claimed, not yet reached, or premium-only without pass.
        /// </summary>
        public bool ClaimTierReward(int tier)
        {
            if (_claimedTiers.Contains(tier)) return false;
            if (GetCurrentTier() < tier) return false;

            TierReward reward = GetTierReward(tier);
            if (reward.premiumOnly && !_isPremiumPass) return false;

            _claimedTiers.Add(tier);

            switch (reward.rewardType)
            {
                case TierRewardType.Money:
                    EconomyManager.Instance?.Earn(reward.moneyAmount);
                    break;
                case TierRewardType.Building:
                case TierRewardType.Item:
                case TierRewardType.Skin:
                    PlayerPrefs.SetInt($"blockside_reward_{reward.itemId}", 1);
                    PlayerPrefs.Save();
                    break;
            }
            SaveState();
            UIManager.Instance?.ShowToast($"🎁 Récompense Tier {tier + 1} réclamée !", "success");
            return true;
        }

        /// <summary>Returns the reward data for a given 0-based tier index.</summary>
        public TierReward GetRewardForTier(int tier) => GetTierReward(Mathf.Clamp(tier, 0, 49));

        /// <summary>Returns true if the reward for this tier has been claimed.</summary>
        public bool IsTierClaimed(int tier) => _claimedTiers.Contains(tier);

        /// <summary>Unlocks the Premium Battle Pass (called after Pi payment success).</summary>
        public void UnlockPremiumPass()
        {
            _isPremiumPass = true;
            SaveState();
            UIManager.Instance?.ShowToast("⭐ Premium Battle Pass activé !", "success");
        }

        // ─── Persistence ──────────────────────────────────────────────────────────
        private void SaveState()
        {
            PlayerPrefs.SetInt(KeyXP, _seasonXP);
            PlayerPrefs.SetInt(KeyPremium, _isPremiumPass ? 1 : 0);
            PlayerPrefs.SetString(KeySeason, JsonUtility.ToJson(_currentSeason));

            // Serialise claimed tiers as comma-separated
            var list = new List<string>();
            foreach (int t in _claimedTiers) list.Add(t.ToString());
            PlayerPrefs.SetString(KeyClaimed, string.Join(",", list));
            PlayerPrefs.Save();
        }

        private void LoadState()
        {
            _seasonXP      = PlayerPrefs.GetInt(KeyXP, 0);
            _isPremiumPass = PlayerPrefs.GetInt(KeyPremium, 0) == 1;

            string seasonJson = PlayerPrefs.GetString(KeySeason, "");
            if (!string.IsNullOrEmpty(seasonJson))
            {
                try { _currentSeason = JsonUtility.FromJson<SeasonData>(seasonJson); } catch { }
            }

            string claimed = PlayerPrefs.GetString(KeyClaimed, "");
            if (!string.IsNullOrEmpty(claimed))
                foreach (string s in claimed.Split(','))
                    if (int.TryParse(s, out int t)) _claimedTiers.Add(t);
        }
    }
}
