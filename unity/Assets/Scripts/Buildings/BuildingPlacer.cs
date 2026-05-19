using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;

namespace BLOCKSIDE
{
    /// <summary>
    /// Handles grid-based isometric building placement.
    /// Shows a ghost preview, highlights valid slots, validates placement,
    /// and snaps the building to the grid on confirmation tap.
    /// </summary>
    public class BuildingPlacer : MonoBehaviour
    {
        // ─── Singleton ────────────────────────────────────────────────────────────
        public static BuildingPlacer Instance { get; private set; }

        // ─── Inspector ────────────────────────────────────────────────────────────
        [Header("Grid")]
        [SerializeField] private Vector2 cellSize = new Vector2(1f, 0.5f);
        [SerializeField] private LayerMask slotLayerMask;

        [Header("Ghost Preview")]
        [SerializeField] private Material ghostMaterial;
        [Tooltip("Alpha of the ghost preview (0-1).")]
        [SerializeField, Range(0f, 1f)] private float ghostAlpha = 0.5f;

        [Header("Highlighting")]
        [SerializeField] private Color validSlotColor   = new Color(0f, 1f, 0.4f, 0.35f);
        [SerializeField] private Color invalidSlotColor = new Color(1f, 0.2f, 0.2f, 0.35f);

        // ─── Private State ────────────────────────────────────────────────────────
        private BuildingData _pendingData;
        private string _targetDistrictId;
        private GameObject _ghostInstance;
        private bool _isPlacing;

        // Track which grid positions are occupied
        private readonly HashSet<Vector2Int> _occupiedSlots = new HashSet<Vector2Int>();

        // Cached slot renderers for highlight management
        private readonly List<SpriteRenderer> _slotRenderers = new List<SpriteRenderer>();

        // ─── Unity Lifecycle ──────────────────────────────────────────────────────
        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
        }

        private void Update()
        {
            if (!_isPlacing) return;
            UpdateGhostPosition();
            HandlePlacementInput();
        }

        // ─── Public API ───────────────────────────────────────────────────────────

        /// <summary>
        /// Begins placement mode for the given building type in the specified district.
        /// Shows the ghost preview and highlights available slots.
        /// </summary>
        public void BeginPlacement(BuildingData data, string districtId)
        {
            if (data == null || data.Prefab == null) return;
            CancelPlacement();

            _pendingData     = data;
            _targetDistrictId = districtId;
            _isPlacing       = true;

            // Spawn ghost
            _ghostInstance = Instantiate(data.Prefab);
            SetGhostAlpha(_ghostInstance, ghostAlpha);
            _ghostInstance.layer = LayerMask.NameToLayer("Ignore Raycast");

            HighlightAvailableSlots(true);
        }

        /// <summary>Cancels an in-progress placement without placing the building.</summary>
        public void CancelPlacement()
        {
            if (_ghostInstance != null) Destroy(_ghostInstance);
            _isPlacing   = false;
            _pendingData = null;
            HighlightAvailableSlots(false);
        }

        /// <summary>Registers a slot position as occupied (called after placement).</summary>
        public void RegisterOccupied(Vector2Int gridPos) => _occupiedSlots.Add(gridPos);

        /// <summary>Frees a slot position (called when a building is removed).</summary>
        public void UnregisterOccupied(Vector2Int gridPos) => _occupiedSlots.Remove(gridPos);

        // ─── Placement Logic ──────────────────────────────────────────────────────

        private void UpdateGhostPosition()
        {
            if (_ghostInstance == null) return;

            Vector3 worldPos = GetPointerWorldPosition();
            Vector2Int gridPos = WorldToGrid(worldPos);
            Vector3 snapped = GridToWorld(gridPos);
            snapped.z = 0f;
            _ghostInstance.transform.position = snapped;
        }

        private void HandlePlacementInput()
        {
            bool tapped = false;
            Vector3 tapWorld = Vector3.zero;

#if UNITY_EDITOR || UNITY_STANDALONE
            if (Input.GetMouseButtonDown(0) && !EventSystem.current.IsPointerOverGameObject())
            {
                tapped = true;
                tapWorld = Camera.main.ScreenToWorldPoint(Input.mousePosition);
            }
            if (Input.GetMouseButtonDown(1))
            {
                CancelPlacement();
                return;
            }
#else
            if (Input.touchCount == 1)
            {
                Touch t = Input.GetTouch(0);
                if (t.phase == TouchPhase.Ended && !EventSystem.current.IsPointerOverGameObject(t.fingerId))
                {
                    tapped = true;
                    tapWorld = Camera.main.ScreenToWorldPoint(t.position);
                }
            }
#endif

            if (!tapped) return;

            Vector2Int gridPos = WorldToGrid(tapWorld);
            TryPlace(gridPos);
        }

        private void TryPlace(Vector2Int gridPos)
        {
            if (_pendingData == null) return;

            // Validate: slot must be free
            if (_occupiedSlots.Contains(gridPos))
            {
                UIManager.Instance?.ShowToast("Ce slot est déjà occupé !", "error");
                return;
            }

            // Validate: enough money
            if (!EconomyManager.Instance.TrySpend(_pendingData.BaseCost))
            {
                UIManager.Instance?.ShowToast("Pas assez d'argent !", "error");
                CancelPlacement();
                return;
            }

            // Validate: district match
            if (!_pendingData.IsAllowedInDistrict(_targetDistrictId))
            {
                UIManager.Instance?.ShowToast("Ce bâtiment n'est pas disponible ici !", "error");
                EconomyManager.Instance.Earn(_pendingData.BaseCost); // refund
                CancelPlacement();
                return;
            }

            // Place
            Vector3 worldPos = GridToWorld(gridPos);
            worldPos.z = 0f;
            GameObject placed = Instantiate(_pendingData.Prefab, worldPos, Quaternion.identity);
            BuildingBase building = placed.GetComponent<BuildingBase>();
            if (building != null)
            {
                building.Initialise(_pendingData, _targetDistrictId);
                building.OnPlace();
            }

            _occupiedSlots.Add(gridPos);
            MissionManager.Instance?.TrackProgress(MissionType.Build, 1);

            CameraController cam = Camera.main?.GetComponent<CameraController>();
            cam?.Shake(0.25f, 0.15f);

            UIManager.Instance?.ShowToast($"✅ {_pendingData.BuildingName} construit !", "success");
            FinishPlacement();
        }

        private void FinishPlacement()
        {
            if (_ghostInstance != null) Destroy(_ghostInstance);
            _isPlacing   = false;
            _pendingData = null;
            HighlightAvailableSlots(false);
        }

        // ─── Helpers ─────────────────────────────────────────────────────────────

        private Vector3 GetPointerWorldPosition()
        {
            Vector3 screenPos;
#if UNITY_EDITOR || UNITY_STANDALONE
            screenPos = Input.mousePosition;
#else
            screenPos = Input.touchCount > 0 ? (Vector3)Input.GetTouch(0).position : Vector3.zero;
#endif
            screenPos.z = Mathf.Abs(Camera.main.transform.position.z);
            return Camera.main.ScreenToWorldPoint(screenPos);
        }

        /// <summary>Converts a world position to the nearest grid cell.</summary>
        private Vector2Int WorldToGrid(Vector3 world)
        {
            int x = Mathf.RoundToInt(world.x / cellSize.x);
            int y = Mathf.RoundToInt(world.y / cellSize.y);
            return new Vector2Int(x, y);
        }

        /// <summary>Converts a grid cell to world-space centre.</summary>
        private Vector3 GridToWorld(Vector2Int grid)
        {
            return new Vector3(grid.x * cellSize.x, grid.y * cellSize.y, 0f);
        }

        private void SetGhostAlpha(GameObject go, float alpha)
        {
            foreach (var renderer in go.GetComponentsInChildren<Renderer>())
            {
                if (ghostMaterial != null)
                {
                    Material mat = new Material(ghostMaterial);
                    Color c = mat.color;
                    c.a = alpha;
                    mat.color = c;
                    renderer.material = mat;
                }
                else
                {
                    foreach (var mat in renderer.materials)
                    {
                        Color c = mat.color;
                        c.a = alpha;
                        mat.color = c;
                    }
                }
            }
        }

        private void HighlightAvailableSlots(bool highlight)
        {
            foreach (var sr in _slotRenderers)
            {
                if (sr == null) continue;
                sr.color = highlight
                    ? (_occupiedSlots.Contains(WorldToGrid(sr.transform.position)) ? invalidSlotColor : validSlotColor)
                    : Color.clear;
            }
        }

        /// <summary>Registers a slot sprite renderer so this placer can highlight it.</summary>
        public void RegisterSlotRenderer(SpriteRenderer sr)
        {
            if (!_slotRenderers.Contains(sr)) _slotRenderers.Add(sr);
        }

#if UNITY_EDITOR
        private void OnDrawGizmos()
        {
            Gizmos.color = new Color(0.2f, 0.8f, 1f, 0.15f);
            for (int x = -10; x <= 10; x++)
            for (int y = -10; y <= 10; y++)
            {
                Vector3 pos = GridToWorld(new Vector2Int(x, y));
                Gizmos.DrawWireCube(pos, new Vector3(cellSize.x * 0.95f, cellSize.y * 0.95f, 0f));
            }
        }
#endif
    }
}
