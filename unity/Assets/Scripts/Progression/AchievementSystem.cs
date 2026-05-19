using System;
using System.Collections.Generic;
using UnityEngine;

namespace BLOCKSIDE
{
    [Serializable]
    public class AchievementReward
    {
        public int money;
        public int rep;
        public int seasonXP;
    }

    [Serializable]
    public class AchievementData
    {
        public string id;
        public string title;
        public string description;
        public string icon;           // emoji or sprite name
        public AchievementReward reward;
    }

    /// <summary>
    /// Manages 15 achievements, checking conditions every game tick.
    /// Grants rewards and shows toasts on unlock.
    /// State is persisted via PlayerPrefs.
    /// </summary>
    public class AchievementSystem : MonoBehaviour
    {
        // ─── Singleton ────────────────────────────────────────────────────────────
        public static AchievementSystem Instance { get; private set; }

        // ─── Events ───────────────────────────────────────────────────────────────
        /// <summary>Fired when an achievement is unlocked for the first time.</summary>
        public static event Action<AchievementData> OnAchievementUnlocked;

        // ─── Achievement Catalogue ────────────────────────────────────────────────
        private static readonly AchievementData[] _catalogue =
        {
            new AchievementData { id="first_build",      title="Premier Bâtiment",      icon="🏗️",  description="Construis ton premier bâtiment.",                         reward=new AchievementReward{money=100, rep=10, seasonXP=50} },
            new AchievementData { id="five_buildings",   title="District en Construction",icon="🏘️", description="Possède 5 bâtiments en même temps.",                     reward=new AchievementReward{money=300, rep=30, seasonXP=150} },
            new AchievementData { id="ten_buildings",    title="Promoteur Immobilier",   icon="🏙️",  description="Possède 10 bâtiments.",                                  reward=new AchievementReward{money=600, rep=60, seasonXP=300} },
            new AchievementData { id="district_boss",    title="District Boss",          icon="👑",  description="Débloque tous les bâtiments dans un district.",           reward=new AchievementReward{money=500, rep=50, seasonXP=250} },
            new AchievementData { id="crew_member",      title="Crew Member",            icon="👥",  description="Rejoins une faction.",                                   reward=new AchievementReward{money=200, rep=20, seasonXP=100} },
            new AchievementData { id="crew_leader",      title="Crew Leader",            icon="🔥",  description="Atteins le rang de leader dans ta faction.",             reward=new AchievementReward{money=1000,rep=100,seasonXP=500} },
            new AchievementData { id="first_pi_purchase",title="Pioneer Pi",             icon="🌐",  description="Effectue ton premier achat avec Pi.",                    reward=new AchievementReward{money=500, rep=50, seasonXP=250} },
            new AchievementData { id="revenue_1k",       title="Hustler",                icon="💰",  description="Gagne 1 000 au total.",                                  reward=new AchievementReward{money=100, rep=10, seasonXP=50} },
            new AchievementData { id="revenue_10k",      title="Money Maker",            icon="💵",  description="Gagne 10 000 au total.",                                 reward=new AchievementReward{money=500, rep=50, seasonXP=250} },
            new AchievementData { id="revenue_100k",     title="Street Millionaire",     icon="💎",  description="Gagne 100 000 au total.",                                reward=new AchievementReward{money=2000,rep=200,seasonXP=1000} },
            new AchievementData { id="rep_500",          title="Rep Building",           icon="⭐",  description="Atteins 500 points de réputation.",                      reward=new AchievementReward{money=300, rep=0,  seasonXP=150} },
            new AchievementData { id="rep_2000",         title="City Legend",            icon="🌟",  description="Atteins 2 000 points de réputation.",                    reward=new AchievementReward{money=800, rep=0,  seasonXP=400} },
            new AchievementData { id="rep_5000",         title="Underground King",       icon="👿",  description="Atteins 5 000 points de réputation.",                    reward=new AchievementReward{money=2000,rep=0,  seasonXP=1000} },
            new AchievementData { id="streak_7",         title="7-Day Streak",           icon="🔥",  description="Connecte-toi 7 jours de suite.",                         reward=new AchievementReward{money=1000,rep=100,seasonXP=500} },
            new AchievementData { id="all_districts",    title="City Owner",             icon="🗺️",  description="Débloque tous les districts.",                           reward=new AchievementReward{money=3000,rep=300,seasonXP=1500} },
        };

        // ─── Persistence ──────────────────────────────────────────────────────────
        private const string SaveKey = "blockside_achievements";
        private HashSet<string> _unlocked = new HashSet<string>();

        // ─── Unity Lifecycle ──────────────────────────────────────────────────────
        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
            LoadState();
        }

        // ─── Public API ───────────────────────────────────────────────────────────

        /// <summary>Returns the full achievement catalogue.</summary>
        public AchievementData[] GetAll() => _catalogue;

        /// <summary>Returns true if an achievement with this id is unlocked.</summary>
        public bool IsUnlocked(string id) => _unlocked.Contains(id);

        /// <summary>
        /// Checks all achievement conditions against the current game state.
        /// Call this after any significant state change (build, collect, rep change, etc.).
        /// </summary>
        public void CheckAll()
        {
            // We need SaveManager or direct state — use EconomyManager references
            EconomyManager eco = EconomyManager.Instance;
            if (eco == null) return;

            int totalBuildings  = eco.TotalBuildings;
            int totalEarned     = eco.TotalEarned;
            int rep             = eco.TotalRep;
            bool hasCrew        = !string.IsNullOrEmpty(eco.CurrentCrewId);
            bool hasPiPurchase  = eco.HasPiPurchase;
            int streak          = DailyRewards.Instance != null ? DailyRewards.Instance.GetStreak() : 0;
            int districtsCount  = eco.UnlockedDistrictCount;
            int maxDistricts    = 5; // hardcoded from design doc

            // Evaluate conditions
            TryUnlock("first_build",       totalBuildings >= 1);
            TryUnlock("five_buildings",    totalBuildings >= 5);
            TryUnlock("ten_buildings",     totalBuildings >= 10);
            TryUnlock("crew_member",       hasCrew);
            TryUnlock("first_pi_purchase", hasPiPurchase);
            TryUnlock("revenue_1k",        totalEarned >= 1000);
            TryUnlock("revenue_10k",       totalEarned >= 10000);
            TryUnlock("revenue_100k",      totalEarned >= 100000);
            TryUnlock("rep_500",           rep >= 500);
            TryUnlock("rep_2000",          rep >= 2000);
            TryUnlock("rep_5000",          rep >= 5000);
            TryUnlock("streak_7",          streak >= 7);
            TryUnlock("all_districts",     districtsCount >= maxDistricts);
            // district_boss and crew_leader are unlocked via specific manager calls
        }

        /// <summary>
        /// Explicitly unlocks an achievement by id (for achievements requiring external context).
        /// Returns false if already unlocked.
        /// </summary>
        public bool UnlockAchievement(string id)
        {
            return TryUnlock(id, true);
        }

        // ─── Internal ─────────────────────────────────────────────────────────────
        private bool TryUnlock(string id, bool condition)
        {
            if (!condition || _unlocked.Contains(id)) return false;
            _unlocked.Add(id);

            AchievementData def = FindAchievement(id);
            if (def != null)
            {
                // Grant reward
                EconomyManager eco = EconomyManager.Instance;
                if (eco != null)
                {
                    eco.Earn(def.reward.money);
                    eco.AddRep(def.reward.rep);
                }
                SeasonSystem.Instance?.AddSeasonXP(def.reward.seasonXP);

                // Notify UI with slight delay to avoid overlap
                OnAchievementUnlocked?.Invoke(def);
                string displayName = def.title;
                // Delayed toast via MonoBehaviour invoke
                Invoke(nameof(DelayedToastPlaceholder), 0.5f);
                _pendingToast = $"🏆 Succès: {displayName}";
            }
            SaveState();
            return true;
        }

        private string _pendingToast;
        private void DelayedToastPlaceholder()
        {
            UIManager.Instance?.ShowToast(_pendingToast, "success");
        }

        private AchievementData FindAchievement(string id)
        {
            foreach (var a in _catalogue)
                if (a.id == id) return a;
            return null;
        }

        // ─── Persistence ──────────────────────────────────────────────────────────
        private void SaveState()
        {
            var list = new List<string>(_unlocked);
            PlayerPrefs.SetString(SaveKey, string.Join(",", list));
            PlayerPrefs.Save();
        }

        private void LoadState()
        {
            string saved = PlayerPrefs.GetString(SaveKey, "");
            if (string.IsNullOrEmpty(saved)) return;
            foreach (string id in saved.Split(','))
                if (!string.IsNullOrEmpty(id)) _unlocked.Add(id);
        }
    }
}
