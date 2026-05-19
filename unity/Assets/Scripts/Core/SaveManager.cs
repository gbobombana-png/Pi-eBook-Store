using UnityEngine;
using System;
using System.IO;
using System.Collections.Generic;
using System.Runtime.Serialization.Formatters.Binary;

namespace BLOCKSIDE.Core
{
    // ─────────────────────────────────────────────────────────────
    // Data classes
    // ─────────────────────────────────────────────────────────────

    [Serializable]
    public class BuildingSaveData
    {
        public string buildingId;
        public int level;
        public long lastCollectTimestamp; // Unix ms
        public int slotIndex;
        public string districtId;
    }

    [Serializable]
    public class DistrictSaveData
    {
        public string districtId;
        public bool unlocked;
        public int extraSlots;
    }

    [Serializable]
    public class SaveData
    {
        public string username;
        public string characterId;
        public long money;
        public long totalEarned;
        public int reputation;
        public string crewId;
        public List<string> premiumOwned = new List<string>();
        public List<DistrictSaveData> districts = new List<DistrictSaveData>();
        public List<BuildingSaveData> buildings = new List<BuildingSaveData>();
        public int totalBuildings;
        public int clickCount;
        public List<string> activityLog = new List<string>();
        public Dictionary<string, bool> achievements = new Dictionary<string, bool>();
        public long lastSaveTime;
        public string version = "1.0.0";
    }

    // ─────────────────────────────────────────────────────────────
    // SaveManager
    // ─────────────────────────────────────────────────────────────

    /// <summary>
    /// Handles serialization, persistence and migration of game save data.
    /// Uses both PlayerPrefs (quick read) and a JSON file (full data).
    /// </summary>
    public class SaveManager : MonoBehaviour
    {
        private const string PREFS_KEY = "blockside_save_v1";
        private const string SAVE_FILENAME = "blockside.save";
        private string SaveFilePath => Path.Combine(Application.persistentDataPath, SAVE_FILENAME);

        [Header("Debug")]
        [SerializeField] private bool logSaves = true;

        #region Events
        public static event Action<SaveData> OnSaveLoaded;
        public static event Action OnSaveDeleted;
        #endregion

        #region Public API
        /// <summary>Persists save data to both PlayerPrefs and file system.</summary>
        public void Save(SaveData data)
        {
            if (data == null) return;
            data.lastSaveTime = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
            string json = JsonUtility.ToJson(data, true);
            // PlayerPrefs for fast access
            PlayerPrefs.SetString(PREFS_KEY, json);
            PlayerPrefs.Save();
            // File system for robustness
            WriteToFile(json);
            if (logSaves) Debug.Log($"[SaveManager] Saved. Money:{data.money} Rep:{data.reputation}");
        }

        /// <summary>Loads save data. Returns null if no save exists.</summary>
        public SaveData Load()
        {
            // Try file first (most complete)
            SaveData fromFile = LoadFromFile();
            if (fromFile != null)
            {
                if (logSaves) Debug.Log($"[SaveManager] Loaded from file. Money:{fromFile.money}");
                OnSaveLoaded?.Invoke(fromFile);
                return fromFile;
            }
            // Fallback to PlayerPrefs
            SaveData fromPrefs = LoadFromPrefs();
            if (fromPrefs != null)
            {
                if (logSaves) Debug.Log($"[SaveManager] Loaded from PlayerPrefs.");
                OnSaveLoaded?.Invoke(fromPrefs);
                return fromPrefs;
            }
            Debug.Log("[SaveManager] No save found.");
            return null;
        }

        /// <summary>Returns true if a save exists.</summary>
        public bool HasSave()
        {
            return File.Exists(SaveFilePath) || PlayerPrefs.HasKey(PREFS_KEY);
        }

        /// <summary>Deletes all save data.</summary>
        public void DeleteSave()
        {
            PlayerPrefs.DeleteKey(PREFS_KEY);
            PlayerPrefs.Save();
            if (File.Exists(SaveFilePath))
                File.Delete(SaveFilePath);
            OnSaveDeleted?.Invoke();
            Debug.Log("[SaveManager] Save deleted.");
        }

        /// <summary>Creates a backup copy of the current save.</summary>
        public void CreateBackup()
        {
            if (!File.Exists(SaveFilePath)) return;
            string backupPath = SaveFilePath + ".bak";
            File.Copy(SaveFilePath, backupPath, overwrite: true);
            Debug.Log("[SaveManager] Backup created: " + backupPath);
        }
        #endregion

        #region Private Helpers
        private void WriteToFile(string json)
        {
            try
            {
                string dir = Path.GetDirectoryName(SaveFilePath);
                if (!Directory.Exists(dir)) Directory.CreateDirectory(dir);
                File.WriteAllText(SaveFilePath, json);
            }
            catch (Exception e)
            {
                Debug.LogWarning("[SaveManager] File write failed: " + e.Message);
            }
        }

        private SaveData LoadFromFile()
        {
            try
            {
                if (!File.Exists(SaveFilePath)) return null;
                string json = File.ReadAllText(SaveFilePath);
                if (string.IsNullOrEmpty(json)) return null;
                SaveData data = JsonUtility.FromJson<SaveData>(json);
                return Validate(data) ? data : null;
            }
            catch (Exception e)
            {
                Debug.LogWarning("[SaveManager] File load failed: " + e.Message);
                return null;
            }
        }

        private SaveData LoadFromPrefs()
        {
            try
            {
                if (!PlayerPrefs.HasKey(PREFS_KEY)) return null;
                string json = PlayerPrefs.GetString(PREFS_KEY);
                if (string.IsNullOrEmpty(json)) return null;
                SaveData data = JsonUtility.FromJson<SaveData>(json);
                return Validate(data) ? data : null;
            }
            catch (Exception e)
            {
                Debug.LogWarning("[SaveManager] Prefs load failed: " + e.Message);
                return null;
            }
        }

        private bool Validate(SaveData data)
        {
            if (data == null) return false;
            if (data.premiumOwned == null) data.premiumOwned = new List<string>();
            if (data.districts == null) data.districts = new List<DistrictSaveData>();
            if (data.buildings == null) data.buildings = new List<BuildingSaveData>();
            if (data.activityLog == null) data.activityLog = new List<string>();
            if (data.achievements == null) data.achievements = new Dictionary<string, bool>();
            return true;
        }
        #endregion
    }
}
