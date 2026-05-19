using UnityEngine;
using System;
using System.Collections.Generic;

namespace BLOCKSIDE.Social
{
    [Serializable]
    public class RepTier
    {
        public int minReputation;
        public string title;
        public string districtUnlock; // districtId to unlock at this tier, or ""
    }

    /// <summary>
    /// Manages player reputation, title progression, and district unlock checks.
    /// </summary>
    public class ReputationSystem : MonoBehaviour
    {
        #region Inspector
        [SerializeField] private List<RepTier> tiers = new List<RepTier>();
        #endregion

        #region State
        private int reputation;
        private string currentTitle = "Street Rookie";
        #endregion

        #region Events
        public static event Action<int, int> OnReputationChanged;   // (newRep, delta)
        public static event Action<string> OnTitleUnlocked;          // new title
        public static event Action<string> OnDistrictUnlocked;       // districtId
        #endregion

        #region Properties
        public int Reputation => reputation;
        public string CurrentTitle => currentTitle;
        #endregion

        #region Init
        private void Awake()
        {
            if (tiers == null || tiers.Count == 0) InitDefaultTiers();
        }

        private void InitDefaultTiers()
        {
            tiers = new List<RepTier>
            {
                new RepTier{minReputation=0,     title="Street Rookie",    districtUnlock="lowside"},
                new RepTier{minReputation=100,   title="Block Hustler",    districtUnlock=""},
                new RepTier{minReputation=500,   title="District Boss",    districtUnlock="neon_market"},
                new RepTier{minReputation=1000,  title="District Boss",    districtUnlock="underblock"},
                new RepTier{minReputation=2000,  title="City Legend",      districtUnlock="sky_district"},
                new RepTier{minReputation=5000,  title="Underground King", districtUnlock="the_edge"},
                new RepTier{minReputation=15000, title="BLOCKSIDE GOD",    districtUnlock=""}
            };
        }

        public void LoadData(int savedRep)
        {
            reputation = savedRep;
            currentTitle = ComputeTitle(reputation);
        }

        public void Reset()
        {
            reputation = 0;
            currentTitle = "Street Rookie";
        }
        #endregion

        #region Add Reputation
        /// <summary>Adds reputation and triggers tier checks.</summary>
        public void AddReputation(int amount)
        {
            if (amount <= 0) return;
            int prev = reputation;
            reputation += amount;
            OnReputationChanged?.Invoke(reputation, amount);
            CheckTierProgression(prev, reputation);
        }

        private void CheckTierProgression(int prevRep, int newRep)
        {
            string newTitle = ComputeTitle(newRep);
            if (newTitle != currentTitle)
            {
                currentTitle = newTitle;
                OnTitleUnlocked?.Invoke(newTitle);
                Debug.Log($"[ReputationSystem] New title: {newTitle}");
            }
            // Check district unlocks
            foreach (var tier in tiers)
            {
                if (prevRep < tier.minReputation && newRep >= tier.minReputation)
                {
                    if (!string.IsNullOrEmpty(tier.districtUnlock))
                    {
                        OnDistrictUnlocked?.Invoke(tier.districtUnlock);
                        Debug.Log($"[ReputationSystem] District unlocked: {tier.districtUnlock}");
                    }
                }
            }
        }
        #endregion

        #region Helpers
        private string ComputeTitle(int rep)
        {
            string title = "Street Rookie";
            foreach (var t in tiers)
                if (rep >= t.minReputation) title = t.title;
            return title;
        }

        /// <summary>Progress toward next tier (0..1).</summary>
        public float GetTierProgress()
        {
            RepTier current = null, next = null;
            for (int i = 0; i < tiers.Count; i++)
            {
                if (reputation >= tiers[i].minReputation) current = tiers[i];
                else if (current != null && next == null) { next = tiers[i]; break; }
            }
            if (current == null) return 0f;
            if (next == null) return 1f;
            float range = next.minReputation - current.minReputation;
            float progress = reputation - current.minReputation;
            return Mathf.Clamp01(progress / range);
        }

        public RepTier GetNextTier()
        {
            foreach (var t in tiers)
                if (reputation < t.minReputation) return t;
            return null;
        }

        public bool IsDistrictUnlocked(string districtId)
        {
            foreach (var t in tiers)
                if (t.districtUnlock == districtId && reputation >= t.minReputation) return true;
            if (districtId == "lowside") return true; // always unlocked
            return false;
        }
        #endregion
    }
}
