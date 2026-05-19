using UnityEngine;
using System;
using System.Collections.Generic;
using Blockside.Economy;
using Blockside.Social;
using Blockside.Pi;
using Blockside.Districts;
using Blockside.UI;
using Blockside.Leaderboard;
using Blockside.Progression;
using Blockside.Customization;
using Blockside.Events;
using Blockside.Core;

namespace Blockside.Core
{
    /// <summary>
    /// Central game manager singleton. Initializes and coordinates all subsystems.
    /// Persists across scene loads via DontDestroyOnLoad.
    /// </summary>
    public class GameManager : MonoBehaviour
    {
        #region Singleton
        public static GameManager Instance { get; private set; }
        #endregion

        #region Inspector References
        [Header("Core Managers")]
        [SerializeField] private SaveManager saveManager;
        [SerializeField] private AudioManager audioManager;

        [Header("Economy")]
        [SerializeField] private EconomyManager economyManager;
        [SerializeField] private BuildingManager buildingManager;
        [SerializeField] private IncomeSystem incomeSystem;

        [Header("Social")]
        [SerializeField] private ReputationSystem reputationSystem;
        [SerializeField] private CrewManager crewManager;

        [Header("Pi Network")]
        [SerializeField] private PiNetworkManager piNetworkManager;
        [SerializeField] private MarketplaceManager marketplaceManager;

        [Header("UI")]
        [SerializeField] private UIManager uiManager;
        [SerializeField] private HUDController hudController;

        [Header("Districts")]
        [SerializeField] private DistrictManager districtManager;

        [Header("Phase 4 — Social")]
        [SerializeField] private LeaderboardManager leaderboardManager;

        [Header("Phase 5 — Cosmétiques")]
        [SerializeField] private SkinManager skinManager;

        [Header("Phase 6 — World")]
        [SerializeField] private PrestigeManager prestigeManager;
        [SerializeField] private WeatherManager weatherManager;

        [Header("Settings")]
        [SerializeField] private bool autoSaveEnabled = true;
        [SerializeField] private float autoSaveInterval = 30f;
        #endregion

        #region State
        public enum GameState { Initializing, Splash, CharacterSelect, Hub, City, District, Crew, Market, Profile }
        private GameState currentState = GameState.Initializing;
        private float autoSaveTimer;
        private bool isInitialized;
        #endregion

        #region Events
        public static event Action<GameState> OnStateChanged;
        public static event Action OnGameInitialized;
        public static event Action OnGameSaved;
        #endregion

        #region Properties
        public SaveManager Save => saveManager;
        public AudioManager Audio => audioManager;
        public EconomyManager Economy => economyManager;
        public BuildingManager Buildings => buildingManager;
        public IncomeSystem Income => incomeSystem;
        public ReputationSystem Reputation => reputationSystem;
        public CrewManager Crew => crewManager;
        public PiNetworkManager PiNetwork => piNetworkManager;
        public MarketplaceManager Marketplace => marketplaceManager;
        public UIManager UI => uiManager;
        public HUDController HUD => hudController;
        public DistrictManager Districts => districtManager;
        public GameState CurrentState => currentState;
        public LeaderboardManager Leaderboard => leaderboardManager;
        public SkinManager Skins => skinManager;
        public PrestigeManager Prestige => prestigeManager;
        public WeatherManager Weather => weatherManager;
        #endregion

        #region Unity Lifecycle
        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
            DontDestroyOnLoad(gameObject);
            InitializeManagers();
        }

        private void Start()
        {
            StartGame();
        }

        private void Update()
        {
            if (!isInitialized) return;
            HandleAutoSave();
            incomeSystem?.Tick(Time.deltaTime);
        }

        private void OnApplicationPause(bool pause)
        {
            if (pause && autoSaveEnabled) SaveGame();
        }

        private void OnApplicationQuit()
        {
            SaveGame();
        }
        #endregion

        #region Initialization
        private void InitializeManagers()
        {
            // Resolve missing manager references by searching the scene
            saveManager = saveManager ? saveManager : FindObjectOfType<SaveManager>() ?? gameObject.AddComponent<SaveManager>();
            audioManager = audioManager ? audioManager : FindObjectOfType<AudioManager>() ?? gameObject.AddComponent<AudioManager>();
            economyManager = economyManager ? economyManager : FindObjectOfType<EconomyManager>() ?? gameObject.AddComponent<EconomyManager>();
            buildingManager = buildingManager ? buildingManager : FindObjectOfType<BuildingManager>() ?? gameObject.AddComponent<BuildingManager>();
            incomeSystem = incomeSystem ? incomeSystem : FindObjectOfType<IncomeSystem>() ?? gameObject.AddComponent<IncomeSystem>();
            reputationSystem = reputationSystem ? reputationSystem : FindObjectOfType<ReputationSystem>() ?? gameObject.AddComponent<ReputationSystem>();
            crewManager = crewManager ? crewManager : FindObjectOfType<CrewManager>() ?? gameObject.AddComponent<CrewManager>();
            piNetworkManager = piNetworkManager ? piNetworkManager : FindObjectOfType<PiNetworkManager>() ?? gameObject.AddComponent<PiNetworkManager>();
            marketplaceManager = marketplaceManager ? marketplaceManager : FindObjectOfType<MarketplaceManager>() ?? gameObject.AddComponent<MarketplaceManager>();
            districtManager    = districtManager    ? districtManager    : FindObjectOfType<DistrictManager>()    ?? gameObject.AddComponent<DistrictManager>();
            leaderboardManager = leaderboardManager ? leaderboardManager : FindObjectOfType<LeaderboardManager>() ?? gameObject.AddComponent<LeaderboardManager>();
            skinManager        = skinManager        ? skinManager        : FindObjectOfType<SkinManager>()        ?? gameObject.AddComponent<SkinManager>();
            prestigeManager    = prestigeManager    ? prestigeManager    : FindObjectOfType<PrestigeManager>()    ?? gameObject.AddComponent<PrestigeManager>();
            weatherManager     = weatherManager     ? weatherManager     : FindObjectOfType<WeatherManager>()     ?? gameObject.AddComponent<WeatherManager>();
        }

        private void StartGame()
        {
            SaveData loaded = saveManager.Load();
            if (loaded != null)
            {
                ApplySaveData(loaded);
                SetState(GameState.Hub);
            }
            else
            {
                SetState(GameState.Splash);
            }
            isInitialized = true;
            OnGameInitialized?.Invoke();
            Debug.Log("[GameManager] Initialized. State: " + currentState);
        }

        private void ApplySaveData(SaveData data)
        {
            economyManager.LoadData(data.money, data.totalEarned);
            reputationSystem.LoadData(data.reputation);
            districtManager.LoadData(data.districts, data.buildings);
            crewManager.LoadData(data.crewId);
            marketplaceManager.LoadData(data.premiumOwned);
        }
        #endregion

        #region State Machine
        /// <summary>Transitions the game to a new state and notifies listeners.</summary>
        public void SetState(GameState newState)
        {
            if (currentState == newState) return;
            GameState prev = currentState;
            currentState = newState;
            Debug.Log($"[GameManager] State: {prev} → {newState}");
            OnStateChanged?.Invoke(newState);
            uiManager?.OnGameStateChanged(newState);
            hudController?.OnGameStateChanged(newState);
        }

        public bool IsInState(GameState state) => currentState == state;
        #endregion

        #region Save
        private void HandleAutoSave()
        {
            if (!autoSaveEnabled) return;
            autoSaveTimer += Time.deltaTime;
            if (autoSaveTimer >= autoSaveInterval)
            {
                autoSaveTimer = 0f;
                SaveGame();
            }
        }

        /// <summary>Gathers all manager data and persists via SaveManager.</summary>
        public void SaveGame()
        {
            SaveData data = GatherSaveData();
            saveManager.Save(data);
            OnGameSaved?.Invoke();
        }

        /// <summary>Public accessor used by subsystems that need to trigger a save externally.</summary>
        public SaveData GatherSaveDataPublic() => GatherSaveData();

        private SaveData GatherSaveData()
        {
            return new SaveData
            {
                money = economyManager.Money,
                totalEarned = economyManager.TotalEarned,
                reputation = reputationSystem.Reputation,
                crewId = crewManager.CurrentCrewId,
                districts = districtManager.GetDistrictSaveData(),
                buildings = buildingManager.GetBuildingSaveData(),
                premiumOwned = marketplaceManager.GetOwnedItemIds(),
                characterId = PlayerPrefs.GetString("selectedCharacter", ""),
                username = PlayerPrefs.GetString("username", "Player"),
                lastSaveTime = DateTimeOffset.UtcNow.ToUnixTimeSeconds()
            };
        }
        #endregion

        #region Public API
        /// <summary>Resets all game data (new game).</summary>
        public void NewGame(string characterId, string username)
        {
            saveManager.DeleteSave();
            economyManager.Reset(500);
            reputationSystem.Reset();
            districtManager.Reset();
            buildingManager.Reset();
            crewManager.Reset();
            marketplaceManager.Reset();
            PlayerPrefs.SetString("selectedCharacter", characterId);
            PlayerPrefs.SetString("username", username);
            PlayerPrefs.Save();
            addInitialActivity();
            SetState(GameState.Hub);
        }

        private void addInitialActivity()
        {
            // Notify UI of fresh start
            hudController?.AddActivity("🎮 Début de l'aventure BLOCKSIDE!");
        }

        /// <summary>Shortcut to transition to the hub screen.</summary>
        public void GoToHub() => SetState(GameState.Hub);

        /// <summary>Shortcut to transition to city view.</summary>
        public void GoToCity() => SetState(GameState.City);

        /// <summary>
        /// Retourne une vue unifiée des données du joueur (utilisée par Leaderboard, Prestige, etc.).
        /// </summary>
        public PlayerData GetPlayerData()
        {
            return new PlayerData
            {
                playerId      = PlayerPrefs.GetString("piUid", "local"),
                username      = PlayerPrefs.GetString("username", "Player"),
                characterId   = PlayerPrefs.GetString("selectedCharacter", ""),
                faction       = crewManager?.CurrentCrewId,
                money         = economyManager?.Money ?? 500,
                totalEarned   = economyManager?.TotalEarned ?? 0,
                reputation    = reputationSystem?.Reputation ?? 0,
                totalBuildings = buildingManager?.TotalBuildings ?? 0,
                prestigeLevel = prestigeManager?.CurrentPrestigeLevel ?? 0,
                activeSkin    = skinManager?.ActiveSkinId ?? "default",
                ownedSkins    = skinManager?.GetOwnedSkinIds() ?? new List<string> { "default" },
                premiumOwned  = marketplaceManager?.GetOwnedItemIds() ?? new List<string>(),
                currentWeather = weatherManager?.CurrentWeather?.id ?? "clear",
            };
        }

        /// <summary>Efface tous les bâtiments — utilisé par le système Prestige.</summary>
        public void ClearAllBuildings()
        {
            buildingManager?.Reset();
            districtManager?.Reset();
        }

        /// <summary>Recharge les données après un Prestige.</summary>
        public void OnPrestigeApplied(int newLevel)
        {
            economyManager?.Reset(500);
            reputationSystem?.Reset();
            ClearAllBuildings();
            hudController?.RefreshAll();
            NotificationSystem.Show("✨ Prestige", $"Prestige {newLevel} activé! Bonus permanent appliqué.");
        }
        #endregion
    }
}
