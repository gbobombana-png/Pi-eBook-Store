using UnityEngine;
using System.Collections.Generic;

namespace BLOCKSIDE.Player
{
    /// <summary>
    /// ScriptableObject that holds a character's static definition data.
    /// Create via Assets > Create > BLOCKSIDE > PlayerData.
    /// </summary>
    [CreateAssetMenu(menuName = "BLOCKSIDE/PlayerData", fileName = "PlayerData_New")]
    public class PlayerData : ScriptableObject
    {
        [Header("Identity")]
        [SerializeField] public string characterId;
        [SerializeField] public string displayName;
        [SerializeField] public string jerseyNumber;
        [SerializeField] public string role;
        [SerializeField] public string description;

        [Header("Visuals")]
        [SerializeField] public Color primaryColor = Color.white;
        [SerializeField] public Sprite characterSprite;
        [SerializeField] public RuntimeAnimatorController animatorController;

        [Header("Bonus")]
        [SerializeField] public BonusType bonusType;
        [SerializeField] public float bonusValue = 1f;
        [SerializeField] public string bonusDescription;

        [Header("Stats — Runtime (not serialized to SO)")]
        [System.NonSerialized] public string username = "Player";
        [System.NonSerialized] public long money;
        [System.NonSerialized] public long totalEarned;
        [System.NonSerialized] public int reputation;
        [System.NonSerialized] public int totalBuildings;
        [System.NonSerialized] public int clickCount;
        [System.NonSerialized] public string crewId;
        [System.NonSerialized] public List<string> premiumOwned = new List<string>();
        [System.NonSerialized] public Dictionary<string, bool> achievements = new Dictionary<string, bool>();
        [System.NonSerialized] public List<string> activityLog = new List<string>();
    }

    public enum BonusType
    {
        None,
        IncomeMultiplier,      // ZAY +20%
        CostReduction,         // NOVA -15%
        DurabilityBonus,       // BRICK +30%
        BlackMarketDiscount,   // RAVEN -20%
        DangerZoneBonus        // KAYO +25%
    }
}
