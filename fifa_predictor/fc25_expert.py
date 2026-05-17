#!/usr/bin/env python3
"""
FC25 PENALTY EXPERT v4.0 — Modèle RNG-aware
Basé sur 240+ vrais matchs FC25 1xbet observés.

VÉRITÉ SUR FC25 1XBET:
- Résultats générés par RNG avec ratings d'équipes FIXES (côté serveur)
- Format: 5 tirs par équipe, mort subite si égalité 5:5
- Les cotes bookmaker = meilleur signal disponible (elles encodent les vraies proba)
- Chaque match est INDÉPENDANT → pas de dynamique Elo

MODÈLE:
  Si cotes disponibles: 65% cotes + 25% H2H + 10% taux victoire
  Sans cotes:           40% taux victoire + 35% H2H + 25% précision/tir
  Simulation: Binomial(5, p_shot) + mort subite
"""
import json, os, math, random
from collections import defaultdict, Counter
from math import comb

# ── Historique FC25 (matchs #55 → #N5) ─────────────────────────────────────
ALL_MATCHES = [
    # #55–#172
    ("Juventus",4,"Inter Miami",3),("Barcelona",5,"Arsenal",3),
    ("Bayern Munich",3,"Inter Miami",2),("Inter Miami",4,"Barcelona",1),
    ("Arsenal",7,"Man City",6),("Inter Miami",4,"PSG",5),
    ("PSG",5,"Juventus",3),("Barcelona",6,"Liverpool",7),
    ("Barcelona",5,"Arsenal",3),("Juventus",4,"PSG",5),
    ("Juventus",4,"PSG",5),("Barcelona",4,"Al Nassr",5),
    ("Barcelona",3,"Al Nassr",4),("PSG",7,"Inter Miami",6),
    ("Barcelona",12,"Man City",11),("Arsenal",5,"Real Madrid",3),
    ("Arsenal",2,"Man City",4),("PSG",5,"Bayern Munich",3),
    ("Arsenal",4,"Inter Miami",2),("Barcelona",5,"Arsenal",4),
    ("Juventus",4,"Liverpool",3),("Al Nassr",5,"Barcelona",4),
    ("PSG",4,"Bayern Munich",3),("PSG",4,"Arsenal",5),
    ("Real Madrid",4,"Bayern Munich",2),("Juventus",4,"Arsenal",3),
    ("Inter Miami",4,"Juventus",5),("Barcelona",4,"Juventus",3),
    ("Arsenal",4,"Juventus",5),("Inter Miami",5,"Man City",4),
    ("Arsenal",4,"Juventus",3),("Liverpool",6,"Arsenal",5),
    ("Arsenal",4,"Inter Miami",5),("Real Madrid",5,"Barcelona",4),
    ("PSG",5,"Man City",4),("Barcelona",5,"Arsenal",4),
    ("Juventus",5,"Bayern Munich",4),("Barcelona",4,"PSG",5),
    ("Man City",5,"Barcelona",4),("Liverpool",4,"Arsenal",3),
    ("Barcelona",7,"Al Nassr",6),("Arsenal",6,"Barcelona",5),
    ("Barcelona",4,"Man City",3),("Real Madrid",5,"Juventus",4),
    ("Liverpool",5,"Man City",6),("PSG",4,"Barcelona",5),
    ("Arsenal",5,"Juventus",4),("Arsenal",4,"Liverpool",3),
    ("Man City",7,"Arsenal",6),("PSG",4,"Arsenal",5),
    ("Arsenal",4,"Liverpool",5),("PSG",4,"Barcelona",5),
    ("Liverpool",3,"Man City",4),("Arsenal",5,"Man City",4),
    ("Man City",4,"Arsenal",5),("Arsenal",4,"Liverpool",3),
    ("Juventus",4,"Inter Miami",5),("Liverpool",5,"PSG",4),
    ("Juventus",4,"Arsenal",3),("PSG",5,"Arsenal",6),
    ("Liverpool",3,"Barcelona",4),("Barcelona",5,"Juventus",4),
    ("Barcelona",4,"Arsenal",3),("Arsenal",5,"Barcelona",4),
    ("Real Madrid",4,"Arsenal",5),("Arsenal",4,"Man City",5),
    ("Man City",5,"PSG",4),("PSG",3,"Man City",4),
    ("Juventus",4,"Barcelona",5),("Arsenal",4,"Bayern Munich",5),
    ("Barcelona",4,"Inter Miami",5),("PSG",4,"Al Nassr",3),
    ("Arsenal",5,"Al Nassr",4),("Man City",4,"Liverpool",3),
    ("Real Madrid",3,"Man City",4),("Arsenal",5,"Bayern Munich",4),
    ("PSG",4,"Real Madrid",5),("Arsenal",4,"Juventus",5),
    ("Man City",5,"Arsenal",4),("Real Madrid",4,"Man City",3),
    ("PSG",4,"Man City",5),("Man City",4,"PSG",5),
    ("PSG",3,"Liverpool",4),("Man City",5,"Real Madrid",4),
    ("Inter Miami",4,"Real Madrid",5),("Liverpool",4,"PSG",3),
    ("Arsenal",4,"PSG",5),("Man City",4,"Juventus",5),
    ("Real Madrid",5,"Man City",4),("PSG",4,"Real Madrid",5),
    ("Inter Miami",4,"Man City",5),("Man City",4,"Inter Miami",5),
    ("Al Nassr",5,"Man City",4),("Real Madrid",5,"PSG",6),
    ("Arsenal",5,"PSG",4),("Liverpool",5,"Real Madrid",4),
    ("Man City",5,"Real Madrid",4),("Real Madrid",5,"Barcelona",6),
    ("Man City",4,"Arsenal",3),("Barcelona",5,"Man City",6),
    ("Al Nassr",4,"Arsenal",5),("Arsenal",4,"Man City",5),
    ("Juventus",4,"PSG",5),("Arsenal",4,"Man City",5),
    ("Arsenal",4,"Barcelona",5),("PSG",4,"Arsenal",5),
    ("Liverpool",5,"Juventus",4),("Juventus",5,"Arsenal",4),
    ("Juventus",4,"Arsenal",5),("Juventus",4,"Liverpool",3),
    ("Juventus",3,"Inter Miami",4),("Barcelona",2,"Al Nassr",4),
    ("Barcelona",3,"Al Nassr",4),("Bayern Munich",4,"Inter Miami",2),
    ("Barcelona",5,"Man City",3),("Barcelona",4,"Liverpool",2),
    ("Barcelona",5,"Man City",6),("PSG",4,"Juventus",5),
    # #173–#281
    ("PSG",5,"Bayern Munich",3),("PSG",4,"Bayern Munich",3),
    ("Juventus",4,"Bayern Munich",2),("Barcelona",5,"Arsenal",3),
    ("Barcelona",5,"Man City",6),("Liverpool",5,"Man City",3),
    ("PSG",4,"Juventus",5),("PSG",6,"Juventus",7),
    ("Barcelona",3,"Al Nassr",1),("Inter Miami",3,"PSG",4),
    ("Barcelona",5,"Arsenal",6),("Juventus",3,"PSG",4),
    ("Real Madrid",4,"Inter Miami",2),("Bayern Munich",5,"Barcelona",4),
    ("Barcelona",4,"Man City",5),("Juventus",4,"PSG",5),
    ("Juventus",4,"PSG",5),("Barcelona",5,"Al Nassr",4),
    ("Barcelona",5,"Arsenal",6),("Real Madrid",7,"Barcelona",6),
    ("PSG",2,"Bayern Munich",4),("Barcelona",4,"Liverpool",2),
    ("Barcelona",4,"Arsenal",5),("PSG",7,"Bayern Munich",6),
    ("Real Madrid",7,"Barcelona",6),("Juventus",4,"Inter Miami",2),
    ("Bayern Munich",5,"Barcelona",3),("Inter Miami",4,"Juventus",3),
    ("Barcelona",4,"Man City",5),("Liverpool",5,"Man City",3),
    ("PSG",5,"Liverpool",3),("Real Madrid",3,"Barcelona",4),
    ("Barcelona",4,"Arsenal",1),("Barcelona",2,"Man City",3),
    ("PSG",4,"Juventus",1),("PSG",2,"Arsenal",4),
    ("Arsenal",1,"Real Madrid",3),("Inter Miami",8,"PSG",9),
    ("Liverpool",4,"Man City",5),("Juventus",3,"Liverpool",4),
    ("Real Madrid",4,"Barcelona",5),("Barcelona",5,"PSG",4),
    ("Real Madrid",4,"Inter Miami",2),("Juventus",4,"PSG",1),
    ("Arsenal",4,"Real Madrid",2),("Juventus",4,"Bayern Munich",5),
    ("Inter Miami",4,"Barcelona",5),("PSG",7,"Inter Miami",8),
    ("Juventus",4,"Bayern Munich",2),("PSG",5,"Bayern Munich",4),
    ("Arsenal",4,"Real Madrid",2),("Barcelona",9,"Arsenal",10),
    ("Barcelona",5,"Liverpool",3),("Man City",4,"Juventus",5),
    ("PSG",4,"Arsenal",5),("Barcelona",6,"Liverpool",5),
    ("Real Madrid",5,"Liverpool",3),("Liverpool",4,"Man City",5),
    ("Juventus",5,"PSG",3),("Liverpool",4,"Man City",5),
    ("PSG",4,"Inter Miami",2),("Barcelona",5,"Arsenal",6),
    ("Arsenal",5,"Man City",4),("Bayern Munich",11,"Barcelona",10),
    ("Juventus",6,"Liverpool",5),("Bayern Munich",2,"Barcelona",4),
    ("Barcelona",4,"Al Nassr",5),("PSG",4,"Inter Miami",2),
    ("Juventus",4,"Inter Miami",3),("PSG",2,"Inter Miami",4),
    ("Real Madrid",5,"Inter Miami",4),("PSG",6,"Juventus",5),
    ("PSG",2,"Bayern Munich",4),("Real Madrid",2,"Liverpool",4),
    ("Inter Miami",4,"Juventus",5),("Real Madrid",5,"Barcelona",4),
    ("PSG",4,"Barcelona",5),("Barcelona",6,"Liverpool",5),
    ("Barcelona",3,"Al Nassr",4),("Man City",4,"Juventus",5),
    ("Barcelona",5,"Liverpool",4),("Barcelona",7,"Man City",6),
    ("Juventus",4,"Bayern Munich",2),("Barcelona",4,"Arsenal",2),
    ("Real Madrid",5,"Liverpool",4),("PSG",3,"Juventus",4),
    ("Real Madrid",4,"PSG",1),("Barcelona",3,"Arsenal",4),
    ("Juventus",4,"Inter Miami",5),("Barcelona",3,"Al Nassr",4),
    ("Barcelona",5,"Liverpool",4),("PSG",2,"Bayern Munich",4),
    ("Barcelona",5,"Al Nassr",6),("Inter Miami",2,"PSG",4),
    ("PSG",4,"Inter Miami",3),("Barcelona",5,"Al Nassr",4),
    ("Man City",4,"Juventus",5),("Man City",4,"Arsenal",1),
    ("Juventus",4,"Inter Miami",5),("Barcelona",2,"Al Nassr",4),
    ("Barcelona",2,"Al Nassr",4),("Juventus",2,"Liverpool",4),
    ("Real Madrid",8,"Inter Miami",9),("Real Madrid",5,"Liverpool",4),
    ("Barcelona",4,"Man City",1),("Real Madrid",2,"Barcelona",4),
    ("Man City",3,"Arsenal",4),("Inter Miami",4,"Barcelona",5),
    ("Barcelona",4,"Liverpool",5),("PSG",4,"Juventus",2),
    # #N282–#N5 (nouvelle série)
    ("Inter Miami",5,"Barcelona",3),("Arsenal",4,"Real Madrid",5),
    ("Barcelona",6,"Liverpool",5),("Barcelona",4,"Al Nassr",5),
    ("Real Madrid",2,"Barcelona",3),("Real Madrid",3,"Inter Miami",4),
    ("Barcelona",4,"Al Nassr",2),("Real Madrid",4,"Barcelona",2),
    ("Barcelona",4,"Arsenal",5),("Barcelona",4,"Arsenal",2),
    ("Barcelona",0,"Arsenal",3),("Barcelona",5,"Arsenal",3),
    # #N10–#N14
    ("Juventus",4,"Liverpool",5),("Barcelona",4,"Liverpool",5),
    ("Juventus",4,"Inter Miami",2),("PSG",5,"Arsenal",4),
    ("Barcelona",8,"Man City",7),("Barcelona",5,"Man City",6),
    ("Juventus",4,"PSG",3),("PSG",5,"Barcelona",4),
    ("Real Madrid",5,"Liverpool",3),
]

TEAMS = ["PSG","Barcelona","Arsenal","Real Madrid","Man City",
         "Juventus","Bayern Munich","Liverpool","Inter Miami","Al Nassr"]


# ── Stats FC25 depuis l'historique ─────────────────────────────────────────

def build_stats():
    gf = defaultdict(list); ga = defaultdict(list)
    wins = defaultdict(int); losses = defaultdict(int)
    h2h  = defaultdict(lambda: {"W":0,"L":0})

    for a, sa, b, sb in ALL_MATCHES:
        gf[a].append(sa); ga[a].append(sb)
        gf[b].append(sb); ga[b].append(sa)
        if sa > sb:
            wins[a] += 1; losses[b] += 1
            h2h[(a,b)]["W"] += 1; h2h[(b,a)]["L"] += 1
        else:
            wins[b] += 1; losses[a] += 1
            h2h[(b,a)]["W"] += 1; h2h[(a,b)]["L"] += 1

    stats = {}
    for t in set(list(gf.keys()) + list(ga.keys())):
        n = len(gf[t])
        avg = sum(gf[t])/n if n else 4.25
        stats[t] = {
            "games":    n,
            "win_rate": wins[t]/n if n else 0.5,
            "avg_gf":   avg,
            "p_shot":   min(0.96, max(0.60, avg / 5)),  # précision par tir
        }
    return stats, h2h


# ── Simulation FC25 (Binomial 5 tirs + mort subite) ─────────────────────────

def simulate_binomial(p_a, p_b, n=100_000):
    """
    Simule le vrai format FC25:
    - Chaque équipe tire 5 pénalties (Binomial indépendant)
    - Si égalité → mort subite (tirs 1 vs 1 jusqu'au vainqueur)
    """
    rng = random.Random()
    wa = wb = 0
    scores_a = []; scores_b = []

    for _ in range(n):
        # Phase régulation: 5 tirs chacun
        sa = sum(1 for _ in range(5) if rng.random() < p_a)
        sb = sum(1 for _ in range(5) if rng.random() < p_b)

        # Mort subite si égalité
        while sa == sb:
            sa += (1 if rng.random() < p_a else 0)
            sb += (1 if rng.random() < p_b else 0)
            if sa != sb:
                break

        scores_a.append(sa); scores_b.append(sb)
        if sa > sb: wa += 1
        else: wb += 1

    total = n
    score_counts = Counter(zip(scores_a, scores_b))
    top = [(f"{s[0]}:{s[1]}", round(c/total*100, 1))
           for s, c in score_counts.most_common(5)]

    return wa/n, wb/n, top, sum(scores_a)/n, sum(scores_b)/n


# ── Probabilité depuis les cotes bookmaker ───────────────────────────────────

def implied_prob(odds_v1, odds_v2):
    """Normalise les cotes 1xbet → vraie probabilité (retire la marge)."""
    raw_a = 1 / odds_v1
    raw_b = 1 / odds_v2
    total = raw_a + raw_b  # sans la cote X (nul impossible)
    return raw_a / total, raw_b / total


# ── Prédiction principale ────────────────────────────────────────────────────

def predict(team_a, team_b, odds_v1=None, odds_v2=None, verbose=True):
    stats, h2h = build_stats()
    global_avg = sum(s for a,sa,b,sb in ALL_MATCHES for s in (sa,sb)) / (2*len(ALL_MATCHES))

    st_a = stats.get(team_a, {"win_rate":0.5,"avg_gf":global_avg,"p_shot":0.85,"games":0})
    st_b = stats.get(team_b, {"win_rate":0.5,"avg_gf":global_avg,"p_shot":0.85,"games":0})

    # H2H
    h = h2h.get((team_a, team_b), {"W":0,"L":0})
    total_h2h = h["W"] + h["L"]
    p_h2h_a = h["W"] / total_h2h if total_h2h >= 4 else None

    # Taux de victoire historique global
    p_wr_a = st_a["win_rate"]

    # Avantage précision/tir
    p_shot_a = st_a["p_shot"]
    p_shot_b = st_b["p_shot"]
    # Proba victoire si p_shot fixe (analytique approx via MC rapide)
    mc_q_a, mc_q_b, _, _, _ = simulate_binomial(p_shot_a, p_shot_b, n=20_000)

    # ── Calcul probabilité combinée ──────────────────────────────────────────
    if odds_v1 and odds_v2:
        # AVEC COTES: cotes bookmaker = signal principal
        p_odds_a, p_odds_b = implied_prob(odds_v1, odds_v2)
        p_h2h = p_h2h_a if p_h2h_a is not None else p_odds_a
        p_a = 0.65 * p_odds_a + 0.25 * p_h2h + 0.10 * p_wr_a
        mode = f"Cotes×65% + H2H×25% + WR×10%  [cotes: {odds_v1}/{odds_v2}]"
    else:
        # SANS COTES: données historiques + précision/tir
        p_h2h = p_h2h_a if p_h2h_a is not None else p_wr_a
        p_a = 0.40 * p_wr_a + 0.35 * p_h2h + 0.25 * mc_q_a
        mode = "WR×40% + H2H×35% + Tir×25%  [sans cotes]"

    p_a = max(0.05, min(0.95, p_a))
    p_b = 1 - p_a

    # p_shot ajustée par la force relative
    adj = (p_a - 0.5) * 0.08
    pa_adj = min(0.96, max(0.55, p_shot_a + adj))
    pb_adj = min(0.96, max(0.55, p_shot_b - adj))

    # Simulation Binomial complète
    mc_a, mc_b, top_scores, exp_a, exp_b = simulate_binomial(pa_adj, pb_adj, n=100_000)

    # Confiance
    diff = abs(p_a - 0.5)
    if odds_v1 and odds_v2:
        confidence = "HAUTE 🔥" if diff >= 0.15 else "MOYENNE ✅" if diff >= 0.08 else "FAIBLE ⚠️"
    else:
        confidence = "HAUTE 🔥" if diff >= 0.20 else "MOYENNE ✅" if diff >= 0.12 else "FAIBLE ⚠️"

    if not verbose:
        winner = team_a if p_a > p_b else team_b
        return {
            "winner": winner, "p_a": round(p_a*100,1), "p_b": round(p_b*100,1),
            "mc_a": round(mc_a*100,1), "mc_b": round(mc_b*100,1),
            "exp_a": round(exp_a,2), "exp_b": round(exp_b,2),
            "top_scores": top_scores, "confidence": confidence,
            "h2h_w": h["W"], "h2h_l": h["L"],
            "games_a": st_a["games"], "games_b": st_b["games"],
            "win_rate_a": round(p_wr_a*100,1),
            "win_rate_b": round(st_b["win_rate"]*100,1),
        }

    # ── Affichage ────────────────────────────────────────────────────────────
    B="\033[1m"; G="\033[92m"; RE="\033[91m"
    Y="\033[93m"; C="\033[96m"; R="\033[0m"; BL="\033[94m"

    winner = team_a if p_a > p_b else team_b
    w_prob = max(p_a, p_b)

    def bar(p, w=22):
        f = int(p/100*w); return "█"*f + "░"*(w-f)

    print(f"\n{B}{BL}{'═'*62}{R}")
    print(f"{B}  ⚽ FC25 PENALTY EXPERT v4.0 — Modèle RNG-Aware{R}")
    print(f"{B}{BL}{'═'*62}{R}")
    print(f"\n  {G}{B}{team_a}{R}  vs  {RE}{B}{team_b}{R}")

    if odds_v1 and odds_v2:
        p_o_a, p_o_b = implied_prob(odds_v1, odds_v2)
        print(f"  {C}Cotes: V1={odds_v1} → {p_o_a*100:.1f}%  |  V2={odds_v2} → {p_o_b*100:.1f}%{R}")

    print(f"\n{B}  📊 Stats FC25 ({len(ALL_MATCHES)} matchs réels){R}")
    print(f"  {team_a:<22} WR:{G}{st_a['win_rate']*100:.0f}%{R}  "
          f"Moy:{C}{st_a['avg_gf']:.2f}{R}  p/tir:{C}{st_a['p_shot']:.3f}{R}  N:{st_a['games']}")
    print(f"  {team_b:<22} WR:{RE}{st_b['win_rate']*100:.0f}%{R}  "
          f"Moy:{C}{st_b['avg_gf']:.2f}{R}  p/tir:{C}{st_b['p_shot']:.3f}{R}  N:{st_b['games']}")

    if total_h2h > 0:
        print(f"\n{B}  🔄 H2H direct{R}: {team_a} {G}{h['W']}{R}W – {RE}{h['L']}{R}L "
              f"({total_h2h} matchs)"
              + (f"  → {p_h2h_a*100:.0f}% A" if p_h2h_a else "  [< 4 matchs → non utilisé]"))

    print(f"\n{B}  🎯 Probabilités de victoire{R}")
    print(f"  {G}{team_a:<24}{R} {bar(p_a*100)} {B}{p_a*100:.1f}%{R}")
    print(f"  {RE}{team_b:<24}{R} {bar(p_b*100)} {B}{p_b*100:.1f}%{R}")
    print(f"\n  Simulation Binomial(5 tirs): {G}{mc_a*100:.1f}%{R} / {RE}{mc_b*100:.1f}%{R}")

    print(f"\n{B}  📈 Scores les plus probables (5 tirs + mort subite){R}")
    for i, (score, prob) in enumerate(top_scores, 1):
        a_s, b_s = score.split(":")
        color = G if int(a_s) > int(b_s) else RE
        medal = ["🥇","🥈","🥉","  4.","  5."][i-1]
        print(f"  {medal} {color}{team_a} {score} {team_b}{R}   {bar(prob, 12)} {prob}%")

    print(f"\n  Buts attendus: {G}{team_a}{R} {exp_a:.2f} – {exp_b:.2f} {RE}{team_b}{R}  "
          f"(p_tir: {pa_adj:.3f} vs {pb_adj:.3f})")

    print(f"\n{B}{'═'*62}{R}")
    print(f"  {B}Vainqueur prédit:{R} {G if p_a>p_b else RE}{B}{winner}{R}  ({w_prob*100:.1f}%)")
    print(f"  {B}Confiance:       {R} {B}{confidence}{R}")
    print(f"  {B}Modèle:          {R} {C}{mode}{R}")
    print(f"{B}{'═'*62}{R}\n")
    print(f"  {Y}⚠  FC25 RNG virtuel — résultats indépendants, pas de garantie.{R}\n")

    return {"winner": winner, "prob": round(w_prob*100,1)}


# ── Interface CLI ────────────────────────────────────────────────────────────

def interactive():
    B="\033[1m"; C="\033[96m"; G="\033[92m"; R="\033[0m"; BL="\033[94m"
    print(f"\n{B}{BL}  FC25 PENALTY EXPERT v4.0 — RNG-Aware{R}")
    print(f"  {C}240+ matchs FC25 | Binomial(5,p) + mort subite | Cotes intégrées{R}\n")
    print(f"Équipes: {', '.join(TEAMS)}\n")

    while True:
        try:
            print(f"{B}Équipe A > {R}", end=""); a = input().strip()
            if a.lower() in ("quit","q","exit",""): break
            print(f"{B}Équipe B > {R}", end=""); b = input().strip()
            if not b: continue
            print(f"{B}Cote V1 (laisser vide si inconnue) > {R}", end="")
            o1 = input().strip()
            print(f"{B}Cote V2 (laisser vide si inconnue) > {R}", end="")
            o2 = input().strip()

            a_m = next((t for t in TEAMS if t.lower().startswith(a.lower())), a)
            b_m = next((t for t in TEAMS if t.lower().startswith(b.lower())), b)
            odds1 = float(o1) if o1 else None
            odds2 = float(o2) if o2 else None

            predict(a_m, b_m, odds1, odds2)
        except (KeyboardInterrupt, EOFError, ValueError):
            break
    print(f"\n{G}Au revoir.{R}")


def main():
    import argparse
    p = argparse.ArgumentParser(description="FC25 Penalty Expert v4.0 — RNG-Aware")
    p.add_argument("--a",    help="Équipe A")
    p.add_argument("--b",    help="Équipe B")
    p.add_argument("--v1",   type=float, help="Cote V1 (ex: 2.555)")
    p.add_argument("--v2",   type=float, help="Cote V2 (ex: 2.57)")
    p.add_argument("--stats",action="store_true", help="Afficher toutes les stats")
    args = p.parse_args()

    if args.stats:
        stats, _ = build_stats()
        print(f"\n{'='*62}")
        print(f"  STATS FC25 — {len(ALL_MATCHES)} matchs analysés")
        print(f"{'='*62}")
        print(f"  {'Équipe':<22} {'WR':>5}  {'Moy':>5}  {'p/tir':>6}  {'N':>4}")
        print(f"  {'-'*55}")
        for t, s in sorted(stats.items(), key=lambda x: -x[1]["win_rate"]):
            print(f"  {t:<22} {s['win_rate']*100:>4.0f}%  {s['avg_gf']:>5.2f}  "
                  f"{s['p_shot']:>6.3f}  {s['games']:>4}")
        return

    if args.a and args.b:
        a = next((t for t in TEAMS if t.lower().startswith(args.a.lower())), args.a)
        b = next((t for t in TEAMS if t.lower().startswith(args.b.lower())), args.b)
        predict(a, b, args.v1, args.v2)
    else:
        interactive()


if __name__ == "__main__":
    main()
