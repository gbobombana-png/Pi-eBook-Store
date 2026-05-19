using System;
using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace Blockside.Bootstrap
{
    /// <summary>
    /// Chargement de scènes avec écran de transition et barre de progression.
    /// Appeler SceneLoader.Load("NomScene") depuis n'importe quel script.
    /// </summary>
    public class SceneLoader : MonoBehaviour
    {
        public static SceneLoader Instance { get; private set; }

        [Header("UI Transition")]
        [SerializeField] private CanvasGroup fadeOverlay;
        [SerializeField] private Slider progressBar;
        [SerializeField] private float fadeDuration = 0.3f;

        public static bool IsLoading { get; private set; }

        void Awake()
        {
            if (Instance != null) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
            if (fadeOverlay) fadeOverlay.alpha = 0;
        }

        public static void Load(string sceneName, Action onComplete = null)
        {
            if (Instance == null)
            {
                SceneManager.LoadScene(sceneName);
                return;
            }
            Instance.StartCoroutine(Instance.LoadAsync(sceneName, onComplete));
        }

        IEnumerator LoadAsync(string sceneName, Action onComplete)
        {
            if (IsLoading) yield break;
            IsLoading = true;

            // Fondu au noir
            yield return Fade(0, 1);

            var op = SceneManager.LoadSceneAsync(sceneName);
            op.allowSceneActivation = false;
            while (op.progress < 0.9f)
            {
                if (progressBar) progressBar.value = op.progress / 0.9f;
                yield return null;
            }
            if (progressBar) progressBar.value = 1;
            yield return new WaitForSeconds(0.1f);

            op.allowSceneActivation = true;
            yield return new WaitUntil(() => op.isDone);

            onComplete?.Invoke();

            // Fondu depuis le noir
            yield return Fade(1, 0);
            IsLoading = false;
        }

        IEnumerator Fade(float from, float to)
        {
            if (fadeOverlay == null) yield break;
            float t = 0;
            while (t < fadeDuration)
            {
                t += Time.deltaTime;
                fadeOverlay.alpha = Mathf.Lerp(from, to, t / fadeDuration);
                yield return null;
            }
            fadeOverlay.alpha = to;
        }
    }
}
