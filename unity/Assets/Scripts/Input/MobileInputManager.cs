using System;
using UnityEngine;
using UnityEngine.EventSystems;

namespace Blockside.Input
{
    /// <summary>
    /// Gestion des entrées tactiles Android — tap, swipe, pinch-to-zoom.
    /// S'abonne aux événements pour éviter le polling.
    /// </summary>
    public class MobileInputManager : MonoBehaviour
    {
        public static MobileInputManager Instance { get; private set; }

        [Header("Paramètres")]
        [SerializeField] private float swipeThreshold = 80f;     // pixels
        [SerializeField] private float tapMaxDuration = 0.2f;    // secondes
        [SerializeField] private float doubleTapInterval = 0.35f;

        // ── Événements ────────────────────────────────────────────────
        public event Action<Vector2> OnTap;
        public event Action<Vector2> OnDoubleTap;
        public event Action<Vector2> OnSwipe;          // direction normalisée
        public event Action<float>   OnPinch;          // delta scale
        public event Action<Vector2> OnLongPress;

        [Header("Debug")]
        [SerializeField] private bool logInputs;

        private Vector2 _touchStart;
        private float   _touchStartTime;
        private float   _lastTapTime;
        private bool    _longPressFired;
        private const float LongPressDuration = 0.6f;

        void Awake()
        {
            if (Instance != null) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
            // Fréquence de balayage tactile cible sur Android
            Input.multiTouchEnabled = true;
            Screen.sleepTimeout = SleepTimeout.NeverSleep;
        }

        void Update()
        {
#if UNITY_EDITOR || UNITY_STANDALONE
            HandleMouseInput();
#else
            HandleTouchInput();
#endif
        }

        // ── Souris (éditeur) ──────────────────────────────────────────
        void HandleMouseInput()
        {
            if (EventSystem.current != null && EventSystem.current.IsPointerOverGameObject()) return;

            if (UnityEngine.Input.GetMouseButtonDown(0))
            {
                _touchStart = UnityEngine.Input.mousePosition;
                _touchStartTime = Time.time;
                _longPressFired = false;
            }

            if (UnityEngine.Input.GetMouseButton(0))
            {
                if (!_longPressFired && Time.time - _touchStartTime >= LongPressDuration)
                {
                    _longPressFired = true;
                    OnLongPress?.Invoke(_touchStart);
                    if (logInputs) Debug.Log($"[Input] LongPress @ {_touchStart}");
                }
            }

            if (UnityEngine.Input.GetMouseButtonUp(0))
            {
                float duration = Time.time - _touchStartTime;
                Vector2 delta  = (Vector2)UnityEngine.Input.mousePosition - _touchStart;
                if (_longPressFired) return;

                if (delta.magnitude > swipeThreshold)
                {
                    OnSwipe?.Invoke(delta.normalized);
                    if (logInputs) Debug.Log($"[Input] Swipe {delta.normalized}");
                }
                else if (duration <= tapMaxDuration)
                {
                    float sinceLastTap = Time.time - _lastTapTime;
                    if (sinceLastTap <= doubleTapInterval)
                    {
                        OnDoubleTap?.Invoke(_touchStart);
                        if (logInputs) Debug.Log("[Input] DoubleTap");
                        _lastTapTime = 0;
                    }
                    else
                    {
                        OnTap?.Invoke(_touchStart);
                        if (logInputs) Debug.Log($"[Input] Tap @ {_touchStart}");
                        _lastTapTime = Time.time;
                    }
                }
            }
        }

        // ── Tactile (Android) ─────────────────────────────────────────
        void HandleTouchInput()
        {
            if (UnityEngine.Input.touchCount == 0) return;

            // Pinch-to-zoom (2 doigts)
            if (UnityEngine.Input.touchCount == 2)
            {
                var t0 = UnityEngine.Input.GetTouch(0);
                var t1 = UnityEngine.Input.GetTouch(1);
                if (t0.phase == TouchPhase.Moved || t1.phase == TouchPhase.Moved)
                {
                    float prevDist = Vector2.Distance(t0.position - t0.deltaPosition, t1.position - t1.deltaPosition);
                    float currDist = Vector2.Distance(t0.position, t1.position);
                    OnPinch?.Invoke(currDist - prevDist);
                }
                return;
            }

            var touch = UnityEngine.Input.GetTouch(0);
            if (EventSystem.current != null && EventSystem.current.IsPointerOverGameObject(touch.fingerId)) return;

            switch (touch.phase)
            {
                case TouchPhase.Began:
                    _touchStart = touch.position;
                    _touchStartTime = Time.time;
                    _longPressFired = false;
                    break;

                case TouchPhase.Stationary:
                    if (!_longPressFired && Time.time - _touchStartTime >= LongPressDuration)
                    {
                        _longPressFired = true;
                        OnLongPress?.Invoke(touch.position);
                    }
                    break;

                case TouchPhase.Ended:
                    if (_longPressFired) break;
                    float dur   = Time.time - _touchStartTime;
                    Vector2 d   = touch.position - _touchStart;
                    if (d.magnitude > swipeThreshold)
                    {
                        OnSwipe?.Invoke(d.normalized);
                    }
                    else if (dur <= tapMaxDuration)
                    {
                        float sinceLastTap = Time.time - _lastTapTime;
                        if (sinceLastTap <= doubleTapInterval) { OnDoubleTap?.Invoke(touch.position); _lastTapTime = 0; }
                        else { OnTap?.Invoke(touch.position); _lastTapTime = Time.time; }
                    }
                    break;
            }
        }

        /// <summary>Retourne vrai si la position est au-dessus d'un élément UI.</summary>
        public static bool IsOverUI(Vector2 screenPos)
            => EventSystem.current != null && EventSystem.current.IsPointerOverGameObject();
    }
}
