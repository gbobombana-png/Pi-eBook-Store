using System;
using UnityEngine;
using UnityEngine.EventSystems;

namespace BLOCKSIDE
{
    /// <summary>
    /// Abstract base class for every placed building in the game world.
    /// Handles income accumulation, level-up logic, events, and mobile tap detection.
    /// Concrete buildings override OnPlace(), OnUpgrade(), and OnCollect().
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public abstract class BuildingBase : MonoBehaviour, IPointerClickHandler
    {
        // ─── Events ───────────────────────────────────────────────────────────────
        /// <summary>Fired when accumulated income is ready to be collected (threshold reached).</summary>
        public static event Action<BuildingBase> OnIncomeReady;
        /// <summary>Fired when the building is successfully upgraded.</summary>
        public static event Action<BuildingBase, int> OnLevelUp;
        /// <summary>Fired when the building is removed from the world.</summary>
        public static event Action<BuildingBase> OnDestroyed;

        // ─── Inspector ────────────────────────────────────────────────────────────
        [Header("Building Runtime")]
        [SerializeField] protected BuildingData buildingData;

        // ─── Runtime State ────────────────────────────────────────────────────────
        /// <summary>Current level (1-based, max defined in BuildingData).</summary>
        public int Level { get; private set; } = 1;
        /// <summary>Epoch milliseconds when the building was placed.</summary>
        public long PlacedAt { get; private set; }
        /// <summary>Epoch milliseconds of the last income collection.</summary>
        public long LastCollect { get; private set; }

        protected string DistrictId;

        // Income-ready notification tracking
        private bool _incomeReadyNotified;

        // ─── Unity Lifecycle ──────────────────────────────────────────────────────
        protected virtual void Awake()
        {
            PlacedAt   = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            LastCollect = PlacedAt;
        }

        protected virtual void Update()
        {
            // Notify once when income crosses the base-income threshold
            if (!_incomeReadyNotified && GetPendingIncome() >= buildingData.BaseIncome)
            {
                _incomeReadyNotified = true;
                OnIncomeReady?.Invoke(this);
            }
        }

        protected virtual void OnDestroy()
        {
            OnDestroyed?.Invoke(this);
        }

        // ─── Abstract Hooks ───────────────────────────────────────────────────────

        /// <summary>Called once immediately after the building is placed on the grid.</summary>
        public abstract void OnPlace();

        /// <summary>Called immediately after a successful upgrade.</summary>
        public abstract void OnUpgrade(int newLevel);

        /// <summary>Called when income is collected from this building.</summary>
        public abstract void OnCollect(int amount);

        // ─── Concrete Logic ───────────────────────────────────────────────────────

        /// <summary>
        /// Initialises the building after instantiation.
        /// Must be called by BuildingPlacer right after placing.
        /// </summary>
        public void Initialise(BuildingData data, string districtId, int level = 1)
        {
            buildingData = data;
            DistrictId   = districtId;
            Level        = Mathf.Clamp(level, 1, data.MaxLevel);
            LastCollect  = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            PlacedAt     = LastCollect;
        }

        /// <summary>Returns how much money has accumulated since the last collection (max 60 min cap).</summary>
        public int GetPendingIncome()
        {
            if (buildingData == null) return 0;

            long nowMs    = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            float minutes = Mathf.Min((nowMs - LastCollect) / 60000f, 60f);
            float income  = minutes * buildingData.GetIncomeAtLevel(Level);

            // Apply live event multiplier if available
            if (LiveEventManager.Instance != null)
                income *= LiveEventManager.Instance.GetEventMultiplier(DistrictId);

            // Apply vehicle bonus if available
            if (VehicleManager.Instance != null)
                income *= VehicleManager.Instance.GetBonusMultiplier(DistrictId);

            return Mathf.FloorToInt(income);
        }

        /// <summary>
        /// Collects all pending income and resets the timer.
        /// Returns the amount collected.
        /// </summary>
        public int CollectIncome()
        {
            int amount = GetPendingIncome();
            if (amount > 0)
            {
                LastCollect = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
                _incomeReadyNotified = false;
                OnCollect(amount);

                // Track mission progress
                MissionManager.Instance?.TrackProgress(MissionType.Collect, 1);
            }
            return amount;
        }

        /// <summary>
        /// Attempts to upgrade the building.
        /// Returns true on success, false if max level or insufficient funds.
        /// </summary>
        public bool Upgrade()
        {
            if (buildingData == null) return false;
            if (Level >= buildingData.MaxLevel) return false;

            int cost = buildingData.GetUpgradeCost(Level);
            EconomyManager economy = EconomyManager.Instance;
            if (economy == null || !economy.TrySpend(cost)) return false;

            Level++;
            OnUpgrade(Level);
            OnLevelUp?.Invoke(this, Level);
            MissionManager.Instance?.TrackProgress(MissionType.Upgrade, 1);
            return true;
        }

        // ─── Mobile Tap ──────────────────────────────────────────────────────────

        /// <summary>Opens the building detail panel when tapped on mobile.</summary>
        public void OnPointerClick(PointerEventData eventData)
        {
            UIManager.Instance?.OpenBuildingDetail(this);
        }

        // ─── Gizmos ───────────────────────────────────────────────────────────────
#if UNITY_EDITOR
        protected virtual void OnDrawGizmosSelected()
        {
            Gizmos.color = new Color(0f, 1f, 0.5f, 0.3f);
            Gizmos.DrawSphere(transform.position, 1.5f);
            Gizmos.color = new Color(0f, 1f, 0.5f, 0.8f);
            Gizmos.DrawWireSphere(transform.position, 1.5f);
        }
#endif
    }
}
