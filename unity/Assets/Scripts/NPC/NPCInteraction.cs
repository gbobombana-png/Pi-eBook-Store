using System;
using System.Collections;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace BLOCKSIDE
{
    /// <summary>
    /// Attached to an NPC GameObject.
    /// Handles tap detection, opens the dialogue panel with a typewriter effect,
    /// presents choices, and integrates with MissionManager for NPC quests.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class NPCInteraction : MonoBehaviour, IPointerClickHandler
    {
        // ─── Inspector ────────────────────────────────────────────────────────────
        [Header("NPC Data")]
        [SerializeField] private NPCData npcData;

        [Header("UI References")]
        [SerializeField] private GameObject dialogPanel;
        [SerializeField] private Image portraitImage;
        [SerializeField] private Text npcNameText;
        [SerializeField] private Text dialogText;
        [SerializeField] private Button nextButton;
        [SerializeField] private Transform choicesContainer;
        [SerializeField] private Button choiceButtonPrefab;

        [Header("Typewriter")]
        [SerializeField] private float typewriterSpeed = 0.04f; // seconds per character

        // ─── Runtime State ────────────────────────────────────────────────────────
        private int _currentLineIndex;
        private Coroutine _typewriterCoroutine;
        private bool _isTyping;

        // ─── Unity Lifecycle ──────────────────────────────────────────────────────
        private void Awake()
        {
            if (dialogPanel != null) dialogPanel.SetActive(false);
            if (nextButton != null)  nextButton.onClick.AddListener(OnNextClicked);
        }

        // ─── IPointerClickHandler ────────────────────────────────────────────────

        /// <summary>Opens the dialogue panel when the NPC is tapped.</summary>
        public void OnPointerClick(PointerEventData eventData)
        {
            OpenDialog();
        }

        // ─── Dialogue Flow ────────────────────────────────────────────────────────

        /// <summary>Opens the NPC dialogue panel and starts the first line.</summary>
        public void OpenDialog()
        {
            if (npcData == null || dialogPanel == null) return;

            _currentLineIndex = 0;
            dialogPanel.SetActive(true);

            if (portraitImage != null && npcData.Portrait != null)
                portraitImage.sprite = npcData.Portrait;

            if (npcNameText != null)
                npcNameText.text = npcData.NpcName;

            // Track visit for missions
            MissionManager.Instance?.TrackProgress(MissionType.Visit, 1);

            ShowLine(_currentLineIndex);
        }

        /// <summary>Closes the dialogue panel.</summary>
        public void CloseDialog()
        {
            if (_typewriterCoroutine != null) StopCoroutine(_typewriterCoroutine);
            if (dialogPanel != null) dialogPanel.SetActive(false);
            ClearChoices();
        }

        private void OnNextClicked()
        {
            if (_isTyping)
            {
                // Skip to end of current line
                if (_typewriterCoroutine != null) StopCoroutine(_typewriterCoroutine);
                _isTyping = false;
                if (npcData.DialogLines != null && _currentLineIndex < npcData.DialogLines.Length)
                    dialogText.text = npcData.DialogLines[_currentLineIndex];
                return;
            }

            _currentLineIndex++;
            if (npcData.DialogLines == null || _currentLineIndex >= npcData.DialogLines.Length)
            {
                // End of dialogue — show choices or close
                ShowEndChoices();
                return;
            }
            ShowLine(_currentLineIndex);
        }

        private void ShowLine(int index)
        {
            if (npcData.DialogLines == null || index >= npcData.DialogLines.Length) return;
            ClearChoices();
            if (_typewriterCoroutine != null) StopCoroutine(_typewriterCoroutine);
            _typewriterCoroutine = StartCoroutine(TypewriterRoutine(npcData.DialogLines[index]));
        }

        private IEnumerator TypewriterRoutine(string line)
        {
            _isTyping = true;
            if (dialogText != null) dialogText.text = "";
            foreach (char c in line)
            {
                if (dialogText != null) dialogText.text += c;
                yield return new WaitForSeconds(typewriterSpeed);
            }
            _isTyping = false;
        }

        private void ShowEndChoices()
        {
            ClearChoices();
            if (nextButton != null) nextButton.gameObject.SetActive(false);

            // Always show Close
            AddChoice("Fermer", CloseDialog);

            // NPC-type-specific choices
            if (npcData.NpcType == NPCType.Merchant && npcData.ShopItems != null && npcData.ShopItems.Length > 0)
            {
                foreach (var item in npcData.ShopItems)
                {
                    string captured = item.itemId;
                    int capturedCost = item.cost;
                    string capturedLabel = item.label;
                    AddChoice($"Acheter {capturedLabel} (${capturedCost})", () => BuyShopItem(captured, capturedCost));
                }
            }

            if (npcData.NpcType == NPCType.QuestGiver && npcData.QuestIds != null)
            {
                AddChoice("Voir les quêtes", () => UIManager.Instance?.OpenMissions());
            }

            if (npcData.NpcType == NPCType.TutorialGuide)
            {
                AddChoice("Revoir le tutoriel", () =>
                {
                    CloseDialog();
                    UIManager.Instance?.StartTutorial(true);
                });
            }
        }

        private void AddChoice(string label, Action onClick)
        {
            if (choicesContainer == null || choiceButtonPrefab == null) return;
            Button btn = Instantiate(choiceButtonPrefab, choicesContainer);
            Text btnText = btn.GetComponentInChildren<Text>();
            if (btnText != null) btnText.text = label;
            btn.onClick.AddListener(() => onClick?.Invoke());
        }

        private void ClearChoices()
        {
            if (nextButton != null) nextButton.gameObject.SetActive(true);
            if (choicesContainer == null) return;
            foreach (Transform child in choicesContainer)
                Destroy(child.gameObject);
        }

        private void BuyShopItem(string itemId, int cost)
        {
            if (!EconomyManager.Instance.TrySpend(cost))
            {
                UIManager.Instance?.ShowToast("Pas assez d'argent !", "error");
                return;
            }
            // Grant item via appropriate manager
            UIManager.Instance?.ShowToast($"✅ {itemId} acheté !", "success");
            CloseDialog();
        }
    }
}
