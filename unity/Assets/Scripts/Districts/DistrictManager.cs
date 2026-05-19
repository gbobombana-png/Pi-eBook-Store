using UnityEngine;
using System;
using System.Collections.Generic;
using System.Linq;
using BLOCKSIDE.Core;
using BLOCKSIDE.Social;
using BuildingSaveData = BLOCKSIDE.Core.BuildingSaveData;
using DistrictSaveData = BLOCKSIDE.Core.DistrictSaveData;

namespace BLOCKSIDE.Districts
{
    [Serializable]
    public class DistrictDefinition
    {
        public string id;
        public string displayName;
        public string emoji;
        public string vibe;
        public int requiredReputation;
        public int slotCount;
        public string gridLayout;  // "3x3", "3x4", "4x4"
        public Color themeColor;
        public bool featured;
    }

    [Serializable]
    public class DistrictState
    {
        public string districtId;
        public bool unlocked;
        public int extraSlots;
    }

    /// <summary>
    /// Manages district definitions, unlock states, and slot counts.
    /// Listens to reputation changes to auto-unlock districts.
    /// </summary>
    public class DistrictManager : MonoBehaviour
    {
        #region Inspector
        [SerializeField] private List<DistrictDefinition> definitions = new List<DistrictDefinition>();
        #endregion

        #region State
        private Dictionary<string, DistrictState> states = new Dictionary<string, DistrictState>();
        private int globalExtraSlots; // from District Key premium item
        #endregion

        #region Events
        public static event Action<string> OnDistrictUnlocked;  // districtId
        public static event Action OnDistrictStateChanged;
        #endregion

        #region Init
        private void Awake()
        {
            if (definitions == null || definitions.Count == 0) InitDefaultDefinitions();
            ReputationSystem.OnDistrictUnlocked += HandleReputationUnlock;
        }

        private void OnDestroy()
        {
            ReputationSystem.OnDistrictUnlocked -= HandleReputationUnlock;
        }

        private void InitDefaultDefinitions()
        {
            definitions = new List<DistrictDefinition>
            {
                new DistrictDefinition{id="lowside",displayName="LOWSIDE",emoji="🏚️",vibe="Underground street vibes",requiredReputation=0,slotCount=9,gridLayout="3x3",themeColor=new Color(1f,.42f,.1f),featured=true},
                new DistrictDefinition{id="neon_market",displayName="NEON MARKET",emoji="🌃",vibe="Centre économique holographique",requiredReputation=500,slotCount=12,gridLayout="3x4",themeColor=new Color(.18f,.61f,1f),featured=false},
                new DistrictDefinition{id="sky_district",displayName="SKY DISTRICT",emoji="🏙️",vibe="Skyline de luxe futuriste",requiredReputation=2000,slotCount=16,gridLayout="4x4",themeColor=new Color(.61f,.18f,1f),featured=false},
                new DistrictDefinition{id="underblock",displayName="UNDERBLOCK",emoji="🌑",vibe="Tunnels, clubs et marchés noirs",requiredReputation=1000,slotCount=9,gridLayout="3x3",themeColor=new Color(1f,.18f,.47f),featured=false},
                new DistrictDefinition{id="the_edge",displayName="THE EDGE",emoji="⚡",vibe="Territoire dangereux — Crew Wars",requiredReputation=5000,slotCount=12,gridLayout="3x4",themeColor=new Color(1f,.84f,0f),featured=false}
            };
        }

        public void LoadData(List<DistrictSaveData> savedDistricts, List<BuildingSaveData> savedBuildings)
        {
            states.Clear();
            if (savedDistricts != null)
            {
                foreach (var s in savedDistricts)
                {
                    states[s.districtId] = new DistrictState
                    {
                        districtId = s.districtId,
                        unlocked = s.unlocked,
                        extraSlots = s.extraSlots
                    };
                }
            }
            // Ensure all definitions have a state entry
            foreach (var def in definitions)
            {
                if (!states.ContainsKey(def.id))
                    states[def.id] = new DistrictState { districtId = def.id, unlocked = def.requiredReputation == 0 };
            }
        }

        public void Reset()
        {
            states.Clear();
            foreach (var def in definitions)
                states[def.id] = new DistrictState { districtId = def.id, unlocked = def.requiredReputation == 0 };
            globalExtraSlots = 0;
        }
        #endregion

        #region Unlock
        private void HandleReputationUnlock(string districtId)
        {
            if (!states.ContainsKey(districtId)) return;
            if (states[districtId].unlocked) return;
            states[districtId].unlocked = true;
            OnDistrictUnlocked?.Invoke(districtId);
            OnDistrictStateChanged?.Invoke();
            Debug.Log("[DistrictManager] Unlocked: " + districtId);
        }

        /// <summary>Manually checks and unlocks districts based on current reputation.</summary>
        public void CheckUnlocks(int currentReputation)
        {
            foreach (var def in definitions)
            {
                if (!states[def.id].unlocked && currentReputation >= def.requiredReputation)
                {
                    states[def.id].unlocked = true;
                    OnDistrictUnlocked?.Invoke(def.id);
                }
            }
        }

        public void AddExtraSlot()
        {
            globalExtraSlots++;
            OnDistrictStateChanged?.Invoke();
        }
        #endregion

        #region Queries
        public DistrictDefinition GetDefinition(string districtId) =>
            definitions.FirstOrDefault(d => d.id == districtId);

        public bool IsUnlocked(string districtId) =>
            states.TryGetValue(districtId, out var s) && s.unlocked;

        public int GetTotalSlots(string districtId)
        {
            var def = GetDefinition(districtId);
            if (def == null) return 0;
            int extra = states.TryGetValue(districtId, out var s) ? s.extraSlots : 0;
            return def.slotCount + extra + globalExtraSlots;
        }

        public List<DistrictDefinition> GetAllDefinitions() => new List<DistrictDefinition>(definitions);

        public List<DistrictDefinition> GetUnlockedDistricts() =>
            definitions.Where(d => IsUnlocked(d.id)).ToList();
        #endregion

        #region Save
        public List<DistrictSaveData> GetDistrictSaveData()
        {
            return states.Values.Select(s => new DistrictSaveData
            {
                districtId = s.districtId,
                unlocked = s.unlocked,
                extraSlots = s.extraSlots
            }).ToList();
        }
        #endregion
    }
}
