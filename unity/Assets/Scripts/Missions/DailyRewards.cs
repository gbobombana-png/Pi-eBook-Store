using System;
using UnityEngine;

namespace BLOCKSIDE
{
    /// <summary>Type of bonus attached to a daily reward tier.</summary>
    public enum DailyBonusType
    {
        None,
        VIPHour,
        Skin,
        LegendaryBonus
    }

    [Serializable]
    public class DailyRewardData
    {
        /// <summary>1-based day index within the 7-day cycle.</summary>
        public int day;
        public int money;
        public int rep;
        public DailyBonusType bonusType;
        public string bonusLabel; // human-readable, e.g. "VIP 1h"
    }

    /// <summary>
    /// 7-day login streak system.
    /// Call <see cref="CheckAndShowReward"/> at game start to show the popup if needed.
    /// Streak resets if the player misses more than 48 hours.
    /// Persisted in PlayerPrefs.
    /// </summary>
    public class DailyRewards : MonoBehaviour
    {
        // ─── Singleton ────────────────────────────────────────────────────────────
        public static DailyRewards Instance { get; private set; }

        // ─── Reward Table ─────────────────────────────────────────────────────────
        private static readonly DailyRewardData[] _rewards =
        {
            new DailyRewardData { day=1, money=100,  rep=0,   bonusType=DailyBonusType.None,          bonusLabel="" },
            new DailyRewardData { day=2, money=200,  rep=0,   bonusType=DailyBonusType.None,          bonusLabel="" },
            new DailyRewardData { day=3, money=300,  rep=0,   bonusType=DailyBonusType.VIPHour,       bonusLabel="VIP 1h" },
            new DailyRewardData { day=4, money=500,  rep=0,   bonusType=DailyBonusType.None,          bonusLabel="" },
            new DailyRewardData { day=5, money=800,  rep=0,   bonusType=DailyBonusType.Skin,          bonusLabel="Skin Exclusif" },
            new DailyRewardData { day=6, money=1200, rep=0,   bonusType=DailyBonusType.None,          bonusLabel="" },
            new DailyRewardData { day=7, money=2000, rep=500, bonusType=DailyBonusType.LegendaryBonus,bonusLabel="Bonus Légendaire" },
        };

        // ─── Persistence Keys ─────────────────────────────────────────────────────
        private const string KeyLastClaim = "blockside_daily_last_claim";
        private const string KeyStreak    = "blockside_daily_streak";
        private const string KeyClaimed   = "blockside_daily_claimed_today";

        // ─── Runtime State ────────────────────────────────────────────────────────
        private int _currentStreak;
        private long _lastClaimTimestamp;
        private bool _claimedToday;

        // ─── Unity Lifecycle ──────────────────────────────────────────────────────
        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
            LoadState();
        }

        // ─── Public API ───────────────────────────────────────────────────────────

        /// <summary>
        /// Returns all reward definitions for the 7-day cycle.
        /// </summary>
        public DailyRewardData[] GetAllRewards() => _rewards;

        /// <summary>Returns the current 1-based day index (1-7), wrapping after 7.</summary>
        public int GetCurrentDay() => ((_currentStreak - 1) % 7) + 1;

        /// <summary>Returns whether the player has already claimed their reward today.</summary>
        public bool HasClaimedToday() => _claimedToday;

        /// <summary>Returns the current streak length (number of consecutive days claimed).</summary>
        public int GetStreak() => _currentStreak;

        /// <summary>
        /// Checks whether the daily reward popup should be shown.
        /// Handles streak-broken detection (> 48 h gap) and resets state accordingly.
        /// Returns true if a reward is available and the popup should open.
        /// </summary>
        public bool CheckAndShowReward()
        {
            long nowMs = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            long hoursSinceLast = (nowMs - _lastClaimTimestamp) / 3_600_000L;

            if (_claimedToday) return false;

            // Streak broken if more than 48 h have passed since last claim
            if (_lastClaimTimestamp > 0 && hoursSinceLast > 48)
            {
                _currentStreak = 0;
                SaveState();
            }

            return true; // reward is available
        }

        /// <summary>
        /// Claims today's reward, grants money and rep, advances the streak.
        /// Returns null if already claimed or an error occurred.
        /// </summary>
        public DailyRewardData ClaimTodayReward()
        {
            if (_claimedToday) return null;

            int dayIndex = GetCurrentDay() - 1; // 0-based
            if (dayIndex < 0 || dayIndex >= _rewards.Length) return null;

            DailyRewardData reward = _rewards[dayIndex];

            // Grant rewards
            EconomyManager economy = EconomyManager.Instance;
            if (economy != null)
            {
                economy.Earn(reward.money);
                if (reward.rep > 0) economy.AddRep(reward.rep);
            }

            // Apply bonus effects
            ApplyBonus(reward.bonusType);

            // Advance state
            _currentStreak++;
            _claimedToday      = true;
            _lastClaimTimestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            SaveState();

            return reward;
        }

        // ─── Bonus Application ────────────────────────────────────────────────────
        private void ApplyBonus(DailyBonusType bonus)
        {
            switch (bonus)
            {
                case DailyBonusType.VIPHour:
                    // Grant one hour of ×2 income multiplier
                    EconomyManager.Instance?.ApplyTemporaryMultiplier(2f, 3600f);
                    break;
                case DailyBonusType.Skin:
                    // Unlock cosmetic skin flag
                    PlayerPrefs.SetInt("blockside_skin_daily", 1);
                    PlayerPrefs.Save();
                    break;
                case DailyBonusType.LegendaryBonus:
                    // Could trigger a special legendary event
                    LiveEventManager.Instance?.TriggerLegendaryEvent();
                    break;
                case DailyBonusType.None:
                default:
                    break;
            }
        }

        // ─── Persistence ──────────────────────────────────────────────────────────
        private void SaveState()
        {
            PlayerPrefs.SetInt(KeyStreak,           _currentStreak);
            PlayerPrefs.SetString(KeyLastClaim,     _lastClaimTimestamp.ToString());
            PlayerPrefs.SetInt(KeyClaimed,          _claimedToday ? 1 : 0);
            PlayerPrefs.Save();

            // Reset claimedToday at the next calendar day boundary
            ScheduleDailyReset();
        }

        private void LoadState()
        {
            _currentStreak      = PlayerPrefs.GetInt(KeyStreak, 0);
            _claimedToday       = PlayerPrefs.GetInt(KeyClaimed, 0) == 1;
            string tsStr        = PlayerPrefs.GetString(KeyLastClaim, "0");
            long.TryParse(tsStr, out _lastClaimTimestamp);

            // Check if the calendar day has rolled over since last session
            if (_claimedToday && _lastClaimTimestamp > 0)
            {
                long nowMs      = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
                long diffHours  = (nowMs - _lastClaimTimestamp) / 3_600_000L;
                if (diffHours >= 24)
                {
                    _claimedToday = false;
                    PlayerPrefs.SetInt(KeyClaimed, 0);
                    PlayerPrefs.Save();
                }
            }
        }

        private void ScheduleDailyReset()
        {
            // At runtime, CancelInvoke/InvokeRepeating could be used;
            // for simplicity we rely on LoadState() checking timestamps on next session start.
        }
    }
}
