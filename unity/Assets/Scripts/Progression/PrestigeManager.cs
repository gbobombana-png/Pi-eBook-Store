using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Events;

namespace Blockside.Progression
{
    [Serializable]
    public class PrestigeTier
    {
        public int level;
        public string name;
        public string bonusDescription;
        public string icon;
        public int requiredReputation;
        public long requiredMoney;
        public float incomeBonusMultiplier;
        public string unlockedSkinId;
    }

    public class PrestigeManager : MonoBehaviour
    {
        public static PrestigeManager Instance { get; private set; }

        [Header("Prestige Tiers")]
        public List<PrestigeTier> tiers = new()
        {
            new PrestigeTier { level=1, name="Prestige I",   icon="⭐", requiredReputation=10000,  requiredMoney=250000,  incomeBonusMultiplier=0.15f, bonusDescription="+15% tous les revenus" },
            new PrestigeTier { level=2, name="Prestige II",  icon="🌟", requiredReputation=30000,  requiredMoney=1000000, incomeBonusMultiplier=0.35f, bonusDescription="+35% tous les revenus + titre exclusif" },
            new PrestigeTier { level=3, name="Prestige III", icon="💫", requiredReputation=75000,  requiredMoney=5000000, incomeBonusMultiplier=0.60f, bonusDescription="+60% tous les revenus + skin Gold offert", unlockedSkinId="gold" },
        };

        public UnityEvent<int> OnPrestigeActivated;
        public UnityEvent<float> OnBonusUpdated;

        public int CurrentPrestigeLevel { get; private set; }
        public float CurrentIncomeBonus => ComputeBonus(CurrentPrestigeLevel);

        void Awake()
        {
            if (Instance != null) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }

        void Start()
        {
            CurrentPrestigeLevel = SaveManager.Instance?.LoadInt("prestige_level") ?? 0;
        }

        public bool CanPrestige(int targetLevel, long currentMoney, int currentRep)
        {
            var tier = GetTier(targetLevel);
            if (tier == null) return false;
            if (CurrentPrestigeLevel >= targetLevel) return false;
            return currentRep >= tier.requiredReputation && currentMoney >= tier.requiredMoney;
        }

        public bool ActivatePrestige(int level)
        {
            var playerData = GameManager.Instance?.GetPlayerData();
            if (playerData == null) return false;

            if (!CanPrestige(level, playerData.money, playerData.reputation))
            {
                Debug.LogWarning($"[Prestige] Cannot activate level {level}: insufficient resources.");
                return false;
            }

            CurrentPrestigeLevel = level;
            SaveManager.Instance?.SaveInt("prestige_level", level);

            // Reset core progression (keep faction and premium)
            playerData.money = 500;
            playerData.reputation = 0;
            playerData.totalBuildings = 0;
            playerData.totalEarned = 0;
            GameManager.Instance?.ClearAllBuildings();

            // Grant skin reward if applicable
            var tier = GetTier(level);
            if (!string.IsNullOrEmpty(tier?.unlockedSkinId))
                SkinManager.Instance?.UnlockSkin(tier.unlockedSkinId);

            OnPrestigeActivated?.Invoke(level);
            OnBonusUpdated?.Invoke(CurrentIncomeBonus);

            Debug.Log($"[Prestige] Level {level} activated — bonus: +{CurrentIncomeBonus * 100:F0}%");
            return true;
        }

        public PrestigeTier GetTier(int level) => tiers.Find(t => t.level == level);
        public PrestigeTier GetNextTier() => tiers.Find(t => t.level == CurrentPrestigeLevel + 1);

        float ComputeBonus(int level)
        {
            var tier = GetTier(level);
            return tier?.incomeBonusMultiplier ?? 0f;
        }
    }
}
