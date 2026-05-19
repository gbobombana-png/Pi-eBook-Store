using UnityEngine;

namespace BLOCKSIDE
{
    /// <summary>
    /// Smooth camera follow for the PlayerController.
    /// Supports a configurable dead zone, offset, and hot-switching
    /// between free-pan and follow modes.
    /// </summary>
    [RequireComponent(typeof(Camera))]
    public class CameraFollowPlayer : MonoBehaviour
    {
        // ─── Inspector ────────────────────────────────────────────────────────────
        [Header("Target")]
        [SerializeField] private Transform target;

        [Header("Follow Settings")]
        [SerializeField] private Vector3 offset = new Vector3(0f, 2f, -10f);
        [SerializeField] private float followSpeed = 6f;

        [Header("Dead Zone")]
        [Tooltip("Camera won't move until the player leaves this radius (world units).")]
        [SerializeField] private float deadZoneRadius = 1.5f;

        [Header("Mode")]
        [SerializeField] private bool followOnStart = true;

        // ─── Private State ────────────────────────────────────────────────────────
        private bool _following;
        private CameraController _cameraController;
        private Vector3 _smoothVelocity;

        // ─── Unity Lifecycle ──────────────────────────────────────────────────────
        private void Awake()
        {
            _cameraController = GetComponent<CameraController>();
            _following = followOnStart;
        }

        private void Start()
        {
            if (_following && target != null)
                SnapToTarget();
        }

        private void LateUpdate()
        {
            if (!_following || target == null) return;

            Vector3 desired = target.position + offset;
            float dist = Vector3.Distance(transform.position, desired);

            // Only move when outside the dead zone
            if (dist > deadZoneRadius)
            {
                transform.position = Vector3.SmoothDamp(
                    transform.position,
                    desired,
                    ref _smoothVelocity,
                    1f / followSpeed
                );
            }
        }

        // ─── Public API ───────────────────────────────────────────────────────────

        /// <summary>Assigns a new target for the camera to follow.</summary>
        public void SetTarget(Transform newTarget)
        {
            target = newTarget;
        }

        /// <summary>Enables follow mode. Disables free-pan on the CameraController if present.</summary>
        public void EnableFollow()
        {
            _following = true;
            if (_cameraController != null) _cameraController.SetFreeMode(false);
        }

        /// <summary>Disables follow mode and returns to free-pan.</summary>
        public void DisableFollow()
        {
            _following = false;
            if (_cameraController != null) _cameraController.SetFreeMode(true);
        }

        /// <summary>Instantly places the camera on the target without lerping.</summary>
        public void SnapToTarget()
        {
            if (target == null) return;
            transform.position = target.position + offset;
            _smoothVelocity = Vector3.zero;
        }

        /// <summary>Sets the world-space offset from the target.</summary>
        public void SetOffset(Vector3 newOffset)
        {
            offset = newOffset;
        }

        /// <summary>Sets the dead-zone radius in world units.</summary>
        public void SetDeadZone(float radius)
        {
            deadZoneRadius = Mathf.Max(0f, radius);
        }

#if UNITY_EDITOR
        private void OnDrawGizmosSelected()
        {
            if (target == null) return;
            Gizmos.color = Color.yellow;
            Gizmos.DrawWireSphere(target.position, deadZoneRadius);
            Gizmos.color = Color.green;
            Gizmos.DrawLine(transform.position, target.position);
        }
#endif
    }
}
