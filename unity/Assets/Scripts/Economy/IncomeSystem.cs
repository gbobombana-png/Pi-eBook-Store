using UnityEngine;
using System;
using System.Collections.Generic;
using BLOCKSIDE.Core;

namespace BLOCKSIDE.Economy
{
    /// <summary>
    /// Calculates and tracks passive income for all placed buildings.
    /// Income is capped at 60 minutes of accumulation per building.
    /// </summary>
    public class IncomeSystem : MonoBehaviour
    {
        #region Constants
        private const float MAX_ACCUMULATION_MINUTES = 60f;
        private const float TICK_INTERVAL = 10f; // seconds between visual updates
        #endregion

        #region State
        private float tickTimer;
        #endregion

        #region Events
        public static event Action<long> OnTotalPendingChanged;    // total pending across all districts
        public static event Action<string, long> OnDistrictPendingChanged; // districtId, pending
        #endregion

        #region Tick
        /// <summary>Called by GameManager every frame.</summary>
        public void Tick(float deltaTime)
        {
            tickTimer += deltaTime;
            if (tickTimer >= TICK_INTERVAL)
            {
                tickTimer = 0f;
                BroadcastPendingChanges();
            }
        }

        private void BroadcastPendingChanges()
        {
            var bm = GameManager.Instance?.Buildings;
            var gm = GameManager.Instance;
            if (bm == null || gm == null) return;

            string charId = PlayerPrefs.GetString("selectedCharacter", "");
            bool vip = gm.Marketplace.IsOwned("vip");

            long total = 0;
            foreach (var d in GetDistrictIds())
            {
                long pending = CalculateDistrictPending(d, charId, vip);
                total += pending;
                OnDistrictPendingChanged?.Invoke(d, pending);
            }
            OnTotalPendingChanged?.Invoke(total);
        }
        #endregion

        #region Calculations
        /// <summary>
        /// Calculates pending income for a single building.
        /// Caps at MAX_ACCUMULATION_MINUTES of income.
        /// </summary>
        public long CalculatePendingIncome(PlacedBuilding building, string characterId, bool vipActive)
        {
            var bm = GameManager.Instance?.Buildings;
            if (bm == null) return 0;
            var def = bm.GetDefinition(building.buildingId);
            if (def == null) return 0;

            long nowMs = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            float elapsedMinutes = Mathf.Min((nowMs - building.lastCollectTimestamp) / 60000f, MAX_ACCUMULATION_MINUTES);

            float incomePerMin = def.baseIncomePerMin * building.level;
            if (vipActive) incomePerMin *= 2f;
            if (characterId == "zay") incomePerMin *= 1.2f;

            return (long)(elapsedMinutes * incomePerMin);
        }

        /// <summary>Total pending income for a district.</summary>
        public long CalculateDistrictPending(string districtId, string characterId, bool vipActive)
        {
            var bm = GameManager.Instance?.Buildings;
            if (bm == null) return 0;
            long total = 0;
            foreach (var b in bm.GetInDistrict(districtId))
                total += CalculatePendingIncome(b, characterId, vipActive);
            return total;
        }

        /// <summary>Total pending income across all districts.</summary>
        public long CalculateTotalPending(string characterId, bool vipActive)
        {
            long total = 0;
            foreach (var d in GetDistrictIds())
                total += CalculateDistrictPending(d, characterId, vipActive);
            return total;
        }

        /// <summary>Income per minute across a district.</summary>
        public long GetDistrictIncomePerMin(string districtId, string characterId, bool vipActive)
        {
            return GameManager.Instance?.Buildings.GetDistrictIncomePerMin(districtId, characterId, vipActive) ?? 0;
        }
        #endregion

        #region Collect
        /// <summary>
        /// Collects all pending income for a district.
        /// Resets lastCollect timestamp for each building.
        /// Returns total collected.
        /// </summary>
        public long CollectDistrict(string districtId)
        {
            var bm = GameManager.Instance?.Buildings;
            var economy = GameManager.Instance?.Economy;
            if (bm == null || economy == null) return 0;

            string charId = PlayerPrefs.GetString("selectedCharacter", "");
            bool vip = GameManager.Instance?.Marketplace.IsOwned("vip") ?? false;

            long total = 0;
            long nowMs = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            foreach (var b in bm.GetInDistrict(districtId))
            {
                long earned = CalculatePendingIncome(b, charId, vip);
                total += earned;
                b.lastCollectTimestamp = nowMs;
            }
            if (total > 0)
            {
                economy.Earn(total, "Collect " + districtId);
                OnDistrictPendingChanged?.Invoke(districtId, 0);
                GameManager.Instance?.SaveGame();
            }
            return total;
        }

        /// <summary>Collects income for a single building slot.</summary>
        public long CollectBuilding(string districtId, int slotIndex)
        {
            var bm = GameManager.Instance?.Buildings;
            var economy = GameManager.Instance?.Economy;
            if (bm == null || economy == null) return 0;

            var b = bm.GetAtSlot(districtId, slotIndex);
            if (b == null) return 0;

            string charId = PlayerPrefs.GetString("selectedCharacter", "");
            bool vip = GameManager.Instance?.Marketplace.IsOwned("vip") ?? false;

            long earned = CalculatePendingIncome(b, charId, vip);
            if (earned > 0)
            {
                b.lastCollectTimestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
                economy.Earn(earned, "Collect building");
            }
            return earned;
        }
        #endregion

        #region Helpers
        private static readonly string[] DistrictIds = { "lowside", "neon_market", "sky_district", "underblock", "the_edge" };
        private IEnumerable<string> GetDistrictIds() => DistrictIds;
        #endregion
    }
}
