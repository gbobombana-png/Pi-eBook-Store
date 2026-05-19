using UnityEngine;
using System;
using System.Collections.Generic;
using System.Linq;
using BLOCKSIDE.Core;

namespace BLOCKSIDE.Economy
{
    // ─────────────────────────────────────────────────────────────
    // Data definitions
    // ─────────────────────────────────────────────────────────────

    [Serializable]
    public class BuildingDefinition
    {
        public string id;
        public string displayName;
        public string emoji;
        public long baseCost;
        public long baseIncomePerMin;
        public int baseRepReward;
        public string rarity;           // common, rare, epic, legendary, mythic
        public List<string> allowedDistricts = new List<string>();
        public int maxLevel = 5;
    }

    [Serializable]
    public class PlacedBuilding
    {
        public string buildingId;
        public string districtId;
        public int slotIndex;
        public int level;
        public long lastCollectTimestamp; // Unix ms
    }

    // ─────────────────────────────────────────────────────────────
    // BuildingManager
    // ─────────────────────────────────────────────────────────────

    /// <summary>
    /// Manages building placement, upgrades, and per-building income for all districts.
    /// </summary>
    public class BuildingManager : MonoBehaviour
    {
        #region Inspector
        [Header("Building Catalog")]
        [SerializeField] private List<BuildingDefinition> catalog = new List<BuildingDefinition>();
        #endregion

        #region State
        private Dictionary<string, List<PlacedBuilding>> placedByDistrict = new Dictionary<string, List<PlacedBuilding>>();
        #endregion

        #region Events
        public static event Action<PlacedBuilding> OnBuildingPlaced;
        public static event Action<PlacedBuilding> OnBuildingUpgraded;
        public static event Action<string, long> OnBuildingIncomeCollected; // districtId, amount
        #endregion

        #region Init
        private void Awake()
        {
            if (catalog == null || catalog.Count == 0) InitDefaultCatalog();
        }

        private void InitDefaultCatalog()
        {
            catalog = new List<BuildingDefinition>
            {
                new BuildingDefinition{id="snack",displayName="Snack Shop",emoji="🍔",baseCost=100,baseIncomePerMin=10,baseRepReward=5,rarity="common",allowedDistricts=new List<string>{"lowside","neon_market"}},
                new BuildingDefinition{id="parking",displayName="Parking",emoji="🚗",baseCost=300,baseIncomePerMin=15,baseRepReward=8,rarity="common",allowedDistricts=new List<string>{"lowside","neon_market","sky_district"}},
                new BuildingDefinition{id="studio",displayName="Mini Studio",emoji="🎵",baseCost=500,baseIncomePerMin=25,baseRepReward=15,rarity="rare",allowedDistricts=new List<string>{"lowside","neon_market","underblock"}},
                new BuildingDefinition{id="club",displayName="Club Neon",emoji="🎉",baseCost=2000,baseIncomePerMin=80,baseRepReward=40,rarity="rare",allowedDistricts=new List<string>{"lowside","neon_market","underblock"}},
                new BuildingDefinition{id="apartment",displayName="Luxury Apartment",emoji="🏢",baseCost=8000,baseIncomePerMin=200,baseRepReward=100,rarity="epic",allowedDistricts=new List<string>{"sky_district","neon_market"}},
                new BuildingDefinition{id="blackmarket",displayName="Black Market",emoji="🕵️",baseCost=20000,baseIncomePerMin=500,baseRepReward=200,rarity="legendary",allowedDistricts=new List<string>{"underblock","the_edge"}},
                new BuildingDefinition{id="gallery",displayName="Neon Gallery",emoji="🖼️",baseCost=12000,baseIncomePerMin=350,baseRepReward=150,rarity="epic",allowedDistricts=new List<string>{"sky_district","neon_market"}},
                new BuildingDefinition{id="helipad",displayName="Hélipad Privé",emoji="🚁",baseCost=50000,baseIncomePerMin=1000,baseRepReward=500,rarity="mythic",allowedDistricts=new List<string>{"sky_district","the_edge"}}
            };
        }

        public void LoadData(List<BuildingSaveData> saved)
        {
            placedByDistrict.Clear();
            if (saved == null) return;
            foreach (var s in saved)
            {
                if (!placedByDistrict.ContainsKey(s.districtId))
                    placedByDistrict[s.districtId] = new List<PlacedBuilding>();
                placedByDistrict[s.districtId].Add(new PlacedBuilding
                {
                    buildingId = s.buildingId,
                    districtId = s.districtId,
                    slotIndex = s.slotIndex,
                    level = s.level,
                    lastCollectTimestamp = s.lastCollectTimestamp
                });
            }
        }

        public void Reset()
        {
            placedByDistrict.Clear();
        }
        #endregion

        #region Queries
        public BuildingDefinition GetDefinition(string buildingId) =>
            catalog.FirstOrDefault(b => b.id == buildingId);

        public List<BuildingDefinition> GetAvailableFor(string districtId) =>
            catalog.Where(b => b.allowedDistricts.Contains(districtId)).ToList();

        public List<PlacedBuilding> GetInDistrict(string districtId) =>
            placedByDistrict.TryGetValue(districtId, out var list) ? list : new List<PlacedBuilding>();

        public PlacedBuilding GetAtSlot(string districtId, int slotIndex) =>
            GetInDistrict(districtId).FirstOrDefault(b => b.slotIndex == slotIndex);

        public int TotalPlacedCount() => placedByDistrict.Values.Sum(l => l.Count);

        public long GetDistrictIncomePerMin(string districtId, string characterId, bool vipActive)
        {
            long total = 0;
            foreach (var b in GetInDistrict(districtId))
            {
                var def = GetDefinition(b.buildingId);
                if (def == null) continue;
                long income = def.baseIncomePerMin * b.level;
                if (vipActive) income *= 2;
                if (characterId == "zay") income = (long)(income * 1.2f);
                total += income;
            }
            return total;
        }
        #endregion

        #region Placement
        /// <summary>Places a building in a district slot after spending money.</summary>
        public bool PlaceBuilding(string districtId, string buildingId, int slotIndex, string characterId)
        {
            var def = GetDefinition(buildingId);
            if (def == null) { Debug.LogWarning("[BuildingManager] Unknown building: " + buildingId); return false; }
            if (!def.allowedDistricts.Contains(districtId)) { Debug.LogWarning("[BuildingManager] District not allowed."); return false; }
            if (GetAtSlot(districtId, slotIndex) != null) { Debug.LogWarning("[BuildingManager] Slot occupied."); return false; }

            long cost = CalculateCost(def, characterId);
            var economy = GameManager.Instance?.Economy;
            if (economy != null && !economy.Spend(cost, "Build " + def.displayName)) return false;

            if (!placedByDistrict.ContainsKey(districtId))
                placedByDistrict[districtId] = new List<PlacedBuilding>();

            var building = new PlacedBuilding
            {
                buildingId = buildingId,
                districtId = districtId,
                slotIndex = slotIndex,
                level = 1,
                lastCollectTimestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
            };
            placedByDistrict[districtId].Add(building);
            GameManager.Instance?.Reputation.AddReputation(def.baseRepReward);
            OnBuildingPlaced?.Invoke(building);
            Debug.Log($"[BuildingManager] Placed {def.displayName} in {districtId}[{slotIndex}]");
            return true;
        }

        public long CalculateCost(BuildingDefinition def, string characterId)
        {
            long cost = def.baseCost;
            if (characterId == "nova") cost = (long)(cost * 0.85f);
            return cost;
        }
        #endregion

        #region Upgrade
        /// <summary>Upgrades a building by one level. Cost = baseCost * level * 2.</summary>
        public bool UpgradeBuilding(string districtId, int slotIndex)
        {
            var building = GetAtSlot(districtId, slotIndex);
            if (building == null) return false;
            var def = GetDefinition(building.buildingId);
            if (def == null) return false;
            if (building.level >= def.maxLevel) { Debug.Log("[BuildingManager] Max level reached."); return false; }

            long upgradeCost = (long)(def.baseCost * building.level * 2);
            var economy = GameManager.Instance?.Economy;
            if (economy != null && !economy.Spend(upgradeCost, "Upgrade " + def.displayName)) return false;

            building.level++;
            OnBuildingUpgraded?.Invoke(building);
            Debug.Log($"[BuildingManager] Upgraded {def.displayName} → Lv{building.level}");
            return true;
        }

        public long GetUpgradeCost(string districtId, int slotIndex)
        {
            var b = GetAtSlot(districtId, slotIndex);
            if (b == null) return 0;
            var def = GetDefinition(b.buildingId);
            if (def == null || b.level >= def.maxLevel) return 0;
            return (long)(def.baseCost * b.level * 2);
        }
        #endregion

        #region Save
        public List<BuildingSaveData> GetBuildingSaveData()
        {
            var result = new List<BuildingSaveData>();
            foreach (var kv in placedByDistrict)
                foreach (var b in kv.Value)
                    result.Add(new BuildingSaveData
                    {
                        buildingId = b.buildingId,
                        districtId = b.districtId,
                        slotIndex = b.slotIndex,
                        level = b.level,
                        lastCollectTimestamp = b.lastCollectTimestamp
                    });
            return result;
        }
        #endregion
    }
}
