using System;
using System.Collections.Generic;
using UnityEngine;

namespace Blockside.Core
{
    /// <summary>
    /// Données du joueur — partagées entre tous les managers via GameManager.GetPlayerData().
    /// </summary>
    [Serializable]
    public class PlayerData
    {
        public string playerId;
        public string username = "Player";
        public string characterId;
        public string faction;

        // Économie
        public long money = 500;
        public long totalEarned;
        public int totalBuildings;

        // Progression
        public int reputation;
        public int prestigeLevel;
        public float prestigeBonus = 1f;

        // Cosmétiques
        public string activeSkin = "default";
        public List<string> ownedSkins = new() { "default" };

        // Achats Pi
        public List<string> premiumOwned = new();
        public bool seasonPass;
        public long goldBoostUntil;

        // Météo
        public string currentWeather = "clear";

        // Session
        public long lastSaveTimestamp;
        public bool tutorialDone;
    }

    [Serializable]
    public class SaveData
    {
        public PlayerData player;
        public List<DistrictSaveEntry> districts = new();
        public List<BuildingSaveEntry> buildings = new();
        public MissionSaveData missions;
        public DailyRewardSaveData dailyReward;
        public VehicleSaveData vehicles;
        public List<string> activityLog = new();
        public int warWins;
        public int warLosses;
        public long savedAt;
    }

    [Serializable]
    public class DistrictSaveEntry
    {
        public string districtId;
        public bool unlocked;
    }

    [Serializable]
    public class BuildingSaveEntry
    {
        public string districtId;
        public string buildingId;
        public int level = 1;
        public int slotIndex;
        public long lastCollectTimestamp;
    }

    [Serializable]
    public class MissionSaveData
    {
        public List<MissionProgress> daily = new();
        public List<MissionProgress> weekly = new();
        public long lastDailyReset;
        public long lastWeeklyReset;
    }

    [Serializable]
    public class MissionProgress
    {
        public string missionId;
        public int progress;
        public bool claimed;
    }

    [Serializable]
    public class DailyRewardSaveData
    {
        public int streak;
        public long lastClaimed;
    }

    [Serializable]
    public class VehicleSaveData
    {
        public List<string> owned = new();
        public string active;
    }
}
