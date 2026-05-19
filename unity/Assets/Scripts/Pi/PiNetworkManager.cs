using UnityEngine;
using System;
using System.Collections;
using System.Runtime.InteropServices;

namespace BLOCKSIDE.Pi
{
    /// <summary>
    /// Pi Network SDK integration for Unity.
    /// Uses JSLib bridge (WebGL) or WebView plugin (mobile) to communicate with Pi SDK.
    /// Falls back to demo mode when Pi SDK is unavailable.
    /// </summary>
    public class PiNetworkManager : MonoBehaviour
    {
        #region Inspector
        [Header("SDK Settings")]
        [SerializeField] private bool sandboxMode = true;
        [SerializeField] private bool demoFallback = true;
        [SerializeField] private float demoDelay = 2f;

        [Header("App Info")]
        [SerializeField] private string appVersion = "1.0.0";
        #endregion

        #region JSLib Imports (WebGL)
        #if UNITY_WEBGL && !UNITY_EDITOR
        [DllImport("__Internal")]
        private static extern void Pi_Authenticate(string callbackObj, string sandboxStr);

        [DllImport("__Internal")]
        private static extern void Pi_CreatePayment(string paymentDataJson, string callbackObj);

        [DllImport("__Internal")]
        private static extern bool Pi_IsAvailable();
        #endif
        #endregion

        #region State
        private bool isAuthenticated;
        private string authenticatedUsername;
        private string authenticatedUid;
        private bool sdkAvailable;
        private Action<PiAuthResult> pendingAuthCallback;
        private Action<PiPaymentResult> pendingPaymentCallback;
        #endregion

        #region Events
        public static event Action<PiAuthResult> OnAuthenticated;
        public static event Action<string> OnAuthError;
        public static event Action<PiPaymentResult> OnPaymentCompleted;
        public static event Action<string> OnPaymentError;
        #endregion

        #region Properties
        public bool IsAuthenticated => isAuthenticated;
        public string Username => authenticatedUsername;
        public string Uid => authenticatedUid;
        public bool SdkAvailable => sdkAvailable;
        public bool SandboxMode => sandboxMode;
        #endregion

        #region Init
        private void Awake()
        {
            CheckSdkAvailability();
        }

        private void CheckSdkAvailability()
        {
            #if UNITY_WEBGL && !UNITY_EDITOR
            sdkAvailable = Pi_IsAvailable();
            #else
            sdkAvailable = false;
            #endif
            Debug.Log($"[PiNetworkManager] SDK available: {sdkAvailable}, Sandbox: {sandboxMode}");
        }
        #endregion

        #region Authentication
        /// <summary>Authenticates the user via Pi Network SDK.</summary>
        public void Authenticate(Action<PiAuthResult> callback)
        {
            pendingAuthCallback = callback;
            if (sdkAvailable)
            {
                #if UNITY_WEBGL && !UNITY_EDITOR
                Pi_Authenticate(gameObject.name, sandboxMode ? "true" : "false");
                #endif
            }
            else if (demoFallback)
            {
                StartCoroutine(SimulateAuth());
            }
            else
            {
                callback?.Invoke(new PiAuthResult { success = false, error = "Pi SDK not available" });
            }
        }

        private IEnumerator SimulateAuth()
        {
            yield return new WaitForSeconds(demoDelay);
            string demoUser = "BlockPlayer_" + UnityEngine.Random.Range(1000, 9999);
            var result = new PiAuthResult
            {
                success = true,
                username = demoUser,
                uid = "demo_" + Guid.NewGuid().ToString("N").Substring(0, 8),
                isDemo = true
            };
            HandleAuthSuccess(result);
        }

        // Called from JSLib
        public void OnPiAuthSuccess(string json)
        {
            var result = JsonUtility.FromJson<PiAuthResult>(json);
            result.success = true;
            HandleAuthSuccess(result);
        }

        public void OnPiAuthError(string error)
        {
            Debug.LogWarning("[PiNetworkManager] Auth error: " + error);
            pendingAuthCallback?.Invoke(new PiAuthResult { success = false, error = error });
            OnAuthError?.Invoke(error);
            if (demoFallback) StartCoroutine(SimulateAuth());
        }

        private void HandleAuthSuccess(PiAuthResult result)
        {
            isAuthenticated = true;
            authenticatedUsername = result.username;
            authenticatedUid = result.uid;
            PlayerPrefs.SetString("username", result.username);
            PlayerPrefs.SetString("piUid", result.uid);
            PlayerPrefs.Save();
            Debug.Log($"[PiNetworkManager] Authenticated as: {result.username}");
            pendingAuthCallback?.Invoke(result);
            OnAuthenticated?.Invoke(result);
        }
        #endregion

        #region Payments
        /// <summary>Initiates a Pi payment for a premium item.</summary>
        public void CreatePayment(PiPaymentData paymentData, Action<PiPaymentResult> callback)
        {
            pendingPaymentCallback = callback;
            if (sdkAvailable)
            {
                #if UNITY_WEBGL && !UNITY_EDITOR
                string json = JsonUtility.ToJson(paymentData);
                Pi_CreatePayment(json, gameObject.name);
                #endif
            }
            else if (demoFallback)
            {
                StartCoroutine(SimulatePayment(paymentData));
            }
            else
            {
                callback?.Invoke(new PiPaymentResult { success = false, error = "Pi SDK not available" });
            }
        }

        private IEnumerator SimulatePayment(PiPaymentData data)
        {
            yield return new WaitForSeconds(demoDelay);
            var result = new PiPaymentResult
            {
                success = true,
                paymentId = "demo_" + Guid.NewGuid().ToString("N").Substring(0, 8),
                txid = "demo_tx_" + Guid.NewGuid().ToString("N").Substring(0, 12),
                itemId = data.metadata,
                amount = data.amount,
                isDemo = true
            };
            HandlePaymentSuccess(result);
        }

        // Called from JSLib
        public void OnPiPaymentComplete(string json)
        {
            var result = JsonUtility.FromJson<PiPaymentResult>(json);
            result.success = true;
            HandlePaymentSuccess(result);
        }

        public void OnPiPaymentError(string error)
        {
            Debug.LogWarning("[PiNetworkManager] Payment error: " + error);
            pendingPaymentCallback?.Invoke(new PiPaymentResult { success = false, error = error });
            OnPaymentError?.Invoke(error);
        }

        public void OnPiPaymentCancelled(string paymentId)
        {
            pendingPaymentCallback?.Invoke(new PiPaymentResult { success = false, error = "cancelled" });
            OnPaymentError?.Invoke("Payment cancelled");
        }

        private void HandlePaymentSuccess(PiPaymentResult result)
        {
            Debug.Log($"[PiNetworkManager] Payment success: {result.paymentId} | item: {result.itemId}");
            pendingPaymentCallback?.Invoke(result);
            OnPaymentCompleted?.Invoke(result);
        }
        #endregion
    }

    // ─────────────────────────────────────────────────────────────
    // Data transfer objects
    // ─────────────────────────────────────────────────────────────

    [Serializable]
    public class PiAuthResult
    {
        public bool success;
        public string username;
        public string uid;
        public string error;
        public bool isDemo;
    }

    [Serializable]
    public class PiPaymentData
    {
        public float amount;
        public string memo;
        public string metadata; // itemId
    }

    [Serializable]
    public class PiPaymentResult
    {
        public bool success;
        public string paymentId;
        public string txid;
        public string itemId;
        public float amount;
        public string error;
        public bool isDemo;
    }
}
