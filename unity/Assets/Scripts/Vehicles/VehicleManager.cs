using System;
using System.Collections.Generic;
using UnityEngine;

namespace BLOCKSIDE
{
    /// <summary>How the vehicle's cost is denominated.</summary>
    public enum VehicleCostType
    {
        Money,
        Pi
    }

    /// <summary>Which aspect of the economy the vehicle bonus affects.</summary>
    public enum VehicleBonusType
    {
        DistrictRevenue,   // bonus to a specific district
        AllCollection      // bonus to collecting from all districts
    }

    [Serializable]
    public class VehicleData
    {
        public string id;
        public string vehicleName;
        public string emoji;
        public int costMoney;        // used when costType == Money
        public float costPi;         // used when costType == Pi
        public VehicleCostType costType;
        public VehicleBonusType bonusType;
        /// <summary>Multiplier added on top of base (e.g., 0.10 = +10%).</summary>
        public float bonusValue;
        /// <summary>District id this bonus targets. Empty = all districts.</summary>
        public string targetDistrict;
        public string description;
    }

    /// <summary>
    /// Manages vehicle ownership, activation, and income bonus application.
    /// Only one vehicle can be active at a time.
    /// Purchases requiring Pi delegate to <see cref="PiNetworkManager"/>.
    /// State is persisted via PlayerPrefs.
    /// </summary>
    public class VehicleManager : MonoBehaviour
    {
        // ─── Singleton ────────────────────────────────────────────────────────────
        public static VehicleManager Instance { get; private set; }

        // ─── Vehicle Catalogue ────────────────────────────────────────────────────
        private static readonly VehicleData[] _catalogue =
        {
            new VehicleData
            {
                id="street_bike",  vehicleName="Street Bike",       emoji="🏍️",
                costMoney=2000,  costPi=0f, costType=VehicleCostType.Money,
                bonusType=VehicleBonusType.DistrictRevenue, bonusValue=0.10f,
                targetDistrict="lowside",
                description="+10% revenus Lowside"
            },
            new VehicleData
            {
                id="muscle_car",   vehicleName="Muscle Car",         emoji="🚗",
                costMoney=8000,  costPi=0f, costType=VehicleCostType.Money,
                bonusType=VehicleBonusType.DistrictRevenue, bonusValue=0.15f,
                targetDistrict="neon_market",
                description="+15% revenus Neon Market"
            },
            new VehicleData
            {
                id="armored_truck",vehicleName="Armored Truck",      emoji="🚛",
                costMoney=25000, costPi=0f, costType=VehicleCostType.Money,
                bonusType=VehicleBonusType.AllCollection,   bonusValue=0.20f,
                targetDistrict="",
                description="+20% collecte tous districts"
            },
            new VehicleData
            {
                id="attack_heli",  vehicleName="Attack Helicopter",  emoji="🚁",
                costMoney=0,     costPi=3f, costType=VehicleCostType.Pi,
                bonusType=VehicleBonusType.DistrictRevenue, bonusValue=0.50f,
                targetDistrict="the_edge",
                description="+50% revenus The Edge"
            },
            new VehicleData
            {
                id="speed_boat",   vehicleName="Speed Boat",         emoji="⛵",
                costMoney=0,     costPi=1f, costType=VehicleCostType.Pi,
                bonusType=VehicleBonusType.DistrictRevenue, bonusValue=0.25f,
                targetDistrict="coastline",
                description="+25% revenus Coastline"
            },
        };

        // ─── Persistence Keys ─────────────────────────────────────────────────────
        private const string KeyOwned  = "blockside_vehicles_owned";
        private const string KeyActive = "blockside_vehicle_active";

        // ─── Runtime State ────────────────────────────────────────────────────────
        private HashSet<string> _ownedIds  = new HashSet<string>();
        private string _activeVehicleId    = "";

        // ─── Unity Lifecycle ──────────────────────────────────────────────────────
        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
            LoadState();
        }

        // ─── Public API ───────────────────────────────────────────────────────────

        /// <summary>Returns the full vehicle catalogue.</summary>
        public VehicleData[] GetCatalogue() => _catalogue;

        /// <summary>Returns true if the player owns the vehicle with this id.</summary>
        public bool IsOwned(string vehicleId) => _ownedIds.Contains(vehicleId);

        /// <summary>Returns the id of the currently active vehicle, or empty string if none.</summary>
        public string GetActiveVehicleId() => _activeVehicleId;

        /// <summary>Returns the data for the currently active vehicle, or null if none.</summary>
        public VehicleData GetActiveVehicle()
        {
            if (string.IsNullOrEmpty(_activeVehicleId)) return null;
            return FindVehicle(_activeVehicleId);
        }

        /// <summary>
        /// Purchases a vehicle.
        /// Money vehicles are deducted immediately via EconomyManager.
        /// Pi vehicles delegate to PiNetworkManager; on success the callback grants ownership.
        /// </summary>
        public void PurchaseVehicle(string vehicleId)
        {
            VehicleData data = FindVehicle(vehicleId);
            if (data == null) { Debug.LogWarning($"[VehicleManager] Unknown vehicle id: {vehicleId}"); return; }
            if (_ownedIds.Contains(vehicleId)) { UIManager.Instance?.ShowToast("Véhicule déjà possédé !", "info"); return; }

            if (data.costType == VehicleCostType.Money)
            {
                if (!EconomyManager.Instance.TrySpend(data.costMoney))
                {
                    UIManager.Instance?.ShowToast("Pas assez d'argent !", "error");
                    return;
                }
                GrantVehicle(vehicleId);
            }
            else
            {
                // Pi payment flow — result handled via callback
                PiNetworkManager.Instance?.CreatePayment(
                    data.costPi,
                    $"BLOCKSIDE - {data.vehicleName}",
                    vehicleId,
                    onSuccess: () => GrantVehicle(vehicleId),
                    onError:   () => UIManager.Instance?.ShowToast("Paiement Pi échoué", "error")
                );
            }
        }

        /// <summary>
        /// Grants ownership of a vehicle directly (e.g., after Pi payment confirmation).
        /// </summary>
        public void GrantVehicle(string vehicleId)
        {
            _ownedIds.Add(vehicleId);
            // Auto-activate the first owned vehicle
            if (string.IsNullOrEmpty(_activeVehicleId))
                SetActiveVehicle(vehicleId);
            SaveState();
            UIManager.Instance?.ShowToast($"🚗 {FindVehicle(vehicleId)?.vehicleName} acquis !", "success");
        }

        /// <summary>
        /// Activates a vehicle the player already owns.
        /// Applies its bonus to the EconomyManager.
        /// </summary>
        public void SetActiveVehicle(string vehicleId)
        {
            if (!_ownedIds.Contains(vehicleId)) { UIManager.Instance?.ShowToast("Vous ne possédez pas ce véhicule !", "error"); return; }
            _activeVehicleId = vehicleId;
            SaveState();
        }

        /// <summary>
        /// Returns the income multiplier bonus (additive on top of 1.0) for a district
        /// from the currently active vehicle. Returns 1.0 if no bonus applies.
        /// </summary>
        public float GetBonusMultiplier(string districtId)
        {
            VehicleData v = GetActiveVehicle();
            if (v == null) return 1f;

            if (v.bonusType == VehicleBonusType.AllCollection)
                return 1f + v.bonusValue;

            if (v.bonusType == VehicleBonusType.DistrictRevenue &&
                string.Equals(v.targetDistrict, districtId, StringComparison.OrdinalIgnoreCase))
                return 1f + v.bonusValue;

            return 1f;
        }

        // ─── Persistence ──────────────────────────────────────────────────────────
        private void SaveState()
        {
            PlayerPrefs.SetString(KeyOwned,  string.Join(",", _ownedIds));
            PlayerPrefs.SetString(KeyActive, _activeVehicleId);
            PlayerPrefs.Save();
        }

        private void LoadState()
        {
            string owned = PlayerPrefs.GetString(KeyOwned, "");
            if (!string.IsNullOrEmpty(owned))
                foreach (string id in owned.Split(','))
                    if (!string.IsNullOrEmpty(id)) _ownedIds.Add(id);

            _activeVehicleId = PlayerPrefs.GetString(KeyActive, "");
        }

        // ─── Helpers ─────────────────────────────────────────────────────────────
        private VehicleData FindVehicle(string id)
        {
            foreach (var v in _catalogue)
                if (v.id == id) return v;
            return null;
        }
    }
}
