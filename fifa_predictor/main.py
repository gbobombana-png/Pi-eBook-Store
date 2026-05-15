#!/usr/bin/env python3
"""
FIFA Virtual Match Predictor
Prédit les scores des matchs virtuels EA FC sur les plateformes de paris
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from predictor import predict_match
from team_data import list_teams

RESET  = "\033[0m";  BOLD  = "\033[1m"
GREEN  = "\033[92m"; BLUE  = "\033[94m"
YELLOW = "\033[93m"; RED   = "\033[91m"
CYAN   = "\033[96m"; WHITE = "\033[97m"

BANNER = """
  ██████╗ ██████╗ ███████╗██████╗ ██╗ ██████╗████████╗
  ██╔══██╗██╔══██╗██╔════╝██╔══██╗██║██╔════╝╚══██╔══╝
  ██████╔╝██████╔╝█████╗  ██║  ██║██║██║        ██║
  ██╔═══╝ ██╔══██╗██╔══╝  ██║  ██║██║██║        ██║
  ██║     ██║  ██║███████╗██████╔╝██║╚██████╗   ██║
  ╚═╝     ╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝ ╚═════╝   ╚═╝
  Virtual FIFA Match Predictor — Poisson Model
"""


def display_result(r):
    if "error" in r:
        print(f"{RED}[!] {r['error']}{RESET}")
        return

    print(f"\n{BOLD}{BLUE}{'='*55}{RESET}")
    print(f"{BOLD}  {r['team_a']} (OVR:{r['rating_a']})  vs  {r['team_b']} (OVR:{r['rating_b']}){RESET}")
    print(f"  Mode: {r['mode'].upper()}")
    print(f"{BOLD}{BLUE}{'='*55}{RESET}")

    # Probabilités
    print(f"\n{BOLD}Probabilités:{RESET}")
    bar_a = "█" * int(r['prob_a_wins'] / 5)
    bar_b = "█" * int(r['prob_b_wins'] / 5)
    bar_d = "█" * int(r['prob_draw'] / 5)

    print(f"  {GREEN}{r['team_a']:<20}{RESET} {bar_a} {r['prob_a_wins']}%")
    if r['mode'] != "penalty":
        print(f"  {YELLOW}{'Nul':<20}{RESET} {bar_d} {r['prob_draw']}%")
    print(f"  {RED}{r['team_b']:<20}{RESET} {bar_b} {r['prob_b_wins']}%")

    # xG
    if r['mode'] != "penalty":
        print(f"\n{BOLD}Expected Goals (xG):{RESET}")
        print(f"  {r['team_a']}: {CYAN}{r['xg_a']}{RESET}  |  {r['team_b']}: {CYAN}{r['xg_b']}{RESET}")

    # Score prédit
    print(f"\n{BOLD}Score le plus probable:{RESET}")
    print(f"  {GREEN}{BOLD}{r['team_a']} {r['predicted_score'].split('-')[0]} - {r['predicted_score'].split('-')[1]} {r['team_b']}{RESET}")
    print(f"  Probabilité: {r['score_probability']}%")

    # Top 5 scores
    if r['top_5_scores']:
        print(f"\n{BOLD}Top 5 scores probables:{RESET}")
        for i, (score, prob) in enumerate(r['top_5_scores'], 1):
            bar = "█" * int(prob * 2)
            color = GREEN if i == 1 else WHITE
            print(f"  {i}. {color}{r['team_a']} {score} {r['team_b']}{RESET}  {bar} {prob}%")

    # Recommandation
    conf_color = GREEN if r['confidence'] == "HAUTE" else YELLOW if r['confidence'] == "MOYENNE" else RED
    print(f"\n{BOLD}Recommandation:{RESET} {GREEN}{r['recommendation']}{RESET}")
    print(f"{BOLD}Confiance:{RESET}      {conf_color}{r['confidence']}{RESET}")
    print(f"\n{YELLOW}⚠ Outil statistique — pas de garantie. Joue responsable.{RESET}")
    print(f"{BLUE}{'='*55}{RESET}\n")


def interactive_mode():
    print(BANNER)
    print(f"{CYAN}Mode interactif — tape 'quit' pour quitter, 'list' pour les équipes{RESET}\n")

    modes = {"1": "normal", "2": "5x5", "3": "penalty"}

    while True:
        print(f"{BOLD}Équipe A:{RESET} ", end="")
        team_a = input().strip()
        if team_a.lower() == "quit":
            break
        if team_a.lower() == "list":
            print("\n".join(f"  - {t}" for t in list_teams()))
            continue

        print(f"{BOLD}Équipe B:{RESET} ", end="")
        team_b = input().strip()
        if team_b.lower() == "quit":
            break

        print(f"{BOLD}Mode (1=normal, 2=5x5 Rush, 3=penalty) [1]:{RESET} ", end="")
        mode_input = input().strip() or "1"
        mode = modes.get(mode_input, "normal")

        result = predict_match(team_a, team_b, mode=mode)
        display_result(result)


def main():
    parser = argparse.ArgumentParser(description="FIFA Virtual Match Predictor")
    parser.add_argument("--team-a",  help="Équipe A")
    parser.add_argument("--team-b",  help="Équipe B")
    parser.add_argument("--mode",    default="normal",
                        choices=["normal", "5x5", "penalty"],
                        help="Mode de jeu (default: normal)")
    parser.add_argument("--list",    action="store_true", help="Lister les équipes disponibles")
    parser.add_argument("--interactive", "-i", action="store_true", help="Mode interactif")
    args = parser.parse_args()

    if args.list:
        print(BANNER)
        print(f"{BOLD}Équipes disponibles:{RESET}")
        for t in list_teams():
            print(f"  - {t}")
        return

    if args.interactive or (not args.team_a and not args.team_b):
        interactive_mode()
        return

    if not args.team_a or not args.team_b:
        parser.print_help()
        return

    print(BANNER)
    result = predict_match(args.team_a, args.team_b, mode=args.mode)
    display_result(result)


if __name__ == "__main__":
    main()
