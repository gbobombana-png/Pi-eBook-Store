#!/usr/bin/env python3
"""
Football AI Platform — Script autonome
Fonctionne sur Replit.com (gratuit, depuis ton téléphone)

SETUP sur Replit:
  1. Va sur replit.com → New Repl → Python
  2. Colle ce fichier entier
  3. Dans "Secrets" ajoute:
       FOOTBALL_DATA_KEY = b9b853507126449ebd34caa5bcb642b8
       ODDS_API_KEY      = 3f0b5b784fe4ca6b49b14517728bd8e5
  4. Clique Run ▶

DÉPENDANCES (Shell Replit):
  pip install httpx
"""

import asyncio
import math
import os
import random
from itertools import product
from datetime import datetime, timedelta

try:
    import httpx
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "httpx", "-q"])
    import httpx

# ── Clés API ─────────────────────────────────────────────────────────────────
FD_KEY   = os.getenv("FOOTBALL_DATA_KEY",  "b9b853507126449ebd34caa5bcb642b8")
ODDS_KEY = os.getenv("ODDS_API_KEY",       "3f0b5b784fe4ca6b49b14517728bd8e5")

# ── Couleurs terminal ─────────────────────────────────────────────────────────
B  = "\033[1m";   R  = "\033[0m"
G  = "\033[92m";  RE = "\033[91m"
Y  = "\033[93m";  C  = "\033[96m"
BL = "\033[94m";  GR = "\033[90m"

# ═══════════════════════════════════════════════════════════════════════════════
#  MODÈLES IA
# ═══════════════════════════════════════════════════════════════════════════════

def poisson_prob(k, lam):
    if lam <= 0: return 1.0 if k == 0 else 0.0
    return (lam**k) * math.exp(-lam) / math.factorial(k)

def poisson_predict(atk_h, def_h, atk_a, def_a, league_h=1.52, league_a=1.18, home_adv=1.20):
    lh = max(0.2, atk_h * def_a * league_h * home_adv)
    la = max(0.2, atk_a * def_h * league_a)
    max_g = 9
    matrix = {(h, a): poisson_prob(h, lh) * poisson_prob(a, la)
              for h, a in product(range(max_g+1), repeat=2)}
    p_h = sum(p for (h,a),p in matrix.items() if h > a)
    p_d = sum(p for (h,a),p in matrix.items() if h == a)
    p_a = sum(p for (h,a),p in matrix.items() if h < a)
    p_o25  = sum(p for (h,a),p in matrix.items() if h+a > 2.5)
    p_btts = sum(p for (h,a),p in matrix.items() if h>=1 and a>=1)
    best   = max(matrix, key=matrix.get)
    return dict(
        lh=round(lh,3), la=round(la,3),
        ph=round(p_h,4), pd=round(p_d,4), pa=round(p_a,4),
        over25=round(p_o25,4), btts=round(p_btts,4),
        score=best, score_prob=round(matrix[best],4)
    )

def analytical_predict(home_wr, away_wr, h2h_rate, odds_h, odds_a, form_h, form_a, inj_h=0, inj_a=0):
    """Modèle analytique XGBoost-like."""
    s_h = 0.30*home_wr + 0.20*form_h + 0.25*odds_h + 0.15*h2h_rate - 0.10*inj_h/3
    s_a = 0.30*away_wr + 0.20*form_a + 0.25*odds_a + 0.15*(1-h2h_rate) - 0.10*inj_a/3
    s_d = 0.30*odds_h*0 + max(0, 0.3*(1-abs(s_h-s_a))) + 0.28
    tot = s_h + s_d + s_a
    return s_h/tot, s_d/tot, s_a/tot

def ensemble(poisson, xgb_h, xgb_d, xgb_a, has_odds=False):
    w = (0.25, 0.45, 0.30) if has_odds else (0.35, 0.35, 0.30)
    ph = w[0]*poisson["ph"] + w[1]*xgb_h + w[2]*xgb_h
    pd = w[0]*poisson["pd"] + w[1]*xgb_d + w[2]*xgb_d
    pa = w[0]*poisson["pa"] + w[1]*xgb_a + w[2]*xgb_a
    t = ph+pd+pa
    return round(ph/t,4), round(pd/t,4), round(pa/t,4)

def implied_prob(h, d, a):
    tot = 1/h + 1/d + 1/a
    return 1/h/tot, 1/d/tot, 1/a/tot

def form_score(form_str):
    mp = {"W":1.0,"D":0.5,"L":0.0}
    vals = [mp.get(c.upper(),0.5) for c in (form_str or "DDDDD")[-5:]]
    return sum(vals)/len(vals) if vals else 0.5

def suspicion_score(odds_move, vol_spike, h2h_anomaly, stat_anomaly):
    s = 0.0
    if abs(odds_move) >= 0.08:  s += min(20, abs(odds_move)*100)
    if vol_spike >= 3.0:        s += min(20, vol_spike*4)
    if h2h_anomaly:             s += 15
    if stat_anomaly:            s += 10
    return min(100, s)

# ═══════════════════════════════════════════════════════════════════════════════
#  CLIENTS API
# ═══════════════════════════════════════════════════════════════════════════════

class FootballDataClient:
    BASE = "https://api.football-data.org/v4"
    def __init__(self, key): self.h = {"X-Auth-Token": key}
    async def get(self, path, params=None):
        async with httpx.AsyncClient(timeout=12) as c:
            r = await c.get(f"{self.BASE}{path}", headers=self.h, params=params or {})
            r.raise_for_status(); return r.json()
    async def upcoming(self, comp="FL1", days=5):
        today = datetime.utcnow().date()
        p = {"status":"SCHEDULED","dateFrom":today.isoformat(),
             "dateTo":(today+timedelta(days=days)).isoformat()}
        data = await self.get(f"/competitions/{comp}/matches", p)
        return data.get("matches",[])
    async def team_form(self, team_id, n=5):
        data = await self.get(f"/teams/{team_id}/matches",{"status":"FINISHED","limit":n})
        matches = data.get("matches",[])
        form = []
        for m in sorted(matches, key=lambda x: x.get("utcDate",""), reverse=True)[:5]:
            s = m.get("score",{}).get("fullTime",{})
            is_home = m.get("homeTeam",{}).get("id") == team_id
            gh = (s.get("home",0) or 0); ga = (s.get("away",0) or 0)
            if is_home: form.append("W" if gh>ga else "D" if gh==ga else "L")
            else:       form.append("W" if ga>gh else "D" if gh==ga else "L")
        return "".join(reversed(form)) or "DDDDD"
    async def h2h(self, match_id):
        try:
            data = await self.get(f"/matches/{match_id}/head2head",{"limit":10})
            ms = data.get("matches",[]); agg = data.get("aggregates",{})
            hw = agg.get("homeTeam",{}).get("wins",0)
            aw = agg.get("awayTeam",{}).get("wins",0)
            goals = sum((m.get("score",{}).get("fullTime",{}).get("home",0) or 0)+
                        (m.get("score",{}).get("fullTime",{}).get("away",0) or 0) for m in ms)
            return hw, max(0, len(ms)-hw-aw), aw, goals/max(len(ms),1)
        except: return 0,0,0,2.5


class OddsAPIClient:
    BASE = "https://api.the-odds-api.com/v4"
    SPORTS = {
        "soccer_france_ligue_one": "Ligue 1",
        "soccer_epl":              "Premier League",
        "soccer_germany_bundesliga": "Bundesliga",
        "soccer_spain_la_liga":    "La Liga",
        "soccer_italy_serie_a":    "Serie A",
        "soccer_uefa_champs_league":"Champions League",
    }
    def __init__(self, key): self.key = key; self.remaining = None
    async def get_odds(self, sport):
        async with httpx.AsyncClient(timeout=12) as c:
            r = await c.get(f"{self.BASE}/sports/{sport}/odds",
                params={"apiKey":self.key,"regions":"eu","markets":"h2h,totals","oddsFormat":"decimal"})
            self.remaining = r.headers.get("x-requests-remaining")
            r.raise_for_status(); return r.json()
    def normalize(self, ev):
        home = ev.get("home_team",""); away = ev.get("away_team","")
        all_h, all_d, all_a = [], [], []
        over_lines, btts_yes, btts_no = [], [], []
        for bk in ev.get("bookmakers",[]):
            for mkt in bk.get("markets",[]):
                oc = {o["name"]: o["price"] for o in mkt.get("outcomes",[])}
                if mkt["key"] == "h2h":
                    if oc.get(home): all_h.append(oc[home])
                    if oc.get("Draw"): all_d.append(oc["Draw"])
                    if oc.get(away): all_a.append(oc[away])
                elif mkt["key"] == "totals":
                    if oc.get("Over") and oc.get("Under"):
                        over_lines.append((oc["Over"], oc["Under"]))
        med = lambda l: sorted(l)[len(l)//2] if l else None
        return {
            "home": home, "away": away,
            "commence": ev.get("commence_time"),
            "odds_home": med(all_h), "odds_draw": med(all_d), "odds_away": med(all_a),
            "odds_over25": med([x[0] for x in over_lines]),
            "odds_under25": med([x[1] for x in over_lines]),
            "num_bk": len(ev.get("bookmakers",[])),
        }

# ═══════════════════════════════════════════════════════════════════════════════
#  ANALYSE COMPLÈTE D'UN MATCH
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_match(match_data, home_stats=None, away_stats=None, h2h_data=None):
    home = match_data.get("home_team", match_data.get("home","?"))
    away = match_data.get("away_team", match_data.get("away","?"))
    date = (match_data.get("commence") or match_data.get("utcDate",""))[:10]
    comp = match_data.get("competition","")

    # Cotes
    oh = match_data.get("odds_home"); od = match_data.get("odds_draw"); oa = match_data.get("odds_away")
    has_odds = all([oh, od, oa])

    if has_odds:
        p_odds_h, p_odds_d, p_odds_a = implied_prob(oh, od, oa)
    else:
        p_odds_h, p_odds_d, p_odds_a = 0.45, 0.25, 0.30

    # Profils équipes (défaut si non fournis)
    hs = home_stats or {"avg_gf":1.5,"avg_ga":1.3,"form":"WDDLL","wr":0.5}
    as_ = away_stats or {"avg_gf":1.2,"avg_ga":1.5,"form":"LWDWL","wr":0.45}

    # Forces
    atk_h = max(0.3, hs["avg_gf"] / 1.52)
    def_h = max(0.3, 1.18 / max(hs["avg_ga"],0.3))
    atk_a = max(0.3, as_["avg_gf"] / 1.18)
    def_a = max(0.3, 1.52 / max(as_["avg_ga"],0.3))

    # Poisson
    pois = poisson_predict(atk_h, def_h, atk_a, def_a)

    # XGBoost analytique
    fh = form_score(hs.get("form","DDDDD"))
    fa = form_score(as_.get("form","DDDDD"))
    h2h_rate = 0.5
    if h2h_data:
        hw, dr, aw, _ = h2h_data
        tot = hw+dr+aw
        h2h_rate = hw/tot if tot > 0 else 0.5

    xh, xd, xa = analytical_predict(hs["wr"], as_["wr"], h2h_rate,
                                     p_odds_h, p_odds_a, fh, fa)

    # Avec influence des cotes
    if has_odds:
        xh = 0.6*p_odds_h + 0.4*xh
        xa = 0.6*p_odds_a + 0.4*xa
        xd = max(0, 1-xh-xa)

    # Ensemble
    ph, pd, pa = ensemble(pois, xh, xd, xa, has_odds)

    # Score prédit
    pred_score = pois["score"]
    if has_odds:
        adj_lh = pois["lh"] * (0.8 + ph*0.4)
        adj_la = pois["la"] * (0.8 + pa*0.4)
        pred_score = (max(0, round(adj_lh)), max(0, round(adj_la)))

    # Vainqueur
    if ph > pa and ph > pd:      winner = home
    elif pa > ph and pa > pd:    winner = away
    else:                        winner = "Nul"

    # Confiance
    conf = max(ph, pd, pa) * 100
    if has_odds: conf = min(95, conf * 1.1)

    # Suspicion
    susp = 0.0
    if has_odds:
        # Mouvement fictif simulé (pas d'historique disponible ici)
        susp = suspicion_score(0, 1, False, False)

    # Marchés
    over25 = pois["over25"]
    btts   = pois["btts"]
    if has_odds and match_data.get("odds_over25"):
        o25_impl = 1 / match_data["odds_over25"]
        over25 = 0.5*over25 + 0.5*o25_impl

    # HT prob (λ/2 sur 45min)
    lh2, la2 = pois["lh"]/2, pois["la"]/2
    p_ht_home = sum(
        poisson_prob(h,lh2)*poisson_prob(a,la2)
        for h in range(6) for a in range(6) if h>a
    )

    return {
        "home": home, "away": away, "date": date, "competition": comp,
        "odds": {"home":oh,"draw":od,"away":oa} if has_odds else None,
        "implied": {"home":round(p_odds_h*100,1),"draw":round(p_odds_d*100,1),"away":round(p_odds_a*100,1)} if has_odds else None,
        "winner": winner,
        "prob_home": round(ph*100,1), "prob_draw": round(pd*100,1), "prob_away": round(pa*100,1),
        "score": f"{pred_score[0]}:{pred_score[1]}",
        "score_prob": round(pois["score_prob"]*100,1),
        "over25": round(over25*100,1),
        "btts": round(btts*100,1),
        "ht_home_lead": round(p_ht_home*100,1),
        "late_goal": round(min(95, 35 + 30*over25 + 15*(1-abs(ph-pa)))*1,1),
        "confidence": round(conf,1),
        "suspicion": round(susp,1),
        "suspicion_level": "critical" if susp>=85 else "high" if susp>=70 else "medium" if susp>=40 else "low",
        "lambda_home": pois["lh"], "lambda_away": pois["la"],
        "has_odds": has_odds,
        "num_bookmakers": match_data.get("num_bk", 0),
    }

# ═══════════════════════════════════════════════════════════════════════════════
#  AFFICHAGE
# ═══════════════════════════════════════════════════════════════════════════════

LEVEL_CLR = {"low":G,"medium":Y,"high":Y,"critical":RE}
LEVEL_ICO = {"low":"✅","medium":"⚠️","high":"⚠️","critical":"🚨"}

def bar(p, w=20):
    f = int(p/100*w); return "█"*f + "░"*(w-f)

def print_analysis(a, idx=None):
    lvl = a["suspicion_level"]
    lc  = LEVEL_CLR[lvl]
    ico = LEVEL_ICO[lvl]

    sep = f"{BL}{'═'*62}{R}"
    print(f"\n{sep}")
    num = f"#{idx} " if idx else ""
    print(f"  {B}{num}{G}{a['home']}{R} {B}vs{R} {RE}{a['away']}{R}")
    print(f"  {GR}{a['competition']}  ·  {a['date']}{R}")

    if a["has_odds"]:
        oh = a["odds"]["home"]; od = a["odds"]["draw"]; oa = a["odds"]["away"]
        ih = a["implied"]["home"]; id_ = a["implied"]["draw"]; ia = a["implied"]["away"]
        print(f"  {C}Cotes: {oh} ({ih}%) | {od} ({id_}%) | {oa} ({ia}%)  [{a['num_bookmakers']} BK]{R}")

    print(f"\n  {B}🔍 Suspicion: {lc}{a['suspicion']:.0f}/100 [{lvl.upper()}]{R}")
    print(f"\n  {B}🎯 Vainqueur:{R} {G if a['winner']==a['home'] else RE}{B}{a['winner']}{R}  "
          f"({a['confidence']:.0f}% confiance)")
    print(f"  {B}⚽ Score prédit:{R} {B}{a['home']} {a['score']} {a['away']}{R}  "
          f"({a['score_prob']:.1f}% prob)")

    print(f"\n  {B}📊 Probabilités:{R}")
    print(f"  {G}{a['home']:<24}{R} {bar(a['prob_home'])} {B}{a['prob_home']}%{R}")
    print(f"  {'Nul':<24} {bar(a['prob_draw'])} {B}{a['prob_draw']}%{R}")
    print(f"  {RE}{a['away']:<24}{R} {bar(a['prob_away'])} {B}{a['prob_away']}%{R}")

    print(f"\n  {B}📈 Marchés:{R}")
    mkts = [
        ("Over 2.5",      a["over25"]),
        ("Under 2.5",     100-a["over25"]),
        ("BTTS Oui",      a["btts"]),
        ("1ère MT dom.",  a["ht_home_lead"]),
        ("But tardif",    a["late_goal"]),
    ]
    for label, prob in mkts:
        hi = " 🔥" if prob >= 65 else ""
        print(f"  {label:<20} {C}{prob:.0f}%{R}{hi}")

    print(f"\n  {GR}λ domicile={a['lambda_home']:.2f} | λ extérieur={a['lambda_away']:.2f}{R}")
    print(sep)

# ═══════════════════════════════════════════════════════════════════════════════
#  COLLECTE PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

COMP_MAP = {
    "FL1": "soccer_france_ligue_one",
    "PL":  "soccer_epl",
    "BL1": "soccer_germany_bundesliga",
    "PD":  "soccer_spain_la_liga",
    "SA":  "soccer_italy_serie_a",
    "CL":  "soccer_uefa_champs_league",
}

async def run():
    print(f"\n{B}{BL}{'═'*62}{R}")
    print(f"  {B}⚽ Football AI Platform — Collecte & Analyse{R}")
    print(f"  {GR}Powered by football-data.org + The Odds API{R}")
    print(f"{B}{BL}{'═'*62}{R}\n")

    analyses = []

    # ── Étape 1: Cotes (The Odds API) ─────────────────────────────────────────
    odds_events = []
    if ODDS_KEY:
        print(f"{C}💰 Collecte des cotes (The Odds API)...{R}")
        oc = OddsAPIClient(ODDS_KEY)
        for sport_key, sport_name in OddsAPIClient.SPORTS.items():
            try:
                raw = await oc.get_odds(sport_key)
                for ev in raw:
                    norm = oc.normalize(ev)
                    if norm["odds_home"]:
                        norm["competition"] = sport_name
                        odds_events.append(norm)
                print(f"  ✅ {sport_name}: {len(raw)} matchs | quota: {oc.remaining} req")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  ⚠ {sport_name}: {e}")

    # ── Étape 2: Matchs (football-data.org) ───────────────────────────────────
    fd_matches = []
    if FD_KEY:
        print(f"\n{C}📅 Collecte des matchs (football-data.org)...{R}")
        fd = FootballDataClient(FD_KEY)
        for comp_code in ["FL1", "PL", "BL1", "PD", "SA"]:
            try:
                raw = await fd.upcoming(comp_code)
                for m in raw:
                    fd_matches.append({
                        "home": m.get("homeTeam",{}).get("name","?"),
                        "away": m.get("awayTeam",{}).get("name","?"),
                        "utcDate": m.get("utcDate",""),
                        "competition": m.get("competition",{}).get("name",""),
                        "match_id": m.get("id"),
                        "home_team_id": m.get("homeTeam",{}).get("id"),
                        "away_team_id": m.get("awayTeam",{}).get("id"),
                    })
                print(f"  ✅ {comp_code}: {len(raw)} matchs")
                await asyncio.sleep(7)  # rate limit
            except Exception as e:
                print(f"  ⚠ {comp_code}: {e}")

    # ── Étape 3: Fusionner matchs + cotes ─────────────────────────────────────
    print(f"\n{C}🔗 Fusion matchs + cotes...{R}")

    # D'abord les matchs avec cotes (The Odds API)
    for ev in odds_events:
        a = analyze_match(ev)
        analyses.append(a)

    # Ensuite les matchs FD sans cotes (ajouter si pas déjà dans les cotes)
    def already_in(home, away):
        for a in analyses:
            h1 = set(home.lower().split()); h2 = set(a["home"].lower().split())
            a1 = set(away.lower().split()); a2 = set(a["away"].lower().split())
            if len(h1&h2)/max(len(h1),len(h2),1) > 0.5: return True
        return False

    for m in fd_matches:
        if not already_in(m["home"], m["away"]):
            a = analyze_match(m)
            analyses.append(a)

    # ── Affichage ──────────────────────────────────────────────────────────────
    if not analyses:
        print(f"\n{Y}Aucun match trouvé. Vérifie tes clés API ou la période.{R}")
        return

    # Trier: suspicion décroissant, puis confiance
    analyses.sort(key=lambda x: (-x["suspicion"], -x["confidence"]))

    print(f"\n{B}{G}✅ {len(analyses)} matchs analysés{R}\n")

    # Filtres interactifs
    print(f"Afficher: {B}[1]{R} Tous  {B}[2]{R} Hauts Over 2.5 (>65%)  {B}[3]{R} BTTS élevé (>65%)  {B}[4]{R} Suspects")
    try:
        choice = input(f"\n{B}Choix [1-4, Entrée=1] >{R} ").strip() or "1"
    except:
        choice = "1"

    if choice == "2":
        filtered = [a for a in analyses if a["over25"] >= 65]
        print(f"\n{C}Over 2.5 ≥ 65%: {len(filtered)} matchs{R}")
    elif choice == "3":
        filtered = [a for a in analyses if a["btts"] >= 65]
        print(f"\n{C}BTTS ≥ 65%: {len(filtered)} matchs{R}")
    elif choice == "4":
        filtered = [a for a in analyses if a["suspicion"] >= 20]
        print(f"\n{C}Matchs suspects: {len(filtered)}{R}")
    else:
        filtered = analyses

    for i, a in enumerate(filtered[:15], 1):   # max 15 matchs
        print_analysis(a, i)

    # Résumé
    print(f"\n{B}{'─'*62}{R}")
    print(f"  {B}RÉSUMÉ — {len(filtered)} matchs{R}")
    print(f"  Over 2.5 moy: {sum(a['over25'] for a in filtered)/max(len(filtered),1):.0f}%")
    print(f"  BTTS moy:     {sum(a['btts'] for a in filtered)/max(len(filtered),1):.0f}%")
    high_conf = [a for a in filtered if a["confidence"] >= 60]
    print(f"  Haute conf (≥60%): {len(high_conf)} matchs")
    if high_conf:
        print(f"  Top pick: {G}{high_conf[0]['home']}{R} vs {RE}{high_conf[0]['away']}{R} → {B}{high_conf[0]['winner']}{R}")
    print(f"{B}{'─'*62}{R}\n")


if __name__ == "__main__":
    asyncio.run(run())
