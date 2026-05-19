using UnityEngine;

namespace Blockside.Core
{
    /// <summary>
    /// Configuration de build — accessible via Resources.Load en runtime.
    /// Modifier les valeurs depuis l'inspecteur Unity (Assets/Resources/BuildConfig.asset).
    /// </summary>
    [CreateAssetMenu(fileName = "BuildConfig", menuName = "BLOCKSIDE/Build Config")]
    public class BuildConfig : ScriptableObject
    {
        [Header("Identité")]
        public string appName    = "BLOCKSIDE";
        public string version    = "1.0.0";
        public int    buildNumber = 1;

        [Header("Backend")]
        [Tooltip("URL de l'API en production")]
        public string apiBaseUrl = "https://api.blockside.io/api";
        [Tooltip("URL locale pour le développement")]
        public string apiBaseUrlDev = "http://10.0.2.2:3001/api"; // 10.0.2.2 = localhost depuis émulateur Android

        [Header("Pi Network")]
        public string piAppId = "blockside_app_id";
        public bool   piSandboxMode = false;

        [Header("Performances")]
        [Range(30, 120)]
        public int targetFrameRate = 60;
        public bool enableVSync = false;

        [Header("Debug")]
        public bool showDebugUI = false;
        public bool logApiCalls = false;

        private static BuildConfig _instance;
        public static BuildConfig Instance
        {
            get
            {
                if (_instance == null)
                    _instance = Resources.Load<BuildConfig>("BuildConfig");
                return _instance;
            }
        }

        public string ActiveApiUrl =>
            Debug.isDebugBuild ? apiBaseUrlDev : apiBaseUrl;

        void OnEnable()
        {
            if (Application.isPlaying)
            {
                Application.targetFrameRate = targetFrameRate;
                QualitySettings.vSyncCount  = enableVSync ? 1 : 0;
            }
        }
    }
}
