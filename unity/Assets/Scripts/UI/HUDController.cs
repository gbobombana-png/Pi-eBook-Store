using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System;
using System.Collections;
using System.Collections.Generic;
using BLOCKSIDE.Core;
using BLOCKSIDE.Economy;
using BLOCKSIDE.Social;
using PlacedBuilding = BLOCKSIDE.Economy.PlacedBuilding;

namespace BLOCKSIDE.UI
{
    /// <summary>
    /// Controls the HUD overlay: stats bar, activity feed, income notifications,
    /// toast messages, and navigation bar. Updates in real time.
    /// </summary>
    public class HUDController : MonoBehaviour
    {
        #region Inspector
        [Header("Top Bar")]
        [SerializeField] private Image avatarCircle;
        [SerializeField] private TextMeshProUGUI usernameText;
        [SerializeField] private TextMeshProUGUI repTitleText;

        [Header("Stats")]
        [SerializeField] private TextMeshProUGUI moneyText;
        [SerializeField] private TextMeshProUGUI reputationText;
        [SerializeField] private TextMeshProUGUI buildingsText;
        [SerializeField] private TextMeshProUGUI pendingIncomeText;

        [Header("Activity Feed")]
        [SerializeField] private Transform activityContainer;
        [SerializeField] private GameObject activityItemPrefab;
        [SerializeField] private int maxActivities = 8;

        [Header("Nav Bar")]
        [SerializeField] private Button hubNavBtn;
        [SerializeField] private Button cityNavBtn;
        [SerializeField] private Button marketNavBtn;
        [SerializeField] private Button crewNavBtn;
        [SerializeField] private Button profileNavBtn;
        [SerializeField] private Color navActiveColor = new Color(1f, .42f, .1f);
        [SerializeField] private Color navInactiveColor = new Color(.42f, .42f, .60f);

        [Header("Notifications")]
        [SerializeField] private GameObject incomeBadge;
        [SerializeField] private TextMeshProUGUI incomeBadgeText;

        [Header("Toast")]
        [SerializeField] private ToastController toastController;
        #endregion

        #region State
        private List<string> activityLog = new List<string>();
        private Coroutine updateCoroutine;
        #endregion

        #region Unity Lifecycle
        private void OnEnable()
        {
            SubscribeToEvents();
            updateCoroutine = StartCoroutine(PeriodicUpdate());
        }

        private void OnDisable()
        {
            UnsubscribeFromEvents();
            if (updateCoroutine != null) StopCoroutine(updateCoroutine);
        }
        #endregion

        #region Event Subscription
        private void SubscribeToEvents()
        {
            EconomyManager.OnMoneyChanged += OnMoneyChanged;
            EconomyManager.OnIncomeCollected += OnIncomeCollected;
            ReputationSystem.OnReputationChanged += OnReputationChanged;
            ReputationSystem.OnTitleUnlocked += OnTitleUnlocked;
            IncomeSystem.OnTotalPendingChanged += OnTotalPendingChanged;
            BuildingManager.OnBuildingPlaced += OnBuildingPlaced;
        }

        private void UnsubscribeFromEvents()
        {
            EconomyManager.OnMoneyChanged -= OnMoneyChanged;
            EconomyManager.OnIncomeCollected -= OnIncomeCollected;
            ReputationSystem.OnReputationChanged -= OnReputationChanged;
            ReputationSystem.OnTitleUnlocked -= OnTitleUnlocked;
            IncomeSystem.OnTotalPendingChanged -= OnTotalPendingChanged;
            BuildingManager.OnBuildingPlaced -= OnBuildingPlaced;
        }
        #endregion

        #region State Response
        public void OnGameStateChanged(GameManager.GameState state)
        {
            RefreshAll();
            UpdateNavActiveState(state);
        }
        #endregion

        #region Refresh
        public void RefreshAll()
        {
            var gm = GameManager.Instance;
            if (gm == null) return;
            string charId = PlayerPrefs.GetString("selectedCharacter", "zay");
            string username = PlayerPrefs.GetString("username", "Player");
            // Top bar
            if (usernameText) usernameText.text = username;
            if (repTitleText) repTitleText.text = gm.Reputation.CurrentTitle;
            // Stats
            long money = gm.Economy.Money;
            int rep = gm.Reputation.Reputation;
            int buildings = gm.Buildings.TotalPlacedCount();
            if (moneyText) moneyText.text = FormatNumber(money);
            if (reputationText) reputationText.text = FormatNumber(rep);
            if (buildingsText) buildingsText.text = buildings.ToString();
            // Pending income
            bool vip = gm.Marketplace.IsOwned("vip");
            long pending = gm.Income.CalculateTotalPending(charId, vip);
            if (pendingIncomeText) pendingIncomeText.text = FormatNumber(pending);
            if (incomeBadge) incomeBadge.SetActive(pending > 0);
            if (incomeBadgeText) incomeBadgeText.text = FormatNumber(pending);
            RefreshActivityFeed();
        }

        private IEnumerator PeriodicUpdate()
        {
            while (true)
            {
                yield return new WaitForSeconds(10f);
                RefreshAll();
            }
        }
        #endregion

        #region Event Handlers
        private void OnMoneyChanged(long newMoney, long delta)
        {
            if (moneyText) moneyText.text = FormatNumber(newMoney);
            if (delta > 0) ShowFloatingText("+" + FormatNumber(delta), Color.green);
        }

        private void OnIncomeCollected(long amount)
        {
            GameManager.Instance?.Audio.PlayCollect();
            AddActivity("💰 Collecte: +" + FormatNumber(amount));
        }

        private void OnReputationChanged(int newRep, int delta)
        {
            if (reputationText) reputationText.text = FormatNumber(newRep);
            if (delta > 0) ShowFloatingText("+⭐" + delta + " rep", new Color(1f, .84f, 0f));
        }

        private void OnTitleUnlocked(string title)
        {
            if (repTitleText) repTitleText.text = title;
            AddActivity("🏆 Nouveau titre: " + title);
            toastController?.Show("🏆 " + title, ToastType.Success);
        }

        private void OnTotalPendingChanged(long pending)
        {
            if (pendingIncomeText) pendingIncomeText.text = FormatNumber(pending);
            if (incomeBadge) incomeBadge.SetActive(pending > 0);
            if (incomeBadgeText) incomeBadgeText.text = FormatNumber(pending);
        }

        private void OnBuildingPlaced(PlacedBuilding building)
        {
            int total = GameManager.Instance?.Buildings.TotalPlacedCount() ?? 0;
            if (buildingsText) buildingsText.text = total.ToString();
            AddActivity("🏗️ Bâtiment construit dans " + building.districtId);
        }
        #endregion

        #region Activity Feed
        public void AddActivity(string text)
        {
            activityLog.Insert(0, text);
            if (activityLog.Count > 20) activityLog.RemoveAt(activityLog.Count - 1);
            RefreshActivityFeed();
        }

        private void RefreshActivityFeed()
        {
            if (!activityContainer) return;
            // Clear old items
            foreach (Transform child in activityContainer)
                Destroy(child.gameObject);
            // Populate
            int count = Mathf.Min(activityLog.Count, maxActivities);
            for (int i = 0; i < count; i++)
            {
                if (!activityItemPrefab) break;
                var item = Instantiate(activityItemPrefab, activityContainer);
                var text = item.GetComponentInChildren<TextMeshProUGUI>();
                if (text) text.text = activityLog[i];
            }
        }
        #endregion

        #region Navigation
        private void UpdateNavActiveState(GameManager.GameState state)
        {
            SetNavActive(hubNavBtn,     state == GameManager.GameState.Hub);
            SetNavActive(cityNavBtn,    state == GameManager.GameState.City || state == GameManager.GameState.District);
            SetNavActive(marketNavBtn,  state == GameManager.GameState.Market);
            SetNavActive(crewNavBtn,    state == GameManager.GameState.Crew);
            SetNavActive(profileNavBtn, state == GameManager.GameState.Profile);
        }

        private void SetNavActive(Button btn, bool active)
        {
            if (!btn) return;
            var graphic = btn.GetComponent<Graphic>();
            if (graphic) graphic.color = active ? navActiveColor : navInactiveColor;
            var tmp = btn.GetComponentInChildren<TextMeshProUGUI>();
            if (tmp) tmp.color = active ? navActiveColor : navInactiveColor;
        }
        #endregion

        #region Floating Text
        private void ShowFloatingText(string text, Color color)
        {
            // Spawn floating "+amount" animation above stats bar
            // Implementation depends on FloatingText prefab setup
            Debug.Log($"[HUD] Floating: {text}");
        }
        #endregion

        #region Helpers
        private static string FormatNumber(long n)
        {
            if (n >= 1_000_000) return $"{n / 1_000_000f:F1}M";
            if (n >= 1_000) return $"{n / 1_000f:F1}K";
            return n.ToString();
        }
        #endregion
    }
}
