using UnityEngine;

namespace BLOCKSIDE
{
    /// <summary>The functional role of an NPC in the game world.</summary>
    public enum NPCType
    {
        TutorialGuide,
        Merchant,
        QuestGiver,
        BlackMarket,
        Prestige
    }

    [Serializable]
    public struct ShopItem
    {
        public string itemId;
        public string label;
        public int cost;
    }

    /// <summary>
    /// ScriptableObject containing all static data for an NPC.
    /// Create via Assets > Create > BLOCKSIDE > NPCData.
    /// </summary>
    [CreateAssetMenu(fileName = "NPCData", menuName = "BLOCKSIDE/NPCData", order = 2)]
    public class NPCData : ScriptableObject
    {
        // ─── Inspector ────────────────────────────────────────────────────────────
        [Header("Identity")]
        [SerializeField] private string id;
        [SerializeField] private string npcName;
        [SerializeField] private NPCType npcType;
        [SerializeField] private Sprite portrait;

        [Header("Dialogue")]
        [SerializeField, TextArea(2, 6)] private string[] dialogLines;

        [Header("Shop")]
        [SerializeField] private ShopItem[] shopItems;

        [Header("Quests")]
        [SerializeField] private string[] questIds;

        // ─── Properties ──────────────────────────────────────────────────────────
        public string Id         => id;
        public string NpcName    => npcName;
        public NPCType NpcType   => npcType;
        public Sprite Portrait   => portrait;
        public string[] DialogLines => dialogLines;
        public ShopItem[] ShopItems => shopItems;
        public string[] QuestIds    => questIds;

        // ─── Built-in NPC Templates ───────────────────────────────────────────────
        // These are reference names; actual ScriptableObjects should be created in the editor.
        // Street Guide  → TutorialGuide   | LOWSIDE
        // Market Queen  → Merchant        | NEON MARKET
        // Shadow Dealer → BlackMarket     | UNDERBLOCK
        // Sky King      → Prestige        | SKY DISTRICT
    }
}
