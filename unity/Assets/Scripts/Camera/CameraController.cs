using System.Collections;
using UnityEngine;
using UnityEngine.EventSystems;

namespace BLOCKSIDE
{
    /// <summary>
    /// Isometric camera controller optimized for mobile.
    /// Supports touch pan/pinch-zoom, keyboard fallback, district bounds clamping,
    /// smooth lerp transitions, and a shake effect coroutine.
    /// </summary>
    public class CameraController : MonoBehaviour
    {
        // ─── Inspector ────────────────────────────────────────────────────────────
        [Header("Zoom Settings")]
        [SerializeField] private float zoomMin = 3f;
        [SerializeField] private float zoomMax = 12f;
        [SerializeField] private float zoomSpeed = 0.05f;
        [SerializeField] private float scrollZoomSpeed = 2f;

        [Header("Pan Settings")]
        [SerializeField] private float panSpeed = 0.015f;
        [SerializeField] private float keyboardPanSpeed = 8f;

        [Header("Smooth Lerp")]
        [SerializeField] private float moveLerpSpeed = 10f;
        [SerializeField] private float zoomLerpSpeed = 8f;

        [Header("District Bounds")]
        [SerializeField] private Vector2 boundsMin = new Vector2(-20f, -20f);
        [SerializeField] private Vector2 boundsMax = new Vector2(20f, 20f);

        [Header("Shake")]
        [SerializeField] private float defaultShakeDuration = 0.3f;
        [SerializeField] private float defaultShakeMagnitude = 0.2f;

        // ─── Private State ────────────────────────────────────────────────────────
        private Camera _cam;
        private Vector3 _targetPosition;
        private float _targetZoom;
        private bool _isFreeMode = true;

        // Touch tracking (reused each frame to avoid allocations)
        private Vector2 _lastTouchPos;
        private float _lastPinchDistance;
        private bool _isPanning;
        private bool _isPinching;

        // Shake coroutine handle
        private Coroutine _shakeCoroutine;

        // ─── Unity Lifecycle ──────────────────────────────────────────────────────
        private void Awake()
        {
            _cam = GetComponent<Camera>();
            if (_cam == null) _cam = Camera.main;
            _targetPosition = transform.position;
            _targetZoom = _cam.orthographicSize;
        }

        private void Update()
        {
            if (!_isFreeMode) return;

            HandleTouchInput();
            HandleKeyboardInput();
            ApplySmoothMovement();
        }

        // ─── Input Handling ───────────────────────────────────────────────────────

        /// <summary>Processes 1-finger pan and 2-finger pinch zoom from touch input.</summary>
        private void HandleTouchInput()
        {
            if (Input.touchCount == 0)
            {
                _isPanning = false;
                _isPinching = false;
                return;
            }

            if (Input.touchCount == 1)
            {
                _isPinching = false;
                Touch t = Input.GetTouch(0);

                // Ignore touches over UI
                if (EventSystem.current != null && EventSystem.current.IsPointerOverGameObject(t.fingerId))
                {
                    _isPanning = false;
                    return;
                }

                if (t.phase == TouchPhase.Began)
                {
                    _lastTouchPos = t.position;
                    _isPanning = true;
                }
                else if (t.phase == TouchPhase.Moved && _isPanning)
                {
                    Vector2 delta = t.position - _lastTouchPos;
                    _lastTouchPos = t.position;
                    Pan(-delta * panSpeed * (_targetZoom / zoomMin));
                }
                else if (t.phase == TouchPhase.Ended || t.phase == TouchPhase.Cancelled)
                {
                    _isPanning = false;
                }
            }
            else if (Input.touchCount == 2)
            {
                _isPanning = false;
                Touch t0 = Input.GetTouch(0);
                Touch t1 = Input.GetTouch(1);

                if (t1.phase == TouchPhase.Began)
                {
                    _lastPinchDistance = Vector2.Distance(t0.position, t1.position);
                    _isPinching = true;
                }
                else if (_isPinching && (t0.phase == TouchPhase.Moved || t1.phase == TouchPhase.Moved))
                {
                    float currentDist = Vector2.Distance(t0.position, t1.position);
                    float delta = _lastPinchDistance - currentDist;
                    _lastPinchDistance = currentDist;
                    _targetZoom = Mathf.Clamp(_targetZoom + delta * zoomSpeed, zoomMin, zoomMax);
                }
            }
        }

        /// <summary>WASD keyboard pan and scroll-wheel zoom fallback for editor/desktop.</summary>
        private void HandleKeyboardInput()
        {
            float h = Input.GetAxisRaw("Horizontal");
            float v = Input.GetAxisRaw("Vertical");
            if (Mathf.Abs(h) > 0.01f || Mathf.Abs(v) > 0.01f)
            {
                Pan(new Vector2(h, v) * keyboardPanSpeed * Time.deltaTime);
            }

            float scroll = Input.GetAxis("Mouse ScrollWheel");
            if (Mathf.Abs(scroll) > 0.001f)
            {
                _targetZoom = Mathf.Clamp(_targetZoom - scroll * scrollZoomSpeed, zoomMin, zoomMax);
            }
        }

        /// <summary>Applies position and zoom lerp each frame.</summary>
        private void ApplySmoothMovement()
        {
            transform.position = Vector3.Lerp(transform.position, _targetPosition, moveLerpSpeed * Time.deltaTime);
            _cam.orthographicSize = Mathf.Lerp(_cam.orthographicSize, _targetZoom, zoomLerpSpeed * Time.deltaTime);
        }

        // ─── Public API ───────────────────────────────────────────────────────────

        /// <summary>Pans the camera by a world-space delta, clamped to district bounds.</summary>
        public void Pan(Vector2 delta)
        {
            Vector3 newPos = _targetPosition + new Vector3(delta.x, delta.y, 0f);
            newPos.x = Mathf.Clamp(newPos.x, boundsMin.x, boundsMax.x);
            newPos.y = Mathf.Clamp(newPos.y, boundsMin.y, boundsMax.y);
            _targetPosition = newPos;
        }

        /// <summary>Smoothly moves the camera to a world position.</summary>
        public void MoveTo(Vector3 worldPos)
        {
            worldPos.x = Mathf.Clamp(worldPos.x, boundsMin.x, boundsMax.x);
            worldPos.y = Mathf.Clamp(worldPos.y, boundsMin.y, boundsMax.y);
            worldPos.z = transform.position.z;
            _targetPosition = worldPos;
        }

        /// <summary>Sets the district boundaries so the camera cannot leave this area.</summary>
        public void SetBounds(Vector2 min, Vector2 max)
        {
            boundsMin = min;
            boundsMax = max;
        }

        /// <summary>Sets whether the camera is in free-pan mode (true) or follow mode (false).</summary>
        public void SetFreeMode(bool free)
        {
            _isFreeMode = free;
        }

        /// <summary>
        /// Triggers a screen shake effect.
        /// Use after building placement, income collection, or explosions.
        /// </summary>
        public void Shake(float duration = -1f, float magnitude = -1f)
        {
            if (_shakeCoroutine != null) StopCoroutine(_shakeCoroutine);
            float dur = duration < 0 ? defaultShakeDuration : duration;
            float mag = magnitude < 0 ? defaultShakeMagnitude : magnitude;
            _shakeCoroutine = StartCoroutine(ShakeRoutine(dur, mag));
        }

        private IEnumerator ShakeRoutine(float duration, float magnitude)
        {
            Vector3 origin = _targetPosition;
            float elapsed = 0f;

            while (elapsed < duration)
            {
                float progress = elapsed / duration;
                float dampedMag = magnitude * (1f - progress); // fade out over time
                float offsetX = Random.Range(-1f, 1f) * dampedMag;
                float offsetY = Random.Range(-1f, 1f) * dampedMag;
                transform.position = _targetPosition + new Vector3(offsetX, offsetY, 0f);
                elapsed += Time.deltaTime;
                yield return null;
            }

            transform.position = _targetPosition;
            _shakeCoroutine = null;
        }

#if UNITY_EDITOR
        private void OnDrawGizmosSelected()
        {
            Gizmos.color = Color.cyan;
            Vector3 center = new Vector3((boundsMin.x + boundsMax.x) * 0.5f, (boundsMin.y + boundsMax.y) * 0.5f, 0f);
            Vector3 size = new Vector3(boundsMax.x - boundsMin.x, boundsMax.y - boundsMin.y, 0f);
            Gizmos.DrawWireCube(center, size);
        }
#endif
    }
}
