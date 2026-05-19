using System;
using System.Collections.Generic;
using UnityEngine;

namespace BLOCKSIDE
{
    /// <summary>Category of live event.</summary>
    public enum LiveEventType
    {
        BlackMarketNight,
        DistrictWars,
        NeonConcert,
        LegendaryEvent
    }

    [Serializable]
    public class LiveEventData
    {
        public string id;
        public string title;
        public string description;
        public string emoji;
        public string colorHex;
        public LiveEventType type;
        /// <summary>Unix timestamp (seconds) when the event starts.</summary>
        public long startTimeSec;
        /// <summary>Unix timestamp (seconds) when the event ends.</summary>
        public long endTimeSec;
        /// <summary>Income multiplier applied to the targetDistrict while active.</summary>
        public float multiplier;
        /// <summary>District id this event affects. Empty = all districts.</summary>
        public string targetDistrict;
    }

    /// <summary>
    /// Manages scheduled live events with income multipliers.
    /// Events rotate on a 6-hour schedule.
    /// Notifies <see cref="EconomyManager"/> when events start or end.
    /// </summary>
    public class LiveEventManager : MonoBehaviour
    {
        // ─── Singleton ────────────────────────────────────────────────────────────
        public static LiveEventManager Instance { get; private set; }

        // ─── Events ───────────────────────────────────────────────────────────────
        /// <summary>Fired when a live event becomes active.</summary>
        public static event Action<LiveEventData> OnEventStarted;
        /// <summary>Fired when a live event expires.</summary>
        public static event Action<LiveEventData> OnEventEnded;

        // ─── Inspector ────────────────────────────────────────────────────────────
        [SerializeField] private float checkIntervalSeconds = 60f;

        // ─── Event Catalogue ──────────────────────────────────────────────────────
        // Events are defined relative to "epoch hour" — they rotate on a 6-h slot.
        private static readonly LiveEventData[] _catalogue =
        {
            new LiveEventData
            {
                id="black_market_night", title="BLACK MARKET NIGHT",
                description="Revenus ×3 dans Underblock — Profite maintenant !",
                emoji="🔥", colorHex="#FF2D78",
                type=LiveEventType.BlackMarketNight,
                multiplier=3f, targetDistrict="underblock"
            },
            new LiveEventData
            {
                id="district_wars", title="DISTRICT WARS",
                description="Rejoins ta faction et combats pour le contrôle de The Edge !",
                emoji="⚔️", colorHex="#FFD700",
                type=LiveEventType.DistrictWars,
                multiplier=2f, targetDistrict="the_edge"
            },
            new LiveEventData
            {
                id="neon_concert", title="NEON CONCERT",
                description="Event exclusif — Snack Shop rapporte ×5 ce soir !",
                emoji="🎵", colorHex="#9B2FFF",
                type=LiveEventType.NeonConcert,
                multiplier=5f, targetDistrict="neon_market"
            },
        };

        // ─── Runtime State ────────────────────────────────────────────────────────
        private readonly List<LiveEventData> _activeEvents = new List<LiveEventData>();
        private float _checkTimer;
        private bool _legendaryActive;

        // ─── Unity Lifecycle ──────────────────────────────────────────────────────
        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }

        private void Start()
        {
            ScheduleEvents();
            EvaluateActiveEvents();
        }

        private void Update()
        {
            _checkTimer += Time.deltaTime;
            if (_checkTimer >= checkIntervalSeconds)
            {
                _checkTimer = 0f;
                EvaluateActiveEvents();
            }
        }

        // ─── Scheduling ───────────────────────────────────────────────────────────

        /// <summary>
        /// Assigns start/end timestamps to catalogue events based on current 6-hour UTC slot.
        /// Each event occupies one 6-hour window per 18-hour day cycle.
        /// </summary>
        private void ScheduleEvents()
        {
            long nowSec       = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
            long slotDuration = 6 * 3600L; // 6 hours in seconds
            long epochSlot    = nowSec / slotDuration; // current slot index

            for (int i = 0; i < _catalogue.Length; i++)
            {
                long slotStart = (epochSlot - (epochSlot % _catalogue.Length) + i) * slotDuration;
                // If this slot is already past, push to next cycle
                while (slotStart + slotDuration < nowSec)
                    slotStart += slotDuration * _catalogue.Length;

                _catalogue[i].startTimeSec = slotStart;
                _catalogue[i].endTimeSec   = slotStart + slotDuration;
            }
        }

        private void EvaluateActiveEvents()
        {
            long nowSec = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
            List<LiveEventData> newlyEnded = new List<LiveEventData>();

            // Check for ended events
            foreach (var e in _activeEvents)
            {
                if (nowSec >= e.endTimeSec)
                {
                    newlyEnded.Add(e);
                    OnEventEnded?.Invoke(e);
                }
            }
            foreach (var e in newlyEnded) _activeEvents.Remove(e);

            // Check for newly started events
            foreach (var e in _catalogue)
            {
                if (nowSec >= e.startTimeSec && nowSec < e.endTimeSec && !_activeEvents.Contains(e))
                {
                    _activeEvents.Add(e);
                    OnEventStarted?.Invoke(e);
                }
            }
        }

        // ─── Public API ───────────────────────────────────────────────────────────

        /// <summary>Returns the list of currently active live events.</summary>
        public IReadOnlyList<LiveEventData> GetActiveEvents() => _activeEvents;

        /// <summary>Returns the full event catalogue (active or not).</summary>
        public LiveEventData[] GetCatalogue() => _catalogue;

        /// <summary>
        /// Returns the combined income multiplier for a given district from all active events.
        /// Returns 1.0 if no events affect that district.
        /// </summary>
        public float GetEventMultiplier(string districtId)
        {
            float multiplier = 1f;
            foreach (var e in _activeEvents)
            {
                if (string.IsNullOrEmpty(e.targetDistrict) ||
                    string.Equals(e.targetDistrict, districtId, StringComparison.OrdinalIgnoreCase))
                {
                    multiplier *= e.multiplier;
                }
            }
            if (_legendaryActive) multiplier *= 1.5f;
            return multiplier;
        }

        /// <summary>
        /// Returns the seconds remaining for the first active event targeting this district.
        /// Returns 0 if no event is active.
        /// </summary>
        public long GetSecondsRemaining(string districtId)
        {
            long nowSec = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
            foreach (var e in _activeEvents)
            {
                if (string.IsNullOrEmpty(e.targetDistrict) ||
                    string.Equals(e.targetDistrict, districtId, StringComparison.OrdinalIgnoreCase))
                {
                    return Mathf.Max(0, (int)(e.endTimeSec - nowSec));
                }
            }
            return 0;
        }

        /// <summary>Triggers a special legendary event (used by DailyRewards day-7 bonus).</summary>
        public void TriggerLegendaryEvent()
        {
            _legendaryActive = true;
            Invoke(nameof(EndLegendaryEvent), 3600f); // 1 hour
        }

        private void EndLegendaryEvent() => _legendaryActive = false;
    }
}
