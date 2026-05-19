using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Blockside.Leaderboard
{
    [Serializable]
    public class LeaderboardEntry
    {
        public string playerId;
        public string username;
        public string faction;
        public int reputation;
        public int buildingCount;
        public int prestigeLevel;
        public long totalEarned;
        public int rank;
    }

    [Serializable]
    public class FactionEntry
    {
        public string factionId;
        public string factionName;
        public int memberCount;
        public long totalReputation;
        public int dominancePercent;
    }

    public enum LeaderboardCategory { Global, Faction, District }

    public class LeaderboardManager : MonoBehaviour
    {
        public static LeaderboardManager Instance { get; private set; }

        [Header("Config")]
        public float refreshIntervalSeconds = 300f;

        private List<LeaderboardEntry> _globalBoard = new();
        private List<FactionEntry> _factionBoard = new();
        private LeaderboardEntry _playerEntry;
        private float _lastRefresh;

        public event Action<List<LeaderboardEntry>> OnGlobalBoardUpdated;
        public event Action<List<FactionEntry>> OnFactionBoardUpdated;
        public event Action<int> OnPlayerRankChanged;

        void Awake()
        {
            if (Instance != null) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }

        void Start()
        {
            StartCoroutine(RefreshLoop());
        }

        IEnumerator RefreshLoop()
        {
            while (true)
            {
                yield return FetchLeaderboards();
                yield return new WaitForSeconds(refreshIntervalSeconds);
            }
        }

        IEnumerator FetchLeaderboards()
        {
            // In production: call backend API; here we build from local data + injected mock peers
            BuildLocalBoard();
            _lastRefresh = Time.time;
            OnGlobalBoardUpdated?.Invoke(_globalBoard);
            OnFactionBoardUpdated?.Invoke(_factionBoard);
            yield return null;
        }

        void BuildLocalBoard()
        {
            var playerData = GameManager.Instance?.GetPlayerData();
            if (playerData == null) return;

            // Seed with mock competitors scaled around the player
            _globalBoard.Clear();
            int baseRep = Mathf.Max(playerData.reputation, 500);

            _globalBoard.Add(new LeaderboardEntry { username = "ALPHA_GOD",   faction = "rebel",  reputation = baseRep * 8,  buildingCount = 67, prestigeLevel = 3 });
            _globalBoard.Add(new LeaderboardEntry { username = "NeonKing",    faction = "purple", reputation = baseRep * 6,  buildingCount = 54, prestigeLevel = 2 });
            _globalBoard.Add(new LeaderboardEntry { username = "ShadowBoss",  faction = "crow",   reputation = baseRep * 5,  buildingCount = 49, prestigeLevel = 2 });
            _globalBoard.Add(new LeaderboardEntry { username = "StreetLord",  faction = "rebel",  reputation = baseRep * 3,  buildingCount = 38, prestigeLevel = 1 });
            _globalBoard.Add(new LeaderboardEntry { username = "CityMaster",  faction = "purple", reputation = baseRep * 2,  buildingCount = 31, prestigeLevel = 1 });

            _playerEntry = new LeaderboardEntry
            {
                playerId = playerData.playerId,
                username = playerData.username,
                faction = playerData.faction,
                reputation = playerData.reputation,
                buildingCount = playerData.totalBuildings,
                prestigeLevel = playerData.prestigeLevel,
                totalEarned = playerData.totalEarned
            };
            _globalBoard.Add(_playerEntry);

            // Add lower peers
            _globalBoard.Add(new LeaderboardEntry { username = "NightRunner", faction = "rebel",  reputation = Mathf.Max(baseRep / 2, 100), buildingCount = 22 });
            _globalBoard.Add(new LeaderboardEntry { username = "UrbanLord",   faction = "purple", reputation = Mathf.Max(baseRep / 4, 50),  buildingCount = 18 });

            _globalBoard.Sort((a, b) => b.reputation.CompareTo(a.reputation));
            for (int i = 0; i < _globalBoard.Count; i++) _globalBoard[i].rank = i + 1;

            int playerRank = _globalBoard.FindIndex(e => e.playerId == playerData.playerId) + 1;
            OnPlayerRankChanged?.Invoke(playerRank);

            // Faction board
            _factionBoard.Clear();
            _factionBoard.Add(new FactionEntry { factionId = "rebel",  factionName = "REBEL CITY",     memberCount = 1247, totalReputation = 2847520, dominancePercent = 52 });
            _factionBoard.Add(new FactionEntry { factionId = "crow",   factionName = "BLACK CROW",     memberCount = 892,  totalReputation = 1984320, dominancePercent = 33 });
            _factionBoard.Add(new FactionEntry { factionId = "purple", factionName = "PURPLE NATION",  memberCount = 634,  totalReputation = 1256840, dominancePercent = 15 });
        }

        public List<LeaderboardEntry> GetGlobalBoard() => _globalBoard;
        public List<FactionEntry> GetFactionBoard() => _factionBoard;
        public LeaderboardEntry GetPlayerEntry() => _playerEntry;
        public int GetPlayerRank() => _playerEntry?.rank ?? -1;
    }
}
