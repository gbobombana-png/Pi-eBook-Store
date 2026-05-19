using UnityEngine;
using System;
using System.Collections.Generic;

namespace BLOCKSIDE.Social
{
    [Serializable]
    public class FactionDefinition
    {
        public string id;
        public string displayName;
        public string emoji;
        public Color primaryColor;
        public string vibe;
        public int memberCount;
    }

    [Serializable]
    public class CrewMission
    {
        public string missionId;
        public string title;
        public string description;
        public int targetValue;
        public int currentValue;
        public int reputationReward;
        public long moneyReward;
        public bool completed;
    }

    [Serializable]
    public class LeaderboardEntry
    {
        public string username;
        public int score;
        public int rank;
    }

    /// <summary>
    /// Manages crew/faction membership, leaderboard, missions, and crew chat state.
    /// </summary>
    public class CrewManager : MonoBehaviour
    {
        #region Inspector
        [SerializeField] private List<FactionDefinition> factions = new List<FactionDefinition>();
        #endregion

        #region State
        private string currentCrewId;
        private List<CrewMission> activeMissions = new List<CrewMission>();
        private List<LeaderboardEntry> leaderboard = new List<LeaderboardEntry>();
        private List<string> chatMessages = new List<string>();
        #endregion

        #region Events
        public static event Action<string> OnCrewJoined;    // crewId
        public static event Action OnCrewLeft;
        public static event Action<CrewMission> OnMissionCompleted;
        #endregion

        #region Properties
        public string CurrentCrewId => currentCrewId;
        public bool InCrew => !string.IsNullOrEmpty(currentCrewId);
        public FactionDefinition CurrentFaction => factions.Find(f => f.id == currentCrewId);
        #endregion

        #region Init
        private void Awake()
        {
            if (factions == null || factions.Count == 0) InitDefaultFactions();
        }

        private void InitDefaultFactions()
        {
            factions = new List<FactionDefinition>
            {
                new FactionDefinition{id="rebel",displayName="REBEL CITY",emoji="🔥",primaryColor=new Color(1f,.42f,.1f),vibe="Vibes street, liberté totale",memberCount=1247},
                new FactionDefinition{id="crow",displayName="BLACK CROW",emoji="🐦",primaryColor=new Color(.61f,.18f,1f),vibe="Hackers, ombres et manipulation",memberCount=892},
                new FactionDefinition{id="purple",displayName="PURPLE NATION",emoji="💜",primaryColor=new Color(.8f,.47f,1f),vibe="Luxe, prestige et domination",memberCount=634}
            };
        }

        public void LoadData(string savedCrewId)
        {
            currentCrewId = savedCrewId;
            if (InCrew)
            {
                GenerateMissions();
                GenerateLeaderboard();
                GenerateChatMessages();
            }
        }

        public void Reset()
        {
            currentCrewId = null;
            activeMissions.Clear();
            leaderboard.Clear();
            chatMessages.Clear();
        }
        #endregion

        #region Faction Actions
        /// <summary>Joins a faction. Leaves previous faction if any.</summary>
        public bool JoinFaction(string factionId)
        {
            if (factions.Find(f => f.id == factionId) == null)
            {
                Debug.LogWarning("[CrewManager] Unknown faction: " + factionId);
                return false;
            }
            currentCrewId = factionId;
            GenerateMissions();
            GenerateLeaderboard();
            GenerateChatMessages();
            OnCrewJoined?.Invoke(factionId);
            Debug.Log("[CrewManager] Joined faction: " + factionId);
            return true;
        }

        public void LeaveFaction()
        {
            currentCrewId = null;
            activeMissions.Clear();
            OnCrewLeft?.Invoke();
        }
        #endregion

        #region Leaderboard
        private void GenerateLeaderboard()
        {
            string username = PlayerPrefs.GetString("username", "Player");
            int playerScore = (Core.GameManager.Instance?.Reputation.Reputation ?? 0) +
                              (int)((Core.GameManager.Instance?.Economy.TotalEarned ?? 0) / 100);
            leaderboard = new List<LeaderboardEntry>
            {
                new LeaderboardEntry{username="ALPHA_WOLF",score=45820,rank=1},
                new LeaderboardEntry{username="NightHunter",score=38240,rank=2},
                new LeaderboardEntry{username="CityLegend",score=29150,rank=3},
                new LeaderboardEntry{username=username,score=playerScore,rank=4},
                new LeaderboardEntry{username="BlockMaster",score=8920,rank=5}
            };
            leaderboard.Sort((a, b) => b.score.CompareTo(a.score));
            for (int i = 0; i < leaderboard.Count; i++) leaderboard[i].rank = i + 1;
        }

        public List<LeaderboardEntry> GetLeaderboard()
        {
            GenerateLeaderboard(); // refresh player score each time
            return new List<LeaderboardEntry>(leaderboard);
        }
        #endregion

        #region Missions
        private void GenerateMissions()
        {
            int buildings = Core.GameManager.Instance?.Buildings.TotalPlacedCount() ?? 0;
            activeMissions = new List<CrewMission>
            {
                new CrewMission{missionId="build_3",title="Construire 3 bâtiments",description="Développe ton empire",targetValue=3,currentValue=Mathf.Min(buildings,3),reputationReward=200,moneyReward=1000,completed=buildings>=3},
                new CrewMission{missionId="collect_5k",title="Collecter 5000$",description="Fais tourner les revenus",targetValue=5000,currentValue=(int)Mathf.Min(Core.GameManager.Instance?.Economy.TotalEarned??0,5000),reputationReward=150,moneyReward=500,completed=(Core.GameManager.Instance?.Economy.TotalEarned??0)>=5000},
                new CrewMission{missionId="reach_rep100",title="Atteindre 100 rep",description="Montre ta valeur",targetValue=100,currentValue=Mathf.Min(Core.GameManager.Instance?.Reputation.Reputation??0,100),reputationReward=50,moneyReward=0,completed=(Core.GameManager.Instance?.Reputation.Reputation??0)>=100}
            };
        }

        public void UpdateMissionProgress(string missionId, int value)
        {
            var m = activeMissions.Find(x => x.missionId == missionId);
            if (m == null || m.completed) return;
            m.currentValue = Mathf.Min(value, m.targetValue);
            if (m.currentValue >= m.targetValue)
            {
                m.completed = true;
                Core.GameManager.Instance?.Economy.Earn(m.moneyReward, "Mission: " + m.title);
                Core.GameManager.Instance?.Reputation.AddReputation(m.reputationReward);
                OnMissionCompleted?.Invoke(m);
            }
        }

        public List<CrewMission> GetMissions()
        {
            GenerateMissions();
            return new List<CrewMission>(activeMissions);
        }
        #endregion

        #region Chat
        private void GenerateChatMessages()
        {
            string username = PlayerPrefs.GetString("username", "Player");
            chatMessages = new List<string>
            {
                "ALPHA_WOLF: On tient le district ce soir 🔥",
                "NightHunter: Nouveau record de revenus!",
                username + ": En route pour UNDERBLOCK 👊",
                "CityLegend: Qui construit le Black Market?"
            };
        }

        public List<string> GetChatMessages() => new List<string>(chatMessages);

        public void AddChatMessage(string message)
        {
            string username = PlayerPrefs.GetString("username", "Player");
            chatMessages.Add(username + ": " + message);
        }
        #endregion

        #region Queries
        public List<FactionDefinition> GetAllFactions() => new List<FactionDefinition>(factions);
        public FactionDefinition GetFaction(string id) => factions.Find(f => f.id == id);
        #endregion
    }
}
