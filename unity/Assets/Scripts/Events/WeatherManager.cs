using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Events;

namespace Blockside.Events
{
    [Serializable]
    public class WeatherCondition
    {
        public string id;
        public string displayName;
        public string icon;
        public string effectDescription;
        public float incomeMultiplier = 1f;
        public string affectedBuildingId; // empty = all buildings
        [Range(0f, 1f)] public float spawnWeight = 1f;
    }

    public class WeatherManager : MonoBehaviour
    {
        public static WeatherManager Instance { get; private set; }

        [Header("Weather Conditions")]
        public List<WeatherCondition> conditions = new()
        {
            new WeatherCondition { id="clear",  displayName="Ciel Dégagé",       icon="☀️",  effectDescription="Revenus normaux",                     incomeMultiplier=1.0f, spawnWeight=2f },
            new WeatherCondition { id="rain",   displayName="Pluie Néon",        icon="🌧️",  effectDescription="Clubs +30% revenus",                  incomeMultiplier=1.3f, affectedBuildingId="club",        spawnWeight=1f },
            new WeatherCondition { id="storm",  displayName="Tempête Électrique",icon="⚡",  effectDescription="Tous revenus +20%",                   incomeMultiplier=1.2f, spawnWeight=0.8f },
            new WeatherCondition { id="fog",    displayName="Brouillard Urbain", icon="🌫️",  effectDescription="Black Market +50% revenus",           incomeMultiplier=1.5f, affectedBuildingId="blackmarket",  spawnWeight=0.5f },
            new WeatherCondition { id="heat",   displayName="Vague de Chaleur",  icon="🌡️",  effectDescription="Snack Shops +40% revenus",            incomeMultiplier=1.4f, affectedBuildingId="snack",        spawnWeight=0.7f },
        };

        [Header("Timing")]
        [Min(60f)] public float minDurationSeconds = 1800f;
        [Min(60f)] public float maxDurationSeconds = 3600f;

        public UnityEvent<WeatherCondition> OnWeatherChanged;

        public WeatherCondition CurrentWeather { get; private set; }

        void Awake()
        {
            if (Instance != null) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }

        void Start()
        {
            string savedId = PlayerPrefs.GetString("current_weather", "clear");
            CurrentWeather = conditions.Find(c => c.id == savedId) ?? conditions[0];
            StartCoroutine(WeatherCycle());
        }

        IEnumerator WeatherCycle()
        {
            while (true)
            {
                float duration = UnityEngine.Random.Range(minDurationSeconds, maxDurationSeconds);
                yield return new WaitForSeconds(duration);
                ChangeWeather();
            }
        }

        void ChangeWeather()
        {
            float totalWeight = 0f;
            conditions.ForEach(c => totalWeight += c.spawnWeight);
            float roll = UnityEngine.Random.Range(0f, totalWeight);
            float acc = 0f;
            WeatherCondition next = conditions[0];
            foreach (var c in conditions)
            {
                acc += c.spawnWeight;
                if (roll <= acc) { next = c; break; }
            }
            // Avoid same weather twice in a row
            if (next.id == CurrentWeather.id)
            {
                int idx = conditions.IndexOf(next);
                next = conditions[(idx + 1) % conditions.Count];
            }
            CurrentWeather = next;
            PlayerPrefs.SetString("current_weather", next.id);
            PlayerPrefs.Save();
            OnWeatherChanged?.Invoke(next);
            NotificationSystem.Show("🌤️ Météo", $"{next.icon} {next.displayName} — {next.effectDescription}");
            Debug.Log($"[Weather] Changed to {next.displayName} (×{next.incomeMultiplier})");
        }

        public float GetBonusFor(string buildingId)
        {
            if (CurrentWeather == null) return 1f;
            if (string.IsNullOrEmpty(CurrentWeather.affectedBuildingId)) return CurrentWeather.incomeMultiplier;
            if (CurrentWeather.affectedBuildingId == buildingId) return CurrentWeather.incomeMultiplier;
            return 1f;
        }
    }
}
