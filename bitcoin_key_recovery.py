#!/usr/bin/env python3
"""
Bitcoin Key Recovery Tool — Wallets era 2010-2011

For recovering your own lost Bitcoin wallets.
Implements vulnerabilities known in early Bitcoin software.

Usage:
  python3 bitcoin_key_recovery.py <bitcoin_address>
  python3 bitcoin_key_recovery.py <bitcoin_address> <wordlist.txt>
  python3 bitcoin_key_recovery.py --pubkey <hex_pubkey>
"""

import hashlib
import struct
import sys
import os
import time
import argparse
from typing import Optional, Tuple, List, Iterator

# ── Fast backend: use coincurve (libsecp256k1) when available ─────────────────
try:
    import coincurve
    _HAVE_COINCURVE = True
except ImportError:
    _HAVE_COINCURVE = False

# ── secp256k1 curve parameters (used by pure-Python fallback) ─────────────────
P  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
G  = (Gx, Gy)


# ── Elliptic curve arithmetic (pure Python fallback) ─────────────────────────

def modinv(a: int, m: int) -> int:
    if a < 0:
        a = a % m
    lm, hm = 1, 0
    low, high = a % m, m
    while low > 1:
        ratio = high // low
        nm, new = hm - lm * ratio, high - low * ratio
        lm, low, hm, high = nm, new, lm, low
    return lm % m


def ec_add(P1: Optional[Tuple], P2: Optional[Tuple]) -> Optional[Tuple]:
    if P1 is None:
        return P2
    if P2 is None:
        return P1
    x1, y1 = P1
    x2, y2 = P2
    if x1 == x2:
        if y1 != y2:
            return None
        m = (3 * x1 * x1 * modinv(2 * y1, P)) % P
    else:
        m = ((y2 - y1) * modinv(x2 - x1, P)) % P
    x3 = (m * m - x1 - x2) % P
    y3 = (m * (x1 - x3) - y1) % P
    return (x3, y3)


def ec_mul(k: int, point: Tuple) -> Optional[Tuple]:
    result = None
    addend = point
    while k:
        if k & 1:
            result = ec_add(result, addend)
        addend = ec_add(addend, addend)
        k >>= 1
    return result


# ── Bitcoin encoding helpers ──────────────────────────────────────────────────

BASE58_CHARS = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
BASE58_MAP   = {c: i for i, c in enumerate(BASE58_CHARS)}


def base58_encode(data: bytes) -> str:
    n = int.from_bytes(data, 'big')
    result = ''
    while n > 0:
        n, rem = divmod(n, 58)
        result = BASE58_CHARS[rem] + result
    for byte in data:
        if byte == 0:
            result = '1' + result
        else:
            break
    return result


def base58check_encode(payload: bytes) -> str:
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    return base58_encode(payload + checksum)


def base58check_decode(s: str) -> Optional[bytes]:
    try:
        n = 0
        for char in s:
            n = n * 58 + BASE58_MAP[char]
        # Determine byte length from string length
        byte_len = (len(s) * 733) // 1000 + 1
        data = n.to_bytes(byte_len, 'big').lstrip(b'\x00')
        # Re-add leading zero bytes for '1' prefix chars
        leading = len(s) - len(s.lstrip('1'))
        data = b'\x00' * leading + data
        payload, checksum = data[:-4], data[-4:]
        computed = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
        if computed != checksum:
            return None
        return payload
    except Exception:
        return None


def ripemd160_sha256(data: bytes) -> bytes:
    sha = hashlib.sha256(data).digest()
    rmd = hashlib.new('ripemd160')
    rmd.update(sha)
    return rmd.digest()


def pubkey_to_address(pubkey_bytes: bytes) -> str:
    pub_hash = ripemd160_sha256(pubkey_bytes)
    return base58check_encode(b'\x00' + pub_hash)


if _HAVE_COINCURVE:
    def privkey_to_pubkey_uncompressed(k: int) -> bytes:
        key_bytes = k.to_bytes(32, 'big')
        pub = coincurve.PublicKey.from_secret(key_bytes)
        return pub.format(compressed=False)

    def privkey_to_pubkey_compressed(k: int) -> bytes:
        key_bytes = k.to_bytes(32, 'big')
        pub = coincurve.PublicKey.from_secret(key_bytes)
        return pub.format(compressed=True)
else:
    def privkey_to_pubkey_uncompressed(k: int) -> bytes:
        point = ec_mul(k, G)
        if point is None:
            raise ValueError("Invalid private key")
        x, y = point
        return b'\x04' + x.to_bytes(32, 'big') + y.to_bytes(32, 'big')

    def privkey_to_pubkey_compressed(k: int) -> bytes:
        point = ec_mul(k, G)
        if point is None:
            raise ValueError("Invalid private key")
        x, y = point
        prefix = b'\x02' if y % 2 == 0 else b'\x03'
        return prefix + x.to_bytes(32, 'big')


def privkey_to_all_addresses(k: int) -> List[str]:
    try:
        unc = privkey_to_pubkey_uncompressed(k)
        com = privkey_to_pubkey_compressed(k)
        return [pubkey_to_address(unc), pubkey_to_address(com)]
    except Exception:
        return []


def privkey_to_wif(k: int, compressed: bool = False) -> str:
    payload = b'\x80' + k.to_bytes(32, 'big')
    if compressed:
        payload += b'\x01'
    return base58check_encode(payload)


def wif_to_privkey(wif: str) -> Optional[Tuple[int, bool]]:
    payload = base58check_decode(wif)
    if payload is None or payload[0] != 0x80:
        return None
    compressed = len(payload) == 34 and payload[-1] == 0x01
    k = int.from_bytes(payload[1:33], 'big')
    return (k, compressed)


def pubkey_hex_to_address(hex_pubkey: str) -> Optional[str]:
    try:
        pub_bytes = bytes.fromhex(hex_pubkey.strip())
        return pubkey_to_address(pub_bytes)
    except Exception:
        return None


# ── Core checker ─────────────────────────────────────────────────────────────

class KeyFinder:
    def __init__(self, target_address: str):
        self.target = target_address
        self.checked = 0
        self.t0 = time.time()

    def check(self, k: int) -> bool:
        if k <= 0 or k >= N:
            return False
        self.checked += 1
        return self.target in privkey_to_all_addresses(k)

    def check_bytes(self, seed: bytes) -> Optional[int]:
        k = int.from_bytes(hashlib.sha256(seed).digest(), 'big')
        return k if self.check(k) else None

    def progress(self, label: str, current: int, total: int):
        elapsed = time.time() - self.t0
        rate = self.checked / elapsed if elapsed > 0 else 0
        pct = current / total * 100 if total > 0 else 0
        print(f"  [{label}] {pct:5.1f}% — {self.checked:,} testées — {rate:,.0f}/s", end='\r', flush=True)

    def report_found(self, strategy: str, privkey_int: int, extra: str = ""):
        print(f"\n\n{'='*60}")
        print(f"  *** CLÉ TROUVÉE — {strategy} ***")
        print(f"{'='*60}")
        if extra:
            print(f"  {extra}")
        print(f"  Clé privée (hex)    : {hex(privkey_int)}")
        print(f"  WIF (non-comprimé)  : {privkey_to_wif(privkey_int, False)}")
        print(f"  WIF (comprimé)      : {privkey_to_wif(privkey_int, True)}")
        addrs = privkey_to_all_addresses(privkey_int)
        for addr in addrs:
            marker = " ← CIBLE" if addr == self.target else ""
            print(f"  Adresse             : {addr}{marker}")
        print(f"{'='*60}")


# ── Strategy 1 — Brain wallet ─────────────────────────────────────────────────

def strategy_brain_wallet(finder: KeyFinder, passphrases: List[str]) -> Optional[int]:
    """SHA256(passphrase) → private key. Very common in 2010-2011."""
    print(f"\n[S1] Brain Wallet — {len(passphrases):,} passphrases...")
    total = len(passphrases)
    for i, phrase in enumerate(passphrases):
        if i % 500 == 0:
            finder.progress("BrainWallet", i, total)
        for encoding in ('utf-8', 'latin-1'):
            try:
                seed = phrase.encode(encoding)
            except Exception:
                continue
            # Single SHA256 (most common)
            k = int.from_bytes(hashlib.sha256(seed).digest(), 'big')
            if finder.check(k):
                finder.report_found("Brain Wallet", k, f"Passphrase : \"{phrase}\"")
                return k
            # Double SHA256 (used by some generators)
            k2 = int.from_bytes(hashlib.sha256(hashlib.sha256(seed).digest()).digest(), 'big')
            if finder.check(k2):
                finder.report_found("Brain Wallet (SHA256²)", k2, f"Passphrase : \"{phrase}\"")
                return k2
    print(f"\n  Aucune passphrase correspondante trouvée.")
    return None


# ── Strategy 2 — Timestamp seed ───────────────────────────────────────────────

def strategy_timestamp_seed(finder: KeyFinder,
                              start_ts: int = 1262304000,   # 2010-01-01 00:00:00 UTC
                              end_ts:   int = 1325376000,   # 2012-01-01 00:00:00 UTC
                              ) -> Optional[int]:
    """SHA256(packed_timestamp) — some early generators seeded from system time."""
    total = end_ts - start_ts
    print(f"\n[S2] Timestamp seed — {total:,} secondes (2010→2012)...")
    print(f"     Cela peut prendre ~{total // 50000 // 60 + 1} minutes")

    for i, ts in enumerate(range(start_ts, end_ts)):
        if i % 200_000 == 0:
            finder.progress("Timestamp", i, total)

        for pack_fmt in ('>I', '<I', '>Q', '<Q'):
            try:
                seed = struct.pack(pack_fmt, ts)
            except struct.error:
                continue
            k = finder.check_bytes(seed)
            if k:
                import datetime
                dt = datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S UTC')
                finder.report_found("Timestamp seed", k, f"Timestamp  : {ts} ({dt})  Format: {pack_fmt}")
                return k

        # Also try raw decimal string representation
        seed_str = str(ts).encode()
        k = finder.check_bytes(seed_str)
        if k:
            finder.report_found("Timestamp seed (string)", k, f"Timestamp  : {ts}")
            return k

    print(f"\n  Aucun timestamp correspondant trouvé.")
    return None


# ── Strategy 3 — Small / sequential private keys ──────────────────────────────

def strategy_small_keys(finder: KeyFinder, max_key: int = 1_000_000) -> Optional[int]:
    """Keys 1..max_key — some early test wallets used trivially small keys."""
    print(f"\n[S3] Clés séquentielles — 1 à {max_key:,}...")
    for k in range(1, max_key + 1):
        if k % 50_000 == 0:
            finder.progress("SmallKey", k, max_key)
        if finder.check(k):
            finder.report_found("Clé séquentielle", k, f"Valeur     : {k}")
            return k
    print(f"\n  Aucune clé séquentielle correspondante trouvée.")
    return None


# ── Strategy 4 — WIF list ────────────────────────────────────────────────────

def strategy_wif_list(finder: KeyFinder, wif_list: List[str]) -> Optional[int]:
    """Try a list of WIF-formatted private key candidates."""
    print(f"\n[S4] WIF candidates — {len(wif_list):,} clés...")
    for wif in wif_list:
        result = wif_to_privkey(wif.strip())
        if result:
            k, compressed = result
            if finder.check(k):
                finder.report_found("WIF candidate", k, f"WIF        : {wif.strip()}")
                return k
    print(f"  Aucun WIF correspondant trouvé.")
    return None


# ── Strategy 5 — Hex key list ─────────────────────────────────────────────────

def strategy_hex_list(finder: KeyFinder, hex_list: List[str]) -> Optional[int]:
    """Try raw hex private key candidates."""
    print(f"\n[S5] Hex key candidates — {len(hex_list):,} clés...")
    for h in hex_list:
        try:
            k = int(h.strip(), 16)
            if finder.check(k):
                finder.report_found("Hex candidate", k, f"Hex        : {h.strip()}")
                return k
        except ValueError:
            continue
    print(f"  Aucun hex correspondant trouvé.")
    return None


# ── Built-in passphrase corpus ────────────────────────────────────────────────

def default_passphrases() -> List[str]:
    """Common passphrases used in early brain wallets (2009-2012 era)."""
    basics = [
        # English common
        "password", "password1", "123456", "qwerty", "letmein", "master",
        "hello", "test", "admin", "root", "secret", "money", "hello world",
        # Bitcoin-specific
        "bitcoin", "satoshi", "nakamoto", "blockchain", "crypto",
        "satoshi nakamoto", "bitcoin is great", "i love bitcoin",
        "bitcoin2010", "bitcoin2011", "bitcoin2009", "mybitcoin", "mywallet",
        "bitcoin wallet", "my bitcoin wallet",
        # Famous early passphrases
        "correct horse battery staple",   # XKCD #936 — widely used
        "to be or not to be",
        "all your base are belong to us",
        "in cryptography we trust",
        "the times 03/jan/2009 chancellor on brink of second bailout for banks",
        "chancellor on brink of second bailout for banks",
        "03/jan/2009",
        "3 january 2009",
        # Common names + years
        "bitcoin2009", "bitcoin2010", "bitcoin2011", "bitcoin2012",
        # Technical
        "sha256", "elliptic", "secp256k1", "genesis",
        # Numbers-only (some generators)
        "1234567890", "0987654321", "11111111", "00000000",
        # French common (if user is French-speaking)
        "motdepasse", "bonjour", "argent", "monportefeuille",
        # Empty / trivial
        "",
        "a", "b", "c",
    ]

    # Add year variants
    years = ["2009", "2010", "2011", "2012"]
    base_words = ["bitcoin", "wallet", "crypto", "satoshi", "password"]
    for w in base_words:
        for y in years:
            basics.append(f"{w}{y}")
            basics.append(f"{y}{w}")
            basics.append(f"{w}_{y}")

    return list(dict.fromkeys(basics))  # deduplicate preserving order


# ── Wordlist / candidate file loader ─────────────────────────────────────────

def load_candidates(path: str) -> Tuple[List[str], List[str], List[str]]:
    """
    Load a file and auto-detect content type.
    Returns (passphrases, wif_candidates, hex_candidates).
    """
    passphrases, wif_list, hex_list = [], [], []
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('5') and len(line) == 51:
                    wif_list.append(line)   # WIF uncompressed
                elif line[0] in ('K', 'L') and len(line) == 52:
                    wif_list.append(line)   # WIF compressed
                elif len(line) == 64 and all(c in '0123456789abcdefABCDEF' for c in line):
                    hex_list.append(line)   # Raw 256-bit hex key
                else:
                    passphrases.append(line)
    except FileNotFoundError:
        print(f"[!] Fichier non trouvé : {path}")
    return passphrases, wif_list, hex_list


# ── Main ──────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Bitcoin Key Recovery — Wallets 2010-2011",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python3 bitcoin_key_recovery.py 1A1zP1eP5QGefi2DMPTfTL5SLmv7Divf
  python3 bitcoin_key_recovery.py 1A1zP1eP5QGefi2DMPTfTL5SLmv7Divf mes_passphrases.txt
  python3 bitcoin_key_recovery.py --pubkey 04a34b...

Fichier candidats (.txt) — une entrée par ligne:
  - Passphrase quelconque  → testée comme brain wallet
  - 64 chars hex           → testée comme clé privée brute
  - WIF (commence par 5/K/L) → testée directement
        """
    )
    p.add_argument('target', nargs='?', help="Adresse Bitcoin (1xxx…) ou clé publique hex")
    p.add_argument('candidates', nargs='?', help="Fichier de candidats (passphrases / WIF / hex)")
    p.add_argument('--pubkey', metavar='HEX', help="Clé publique en hex (04xx… ou 02/03xx…)")
    p.add_argument('--no-timestamp', action='store_true', help="Ignorer la stratégie timestamp (lente)")
    p.add_argument('--no-sequential', action='store_true', help="Ignorer les clés séquentielles")
    p.add_argument('--timestamp-start', type=int, default=1262304000, metavar='TS',
                   help="Timestamp début (défaut: 2010-01-01)")
    p.add_argument('--timestamp-end', type=int, default=1325376000, metavar='TS',
                   help="Timestamp fin (défaut: 2012-01-01)")
    p.add_argument('--max-sequential', type=int, default=1_000_000, metavar='N',
                   help="Clés séquentielles max (défaut: 1 000 000)")
    return p.parse_args()


def main():
    print("=" * 60)
    print("  Bitcoin Key Recovery Tool — Wallets 2010-2011")
    print("  Usage légal uniquement : récupération de vos propres fonds")
    print("=" * 60)

    args = parse_args()

    # Resolve target address
    target_address = None

    if args.pubkey:
        addr = pubkey_hex_to_address(args.pubkey)
        if addr is None:
            print("[!] Clé publique hex invalide")
            sys.exit(1)
        print(f"[+] Clé publique → adresse : {addr}")
        target_address = addr
    elif args.target:
        if args.target.startswith('1') and 25 <= len(args.target) <= 34:
            target_address = args.target
        elif len(args.target) >= 66 and all(c in '0123456789abcdefABCDEF' for c in args.target.lower()):
            addr = pubkey_hex_to_address(args.target)
            if addr:
                print(f"[+] Clé publique détectée → adresse : {addr}")
                target_address = addr
        if target_address is None:
            print("[!] Format non reconnu. Fournissez une adresse Bitcoin (1xxx…) ou une clé publique hex.")
            sys.exit(1)
    else:
        target_address = input("Adresse Bitcoin cible (1xxx…) : ").strip()
        if not target_address:
            print("[!] Adresse requise.")
            sys.exit(1)

    backend = "coincurve (libsecp256k1 — rapide)" if _HAVE_COINCURVE else "Python pur (lent — installez coincurve)"
    print(f"\n[*] Cible    : {target_address}")
    print(f"[*] Backend  : {backend}")
    print(f"[*] Démarrage: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    finder = KeyFinder(target_address)

    # Load external candidates
    ext_passphrases, ext_wif, ext_hex = [], [], []
    if args.candidates:
        ext_passphrases, ext_wif, ext_hex = load_candidates(args.candidates)
        print(f"[+] Candidats chargés : {len(ext_passphrases)} passphrases, "
              f"{len(ext_wif)} WIF, {len(ext_hex)} hex")

    # Merge passphrases
    all_passphrases = default_passphrases() + ext_passphrases

    # Run strategies in order (fastest first)
    strategies = [
        ("Brain wallet",     lambda: strategy_brain_wallet(finder, all_passphrases)),
    ]
    if ext_wif:
        strategies.append(("WIF list",     lambda: strategy_wif_list(finder, ext_wif)))
    if ext_hex:
        strategies.append(("Hex list",     lambda: strategy_hex_list(finder, ext_hex)))
    if not args.no_sequential:
        strategies.append(("Séquentielles", lambda: strategy_small_keys(finder, args.max_sequential)))
    if not args.no_timestamp:
        strategies.append(("Timestamp",    lambda: strategy_timestamp_seed(finder, args.timestamp_start, args.timestamp_end)))

    found = False
    for name, fn in strategies:
        result = fn()
        if result is not None:
            found = True
            break

    elapsed = time.time() - finder.t0
    print(f"\n[*] Fin : {finder.checked:,} clés testées en {elapsed:.1f}s "
          f"({finder.checked / elapsed:,.0f} clés/s)")

    if not found:
        print("\n[!] Clé non trouvée avec les stratégies automatiques.")
        print("\nPistes supplémentaires :")
        print("  1. Créez un fichier texte avec vos passphrases candidates")
        print("     (une par ligne) et relancez avec ce fichier en argument.")
        print("  2. Si vous avez le fichier wallet.dat mais oublié le mot")
        print("     de passe : utilisez bitcoin2john.py + hashcat/john.")
        print("  3. Si vous vous souvenez d'une partie de la passphrase,")
        print("     générez des variantes avec un script et fournissez-les.")
        print("  4. Pour une plage timestamp plus large :")
        print(f"     --timestamp-start 1230768000  (2009-01-01)")
        print(f"     --timestamp-end   1356998400  (2013-01-01)")
        sys.exit(1)


if __name__ == "__main__":
    main()
