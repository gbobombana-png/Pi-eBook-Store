using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;
using Blockside.Core;

namespace Blockside.Bootstrap
{
    /// <summary>
    /// Point d'entrée de l'application — scène vide chargée en premier.
    /// Instancie tous les singletons persistants puis charge la scène principale.
    /// </summary>
    public class SceneBootstrap : MonoBehaviour
    {
        [Header("Prefabs singletons (DontDestroyOnLoad)")]
        [SerializeField] private GameObject gameManagerPrefab;
        [SerializeField] private GameObject notificationSystemPrefab;
        [SerializeField] private GameObject mobileInputPrefab;
        [SerializeField] private GameObject audioManagerPrefab;

        [Header("Scène à charger après bootstrap")]
        [SerializeField] private string mainSceneName = "SplashScene";

        [Header("Version")]
        [SerializeField] private string buildVersion = "1.0.0";

        void Awake()
        {
            Application.targetFrameRate = 60;
            QualitySettings.vSyncCount  = 0;
            Screen.orientation = ScreenOrientation.Portrait;
            Debug.Log($"[Bootstrap] BLOCKSIDE v{buildVersion} — Démarrage...");
        }

        IEnumerator Start()
        {
            // Instancie les singletons dans l'ordre
            InstantiateIfAbsent<NotificationSystem>(notificationSystemPrefab, "NotificationSystem");
            InstantiateIfAbsent<MobileInputManager>(mobileInputPrefab,       "MobileInputManager");
            InstantiateIfAbsent<GameManager>(gameManagerPrefab,             "GameManager");

            // Petit délai pour laisser les Awake() se finaliser
            yield return null;

            Debug.Log("[Bootstrap] Singletons prêts — chargement scène principale...");
            SceneManager.LoadScene(mainSceneName);
        }

        static void InstantiateIfAbsent<T>(GameObject prefab, string fallbackName) where T : Component
        {
            if (FindObjectOfType<T>() != null) return;
            if (prefab != null)
                Instantiate(prefab);
            else
            {
                var go = new GameObject(fallbackName);
                go.AddComponent<T>();
            }
        }
    }
}
