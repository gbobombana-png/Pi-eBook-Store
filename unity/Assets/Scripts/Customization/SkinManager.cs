using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Events;

namespace Blockside.Customization
{
    [Serializable]
    public class CharacterSkin
    {
        public string id;
        public string displayName;
        public string emoji;
        public int piCost;
        public bool freeByDefault;
        public Color accentColor;
        [TextArea] public string description;
    }

    public class SkinManager : MonoBehaviour
    {
        public static SkinManager Instance { get; private set; }

        [Header("Available Skins")]
        public List<CharacterSkin> allSkins = new()
        {
            new CharacterSkin { id="default", displayName="Default",  emoji="😎", freeByDefault=true,  piCost=0, accentColor=Color.white },
            new CharacterSkin { id="neon",    displayName="Néon",     emoji="🌟", freeByDefault=false, piCost=2, accentColor=new Color(0f, 0.87f, 1f) },
            new CharacterSkin { id="void",    displayName="Void",     emoji="🌑", freeByDefault=false, piCost=2, accentColor=new Color(0.42f, 0.18f, 1f) },
            new CharacterSkin { id="gold",    displayName="Gold",     emoji="👑", freeByDefault=false, piCost=3, accentColor=new Color(1f, 0.84f, 0f) },
            new CharacterSkin { id="fire",    displayName="Inferno",  emoji="🔥", freeByDefault=false, piCost=3, accentColor=new Color(1f, 0.27f, 0f) },
            new CharacterSkin { id="ghost",   displayName="Ghost",    emoji="👻", freeByDefault=false, piCost=5, accentColor=new Color(0.8f, 0.8f, 1f) },
        };

        [Header("Events")]
        public UnityEvent<string> OnSkinActivated;
        public UnityEvent<string> OnSkinUnlocked;

        private HashSet<string> _ownedSkins = new();
        private string _activeSkinId = "default";

        public string ActiveSkinId => _activeSkinId;

        void Awake()
        {
            if (Instance != null) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }

        void Start()
        {
            LoadSkins();
        }

        void LoadSkins()
        {
            _activeSkinId = PlayerPrefs.GetString("active_skin", "default");
            string raw = PlayerPrefs.GetString("owned_skins", "default");
            _ownedSkins = new HashSet<string>(raw.Split(','));
            // Always own default
            _ownedSkins.Add("default");
            foreach (var s in allSkins) if (s.freeByDefault) _ownedSkins.Add(s.id);
        }

        void SaveSkins()
        {
            PlayerPrefs.SetString("active_skin", _activeSkinId);
            PlayerPrefs.SetString("owned_skins", string.Join(",", _ownedSkins));
            PlayerPrefs.Save();
        }

        public bool IsSkinOwned(string id) => _ownedSkins.Contains(id);

        public bool ActivateSkin(string id)
        {
            if (!IsSkinOwned(id))
            {
                Debug.LogWarning($"[Skins] Skin '{id}' not owned.");
                return false;
            }
            _activeSkinId = id;
            SaveSkins();
            OnSkinActivated?.Invoke(id);
            ApplySkinToPlayer(id);
            return true;
        }

        public void UnlockSkin(string id)
        {
            if (_ownedSkins.Add(id))
            {
                SaveSkins();
                OnSkinUnlocked?.Invoke(id);
                Debug.Log($"[Skins] Unlocked skin: {id}");
            }
        }

        public CharacterSkin GetSkin(string id) => allSkins.Find(s => s.id == id);
        public CharacterSkin GetActiveSkin() => GetSkin(_activeSkinId);
        public List<string> GetOwnedSkinIds() => new(_ownedSkins);

        void ApplySkinToPlayer(string skinId)
        {
            var skin = GetSkin(skinId);
            if (skin == null) return;
            // In a real scene, find the PlayerRenderer and swap materials/colors
            var playerObj = GameObject.FindWithTag("Player");
            if (playerObj == null) return;
            var renderers = playerObj.GetComponentsInChildren<Renderer>();
            foreach (var r in renderers)
                foreach (var mat in r.materials)
                    if (mat.HasProperty("_Color")) mat.color = skin.accentColor;
        }
    }
}
