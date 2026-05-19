using UnityEngine;
using UnityEngine.Audio;
using System.Collections;
using System.Collections.Generic;

namespace BLOCKSIDE.Core
{
    /// <summary>
    /// Centralized audio manager. Handles background music with crossfade,
    /// SFX playback, volume mixing, and persistence of audio settings.
    /// </summary>
    public class AudioManager : MonoBehaviour
    {
        #region Inspector
        [Header("Mixer")]
        [SerializeField] private AudioMixer masterMixer;

        [Header("Music Sources")]
        [SerializeField] private AudioSource musicSourceA;
        [SerializeField] private AudioSource musicSourceB;

        [Header("SFX Pool")]
        [SerializeField] private int sfxPoolSize = 8;
        [SerializeField] private AudioSource sfxSourcePrefab;

        [Header("Music Clips")]
        [SerializeField] private AudioClip hubMusic;
        [SerializeField] private AudioClip cityMusic;
        [SerializeField] private AudioClip districtMusic;
        [SerializeField] private AudioClip marketMusic;
        [SerializeField] private AudioClip crewMusic;

        [Header("SFX Clips")]
        [SerializeField] private AudioClip clickSfx;
        [SerializeField] private AudioClip buildSfx;
        [SerializeField] private AudioClip collectSfx;
        [SerializeField] private AudioClip upgradeSfx;
        [SerializeField] private AudioClip unlockSfx;
        [SerializeField] private AudioClip buySfx;
        [SerializeField] private AudioClip errorSfx;
        [SerializeField] private AudioClip notifSfx;

        [Header("Settings")]
        [SerializeField] private float defaultMusicVolume = 0.6f;
        [SerializeField] private float defaultSfxVolume = 0.9f;
        [SerializeField] private float crossfadeDuration = 1.5f;
        #endregion

        #region Private State
        private List<AudioSource> sfxPool = new List<AudioSource>();
        private AudioSource activeMusicSource;
        private AudioSource inactiveMusicSource;
        private Coroutine crossfadeCoroutine;
        private float musicVolume;
        private float sfxVolume;
        private bool musicEnabled = true;
        private bool sfxEnabled = true;
        private const string MUSIC_VOL_KEY = "blockside_musicVol";
        private const string SFX_VOL_KEY = "blockside_sfxVol";
        private const string MUSIC_ON_KEY = "blockside_musicOn";
        private const string SFX_ON_KEY = "blockside_sfxOn";
        #endregion

        #region Unity Lifecycle
        private void Awake()
        {
            LoadAudioSettings();
            SetupSources();
            BuildSfxPool();
        }
        #endregion

        #region Setup
        private void SetupSources()
        {
            if (!musicSourceA)
            {
                musicSourceA = gameObject.AddComponent<AudioSource>();
                musicSourceA.loop = true;
                musicSourceA.playOnAwake = false;
            }
            if (!musicSourceB)
            {
                musicSourceB = gameObject.AddComponent<AudioSource>();
                musicSourceB.loop = true;
                musicSourceB.playOnAwake = false;
            }
            activeMusicSource = musicSourceA;
            inactiveMusicSource = musicSourceB;
            ApplyVolumeSettings();
        }

        private void BuildSfxPool()
        {
            for (int i = 0; i < sfxPoolSize; i++)
            {
                AudioSource source = sfxSourcePrefab
                    ? Instantiate(sfxSourcePrefab, transform)
                    : gameObject.AddComponent<AudioSource>();
                source.playOnAwake = false;
                sfxPool.Add(source);
            }
        }
        #endregion

        #region Music
        /// <summary>Plays music with crossfade. Skips if same clip already playing.</summary>
        public void PlayMusic(AudioClip clip, bool forceRestart = false)
        {
            if (clip == null || !musicEnabled) return;
            if (!forceRestart && activeMusicSource.clip == clip && activeMusicSource.isPlaying) return;
            if (crossfadeCoroutine != null) StopCoroutine(crossfadeCoroutine);
            crossfadeCoroutine = StartCoroutine(CrossfadeMusic(clip));
        }

        private IEnumerator CrossfadeMusic(AudioClip newClip)
        {
            inactiveMusicSource.clip = newClip;
            inactiveMusicSource.volume = 0f;
            inactiveMusicSource.Play();
            float elapsed = 0f;
            float startVol = activeMusicSource.volume;
            while (elapsed < crossfadeDuration)
            {
                elapsed += Time.deltaTime;
                float t = elapsed / crossfadeDuration;
                activeMusicSource.volume = Mathf.Lerp(startVol, 0f, t);
                inactiveMusicSource.volume = Mathf.Lerp(0f, musicVolume, t);
                yield return null;
            }
            activeMusicSource.Stop();
            activeMusicSource.volume = musicVolume;
            // Swap sources
            (activeMusicSource, inactiveMusicSource) = (inactiveMusicSource, activeMusicSource);
        }

        public void StopMusic(bool fade = true)
        {
            if (fade) StartCoroutine(FadeOutMusic());
            else activeMusicSource.Stop();
        }

        private IEnumerator FadeOutMusic()
        {
            float start = activeMusicSource.volume;
            float elapsed = 0f;
            while (elapsed < crossfadeDuration)
            {
                elapsed += Time.deltaTime;
                activeMusicSource.volume = Mathf.Lerp(start, 0f, elapsed / crossfadeDuration);
                yield return null;
            }
            activeMusicSource.Stop();
            activeMusicSource.volume = musicVolume;
        }

        /// <summary>Selects and plays music appropriate for the current game state.</summary>
        public void PlayMusicForState(GameManager.GameState state)
        {
            AudioClip clip = state switch
            {
                GameManager.GameState.Hub => hubMusic,
                GameManager.GameState.City => cityMusic,
                GameManager.GameState.District => districtMusic,
                GameManager.GameState.Market => marketMusic,
                GameManager.GameState.Crew => crewMusic,
                _ => hubMusic
            };
            PlayMusic(clip);
        }
        #endregion

        #region SFX
        private AudioSource GetAvailableSfxSource()
        {
            foreach (var src in sfxPool)
                if (!src.isPlaying) return src;
            return sfxPool[0]; // reuse oldest
        }

        private void PlaySfx(AudioClip clip)
        {
            if (clip == null || !sfxEnabled) return;
            AudioSource src = GetAvailableSfxSource();
            src.clip = clip;
            src.volume = sfxVolume;
            src.pitch = UnityEngine.Random.Range(0.95f, 1.05f);
            src.Play();
        }

        public void PlayClick() => PlaySfx(clickSfx);
        public void PlayBuild() => PlaySfx(buildSfx);
        public void PlayCollect() => PlaySfx(collectSfx);
        public void PlayUpgrade() => PlaySfx(upgradeSfx);
        public void PlayUnlock() => PlaySfx(unlockSfx);
        public void PlayBuy() => PlaySfx(buySfx);
        public void PlayError() => PlaySfx(errorSfx);
        public void PlayNotif() => PlaySfx(notifSfx);
        #endregion

        #region Volume Control
        public void SetMusicVolume(float volume)
        {
            musicVolume = Mathf.Clamp01(volume);
            activeMusicSource.volume = musicVolume;
            if (masterMixer) masterMixer.SetFloat("MusicVolume", Mathf.Log10(Mathf.Max(musicVolume, 0.0001f)) * 20f);
            PlayerPrefs.SetFloat(MUSIC_VOL_KEY, musicVolume);
            PlayerPrefs.Save();
        }

        public void SetSfxVolume(float volume)
        {
            sfxVolume = Mathf.Clamp01(volume);
            if (masterMixer) masterMixer.SetFloat("SFXVolume", Mathf.Log10(Mathf.Max(sfxVolume, 0.0001f)) * 20f);
            PlayerPrefs.SetFloat(SFX_VOL_KEY, sfxVolume);
            PlayerPrefs.Save();
        }

        public void SetMusicEnabled(bool enabled)
        {
            musicEnabled = enabled;
            if (!enabled) StopMusic();
            PlayerPrefs.SetInt(MUSIC_ON_KEY, enabled ? 1 : 0);
            PlayerPrefs.Save();
        }

        public void SetSfxEnabled(bool enabled)
        {
            sfxEnabled = enabled;
            PlayerPrefs.SetInt(SFX_ON_KEY, enabled ? 1 : 0);
            PlayerPrefs.Save();
        }

        private void LoadAudioSettings()
        {
            musicVolume = PlayerPrefs.GetFloat(MUSIC_VOL_KEY, defaultMusicVolume);
            sfxVolume = PlayerPrefs.GetFloat(SFX_VOL_KEY, defaultSfxVolume);
            musicEnabled = PlayerPrefs.GetInt(MUSIC_ON_KEY, 1) == 1;
            sfxEnabled = PlayerPrefs.GetInt(SFX_ON_KEY, 1) == 1;
        }

        private void ApplyVolumeSettings()
        {
            musicSourceA.volume = musicEnabled ? musicVolume : 0f;
            musicSourceB.volume = 0f;
        }

        public float MusicVolume => musicVolume;
        public float SfxVolume => sfxVolume;
        public bool MusicEnabled => musicEnabled;
        public bool SfxEnabled => sfxEnabled;
        #endregion
    }
}
