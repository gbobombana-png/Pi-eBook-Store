using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections;

namespace BLOCKSIDE.UI
{
    /// <summary>
    /// Manages animated toast notifications that slide in from the top.
    /// </summary>
    public class ToastController : MonoBehaviour
    {
        #region Inspector
        [SerializeField] private CanvasGroup canvasGroup;
        [SerializeField] private RectTransform toastRect;
        [SerializeField] private TextMeshProUGUI messageText;
        [SerializeField] private Image backgroundImage;

        [Header("Colors")]
        [SerializeField] private Color infoColor    = new Color(.18f,.61f,1f);
        [SerializeField] private Color successColor = new Color(.29f,.87f,.5f);
        [SerializeField] private Color errorColor   = new Color(1f,.18f,.47f);
        [SerializeField] private Color warningColor = new Color(1f,.84f,0f);

        [Header("Animation")]
        [SerializeField] private float slideInDuration  = 0.3f;
        [SerializeField] private float holdDuration     = 2.5f;
        [SerializeField] private float slideOutDuration = 0.25f;
        [SerializeField] private float offscreenY       = 120f;
        #endregion

        private Coroutine currentToast;

        private void Awake()
        {
            if (canvasGroup) { canvasGroup.alpha = 0f; canvasGroup.interactable = false; }
        }

        public void Show(string message, ToastType type = ToastType.Info, float duration = -1f)
        {
            if (currentToast != null) StopCoroutine(currentToast);
            currentToast = StartCoroutine(AnimateToast(message, type, duration > 0 ? duration : holdDuration));
        }

        private IEnumerator AnimateToast(string message, ToastType type, float duration)
        {
            if (!messageText || !toastRect || !canvasGroup) yield break;

            messageText.text = message;
            if (backgroundImage)
            {
                backgroundImage.color = type switch
                {
                    ToastType.Success => successColor,
                    ToastType.Error   => errorColor,
                    ToastType.Warning => warningColor,
                    _                 => infoColor
                };
            }

            Vector2 onscreen  = new Vector2(toastRect.anchoredPosition.x, -20f);
            Vector2 offscreen = new Vector2(toastRect.anchoredPosition.x, offscreenY);

            // Slide in
            float t = 0f;
            while (t < slideInDuration)
            {
                t += Time.deltaTime;
                float p = Mathf.SmoothStep(0f, 1f, t / slideInDuration);
                toastRect.anchoredPosition = Vector2.Lerp(offscreen, onscreen, p);
                canvasGroup.alpha = p;
                yield return null;
            }
            toastRect.anchoredPosition = onscreen;
            canvasGroup.alpha = 1f;

            yield return new WaitForSeconds(duration);

            // Slide out
            t = 0f;
            while (t < slideOutDuration)
            {
                t += Time.deltaTime;
                float p = Mathf.SmoothStep(0f, 1f, t / slideOutDuration);
                toastRect.anchoredPosition = Vector2.Lerp(onscreen, offscreen, p);
                canvasGroup.alpha = 1f - p;
                yield return null;
            }
            canvasGroup.alpha = 0f;
            toastRect.anchoredPosition = offscreen;
        }
    }
}
