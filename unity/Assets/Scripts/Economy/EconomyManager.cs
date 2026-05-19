using UnityEngine;
using System;
using System.Collections.Generic;

namespace BLOCKSIDE.Economy
{
    /// <summary>
    /// Manages the player's currency, transactions, and income events.
    /// All money operations funnel through this class for consistent tracking.
    /// </summary>
    public class EconomyManager : MonoBehaviour
    {
        #region Inspector
        [Header("Starting Values")]
        [SerializeField] private long startingMoney = 500;

        [Header("VIP Multiplier")]
        [SerializeField] private float vipMultiplier = 2f;
        #endregion

        #region State
        private long money;
        private long totalEarned;
        private bool vipActive;
        private List<string> transactionLog = new List<string>();
        #endregion

        #region Events
        public static event Action<long, long> OnMoneyChanged;   // (newAmount, delta)
        public static event Action<long> OnIncomeCollected;       // (amount)
        public static event Action OnInsufficientFunds;
        #endregion

        #region Properties
        public long Money => money;
        public long TotalEarned => totalEarned;
        public bool VipActive => vipActive;
        public float IncomeMultiplier => vipActive ? vipMultiplier : 1f;
        #endregion

        #region Init
        public void LoadData(long savedMoney, long savedTotalEarned)
        {
            money = savedMoney;
            totalEarned = savedTotalEarned;
            Debug.Log($"[EconomyManager] Loaded: money={money}, totalEarned={totalEarned}");
        }

        public void Reset(long initialMoney = 500)
        {
            money = initialMoney;
            totalEarned = 0;
            vipActive = false;
            transactionLog.Clear();
        }
        #endregion

        #region Transactions
        /// <summary>Awards money to the player. Returns true always.</summary>
        public bool Earn(long amount, string reason = "")
        {
            if (amount <= 0) return false;
            money += amount;
            totalEarned += amount;
            LogTransaction("+", amount, reason);
            OnMoneyChanged?.Invoke(money, amount);
            OnIncomeCollected?.Invoke(amount);
            return true;
        }

        /// <summary>Spends money. Returns false and fires event if insufficient.</summary>
        public bool Spend(long amount, string reason = "")
        {
            if (amount <= 0) return false;
            if (money < amount)
            {
                OnInsufficientFunds?.Invoke();
                return false;
            }
            money -= amount;
            LogTransaction("-", amount, reason);
            OnMoneyChanged?.Invoke(money, -amount);
            return true;
        }

        /// <summary>Checks affordability without spending.</summary>
        public bool CanAfford(long amount) => money >= amount;

        /// <summary>Applies character-specific and VIP income multipliers to a raw value.</summary>
        public long ApplyMultipliers(long rawIncome, string characterId)
        {
            float mult = 1f;
            if (vipActive) mult *= vipMultiplier;
            if (characterId == "zay") mult *= 1.2f;
            return (long)(rawIncome * mult);
        }

        public void ActivateVIP()
        {
            vipActive = true;
            Debug.Log("[EconomyManager] VIP activated — income x2");
        }
        #endregion

        #region Transaction Log
        private void LogTransaction(string sign, long amount, string reason)
        {
            string entry = $"[{DateTime.Now:HH:mm}] {sign}{FormatMoney(amount)} — {reason}";
            transactionLog.Insert(0, entry);
            if (transactionLog.Count > 50) transactionLog.RemoveAt(transactionLog.Count - 1);
        }

        public List<string> GetTransactionLog() => new List<string>(transactionLog);

        public static string FormatMoney(long amount)
        {
            if (amount >= 1_000_000) return $"{amount / 1_000_000f:F1}M";
            if (amount >= 1_000) return $"{amount / 1_000f:F1}K";
            return amount.ToString();
        }
        #endregion
    }
}
