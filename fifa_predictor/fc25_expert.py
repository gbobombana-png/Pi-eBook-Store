#!/usr/bin/env python3
"""
FC25 PENALTY EXPERT PREDICTOR — Ultra Précis
Basé sur 272+ vrais matchs FC25 observés.
Aucune stat du vrai football — modèle 100% FC25 virtuel.
"""
import json, os, random, math
from collections import defaultdict

# ── Tout l'historique FC25 (matchs #55 → #288) ─────────────────────────────
ALL_MATCHES = [
    # #55–#172 (batch_elo_update.py)
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
    # #N282–#N288
    ("Inter Miami",5,"Barcelona",3),("Arsenal",4,"Real Madrid",5),
    ("Barcelona",6,"Liverpool",5),("Barcelona",4,"Al Nassr",5),
    ("Real Madrid",2,"Barcelona",3),("Real Madrid",3,"Inter Miami",4),
    ("Barcelona",4,"Al Nassr",2),
]

TEAMS = ["PSG","Barcelona","Arsenal","Real Madrid","Man City",
         "Juventus","Bayern Munich","Liverpool","Inter Miami","Al Nassr"]

ELO_FILE = os.path.join(os.path.dirname(__file__), "elo_ratings.json")
BASE_ELO  = 1500


# ── Analyse complète de l'historique ───────────────────────────────────────

def build_stats():
    goals_for     = defaultdict(list)
    goals_against = defaultdict(list)
    wins          = defaultdict(int)
    losses        = defaultdict(int)
    h2h           = defaultdict(lambda: {"W":0,"L":0,"gf":0,"ga":0})

    for a, sa, b, sb in ALL_MATCHES:
        goals_for[a].append(sa); goals_against[a].append(sb)
        goals_for[b].append(sb); goals_against[b].append(sa)
        if sa > sb:
            wins[a]  += 1; losses[b] += 1
            h2h[(a,b)]["W"] += 1; h2h[(a,b)]["gf"] += sa; h2h[(a,b)]["ga"] += sb
            h2h[(b,a)]["L"] += 1
        else:
            wins[b]  += 1; losses[a] += 1
            h2h[(b,a)]["W"] += 1; h2h[(b,a)]["gf"] += sb; h2h[(b,a)]["ga"] += sa
            h2h[(a,b)]["L"] += 1

    stats = {}
    for t in set(list(goals_for.keys())+list(goals_against.keys())):
        gf = goals_for[t];   ga = goals_against[t]
        n  = len(gf)
        w  = wins[t];        l = losses[t]
        stats[t] = {
            "games":    n,
            "win_rate": w/n if n else 0.5,
            "avg_gf":   sum(gf)/n if n else 4.5,
            "avg_ga":   sum(ga)/n if n else 4.5,
            "std_gf":   _std(gf),
            "attack":   (sum(gf)/n) / _global_avg_goals() if n else 1.0,
            "defense":  _global_avg_goals() / (sum(ga)/n) if n and sum(ga)/n > 0 else 1.0,
        }
    return stats, h2h


def _std(lst):
    if len(lst) < 2: return 1.5
    m = sum(lst)/len(lst)
    return math.sqrt(sum((x-m)**2 for x in lst)/len(lst))


def _global_avg_goals():
    all_goals = [s for a,sa,b,sb in ALL_MATCHES for s in (sa,sb)]
    return sum(all_goals)/len(all_goals) if all_goals else 4.5


def get_elo(team):
    if os.path.exists(ELO_FILE):
        with open(ELO_FILE) as f:
            ratings = json.load(f)
        return ratings.get(team, BASE_ELO)
    return BASE_ELO


def elo_win_prob(elo_a, elo_b):
    return 1 / (1 + 10**((elo_b - elo_a)/400))


# ── Monte Carlo FC25 Penalty ────────────────────────────────────────────────

def simulate_fc25_penalty(exp_a, exp_b, std_a, std_b, n=100_000):
    """
    Simule des tirs au but FC25 :
    - Score = Normal(mu=exp, sigma=std), min 1
    - Pas de nul → si égalité, mort subite simulée
    """
    rng = random.Random()
    wa = wb = 0
    scores_a = []; scores_b = []

    for _ in range(n):
        # Score pénalty FC25 ~ Normal tronquée à l'entier le plus proche
        sa = max(1, round(rng.gauss(exp_a, std_a)))
        sb = max(1, round(rng.gauss(exp_b, std_b)))

        # Mort subite si égalité (probabilité 50/50 légèrement biaisée par attack)
        if sa == sb:
            bias = exp_a / (exp_a + exp_b)
            if rng.random() < bias:
                sa += 1
            else:
                sb += 1

        scores_a.append(sa); scores_b.append(sb)
        if sa > sb: wa += 1
        else:       wb += 1

    # Distribution des scores les plus probables
    from collections import Counter
    score_counts = Counter(zip(scores_a, scores_b))
    total = sum(score_counts.values())
    top = [(f"{s[0]}:{s[1]}", round(c/total*100, 1))
           for s,c in score_counts.most_common(5)]

    return wa/n, wb/n, top, sum(scores_a)/n, sum(scores_b)/n


# ── Prédiction principale ───────────────────────────────────────────────────

def predict(team_a, team_b, verbose=True):
    stats, h2h = build_stats()

    st_a = stats.get(team_a, {"avg_gf":4.5,"avg_ga":4.5,"std_gf":1.5,"attack":1.0,"defense":1.0,"win_rate":0.5,"games":0})
    st_b = stats.get(team_b, {"avg_gf":4.5,"avg_ga":4.5,"std_gf":1.5,"attack":1.0,"defense":1.0,"win_rate":0.5,"games":0})

    elo_a = get_elo(team_a);  elo_b = get_elo(team_b)

    # Elo probability (poids 45%)
    p_elo_a = elo_win_prob(elo_a, elo_b)

    # Stats probability (poids 35%) — basé sur attaque/défense FC25
    att_a = st_a["attack"] * st_b["defense"]  # force relative de A vs défense de B
    att_b = st_b["attack"] * st_a["defense"]
    p_stats_a = att_a / (att_a + att_b) if (att_a+att_b) > 0 else 0.5

    # H2H specific (poids 20%)
    h = h2h.get((team_a, team_b), {"W":0,"L":0})
    total_h2h = h["W"] + h["L"]
    p_h2h_a = h["W"]/total_h2h if total_h2h >= 3 else p_elo_a

    # Probabilité combinée
    p_a = 0.45*p_elo_a + 0.35*p_stats_a + 0.20*p_h2h_a
    p_b = 1 - p_a

    # Expected goals FC25 (ajusté par la force relative)
    global_avg = _global_avg_goals()
    exp_a = global_avg * st_a["attack"] * st_b["defense"]
    exp_b = global_avg * st_b["attack"] * st_a["defense"]
    exp_a = max(2.0, min(exp_a, 8.0))
    exp_b = max(2.0, min(exp_b, 8.0))

    # Ajustement probabiliste sur les expected goals
    exp_a *= (1 + 0.1*(p_a - 0.5))
    exp_b *= (1 + 0.1*(p_b - 0.5))

    # Simulation Monte Carlo FC25
    mc_a, mc_b, top_scores, sim_gf_a, sim_gf_b = simulate_fc25_penalty(
        exp_a, exp_b, st_a["std_gf"], st_b["std_gf"]
    )

    # Confiance
    elo_diff = abs(elo_a - elo_b)
    if p_a >= 0.72 or p_b >= 0.72:
        confidence = "HAUTE 🔥"
    elif p_a >= 0.58 or p_b >= 0.58:
        confidence = "MOYENNE ✅"
    else:
        confidence = "FAIBLE ⚠️"

    if not verbose:
        return {
            "team_a": team_a, "team_b": team_b,
            "p_a": round(p_a*100,1), "p_b": round(p_b*100,1),
            "mc_a": round(mc_a*100,1), "mc_b": round(mc_b*100,1),
            "exp_a": round(exp_a,1), "exp_b": round(exp_b,1),
            "top_scores": top_scores, "confidence": confidence,
            "elo_a": elo_a, "elo_b": elo_b,
            "h2h_w": h["W"], "h2h_l": h["L"],
            "games_a": st_a["games"], "games_b": st_b["games"],
            "win_rate_a": round(st_a["win_rate"]*100,1),
            "win_rate_b": round(st_b["win_rate"]*100,1),
        }

    # ── Affichage ──────────────────────────────────────────────────────────
    W="\033[97m"; B="\033[1m"; G="\033[92m"; RE="\033[91m"
    Y="\033[93m"; C="\033[96m"; M="\033[95m"; R="\033[0m"; BL="\033[94m"

    winner = team_a if p_a > p_b else team_b
    w_prob  = max(p_a, p_b)

    print(f"\n{B}{BL}{'═'*60}{R}")
    print(f"{B}  ⚽ FC25 PENALTY EXPERT — Analyse Ultra Précise{R}")
    print(f"{B}{BL}{'═'*60}{R}")
    print(f"\n  {G}{B}{team_a}{R}  vs  {RE}{B}{team_b}{R}")
    print(f"  Elo: {C}{elo_a}{R}  vs  {C}{elo_b}{R}  (diff: {abs(elo_a-elo_b):.0f})")

    print(f"\n{B}  📊 Stats FC25 (sur données réelles){R}")
    print(f"  {team_a:<20} Taux victoire: {G}{st_a['win_rate']*100:.0f}%{R}  "
          f"Moy buts: {C}{st_a['avg_gf']:.1f}{R}  Matchs: {st_a['games']}")
    print(f"  {team_b:<20} Taux victoire: {RE}{st_b['win_rate']*100:.0f}%{R}  "
          f"Moy buts: {C}{st_b['avg_gf']:.1f}{R}  Matchs: {st_b['games']}")

    if total_h2h > 0:
        print(f"\n{B}  🔄 H2H direct{R}: {team_a} {G}{h['W']}{R}W – {RE}{h['L']}{R}L  "
              f"({total_h2h} matchs)")

    def bar(p, w=22):
        f = int(p/100*w)
        return "█"*f + "░"*(w-f)

    print(f"\n{B}  🎯 Probabilités de victoire{R}")
    print(f"  {G}{team_a:<22}{R} {bar(p_a*100)} {B}{p_a*100:.1f}%{R}")
    print(f"  {RE}{team_b:<22}{R} {bar(p_b*100)} {B}{p_b*100:.1f}%{R}")
    print(f"\n  Monte Carlo (100k sim): {G}{mc_a*100:.1f}%{R} / {RE}{mc_b*100:.1f}%{R}")

    print(f"\n{B}  📈 Scores FC25 les plus probables{R}")
    for i,(score,prob) in enumerate(top_scores, 1):
        a_s, b_s = score.split(":")
        color = G if int(a_s) > int(b_s) else RE if int(a_s) < int(b_s) else Y
        medal = ["🥇","🥈","🥉","  4.","  5."][i-1]
        print(f"  {medal} {color}{team_a} {score} {team_b}{R}   {bar(prob, 12)} {prob}%")

    print(f"\n  Buts attendus: {G}{team_a}{R} {exp_a:.1f} – {exp_b:.1f} {RE}{team_b}{R}")

    print(f"\n{B}{'═'*60}{R}")
    print(f"  {B}Vainqueur prédit:{R} {G}{B}{winner}{R}  ({w_prob*100:.1f}%)")
    print(f"  {B}Confiance:       {R} {B}{confidence}{R}")
    conf_detail = (f"Elo×45% + Stats FC25×35% + H2H×20%")
    print(f"  {B}Modèle:          {R} {C}{conf_detail}{R}")
    print(f"{B}{'═'*60}{R}\n")
    print(f"  {Y}⚠  FC25 virtuel — résultat statistique, pas de garantie.{R}\n")

    return {"winner": winner, "prob": round(w_prob*100,1)}


# ── Interface interactive ───────────────────────────────────────────────────

def interactive():
    G="\033[92m"; B="\033[1m"; C="\033[96m"; R="\033[0m"; BL="\033[94m"
    print(f"\n{B}{BL}  FC25 PENALTY EXPERT — Ultra Précis v3.0{R}")
    print(f"  {C}272+ matchs réels analysés | Modèle hybride Elo+Stats+H2H+MC{R}\n")
    print(f"Équipes: {', '.join(TEAMS)}\n")

    while True:
        try:
            print(f"{B}Équipe A > {R}", end=""); a = input().strip()
            if a.lower() in ("quit","q","exit"): break
            if not a: continue

            print(f"{B}Équipe B > {R}", end=""); b = input().strip()
            if not b: continue

            # Matching partiel
            a_match = next((t for t in TEAMS if t.lower().startswith(a.lower())), a)
            b_match = next((t for t in TEAMS if t.lower().startswith(b.lower())), b)

            predict(a_match, b_match)

        except (KeyboardInterrupt, EOFError):
            break
    print(f"\n{G}Au revoir.{R}")


def main():
    import argparse
    p = argparse.ArgumentParser(description="FC25 Penalty Expert Predictor v3.0")
    p.add_argument("--a", help="Équipe A")
    p.add_argument("--b", help="Équipe B")
    p.add_argument("--stats", action="store_true", help="Afficher toutes les stats")
    args = p.parse_args()

    if args.stats:
        stats, _ = build_stats()
        print(f"\n{'='*55}")
        print(f"  STATS FC25 — {len(ALL_MATCHES)} matchs analysés")
        print(f"{'='*55}")
        for t, s in sorted(stats.items(), key=lambda x: -x[1]["win_rate"]):
            print(f"  {t:<20} WR:{s['win_rate']*100:.0f}%  "
                  f"Moy:{s['avg_gf']:.1f}  σ:{s['std_gf']:.1f}  N:{s['games']}")
        return

    if args.a and args.b:
        a = next((t for t in TEAMS if t.lower().startswith(args.a.lower())), args.a)
        b = next((t for t in TEAMS if t.lower().startswith(args.b.lower())), args.b)
        predict(a, b)
    else:
        interactive()


if __name__ == "__main__":
    main()
