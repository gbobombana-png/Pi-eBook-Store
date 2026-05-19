using System;
using System.Collections.Generic;
using UnityEngine;

namespace BLOCKSIDE
{
    /// <summary>Type of action a mission tracks.</summary>
    public enum MissionType
    {
        Build,
        Collect,
        Visit,
        Upgrade,
        Rep,
        Social
    }

    /// <summary>Identifies whether a mission resets daily or weekly.</summary>
    public enum MissionCadence
    {
        Daily,
        Weekly
    }

    [Serializable]
    public class MissionReward
    {
        public int money;
        public int rep;
    }

    [Serializable]
    public class MissionData
    {
        public string id;
        public string title;
        public string description;
        public MissionType type;
        public int target;
        public MissionReward reward;
        public MissionCadence cadence;
    }

    [Serializable]
    public class MissionProgress
    {
        public string missionId;
        public int current;
        public bool claimed;
    }

    /// <summary>
    /// Manages daily and weekly missions: tracking progress, resets, and reward claims.
    /// Notifies <see cref="EconomyManager"/> on reward claim.
    /// Persisted via <see cref="SaveManager"/>.
    /// </summary>
    public class MissionManager : MonoBehaviour
    {
        // ─── Singleton ────────────────────────────────────────────────────────────
        public static MissionManager Instance { get; private set; }

        // ─── Events ───────────────────────────────────────────────────────────────
        /// <summary>Fired whenever a mission's progress value changes.</summary>
        public static event Action<MissionData, int> OnMissionProgress;
        /// <summary>Fired when a mission reaches its target.</summary>
        public static event Action<MissionData> OnMissionComplete;
        /// <summary>Fired when the player successfully claims a mission reward.</summary>
        public static event Action<MissionData> OnRewardClaimed;

        // ─── Mission Definitions ──────────────────────────────────────────────────
        private static readonly MissionData[] _allMissions =
        {
            // Daily
            new MissionData { id="d_build",   title="Construire 1 bâtiment",       description="Place un bâtiment dans n'importe quel district.", type=MissionType.Build,   target=1,  reward=new MissionReward{money=200, rep=20},  cadence=MissionCadence.Daily  },
            new MissionData { id="d_collect",  title="Collecter des revenus 3 fois", description="Collecte les revenus dans tes districts.",         type=MissionType.Collect, target=3,  reward=new MissionReward{money=300, rep=0},   cadence=MissionCadence.Daily  },
            new MissionData { id="d_visit",    title="Visiter 2 districts",          description="Ouvre la vue de 2 districts différents.",           type=MissionType.Visit,   target=2,  reward=new MissionReward{money=150, rep=15},  cadence=MissionCadence.Daily  },
            new MissionData { id="d_upgrade",  title="Upgrader un bâtiment",         description="Améliore un bâtiment au niveau supérieur.",         type=MissionType.Upgrade, target=1,  reward=new MissionReward{money=500, rep=50},  cadence=MissionCadence.Daily  },
            // Weekly
            new MissionData { id="w_rep",      title="Atteindre 1000 rep",           description="Accumule 1000 points de réputation.",               type=MissionType.Rep,     target=1000, reward=new MissionReward{money=2000, rep=0}, cadence=MissionCadence.Weekly },
            new MissionData { id="w_buildings",title="Posséder 5 bâtiments",         description="Détiens 5 bâtiments en même temps.",                type=MissionType.Build,   target=5,  reward=new MissionReward{money=1000, rep=0}, cadence=MissionCadence.Weekly },
            new MissionData { id="w_faction",  title="Rejoindre une faction",        description="Rejoins l'une des trois factions de la ville.",      type=MissionType.Social,  target=1,  reward=new MissionReward{money=800,  rep=0},  cadence=MissionCadence.Weekly },
        };

        // ─── Runtime State ────────────────────────────────────────────────────────
        private Dictionary<string, MissionProgress> _progress = new Dictionary<string, MissionProgress>();
        private long _dailyResetTimestamp;
        private long _weeklyResetTimestamp;

        // ─── Unity Lifecycle ──────────────────────────────────────────────────────
        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
            LoadProgress();
            CheckResets();
        }

        // ─── Reset Logic ──────────────────────────────────────────────────────────

        /// <summary>Resets all daily missions. Called at midnight (server-side tick or client timer).</summary>
        public void ResetDaily()
        {
            foreach (var m in _allMissions)
            {
                if (m.cadence == MissionCadence.Daily)
                {
                    if (_progress.TryGetValue(m.id, out var p))
                    {
                        p.current = 0;
                        p.claimed = false;
                    }
                }
            }
            _dailyResetTimestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            SaveProgress();
        }

        /// <summary>Resets all weekly missions. Called every Monday at midnight.</summary>
        public void ResetWeekly()
        {
            foreach (var m in _allMissions)
            {
                if (m.cadence == MissionCadence.Weekly)
                {
                    if (_progress.TryGetValue(m.id, out var p))
                    {
                        p.current = 0;
                        p.claimed = false;
                    }
                }
            }
            _weeklyResetTimestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            SaveProgress();
        }

        private void CheckResets()
        {
            long now = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            // Daily: 24 h = 86_400_000 ms
            if (now - _dailyResetTimestamp > 86_400_000L) ResetDaily();
            // Weekly: 7 days = 604_800_000 ms
            if (now - _weeklyResetTimestamp > 604_800_000L) ResetWeekly();
        }

        // ─── Progress Tracking ────────────────────────────────────────────────────

        /// <summary>
        /// Records progress for all missions matching <paramref name="type"/>.
        /// Call this from BuildingManager, EconomyManager, etc.
        /// </summary>
        public void TrackProgress(MissionType type, int amount)
        {
            foreach (var m in _allMissions)
            {
                if (m.type != type) continue;
                if (!_progress.TryGetValue(m.id, out var p)) continue;
                if (p.claimed || p.current >= m.target) continue;

                p.current = Mathf.Min(p.current + amount, m.target);
                OnMissionProgress?.Invoke(m, p.current);

                if (p.current >= m.target)
                    OnMissionComplete?.Invoke(m);
            }
            SaveProgress();
        }

        /// <summary>Special overload for Rep tracking — compares absolute value.</summary>
        public void TrackRep(int totalRep)
        {
            foreach (var m in _allMissions)
            {
                if (m.type != MissionType.Rep) continue;
                if (!_progress.TryGetValue(m.id, out var p)) continue;
                if (p.claimed) continue;

                p.current = Mathf.Min(totalRep, m.target);
                OnMissionProgress?.Invoke(m, p.current);

                if (p.current >= m.target && !p.claimed)
                    OnMissionComplete?.Invoke(m);
            }
        }

        // ─── Reward Claiming ─────────────────────────────────────────────────────

        /// <summary>
        /// Claims the reward for a completed mission.
        /// Grants money and rep via EconomyManager. Returns false if not claimable.
        /// </summary>
        public bool ClaimReward(string missionId)
        {
            MissionData def = FindMission(missionId);
            if (def == null) return false;

            if (!_progress.TryGetValue(missionId, out var p)) return false;
            if (p.claimed || p.current < def.target) return false;

            p.claimed = true;
            EconomyManager economy = EconomyManager.Instance;
            if (economy != null)
            {
                economy.Earn(def.reward.money);
                economy.AddRep(def.reward.rep);
            }
            OnRewardClaimed?.Invoke(def);
            SaveProgress();
            return true;
        }

        // ─── Queries ─────────────────────────────────────────────────────────────

        /// <summary>Returns all mission definitions.</summary>
        public MissionData[] GetAllMissions() => _allMissions;

        /// <summary>Returns the progress state for a given mission id.</summary>
        public MissionProgress GetProgress(string missionId)
        {
            _progress.TryGetValue(missionId, out var p);
            return p;
        }

        /// <summary>Returns true if the mission is complete but not yet claimed.</summary>
        public bool HasClaimable(string missionId)
        {
            MissionData def = FindMission(missionId);
            if (def == null) return false;
            if (!_progress.TryGetValue(missionId, out var p)) return false;
            return p.current >= def.target && !p.claimed;
        }

        // ─── Persistence ──────────────────────────────────────────────────────────
        private const string SaveKey = "blockside_missions";

        private void SaveProgress()
        {
            var save = new MissionSaveData
            {
                progressList     = new List<MissionProgress>(_progress.Values),
                dailyResetTs     = _dailyResetTimestamp,
                weeklyResetTs    = _weeklyResetTimestamp
            };
            PlayerPrefs.SetString(SaveKey, JsonUtility.ToJson(save));
            PlayerPrefs.Save();
        }

        private void LoadProgress()
        {
            // Initialise all missions
            foreach (var m in _allMissions)
                _progress[m.id] = new MissionProgress { missionId = m.id, current = 0, claimed = false };

            string json = PlayerPrefs.GetString(SaveKey, "");
            if (string.IsNullOrEmpty(json)) return;

            try
            {
                var save = JsonUtility.FromJson<MissionSaveData>(json);
                _dailyResetTimestamp  = save.dailyResetTs;
                _weeklyResetTimestamp = save.weeklyResetTs;
                foreach (var p in save.progressList)
                    _progress[p.missionId] = p;
            }
            catch { /* corrupt save — use defaults */ }
        }

        private MissionData FindMission(string id)
        {
            foreach (var m in _allMissions)
                if (m.id == id) return m;
            return null;
        }

        // ─── Serialisation Helper ─────────────────────────────────────────────────
        [Serializable]
        private class MissionSaveData
        {
            public List<MissionProgress> progressList;
            public long dailyResetTs;
            public long weeklyResetTs;
        }
    }
}
