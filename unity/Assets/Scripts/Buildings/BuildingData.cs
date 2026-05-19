using System;
using UnityEngine;

namespace BLOCKSIDE
{
    /// <summary>Rarity tier for a building, drives visual colour and income scaling.</summary>
    public enum Rarity
    {
        Common,
        Rare,
        Epic,
        Legendary,
        Mythic
    }

    /// <summary>
    /// ScriptableObject that stores all static data for a building type.
    /// Create via Assets > Create > BLOCKSIDE > BuildingData.
    /// </summary>
    [CreateAssetMenu(fileName = "BuildingData", menuName = "BLOCKSIDE/BuildingData", order = 1)]
    public class BuildingData : ScriptableObject
    {
        // ─── Identity ─────────────────────────────────────────────────────────────
        [Header("Identity")]
        [SerializeField] private string id;
        [SerializeField] private string buildingName;
        [SerializeField, TextArea(2, 4)] private string description;
        [SerializeField] private Sprite icon;
        [SerializeField] private GameObject prefab;

        // ─── Economy ──────────────────────────────────────────────────────────────
        [Header("Economy")]
        [SerializeField] private int baseCost = 100;
        [SerializeField] private int baseIncome = 10;   // per minute
        [SerializeField] private int repGain = 5;

        // ─── Progression ─────────────────────────────────────────────────────────
        [Header("Progression")]
        [SerializeField] private int maxLevel = 5;
        [SerializeField] private float upgradeCostMultiplier = 2f;

        // ─── Placement ───────────────────────────────────────────────────────────
        [Header("Placement")]
        [SerializeField] private Rarity rarity = Rarity.Common;
        [SerializeField] private string[] allowedDistricts;

        // ─── Properties ──────────────────────────────────────────────────────────
        /// <summary>Unique string key used in save data and lookups.</summary>
        public string Id => id;
        public string BuildingName => buildingName;
        public string Description => description;
        public Sprite Icon => icon;
        public GameObject Prefab => prefab;
        public int BaseCost => baseCost;
        public int BaseIncome => baseIncome;
        public int RepGain => repGain;
        public int MaxLevel => maxLevel;
        public float UpgradeCostMultiplier => upgradeCostMultiplier;
        public Rarity Rarity => rarity;
        public string[] AllowedDistricts => allowedDistricts;

        /// <summary>Returns the display colour for this building's rarity.</summary>
        public Color RarityColor
        {
            get
            {
                switch (rarity)
                {
                    case Rarity.Common:    return new Color(0.67f, 0.67f, 0.80f);
                    case Rarity.Rare:      return new Color(0.18f, 0.61f, 1.00f);
                    case Rarity.Epic:      return new Color(0.61f, 0.18f, 1.00f);
                    case Rarity.Legendary: return new Color(1.00f, 0.84f, 0.00f);
                    case Rarity.Mythic:    return new Color(1.00f, 0.18f, 0.47f);
                    default:               return Color.white;
                }
            }
        }

        /// <summary>Returns the cost to upgrade from <paramref name="currentLevel"/> to the next level.</summary>
        public int GetUpgradeCost(int currentLevel)
        {
            return Mathf.RoundToInt(baseCost * currentLevel * upgradeCostMultiplier);
        }

        /// <summary>Returns income per minute at <paramref name="level"/>.</summary>
        public int GetIncomeAtLevel(int level)
        {
            return baseIncome * Mathf.Max(1, level);
        }

        /// <summary>Returns true when <paramref name="districtId"/> is in the allowed list.</summary>
        public bool IsAllowedInDistrict(string districtId)
        {
            if (allowedDistricts == null || allowedDistricts.Length == 0) return true;
            foreach (string d in allowedDistricts)
                if (string.Equals(d, districtId, StringComparison.OrdinalIgnoreCase)) return true;
            return false;
        }
    }
}
