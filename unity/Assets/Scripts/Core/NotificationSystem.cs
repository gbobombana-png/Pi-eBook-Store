using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace Blockside.Core
{
    /// <summary>
    /// Système de notifications in-game — toast + notifications persistantes.
    /// Utilisé par WeatherManager, LiveEventManager, etc.
    /// </summary>
    public class NotificationSystem : MonoBehaviour
    {
        public static NotificationSystem Instance { get; private set; }

        [Header("Toast UI")]
        [SerializeField] private GameObject toastPrefab;
        [SerializeField] private Transform toastContainer;
        [SerializeField] private float toastDuration = 3f;

        [Header("Notification Panel")]
        [SerializeField] private Transform notifListContainer;
        [SerializeField] private GameObject notifEntryPrefab;
        [SerializeField] private int maxNotifications = 20;

        private readonly Queue<(string title, string text)> _pending = new();
        private bool _isShowingToast;
        private readonly List<NotifEntry> _notifications = new();

        private record NotifEntry(string Title, string Text, long Time);

        void Awake()
        {
            if (Instance != null) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }

        /// <summary>Affiche un toast et enregistre une notification persistante.</summary>
        public static void Show(string title, string text)
        {
            if (Instance == null)
            {
                Debug.Log($"[Notif] {title} — {text}");
                return;
            }
            Instance._notifications.Insert(0, new NotifEntry(title, text, DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()));
            if (Instance._notifications.Count > Instance.maxNotifications)
                Instance._notifications.RemoveAt(Instance._notifications.Count - 1);
            Instance.RefreshNotifPanel();
            Instance._pending.Enqueue((title, text));
            if (!Instance._isShowingToast) Instance.StartCoroutine(Instance.ProcessToastQueue());
        }

        IEnumerator ProcessToastQueue()
        {
            _isShowingToast = true;
            while (_pending.Count > 0)
            {
                var (title, text) = _pending.Dequeue();
                yield return ShowToast(title, text);
            }
            _isShowingToast = false;
        }

        IEnumerator ShowToast(string title, string text)
        {
            if (toastPrefab == null || toastContainer == null) yield break;
            var go = Instantiate(toastPrefab, toastContainer);
            var labels = go.GetComponentsInChildren<TextMeshProUGUI>();
            if (labels.Length >= 1) labels[0].text = title;
            if (labels.Length >= 2) labels[1].text = text;

            // Slide in
            var rect = go.GetComponent<RectTransform>();
            if (rect != null)
            {
                rect.anchoredPosition = new Vector2(0, -80);
                float t = 0;
                while (t < 0.3f) { t += Time.deltaTime; rect.anchoredPosition = Vector2.Lerp(new(0,-80), Vector2.zero, t/0.3f); yield return null; }
            }
            yield return new WaitForSeconds(toastDuration);

            // Slide out
            if (rect != null)
            {
                float t = 0;
                while (t < 0.2f) { t += Time.deltaTime; rect.anchoredPosition = Vector2.Lerp(Vector2.zero, new(0,-80), t/0.2f); yield return null; }
            }
            Destroy(go);
        }

        void RefreshNotifPanel()
        {
            if (notifListContainer == null || notifEntryPrefab == null) return;
            foreach (Transform c in notifListContainer) Destroy(c.gameObject);
            foreach (var n in _notifications)
            {
                var go = Instantiate(notifEntryPrefab, notifListContainer);
                var labels = go.GetComponentsInChildren<TextMeshProUGUI>();
                if (labels.Length >= 1) labels[0].text = n.Title;
                if (labels.Length >= 2) labels[1].text = n.Text;
            }
        }

        public List<(string title, string text, long time)> GetAll()
            => _notifications.ConvertAll(n => (n.Title, n.Text, n.Time));

        public void ClearAll()
        {
            _notifications.Clear();
            RefreshNotifPanel();
        }
    }
}
