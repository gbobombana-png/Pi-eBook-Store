using UnityEngine;
using BLOCKSIDE.Player;

namespace BLOCKSIDE.Player
{
    /// <summary>
    /// Handles player character movement, input processing, and camera follow.
    /// Designed for mobile (touch) with optional keyboard input for editor testing.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public class PlayerController : MonoBehaviour
    {
        #region Inspector
        [Header("References")]
        [SerializeField] private PlayerData playerData;
        [SerializeField] private Animator animator;
        [SerializeField] private SpriteRenderer spriteRenderer;
        [SerializeField] private Camera followCamera;

        [Header("Movement")]
        [SerializeField] private float moveSpeed = 5f;
        [SerializeField] private float runMultiplier = 1.8f;
        [SerializeField] private float acceleration = 20f;
        [SerializeField] private float deceleration = 25f;

        [Header("Camera")]
        [SerializeField] private float cameraSmoothing = 8f;
        [SerializeField] private Vector3 cameraOffset = new Vector3(0f, 2f, -10f);
        [SerializeField] private Vector2 cameraBoundsMin = new Vector2(-50f, -50f);
        [SerializeField] private Vector2 cameraBoundsMax = new Vector2(50f, 50f);

        [Header("Touch Input")]
        [SerializeField] private float touchDeadzone = 0.1f;
        [SerializeField] private FloatingJoystick joystick; // Optional on-screen joystick
        #endregion

        #region Private State
        private Rigidbody2D rb;
        private Vector2 moveInput;
        private Vector2 currentVelocity;
        private bool isMoving;
        private bool isFacingRight = true;
        private static readonly int AnimSpeed = Animator.StringToHash("Speed");
        private static readonly int AnimMoving = Animator.StringToHash("IsMoving");
        #endregion

        #region Properties
        public Vector2 Position => transform.position;
        public bool IsMoving => isMoving;
        #endregion

        #region Unity Lifecycle
        private void Awake()
        {
            rb = GetComponent<Rigidbody2D>();
            rb.gravityScale = 0f;
            rb.constraints = RigidbodyConstraints2D.FreezeRotation;
            if (!followCamera) followCamera = Camera.main;
            ApplyCharacterVisuals();
        }

        private void Update()
        {
            GatherInput();
            UpdateAnimation();
        }

        private void FixedUpdate()
        {
            ApplyMovement();
        }

        private void LateUpdate()
        {
            UpdateCamera();
        }
        #endregion

        #region Input
        private void GatherInput()
        {
            moveInput = Vector2.zero;
            // Joystick (mobile)
            if (joystick != null)
            {
                moveInput = new Vector2(joystick.Horizontal, joystick.Vertical);
                if (moveInput.magnitude < touchDeadzone) moveInput = Vector2.zero;
            }
            // Keyboard fallback (editor / desktop)
            #if UNITY_EDITOR || UNITY_STANDALONE
            float h = Input.GetAxisRaw("Horizontal");
            float v = Input.GetAxisRaw("Vertical");
            if (Mathf.Abs(h) > 0.01f || Mathf.Abs(v) > 0.01f)
                moveInput = new Vector2(h, v).normalized;
            #endif
            if (moveInput.magnitude > 1f) moveInput.Normalize();
        }
        #endregion

        #region Movement
        private void ApplyMovement()
        {
            float speed = moveSpeed;
            if (Input.GetKey(KeyCode.LeftShift)) speed *= runMultiplier;
            Vector2 targetVel = moveInput * speed;
            float rate = moveInput.magnitude > 0.01f ? acceleration : deceleration;
            currentVelocity = Vector2.MoveTowards(currentVelocity, targetVel, rate * Time.fixedDeltaTime);
            rb.velocity = currentVelocity;
            isMoving = currentVelocity.magnitude > 0.1f;
            if (isMoving && currentVelocity.x != 0)
            {
                bool shouldFaceRight = currentVelocity.x > 0;
                if (shouldFaceRight != isFacingRight) Flip();
            }
        }

        private void Flip()
        {
            isFacingRight = !isFacingRight;
            if (spriteRenderer) spriteRenderer.flipX = !isFacingRight;
        }
        #endregion

        #region Camera
        private void UpdateCamera()
        {
            if (!followCamera) return;
            Vector3 target = transform.position + cameraOffset;
            target.x = Mathf.Clamp(target.x, cameraBoundsMin.x, cameraBoundsMax.x);
            target.y = Mathf.Clamp(target.y, cameraBoundsMin.y, cameraBoundsMax.y);
            followCamera.transform.position = Vector3.Lerp(followCamera.transform.position, target, cameraSmoothing * Time.deltaTime);
        }
        #endregion

        #region Animation
        private void UpdateAnimation()
        {
            if (!animator) return;
            animator.SetFloat(AnimSpeed, currentVelocity.magnitude);
            animator.SetBool(AnimMoving, isMoving);
        }
        #endregion

        #region Visuals
        private void ApplyCharacterVisuals()
        {
            if (playerData == null || spriteRenderer == null) return;
            if (playerData.characterSprite) spriteRenderer.sprite = playerData.characterSprite;
            spriteRenderer.color = playerData.primaryColor;
            if (animator && playerData.animatorController) animator.runtimeAnimatorController = playerData.animatorController;
        }

        public void SetPlayerData(PlayerData data)
        {
            playerData = data;
            ApplyCharacterVisuals();
        }
        #endregion

        #region Public API
        public void Teleport(Vector2 position)
        {
            rb.position = position;
            currentVelocity = Vector2.zero;
            rb.velocity = Vector2.zero;
        }

        public void SetMovementEnabled(bool enabled)
        {
            this.enabled = enabled;
            if (!enabled) { rb.velocity = Vector2.zero; currentVelocity = Vector2.zero; }
        }
        #endregion
    }

    // Stub for FloatingJoystick — replace with actual joystick package
    public class FloatingJoystick : MonoBehaviour
    {
        public float Horizontal { get; protected set; }
        public float Vertical { get; protected set; }
    }
}
