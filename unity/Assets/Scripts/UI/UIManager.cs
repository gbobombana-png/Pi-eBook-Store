using UnityEngine;
using System;
using System.Collections;
using System.Collections.Generic;
using BLOCKSIDE.Core;

namespace BLOCKSIDE.UI
{
    /// <summary>
    /// Central UI controller. Manages screen navigation, panel transitions,
    /// and modal dialogs across the entire game.
    /// </summary>
    public class UIManager : MonoBehaviour
    {
        #region Inspector
        [Header("Screens")]
        [SerializeField] private GameObject splashScreen;
        [SerializeField] private GameObject charSelectScreen;
        [SerializeField] private GameObject hubScreen;
        [SerializeField] private GameObject cityScreen;
        [SerializeField] private GameObject districtScreen;
        [SerializeField] private GameObject crewScreen;
        [SerializeField] private GameObject marketScreen;
        [SerializeField] private GameObject profileScreen;

        [Header("Modals")]
        [SerializeField] private GameObject buildModal;
        [SerializeField] private GameObject buildingDetailModal;
        [SerializeField] private GameObject paymentModal;
        [SerializeField] private GameObject confirmModal;

        [Header("Common UI")]
        [SerializeField] private GameObject toastContainer;
        [SerializeField] private ToastController toastController;
        [SerializeField] private GameObject loadingOverlay;
        [SerializeField] private CanvasGroup fadeOverlay;

        [Header("Transition")]
        [SerializeField] private float fadeDuration = 0.25f;
        [SerializeField] private bool useFadeTransitions = true;
        #endregion

        #region State
        private GameObject currentScreen;
        private GameObject previousScreen;
        private Stack<GameObject> screenHistory = new Stack<GameObject>();
        private bool isTransitioning;
        private Dictionary<GameManager.GameState, GameObject> stateToScreen;
        #endregion

        #region Events
        public static event Action<string> OnScreenShown;
        public static event Action OnBackPressed;
        #endregion

        #region Init
        private void Awake()
        {
            BuildStateMap();
            HideAllScreens();
        }

        private void BuildStateMap()
        {
            stateToScreen = new Dictionary<GameManager.GameState, GameObject>
            {
                { GameManager.GameState.Splash,          splashScreen },
                { GameManager.GameState.CharacterSelect, charSelectScreen },
                { GameManager.GameState.Hub,             hubScreen },
                { GameManager.GameState.City,            cityScreen },
                { GameManager.GameState.District,        districtScreen },
                { GameManager.GameState.Crew,            crewScreen },
                { GameManager.GameState.Market,          marketScreen },
                { GameManager.GameState.Profile,         profileScreen }
            };
        }

        private void HideAllScreens()
        {
            foreach (var screen in stateToScreen.Values)
                if (screen) screen.SetActive(false);
            if (buildModal) buildModal.SetActive(false);
            if (buildingDetailModal) buildingDetailModal.SetActive(false);
            if (paymentModal) paymentModal.SetActive(false);
            if (confirmModal) confirmModal.SetActive(false);
        }
        #endregion

        #region State Response
        /// <summary>Called by GameManager when the game state changes.</summary>
        public void OnGameStateChanged(GameManager.GameState newState)
        {
            if (stateToScreen.TryGetValue(newState, out var screen))
                ShowScreen(screen);
        }
        #endregion

        #region Screen Navigation
        /// <summary>Shows a screen with optional fade transition.</summary>
        public void ShowScreen(GameObject screen, bool pushHistory = true)
        {
            if (screen == null || isTransitioning) return;
            if (useFadeTransitions)
                StartCoroutine(FadeToScreen(screen, pushHistory));
            else
                SwitchScreenImmediate(screen, pushHistory);
        }

        private void SwitchScreenImmediate(GameObject screen, bool pushHistory)
        {
            if (currentScreen)
            {
                if (pushHistory) screenHistory.Push(currentScreen);
                currentScreen.SetActive(false);
            }
            previousScreen = currentScreen;
            currentScreen = screen;
            currentScreen.SetActive(true);
            OnScreenShown?.Invoke(screen.name);
            GameManager.Instance?.Audio.PlayClick();
        }

        private IEnumerator FadeToScreen(GameObject screen, bool pushHistory)
        {
            isTransitioning = true;
            // Fade out
            yield return StartCoroutine(SetFadeAlpha(0f, 1f, fadeDuration / 2f));
            SwitchScreenImmediate(screen, pushHistory);
            // Fade in
            yield return StartCoroutine(SetFadeAlpha(1f, 0f, fadeDuration / 2f));
            isTransitioning = false;
        }

        private IEnumerator SetFadeAlpha(float from, float to, float duration)
        {
            if (!fadeOverlay) yield break;
            fadeOverlay.gameObject.SetActive(true);
            float elapsed = 0f;
            while (elapsed < duration)
            {
                elapsed += Time.deltaTime;
                fadeOverlay.alpha = Mathf.Lerp(from, to, elapsed / duration);
                yield return null;
            }
            fadeOverlay.alpha = to;
            if (to <= 0f) fadeOverlay.gameObject.SetActive(false);
        }

        /// <summary>Returns to the previous screen in history.</summary>
        public void GoBack()
        {
            if (screenHistory.Count == 0) return;
            var prev = screenHistory.Pop();
            if (currentScreen) currentScreen.SetActive(false);
            currentScreen = prev;
            currentScreen.SetActive(true);
            OnBackPressed?.Invoke();
            OnScreenShown?.Invoke(currentScreen.name);
        }
        #endregion

        #region Modals
        public void ShowBuildModal() => SetModalActive(buildModal, true);
        public void HideBuildModal() => SetModalActive(buildModal, false);
        public void ShowDetailModal() => SetModalActive(buildingDetailModal, true);
        public void HideDetailModal() => SetModalActive(buildingDetailModal, false);
        public void ShowPaymentModal() => SetModalActive(paymentModal, true);
        public void HidePaymentModal() => SetModalActive(paymentModal, false);

        private void SetModalActive(GameObject modal, bool active)
        {
            if (!modal) return;
            modal.SetActive(active);
            if (active) GameManager.Instance?.Audio.PlayClick();
        }
        #endregion

        #region Loading
        public void ShowLoading() => { if (loadingOverlay) loadingOverlay.SetActive(true); }
        public void HideLoading() => { if (loadingOverlay) loadingOverlay.SetActive(false); }
        #endregion

        #region Toast
        public void ShowToast(string message, ToastType type = ToastType.Info, float duration = 3f)
        {
            toastController?.Show(message, type, duration);
        }
        #endregion

        #region Android Back Button
        private void Update()
        {
            if (Input.GetKeyDown(KeyCode.Escape)) GoBack();
        }
        #endregion
    }

    public enum ToastType { Info, Success, Error, Warning }
}
