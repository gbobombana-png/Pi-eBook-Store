#!/usr/bin/env python3
"""
Script CLI de collecte de données.
Usage:
  python collect.py                           # collecte tout
  python collect.py --comp PL FL1            # seulement PL + Ligue 1
  python collect.py --comp FL1 --show        # afficher les prédictions
  python collect.py --test                   # tester les connexions API

Variables d'environnement requises (dans .env):
  FOOTBALL_DATA_API_KEY=votre_clé_ici
  ODDS_API_KEY=votre_clé_ici
"""
import asyncio
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()


async def main():
    parser = argparse.ArgumentParser(description="Football AI — Collecteur de données")
    parser.add_argument("--comp",  nargs="+", default=["PL", "FL1", "BL1"],
                        help="Compétitions (PL, FL1, BL1, PD, SA, CL)")
    parser.add_argument("--show",  action="store_true", help="Afficher les prédictions détaillées")
    parser.add_argument("--test",  action="store_true", help="Tester les connexions API uniquement")
    parser.add_argument("--json",  action="store_true", help="Sortie JSON brute")
    args = parser.parse_args()

    fd_key   = os.getenv("FOOTBALL_DATA_API_KEY", "")
    odds_key = os.getenv("ODDS_API_KEY", "")

    if not fd_key or not odds_key:
        print("❌  Clés API manquantes !")
        print()
        print("  1. Crée un fichier .env dans football_ai_platform/backend/")
        print("  2. Ajoute:")
        print("       FOOTBALL_DATA_API_KEY=ta_clé_football_data")
        print("       ODDS_API_KEY=ta_clé_odds_api")
        print()
        print("  Clé football-data.org (gratuite): https://www.football-data.org/client/register")
        print("  Clé The Odds API (gratuite):      https://the-odds-api.com/#get-access")
        sys.exit(1)

    if args.test:
        await run_tests(fd_key, odds_key)
        return

    from app.collectors.scheduler import CollectionScheduler
    scheduler = CollectionScheduler(fd_key, odds_key)

    print(f"\n{'═'*60}")
    print("  ⚽ Football AI Platform — Collecte de données")
    print(f"{'═'*60}")
    print(f"  Compétitions: {', '.join(args.comp)}")
    print()

    result = await scheduler.run_once(competitions=args.comp)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return

    print(f"\n{'─'*60}")
    print(f"  📅 Matchs collectés: {result['total']}")
    print(f"  💰 Quota Odds API restant: {scheduler.pipeline.odds.remaining_requests()}")
    print(f"{'─'*60}\n")

    analyses = result.get("analyses", [])
    if not analyses:
        print("  Aucune analyse disponible.")
        return

    # Trier par score de suspicion décroissant
    analyses.sort(key=lambda x: x["suspicion_score"], reverse=True)

    B  = "\033[1m";  R  = "\033[0m"
    G  = "\033[92m"; RE = "\033[91m"
    Y  = "\033[93m"; C  = "\033[96m"

    LEVEL_COLOR = {"low": G, "medium": Y, "high": Y, "critical": RE}

    for a in analyses:
        lvl_color = LEVEL_COLOR.get(a["suspicion_level"], Y)
        susp_icon = "🚨" if a["suspicion_level"] == "critical" else "⚠️" if a["suspicion_level"] == "high" else "✅"

        print(f"  {B}{a['match']}{R}")
        print(f"  {C}{a.get('competition','')}{R}  ·  {a.get('date','')[:10]}")
        print(f"  {susp_icon} Suspicion: {lvl_color}{a['suspicion_score']:.0f}/100 [{a['suspicion_level'].upper()}]{R}")
        print(f"  🎯 Vainqueur: {B}{a['winner']}{R} ({a['confidence']:.0f}% conf) | Score: {B}{a['score']}{R}")
        print(f"  📊 Dom {G}{a['prob_home']}%{R}  Nul {a['prob_draw']}%  Ext {RE}{a['prob_away']}%{R}")
        print(f"  📈 Over2.5: {a['over25']}%  BTTS: {a['btts']}%")

        if args.show and a.get("flags"):
            for f in a["flags"]:
                print(f"  ⚡ {f}")
        print()


async def run_tests(fd_key: str, odds_key: str):
    print("\n🔧 Test des connexions API...\n")

    # Test football-data.org
    from app.collectors.football_data import FootballDataClient
    fd = FootballDataClient(fd_key)
    try:
        matches = await fd.get_matches(competition="FL1")
        print(f"  ✅ football-data.org: OK ({len(matches)} matchs Ligue 1 trouvés)")
        if matches:
            m = matches[0]
            print(f"     Prochain: {m.get('homeTeam',{}).get('name')} vs {m.get('awayTeam',{}).get('name')}")
    except Exception as e:
        print(f"  ❌ football-data.org: {e}")

    # Test The Odds API
    from app.collectors.odds_api import OddsAPIClient
    oa = OddsAPIClient(odds_key)
    try:
        events = await oa.get_odds(sport="soccer_france_ligue_one")
        print(f"  ✅ The Odds API: OK ({len(events)} matchs avec cotes)")
        print(f"     Quota restant: {oa.remaining_requests()} requêtes")
        if events:
            ev = oa.normalize_event(events[0])
            c = ev["consensus"]
            print(f"     Exemple: {ev['home_team']} vs {ev['away_team']}")
            print(f"     Cotes: D={c['home']:.2f} | N={c['draw']:.2f} | E={c['away']:.2f}")
    except Exception as e:
        print(f"  ❌ The Odds API: {e}")

    print()


if __name__ == "__main__":
    asyncio.run(main())
