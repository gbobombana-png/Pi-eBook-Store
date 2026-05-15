#!/usr/bin/env python3
import argparse, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from predictor import predict_match
from team_data import list_teams
from elo import update as elo_update, get_all as elo_all

R="\033[0m"; B="\033[1m"; G="\033[92m"; BL="\033[94m"
Y="\033[93m"; RE="\033[91m"; C="\033[96m"; W="\033[97m"; M="\033[95m"

BANNER = f"""{B}{BL}
  ██████╗ ██████╗ ███████╗██████╗ ██╗ ██████╗████████╗
  ██╔══██╗██╔══██╗██╔════╝██╔══██╗██║██╔════╝╚══██╔══╝
  ██████╔╝██████╔╝█████╗  ██║  ██║██║██║        ██║
  ██╔═══╝ ██╔══██╗██╔══╝  ██║  ██║██║██║        ██║
  ██║     ██║  ██║███████╗██████╔╝██║╚██████╗   ██║
  ╚═╝     ╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝ ╚═════╝   ╚═╝{R}
{C}  Virtual EA FC Predictor — Expert Edition v2.0{R}
{W}  Poisson + Dixon-Coles + Monte Carlo 50K + Elo{R}
"""


def bar(pct, width=20):
    filled = int(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


def display(r):
    if "error" in r:
        print(f"{RE}[!] {r['error']}{R}"); return

    mode_label = {"normal":"11v11","5x5":"5v5 Rush","rush":"5v5 Rush","penalty":"Tirs au but"}.get(r["mode"], r["mode"])
    print(f"\n{B}{BL}{'═'*58}{R}")
    print(f"{B}  {r['team_a']} (OVR:{r['rating_a']}) vs {r['team_b']} (OVR:{r['rating_b']}){R}")
    print(f"  Mode: {C}{mode_label}{R}  |  Simulations: {C}50 000{R}")
    print(f"{B}{BL}{'═'*58}{R}")

    # Joueurs stars
    print(f"\n{B}★ Joueurs Clés:{R}")
    print(f"  {G}{r['team_a']}{R}: {r['star_a']}")
    print(f"  {RE}{r['team_b']}{R}: {r['star_b']}")

    # Elo
    print(f"\n{B}Elo Dynamique:{R}")
    print(f"  {r['team_a']}: {C}{r['elo_a']}{R}  |  {r['team_b']}: {C}{r['elo_b']}{R}")

    # xG
    if r["xg_a"] != "-":
        print(f"\n{B}Expected Goals (xG):{R}")
        print(f"  {G}{r['team_a']}{R}: {C}{r['xg_a']}{R}  |  {RE}{r['team_b']}{R}: {C}{r['xg_b']}{R}")

    # Probabilités
    print(f"\n{B}Probabilités (Stats+Elo+MC):{R}")
    print(f"  {G}{r['team_a']:<22}{R} {bar(r['prob_a_wins'])} {B}{r['prob_a_wins']}%{R}")
    if r["mode"] not in ("penalty",):
        print(f"  {Y}{'Nul':<22}{R} {bar(r['prob_draw'])} {B}{r['prob_draw']}%{R}")
    print(f"  {RE}{r['team_b']:<22}{R} {bar(r['prob_b_wins'])} {B}{r['prob_b_wins']}%{R}")

    print(f"\n  {W}Monte Carlo ({r['mc_prob_a']}% / {r['mc_prob_b']}%){R}")

    # Score prédit
    print(f"\n{B}{'═'*58}{R}")
    if r["top_scores"]:
        print(f"{B}  Top Scores Probables:{R}")
        for i, (score, prob) in enumerate(r["top_scores"], 1):
            color = G if i == 1 else W
            medal = "🥇" if i == 1 else f" {i}."
            print(f"  {medal} {color}{r['team_a']} {score} {r['team_b']}{R}  {bar(prob, 14)} {prob}%")
    else:
        s = r['predicted_score']
        print(f"  {G}{B}{r['team_a']} {s} {r['team_b']}{R}  ({r['score_probability']}%)")

    # Analyse
    if r.get("analysis"):
        print(f"\n{B}Analyse Technique:{R}")
        for line in r["analysis"]:
            print(f"  {C}▸{R} {line}")

    # Recommandation
    conf_c = G if "HAUTE" in r["confidence"] else Y if "MOYENNE" in r["confidence"] else RE
    print(f"\n{B}{'═'*58}{R}")
    print(f"  {B}Recommandation:{R} {G}{B}{r['recommendation']}{R}")
    print(f"  {B}Confiance:     {R} {conf_c}{B}{r['confidence']}{R}")
    print(f"{B}{BL}{'═'*58}{R}")
    print(f"{Y}  ⚠ Modèle statistique — pas de garantie. Joue responsable.{R}\n")


def interactive():
    print(BANNER)
    print(f"{C}Commandes: 'list' = équipes | 'elo' = classement Elo | 'update' = ajouter résultat | 'quit' = quitter{R}\n")
    modes = {"1":"normal","2":"5x5","3":"penalty","n":"normal","5":"5x5","p":"penalty"}

    while True:
        try:
            print(f"{B}Équipe A >{R} ", end=""); team_a = input().strip()
            if not team_a: continue
            if team_a.lower() == "quit": break
            if team_a.lower() == "list":
                print(f"\n{B}Équipes disponibles:{R}")
                for t in list_teams(): print(f"  {C}·{R} {t}")
                print(); continue
            if team_a.lower() == "elo":
                ratings = elo_all()
                print(f"\n{B}Classement Elo:{R}")
                for t, e in sorted(ratings.items(), key=lambda x: -x[1])[:20]:
                    print(f"  {C}{e:>6}{R}  {t}")
                print(); continue
            if team_a.lower() == "update":
                print(f"Équipe A: ", end=""); a = input().strip()
                print(f"Score A: ", end=""); sa = int(input().strip())
                print(f"Équipe B: ", end=""); b = input().strip()
                print(f"Score B: ", end=""); sb = int(input().strip())
                r = elo_update(a, sa, b, sb)
                print(f"{G}Elo mis à jour:{R} {a}: {r['old_a']}→{G}{r['new_a']}{R}  {b}: {r['old_b']}→{RE}{r['new_b']}{R}\n")
                continue

            print(f"{B}Équipe B >{R} ", end=""); team_b = input().strip()
            if not team_b: continue

            print(f"{B}Mode (1=11v11  2=5v5 Rush  3=Penalty) [1] >{R} ", end="")
            m = input().strip() or "1"
            mode = modes.get(m, "normal")

            result = predict_match(team_a, team_b, mode=mode)
            display(result)

        except (KeyboardInterrupt, EOFError):
            break
    print(f"\n{G}Au revoir.{R}")


def main():
    parser = argparse.ArgumentParser(description="EA FC Virtual Match Predictor — Expert v2.0")
    parser.add_argument("--team-a",  help="Équipe A")
    parser.add_argument("--team-b",  help="Équipe B")
    parser.add_argument("--mode",    default="normal", choices=["normal","5x5","penalty"])
    parser.add_argument("--list",    action="store_true")
    parser.add_argument("--elo",     action="store_true", help="Voir classement Elo")
    parser.add_argument("--update",  nargs=4, metavar=("A","SCORE_A","B","SCORE_B"),
                        help="Ajouter résultat: --update France 2 Brazil 1")
    parser.add_argument("-i","--interactive", action="store_true")
    args = parser.parse_args()

    if args.list:
        print(BANNER)
        for t in list_teams(): print(f"  · {t}")
        return
    if args.elo:
        print(BANNER)
        ratings = elo_all()
        if not ratings:
            print(f"{Y}Aucun Elo enregistré. Les équipes démarrent à 1500.{R}")
        for t, e in sorted(ratings.items(), key=lambda x: -x[1]):
            print(f"  {C}{e:>6}{R}  {t}")
        return
    if args.update:
        a, sa, b, sb = args.update[0], int(args.update[1]), args.update[2], int(args.update[3])
        r = elo_update(a, sa, b, sb)
        print(f"{G}Elo mis à jour:{R} {a}: {r['old_a']}→{G}{r['new_a']}{R}  {b}: {r['old_b']}→{RE}{r['new_b']}{R}")
        return
    if args.interactive or (not args.team_a and not args.team_b):
        interactive(); return
    if not args.team_a or not args.team_b:
        parser.print_help(); return

    print(BANNER)
    display(predict_match(args.team_a, args.team_b, mode=args.mode))


if __name__ == "__main__":
    main()
