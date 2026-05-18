#!/usr/bin/env python3
"""
FC25 PENALTY EXPERT v5.0 — Moteur IA Bayésien
Basé sur 629+ vrais matchs FC25 1xbet observés.

VÉRITÉ SUR FC25 1XBET:
- Résultats générés par RNG avec ratings d'équipes FIXES (côté serveur)
- Format: 5 tirs par équipe, mort subite si égalité
- Les cotes bookmaker = meilleur signal disponible (elles encodent les vraies proba)
- Chaque match est INDÉPENDANT → pas de dynamique Elo

AMÉLIORATIONS v5.0:
  - Modèle Bayésien Beta-Binomial pour estimer p_tir
  - Calibration p_tir depuis les cotes (bisection analytique)
  - Détection de séries/momentum (streak factor)
  - Monte Carlo vectorisé NumPy (200k simulations)
  - Test de runs Wald-Wolfowitz (détection patterns RNG)
  - Expected Value bookmaker
  - Score de confiance multi-facteurs

MODÈLE:
  Si cotes disponibles: 55% calibration-cotes + 25% Bayésien + 15% H2H + 5% streak
  Sans cotes:           35% Bayésien + 35% H2H + 25% MC-tir + 5% streak
  Simulation: Binomial(5, p_shot_calibré) + mort subite
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
    # #N10–#N18
    ("Juventus",4,"Liverpool",5),("Barcelona",4,"Liverpool",5),
    ("Juventus",4,"Inter Miami",2),("PSG",5,"Arsenal",4),
    ("Barcelona",8,"Man City",7),("Barcelona",5,"Man City",6),
    ("Juventus",4,"PSG",3),("PSG",5,"Barcelona",4),
    ("Real Madrid",5,"Liverpool",3),
    # #N19–#N118
    ("Bayern Munich",2,"Barcelona",3),("PSG",11,"Liverpool",10),
    ("PSG",4,"Inter Miami",3),("Barcelona",2,"Man City",3),
    ("Barcelona",2,"Al Nassr",4),("Arsenal",4,"Man City",1),
    ("Barcelona",12,"Al Nassr",11),("Juventus",5,"PSG",6),
    ("Inter Miami",4,"Barcelona",5),("Inter Miami",4,"PSG",5),
    ("PSG",4,"Inter Miami",3),("Juventus",2,"Bayern Munich",4),
    ("Arsenal",17,"Real Madrid",16),("Barcelona",5,"Liverpool",3),
    ("Barcelona",12,"Al Nassr",11),("Man City",3,"Juventus",4),
    ("Barcelona",3,"Al Nassr",4),("Juventus",9,"Inter Miami",8),
    ("Juventus",4,"Bayern Munich",3),("Liverpool",4,"Man City",5),
    ("Inter Miami",0,"PSG",3),("Juventus",9,"PSG",8),
    ("PSG",9,"Juventus",8),("Barcelona",3,"Al Nassr",4),
    ("Inter Miami",5,"PSG",6),("PSG",3,"Inter Miami",4),
    ("Liverpool",4,"Man City",3),("Barcelona",5,"Liverpool",3),
    ("Juventus",5,"PSG",3),("Inter Miami",4,"Barcelona",5),
    ("Real Madrid",4,"Liverpool",3),("Inter Miami",2,"Barcelona",3),
    ("PSG",5,"Arsenal",4),("Barcelona",6,"Liverpool",5),
    ("Arsenal",2,"Real Madrid",4),("Juventus",5,"PSG",3),
    ("Juventus",5,"Inter Miami",3),("Inter Miami",4,"PSG",2),
    ("Inter Miami",3,"Barcelona",4),("Barcelona",5,"Man City",3),
    ("Barcelona",3,"Al Nassr",4),("Juventus",6,"Inter Miami",5),
    ("Inter Miami",6,"PSG",5),("Juventus",3,"PSG",4),
    ("PSG",5,"Arsenal",3),("Bayern Munich",8,"Barcelona",7),
    ("Juventus",3,"PSG",4),("PSG",2,"Inter Miami",4),
    ("Arsenal",3,"Man City",2),("Inter Miami",4,"PSG",2),
    ("Barcelona",4,"Arsenal",5),("Arsenal",2,"Real Madrid",4),
    ("PSG",5,"Juventus",3),("Man City",3,"Barcelona",4),
    ("Real Madrid",3,"Liverpool",4),("Barcelona",3,"Al Nassr",1),
    ("Barcelona",3,"Arsenal",4),("Barcelona",5,"Arsenal",4),
    ("Juventus",4,"PSG",5),("Barcelona",4,"Al Nassr",5),
    ("Barcelona",10,"Arsenal",9),("Real Madrid",4,"Inter Miami",1),
    ("Real Madrid",2,"PSG",4),("PSG",3,"Barcelona",4),
    ("Barcelona",3,"Man City",4),("Juventus",6,"PSG",7),
    ("PSG",5,"Inter Miami",3),("Barcelona",5,"PSG",3),
    ("Inter Miami",5,"Barcelona",3),("Barcelona",4,"Liverpool",5),
    ("Liverpool",11,"Man City",10),("PSG",3,"Bayern Munich",4),
    ("Real Madrid",3,"PSG",4),("Juventus",3,"Inter Miami",4),
    ("Barcelona",5,"Liverpool",3),("Man City",6,"Juventus",7),
    ("Barcelona",4,"Liverpool",2),("Barcelona",4,"Liverpool",1),
    ("Barcelona",2,"Al Nassr",4),("PSG",4,"Juventus",2),
    ("PSG",4,"Inter Miami",3),("Juventus",7,"Liverpool",6),
    ("Liverpool",11,"Man City",10),("Barcelona",5,"Al Nassr",3),
    ("PSG",2,"Inter Miami",1),("Inter Miami",5,"Barcelona",3),
    ("Juventus",4,"Inter Miami",5),("Juventus",7,"Liverpool",6),
    ("PSG",2,"Inter Miami",1),("Arsenal",11,"Real Madrid",12),
    ("PSG",5,"Inter Miami",3),("Inter Miami",12,"Barcelona",13),
    ("Inter Miami",3,"PSG",4),("Juventus",3,"PSG",4),
    ("Arsenal",6,"Real Madrid",5),("Barcelona",4,"Liverpool",1),
    ("Barcelona",5,"Liverpool",3),("Barcelona",5,"Al Nassr",3),
    ("Barcelona",9,"Man City",8),("Juventus",4,"Bayern Munich",5),
    # #N119–#N151
    ("Inter Miami",4,"PSG",1),("Barcelona",4,"Arsenal",1),
    ("Real Madrid",5,"Barcelona",4),("Barcelona",5,"Arsenal",6),
    ("Barcelona",8,"Man City",9),("Real Madrid",4,"Inter Miami",1),
    ("Barcelona",5,"Liverpool",3),("Real Madrid",2,"Inter Miami",4),
    ("Barcelona",5,"Al Nassr",3),("Barcelona",5,"Liverpool",4),
    ("PSG",3,"Bayern Munich",1),("PSG",2,"Bayern Munich",4),
    ("Real Madrid",10,"PSG",9),("Barcelona",5,"Liverpool",4),
    ("Barcelona",6,"Al Nassr",5),("Inter Miami",4,"Barcelona",1),
    ("Barcelona",8,"Man City",9),("Barcelona",2,"Liverpool",4),
    ("Barcelona",5,"Arsenal",6),("Real Madrid",5,"Barcelona",6),
    ("Bayern Munich",4,"Barcelona",5),("Juventus",4,"PSG",2),
    ("Inter Miami",3,"Real Madrid",2),("Inter Miami",6,"Barcelona",7),
    ("Barcelona",6,"Al Nassr",5),("Barcelona",4,"Al Nassr",1),
    ("Barcelona",3,"Liverpool",4),("Real Madrid",6,"Inter Miami",7),
    ("Real Madrid",9,"Inter Miami",8),("PSG",4,"Liverpool",2),
    ("Barcelona",4,"Arsenal",5),("Barcelona",4,"Al Nassr",1),
    ("Juventus",1,"Inter Miami",3),
    # #N152–#N251
    ("Barcelona",5,"Arsenal",3),("Barcelona",6,"Al Nassr",7),
    ("Inter Miami",4,"Juventus",5),("Barcelona",4,"Man City",1),
    ("PSG",3,"Juventus",1),("Liverpool",4,"Man City",2),
    ("PSG",7,"Barcelona",6),("Barcelona",4,"Al Nassr",2),
    ("Juventus",1,"PSG",3),("Juventus",5,"PSG",3),
    ("Bayern Munich",3,"Inter Miami",4),("Juventus",4,"PSG",5),
    ("PSG",6,"Inter Miami",7),("PSG",4,"Inter Miami",5),
    ("Real Madrid",3,"Bayern Munich",4),("Liverpool",8,"Man City",9),
    ("Barcelona",4,"Al Nassr",5),("Barcelona",4,"Al Nassr",5),
    ("Barcelona",5,"Al Nassr",3),("Juventus",4,"Bayern Munich",5),
    ("PSG",4,"Arsenal",1),("PSG",4,"Bayern Munich",2),
    ("Liverpool",8,"Man City",9),("Real Madrid",9,"Barcelona",8),
    ("Juventus",5,"Liverpool",4),("Barcelona",5,"Al Nassr",4),
    ("Juventus",2,"Inter Miami",4),("Liverpool",4,"Man City",2),
    ("Real Madrid",6,"Liverpool",7),("Real Madrid",1,"Inter Miami",3),
    ("Arsenal",4,"Man City",5),("Bayern Munich",4,"Barcelona",1),
    ("PSG",3,"Liverpool",4),("Man City",3,"Barcelona",2),
    ("PSG",4,"Inter Miami",2),("PSG",4,"Arsenal",1),
    ("Inter Miami",6,"PSG",5),("Real Madrid",4,"PSG",5),
    ("PSG",4,"Juventus",5),("Bayern Munich",1,"Inter Miami",3),
    ("PSG",4,"Bayern Munich",2),("Man City",6,"Juventus",5),
    ("Bayern Munich",3,"Barcelona",4),("Inter Miami",6,"Barcelona",7),
    ("PSG",4,"Barcelona",1),("Man City",6,"Juventus",5),
    ("Juventus",5,"Bayern Munich",4),("Real Madrid",5,"Inter Miami",4),
    ("Barcelona",3,"Liverpool",4),("Barcelona",5,"Liverpool",3),
    ("Barcelona",5,"Al Nassr",4),("Arsenal",1,"Man City",3),
    ("Man City",1,"Barcelona",3),("PSG",3,"Juventus",4),
    ("Juventus",2,"Bayern Munich",4),("Arsenal",5,"Real Madrid",4),
    ("Barcelona",5,"Al Nassr",4),("Real Madrid",5,"PSG",4),
    ("Arsenal",5,"Real Madrid",4),("Barcelona",1,"Liverpool",3),
    ("Juventus",9,"Liverpool",8),("Man City",5,"Juventus",6),
    ("Inter Miami",5,"Barcelona",3),("Barcelona",4,"Al Nassr",1),
    ("Arsenal",3,"Real Madrid",4),("Man City",3,"Juventus",1),
    ("Juventus",2,"Inter Miami",4),("Inter Miami",4,"PSG",3),
    ("Barcelona",4,"Al Nassr",2),("Real Madrid",9,"Barcelona",8),
    ("Barcelona",4,"Liverpool",1),("Juventus",4,"PSG",5),
    ("Arsenal",4,"Real Madrid",5),("PSG",4,"Arsenal",2),
    ("Barcelona",4,"Al Nassr",2),("Inter Miami",4,"PSG",2),
    ("PSG",5,"Barcelona",4),("Inter Miami",3,"PSG",4),
    ("Juventus",5,"Inter Miami",3),("Barcelona",1,"Man City",3),
    ("Inter Miami",5,"Barcelona",3),("Real Madrid",5,"PSG",3),
    ("PSG",4,"Juventus",5),("Juventus",5,"Inter Miami",3),
    ("Barcelona",3,"Al Nassr",4),("PSG",5,"Liverpool",3),
    ("PSG",5,"Barcelona",3),("Arsenal",4,"Real Madrid",5),
    ("Real Madrid",5,"PSG",6),("Bayern Munich",4,"Barcelona",1),
    ("Barcelona",2,"Arsenal",4),("Real Madrid",4,"Bayern Munich",5),
    ("PSG",1,"Juventus",3),("Barcelona",3,"Liverpool",4),
    ("Barcelona",4,"Al Nassr",3),("PSG",4,"Inter Miami",5),
    ("Real Madrid",1,"Barcelona",3),("Real Madrid",2,"PSG",3),
    ("Juventus",5,"Bayern Munich",6),("Barcelona",4,"Man City",5),
    # #N252–#N288
    ("PSG",5,"Liverpool",3),("PSG",7,"Barcelona",6),
    ("Juventus",3,"Inter Miami",4),("Juventus",5,"Inter Miami",6),
    ("Inter Miami",4,"Juventus",5),("Man City",3,"Juventus",1),
    ("Inter Miami",6,"Real Madrid",5),("PSG",2,"Arsenal",3),
    ("Arsenal",3,"Man City",4),("PSG",4,"Barcelona",5),
    ("Bayern Munich",4,"Barcelona",1),("Juventus",3,"Inter Miami",4),
    ("PSG",9,"Inter Miami",8),("Juventus",1,"PSG",3),
    ("Juventus",5,"Inter Miami",3),("Juventus",5,"PSG",4),
    ("Real Madrid",4,"PSG",5),("Barcelona",4,"Man City",5),
    ("Liverpool",3,"Man City",2),("Barcelona",3,"Al Nassr",4),
    ("Inter Miami",4,"Barcelona",1),("Barcelona",7,"Al Nassr",6),
    ("Inter Miami",4,"Barcelona",5),("Barcelona",3,"Liverpool",4),
    ("Barcelona",5,"Man City",4),("Juventus",5,"Bayern Munich",4),
    ("Barcelona",2,"Arsenal",4),("Real Madrid",5,"Barcelona",6),
    ("Barcelona",5,"Al Nassr",3),("Barcelona",6,"Man City",5),
    ("Liverpool",6,"Man City",5),("Barcelona",5,"Al Nassr",3),
    ("Arsenal",13,"Man City",14),("PSG",2,"Bayern Munich",4),
    ("Real Madrid",5,"Barcelona",3),("PSG",5,"Juventus",3),
    ("PSG",2,"Bayern Munich",4),
    # #N1–#N63 (nouvelle série)
    ("Juventus",0,"Bayern Munich",3),("Barcelona",2,"Liverpool",4),
    ("PSG",2,"Arsenal",3),("PSG",4,"Barcelona",5),
    ("Inter Miami",1,"Barcelona",3),("Man City",4,"Juventus",2),
    ("Barcelona",5,"Liverpool",3),("Man City",5,"Juventus",6),
    ("Real Madrid",5,"PSG",3),("Barcelona",3,"Arsenal",1),
    ("Barcelona",3,"Arsenal",1),("Real Madrid",5,"Barcelona",4),
    ("PSG",4,"Barcelona",5),("Inter Miami",2,"PSG",4),
    ("Inter Miami",4,"Barcelona",5),("Juventus",2,"Liverpool",4),
    ("Arsenal",5,"Real Madrid",6),("Barcelona",3,"Al Nassr",1),
    ("Arsenal",5,"Man City",3),("Barcelona",3,"Arsenal",4),
    ("Barcelona",3,"Liverpool",4),("Real Madrid",5,"Barcelona",4),
    ("Barcelona",4,"Al Nassr",2),("Inter Miami",7,"PSG",6),
    ("Real Madrid",4,"Barcelona",5),("Man City",5,"Juventus",3),
    ("PSG",4,"Barcelona",5),("PSG",5,"Juventus",3),
    ("PSG",5,"Arsenal",6),("Juventus",14,"Liverpool",13),
    ("Barcelona",5,"Al Nassr",3),("Inter Miami",3,"PSG",4),
    ("Man City",4,"Barcelona",3),("Inter Miami",3,"Real Madrid",4),
    ("Juventus",8,"PSG",9),("Barcelona",4,"Arsenal",3),
    ("PSG",8,"Juventus",9),("Barcelona",5,"Liverpool",3),
    ("Barcelona",5,"Man City",3),("Inter Miami",8,"PSG",7),
    ("Barcelona",0,"Al Nassr",3),("Barcelona",0,"Al Nassr",3),
    ("Inter Miami",6,"Juventus",5),("Barcelona",2,"Arsenal",4),
    ("PSG",4,"Juventus",3),("Barcelona",6,"Al Nassr",7),
    ("Man City",5,"Arsenal",3),("Arsenal",3,"Real Madrid",4),
    ("PSG",5,"Bayern Munich",4),("Arsenal",3,"Real Madrid",4),
    ("PSG",5,"Inter Miami",3),("Arsenal",4,"Man City",5),
    ("Juventus",4,"PSG",5),("PSG",4,"Inter Miami",5),
    ("Barcelona",2,"Arsenal",4),("Barcelona",5,"Liverpool",3),
    ("Juventus",4,"Inter Miami",5),("Juventus",2,"PSG",4),
    ("Barcelona",4,"Al Nassr",2),("Barcelona",4,"Liverpool",5),
    ("Juventus",4,"Bayern Munich",1),("Real Madrid",4,"Barcelona",5),
    ("Real Madrid",4,"Barcelona",5),
    # #N64–#N140
    ("Barcelona",5,"Liverpool",3),("Real Madrid",4,"Barcelona",3),
    ("Man City",1,"Arsenal",3),("Juventus",2,"PSG",3),
    ("Man City",5,"Barcelona",3),("Barcelona",4,"Al Nassr",2),
    ("PSG",5,"Inter Miami",3),("Inter Miami",5,"PSG",3),
    ("Barcelona",7,"Man City",6),("Barcelona",5,"Liverpool",3),
    ("Barcelona",5,"Al Nassr",4),("Juventus",8,"PSG",9),
    ("Real Madrid",6,"Barcelona",5),("Man City",3,"Juventus",4),
    ("PSG",4,"Barcelona",5),("PSG",5,"Inter Miami",3),
    ("Barcelona",3,"Al Nassr",4),("Man City",7,"Barcelona",6),
    ("Inter Miami",5,"PSG",6),("PSG",4,"Inter Miami",3),
    ("Real Madrid",4,"Inter Miami",2),("Barcelona",5,"Al Nassr",3),
    ("Barcelona",3,"Al Nassr",4),("PSG",3,"Bayern Munich",2),
    ("Bayern Munich",3,"Inter Miami",4),("Juventus",7,"PSG",6),
    ("Barcelona",5,"Arsenal",4),("Juventus",7,"PSG",6),
    ("Inter Miami",5,"PSG",4),("Juventus",5,"Inter Miami",3),
    ("PSG",4,"Arsenal",5),("PSG",8,"Bayern Munich",7),
    ("Juventus",5,"Liverpool",3),("Barcelona",5,"Al Nassr",3),
    ("Liverpool",5,"Man City",3),("Juventus",9,"PSG",8),
    ("Barcelona",2,"Arsenal",3),("Liverpool",5,"Man City",3),
    ("Barcelona",4,"PSG",5),("Barcelona",4,"Al Nassr",5),
    ("Barcelona",3,"Man City",1),("Arsenal",1,"Man City",3),
    ("Inter Miami",4,"Barcelona",1),("Barcelona",4,"Man City",5),
    ("Barcelona",5,"Al Nassr",6),("Barcelona",6,"Liverpool",5),
    ("Real Madrid",3,"Barcelona",2),("Real Madrid",4,"Inter Miami",1),
    ("PSG",4,"Inter Miami",5),("PSG",4,"Juventus",3),
    ("Juventus",5,"Liverpool",3),("Real Madrid",3,"Barcelona",2),
    ("PSG",3,"Barcelona",4),("Arsenal",4,"Man City",5),
    ("Barcelona",2,"Al Nassr",4),("Real Madrid",4,"Inter Miami",1),
    ("Real Madrid",4,"Inter Miami",2),("Barcelona",3,"Arsenal",4),
    ("Barcelona",4,"Al Nassr",3),("Bayern Munich",4,"Inter Miami",2),
    ("PSG",5,"Juventus",4),("Barcelona",2,"Liverpool",4),
    ("Juventus",4,"Inter Miami",5),("Juventus",4,"Inter Miami",5),
    ("Man City",6,"Barcelona",7),("Man City",5,"Juventus",3),
    ("Barcelona",4,"Arsenal",5),("Barcelona",5,"Arsenal",4),
    ("Juventus",1,"Inter Miami",3),("Barcelona",2,"Liverpool",4),
    ("Real Madrid",4,"Inter Miami",5),("Barcelona",4,"Liverpool",5),
    ("Inter Miami",4,"Juventus",2),("Barcelona",5,"Man City",3),
    ("PSG",5,"Inter Miami",3),("Barcelona",3,"PSG",4),
    # #N141–#N152
    ("Arsenal",4,"Man City",5),("Arsenal",9,"Real Madrid",10),
    ("Real Madrid",1,"Inter Miami",3),("Liverpool",8,"Man City",7),
    ("Real Madrid",4,"Inter Miami",2),("Juventus",4,"PSG",3),
    ("Juventus",4,"PSG",2),("PSG",4,"Juventus",2),
    ("PSG",2,"Inter Miami",1),("Man City",4,"Arsenal",1),
    ("Barcelona",5,"Al Nassr",4),("Juventus",4,"Liverpool",5),
]

TEAMS = ["PSG","Barcelona","Arsenal","Real Madrid","Man City",
         "Juventus","Bayern Munich","Liverpool","Inter Miami","Al Nassr"]


# ══════════════════════════════════════════════════════════════════════════════
#  STATS & MODÈLES v5.0
# ══════════════════════════════════════════════════════════════════════════════

def build_stats():
    """Construit les stats avec p_tir Bayésien Beta-Binomial."""
    gf = defaultdict(list); ga = defaultdict(list)
    wins = defaultdict(int); shots_taken = defaultdict(int)
    h2h  = defaultdict(lambda: {"W":0,"L":0})

    for a, sa, b, sb in ALL_MATCHES:
        gf[a].append(sa); ga[a].append(sb)
        gf[b].append(sb); ga[b].append(sa)
        shots_taken[a] += 5; shots_taken[b] += 5
        if sa > sb:
            wins[a] += 1
            h2h[(a,b)]["W"] += 1; h2h[(b,a)]["L"] += 1
        else:
            wins[b] += 1
            h2h[(b,a)]["W"] += 1; h2h[(a,b)]["L"] += 1

    stats = {}
    for t in set(list(gf.keys()) + list(ga.keys())):
        n = len(gf[t])
        total_goals = sum(gf[t])
        total_shots = shots_taken[t]
        avg = total_goals / n if n else 4.25

        # ── Bayésien Beta-Binomial ────────────────────────────────────────
        # Prior: Beta(8, 3) → centré sur 0.727 (taux pénalty réel FIFA)
        alpha_prior, beta_prior = 8.0, 3.0
        alpha_post = alpha_prior + total_goals
        beta_post  = beta_prior  + (total_shots - total_goals)
        p_bayes    = alpha_post / (alpha_post + beta_post)

        # Intervalle de crédibilité 90% (approximation normale)
        n_eff = alpha_post + beta_post
        ci_half = 1.645 * math.sqrt(p_bayes * (1-p_bayes) / n_eff)

        stats[t] = {
            "games":    n,
            "win_rate": wins[t]/n if n else 0.5,
            "avg_gf":   round(avg, 3),
            "p_shot":   round(min(0.97, max(0.55, p_bayes)), 4),
            "p_shot_ci": (round(max(0.50, p_bayes - ci_half), 4),
                          round(min(0.97, p_bayes + ci_half), 4)),
            "total_goals": total_goals,
            "total_shots": total_shots,
        }
    return stats, h2h


# ── Probabilité analytique de victoire (Binomial + mort subite) ──────────────

def binomial_win_prob(p_h: float, p_a: float) -> float:
    """
    Calcule P(H gagne) analytiquement via Binomial(5) + mort subite.
    Beaucoup plus rapide qu'une simulation Monte Carlo.
    """
    win_h = 0.0
    p_tie_total = 0.0

    for h in range(6):
        bh = comb(5, h) * p_h**h * (1-p_h)**(5-h)
        for a in range(6):
            ba = comb(5, a) * p_a**a * (1-p_a)**(5-a)
            if h > a:
                win_h += bh * ba
            elif h == a:
                p_tie_total += bh * ba

    # P(H gagne mort subite | égalité)
    denom = p_h*(1-p_a) + p_a*(1-p_h)
    p_sd_h = p_h*(1-p_a) / denom if denom > 1e-9 else 0.5

    return win_h + p_tie_total * p_sd_h


# ── Calibration p_tir depuis les cotes (bisection) ───────────────────────────

def calibrate_p_shot_from_odds(target_win_h: float, target_win_a: float,
                                 base_avg: float = 0.72) -> tuple:
    """
    Inverse le modèle Binomial: trouve (p_h, p_a) tels que
    binomial_win_prob(p_h, p_a) ≈ target_win_h.

    Utilise une bisection sur δ = p_h - p_a avec p_moy fixe.
    """
    p_avg = base_avg

    # Bisection sur l'écart δ
    lo, hi = -0.28, 0.28
    for _ in range(50):
        delta = (lo + hi) / 2
        ph = min(0.97, max(0.52, p_avg + delta * 0.65))
        pa = min(0.97, max(0.52, p_avg - delta * 0.35))
        win = binomial_win_prob(ph, pa)
        if win < target_win_h:
            lo = delta
        else:
            hi = delta
        if (hi - lo) < 0.0005:
            break

    return round(ph, 4), round(pa, 4)


# ── Implied prob depuis les cotes ─────────────────────────────────────────────

def implied_prob(odds_v1: float, odds_v2: float) -> tuple:
    """Normalise les cotes 1xbet → vraie probabilité (retire la marge)."""
    raw_a = 1 / odds_v1
    raw_b = 1 / odds_v2
    total = raw_a + raw_b
    return raw_a / total, raw_b / total


# ── Streak / momentum des derniers matchs ────────────────────────────────────

def streak_factor(team: str, n: int = 12) -> tuple:
    """
    Calcule le facteur momentum sur les n derniers matchs.
    Retourne (delta_prob, liste_résultats, longueur_série_actuelle).
    """
    recent = []
    for a, sa, b, sb in reversed(ALL_MATCHES):
        if a == team or b == team:
            win = (sa > sb and a == team) or (sb > sa and b == team)
            recent.append(1 if win else 0)
            if len(recent) >= n:
                break

    if len(recent) < 4:
        return 0.0, recent, 0

    # Poids exponentiels décroissants (matchs récents = plus importants)
    weights = [0.75**i for i in range(len(recent))]
    weighted_wr = sum(r*w for r,w in zip(recent, weights)) / sum(weights)

    # Longueur et direction de la série actuelle
    streak_len = 1
    direction = recent[0]
    for r in recent[1:]:
        if r == direction:
            streak_len += 1
        else:
            break

    # Delta: écart à 0.5 × facteur d'amplitude
    base_delta = (weighted_wr - 0.5) * 0.10
    streak_bonus = max(-0.04, min(0.04, (streak_len - 2) * 0.007 * (1 if direction else -1)))
    total_delta = max(-0.07, min(0.07, base_delta + streak_bonus))

    return round(total_delta, 4), recent, streak_len * (1 if direction else -1)


# ── Test de runs Wald-Wolfowitz ───────────────────────────────────────────────

def runs_test(team: str, n: int = 40) -> dict | None:
    """
    Détecte si la séquence W/L est aléatoire (H0) ou présente des patterns.
    p_value > 0.05 → séquence normale (i.i.d.)
    """
    results = []
    for a, sa, b, sb in reversed(ALL_MATCHES):
        if a == team or b == team:
            win = (sa > sb and a == team) or (sb > sa and b == team)
            results.append(1 if win else 0)
            if len(results) >= n:
                break

    results = list(reversed(results))
    m = len(results)
    if m < 10:
        return None

    n1 = sum(results)
    n0 = m - n1
    if n0 == 0 or n1 == 0:
        return None

    runs = 1 + sum(1 for i in range(1, m) if results[i] != results[i-1])

    mu    = 2*n1*n0/m + 1
    denom = m**2 * (m-1)
    sigma = math.sqrt(2*n1*n0*(2*n1*n0-m) / denom) if denom > 0 else 1.0

    z = (runs - mu) / sigma if sigma > 1e-9 else 0.0
    # p-value via erf (sans scipy)
    p_val = 2 * (1 - 0.5*(1 + math.erf(abs(z)/math.sqrt(2))))

    return {
        "z":         round(z, 2),
        "p_value":   round(p_val, 4),
        "is_random": p_val > 0.05,
        "pattern":   "Alternance forcée" if z > 2.0 else
                     "Séries longues"    if z < -2.0 else
                     "Aléatoire ✓",
    }


# ── Expected Value bookmaker ──────────────────────────────────────────────────

def compute_ev(odds: float, true_prob: float) -> float:
    """EV pour 1 unité misée à ces cotes avec cette vraie probabilité."""
    return round(true_prob * (odds - 1) - (1 - true_prob), 4)


# ── Monte Carlo vectorisé (NumPy si disponible) ───────────────────────────────

def simulate_vectorized(p_a: float, p_b: float, n: int = 200_000) -> tuple:
    """
    Monte Carlo vectorisé. Utilise NumPy si disponible (10× plus rapide),
    sinon fallback Python pur.
    """
    try:
        import numpy as np
        rng = np.random.default_rng()
        sa = rng.binomial(5, p_a, n).astype(np.int16)
        sb = rng.binomial(5, p_b, n).astype(np.int16)

        # Mort subite vectorisée
        tied = sa == sb
        while tied.any():
            nt = int(tied.sum())
            ga = rng.binomial(1, p_a, nt).astype(np.int16)
            gb = rng.binomial(1, p_b, nt).astype(np.int16)
            resolved = ga != gb
            idx = np.where(tied)[0][resolved]
            sa[idx] += ga[resolved]
            sb[idx] += gb[resolved]
            tied[idx] = False

        wa = float((sa > sb).mean())
        wb = float((sb > sa).mean())
        exp_a = float(sa.mean())
        exp_b = float(sb.mean())

        sc = Counter(zip(sa.tolist(), sb.tolist()))
        top = [(f"{h}:{a}", round(c/n*100, 1))
               for (h,a), c in sc.most_common(5)]
        return wa, wb, top, exp_a, exp_b

    except ImportError:
        # Fallback Python pur
        rng = random.Random()
        wa = wb = 0
        sa_l, sb_l = [], []
        for _ in range(min(n, 80_000)):
            s_a = sum(1 for _ in range(5) if rng.random() < p_a)
            s_b = sum(1 for _ in range(5) if rng.random() < p_b)
            while s_a == s_b:
                s_a += 1 if rng.random() < p_a else 0
                s_b += 1 if rng.random() < p_b else 0
            sa_l.append(s_a); sb_l.append(s_b)
            if s_a > s_b: wa += 1
            else: wb += 1
        nn = len(sa_l)
        sc = Counter(zip(sa_l, sb_l))
        top = [(f"{h}:{a}", round(c/nn*100,1)) for (h,a),c in sc.most_common(5)]
        return wa/nn, wb/nn, top, sum(sa_l)/nn, sum(sb_l)/nn


# ── Prédiction principale v5.0 ────────────────────────────────────────────────

def predict(team_a, team_b, odds_v1=None, odds_v2=None, verbose=True):
    stats, h2h_map = build_stats()
    global_avg = sum(s for a,sa,b,sb in ALL_MATCHES for s in (sa,sb)) / (2*len(ALL_MATCHES))
    global_p   = min(0.97, max(0.55, global_avg / 5))

    st_a = stats.get(team_a, {"win_rate":0.5,"avg_gf":global_avg,
                               "p_shot":global_p,"games":0,
                               "p_shot_ci":(global_p-0.02,global_p+0.02)})
    st_b = stats.get(team_b, {"win_rate":0.5,"avg_gf":global_avg,
                               "p_shot":global_p,"games":0,
                               "p_shot_ci":(global_p-0.02,global_p+0.02)})

    # ── H2H ──────────────────────────────────────────────────────────────────
    h        = h2h_map.get((team_a, team_b), {"W":0,"L":0})
    total_h2h = h["W"] + h["L"]
    p_h2h_a   = h["W"] / total_h2h if total_h2h >= 4 else None

    # ── Streak / momentum ────────────────────────────────────────────────────
    streak_a, recent_a, s_len_a = streak_factor(team_a)
    streak_b, recent_b, s_len_b = streak_factor(team_b)

    # ── Modèle Bayésien (p_shot historique) ──────────────────────────────────
    p_shot_a = st_a["p_shot"]
    p_shot_b = st_b["p_shot"]
    p_bayes_a = binomial_win_prob(p_shot_a, p_shot_b)

    # ── Calcul probabilité combinée ──────────────────────────────────────────
    if odds_v1 and odds_v2:
        p_odds_a, p_odds_b = implied_prob(odds_v1, odds_v2)

        # Calibration: extraire p_tir depuis les cotes
        p_cal_a, p_cal_b = calibrate_p_shot_from_odds(p_odds_a, p_odds_b,
                                                        base_avg=global_avg/5)

        p_h2h = p_h2h_a if p_h2h_a is not None else p_odds_a

        # Fusion 4 signaux
        p_a = (0.55 * p_odds_a +
               0.25 * p_bayes_a +
               0.15 * p_h2h +
               0.05 * (0.5 + streak_a - streak_b))
        mode = (f"Cotes×55%+Bayes×25%+H2H×15%+Streak×5%  "
                f"[V1={odds_v1} V2={odds_v2}]")
    else:
        p_cal_a, p_cal_b = p_shot_a, p_shot_b
        p_h2h = p_h2h_a if p_h2h_a is not None else st_a["win_rate"]

        p_a = (0.35 * p_bayes_a +
               0.35 * p_h2h +
               0.25 * st_a["win_rate"] +
               0.05 * (0.5 + streak_a - streak_b))
        mode = "Bayes×35%+H2H×35%+WR×25%+Streak×5%  [sans cotes]"

    p_a = max(0.05, min(0.95, p_a))
    p_b = 1 - p_a

    # ── Simulation Monte Carlo vectorisée ────────────────────────────────────
    mc_a, mc_b, top_scores, exp_a, exp_b = simulate_vectorized(p_cal_a, p_cal_b)

    # ── Score de confiance multi-facteurs ────────────────────────────────────
    diff = abs(p_a - 0.5)
    h2h_bonus    = 0.05 if total_h2h >= 10 else 0.02 if total_h2h >= 4 else 0
    streak_bonus = 0.03 if abs(streak_a - streak_b) >= 0.04 else 0
    odds_bonus   = 0.05 if (odds_v1 and odds_v2) else 0
    conf_score   = diff + h2h_bonus + streak_bonus + odds_bonus

    if conf_score >= 0.22:   confidence = "HAUTE 🔥"
    elif conf_score >= 0.12: confidence = "MOYENNE ✅"
    else:                    confidence = "FAIBLE ⚠️"

    # ── Expected Value ────────────────────────────────────────────────────────
    ev_a = compute_ev(odds_v1, p_a) if odds_v1 else None
    ev_b = compute_ev(odds_v2, p_b) if odds_v2 else None

    # ── Test de runs ──────────────────────────────────────────────────────────
    rt_a = runs_test(team_a)
    rt_b = runs_test(team_b)

    # ── Résultat court (sans affichage) ──────────────────────────────────────
    winner = team_a if p_a > p_b else team_b
    if not verbose:
        return {
            "winner": winner, "p_a": round(p_a*100,1), "p_b": round(p_b*100,1),
            "mc_a": round(mc_a*100,1), "mc_b": round(mc_b*100,1),
            "exp_a": round(exp_a,2), "exp_b": round(exp_b,2),
            "top_scores": top_scores, "confidence": confidence,
            "h2h_w": h["W"], "h2h_l": h["L"],
            "games_a": st_a["games"], "games_b": st_b["games"],
            "win_rate_a": round(st_a["win_rate"]*100,1),
            "win_rate_b": round(st_b["win_rate"]*100,1),
            "streak_a": streak_a, "streak_b": streak_b,
            "ev_a": ev_a, "ev_b": ev_b,
        }

    # ══════════════════════════════════════════════════════════════════════════
    #  AFFICHAGE
    # ══════════════════════════════════════════════════════════════════════════
    B="\033[1m"; G="\033[92m"; RE="\033[91m"
    Y="\033[93m"; C="\033[96m"; R="\033[0m"; BL="\033[94m"; GR="\033[90m"

    w_prob = max(p_a, p_b)

    def bar(p, w=22):
        f = int(p/100*w); return "█"*f + "░"*(w-f)

    def streak_str(s_len):
        if s_len > 0:  return f"{G}▲{s_len}V{R}"
        elif s_len < 0: return f"{RE}▼{abs(s_len)}D{R}"
        return f"{Y}~{R}"

    print(f"\n{B}{BL}{'═'*64}{R}")
    print(f"{B}  ⚽ FC25 PENALTY EXPERT v5.0 — Moteur IA Bayésien{R}")
    print(f"{B}{BL}{'═'*64}{R}")
    print(f"\n  {G}{B}{team_a}{R}  vs  {RE}{B}{team_b}{R}")

    if odds_v1 and odds_v2:
        p_o_a, p_o_b = implied_prob(odds_v1, odds_v2)
        margin = (1/odds_v1 + 1/odds_v2 - 1) * 100
        print(f"  {C}Cotes: V1={odds_v1} ({p_o_a*100:.1f}%)  V2={odds_v2} ({p_o_b*100:.1f}%)"
              f"  Marge BK={margin:.1f}%{R}")
        print(f"  {C}p_tir calibrés: {team_a}={p_cal_a:.3f}  {team_b}={p_cal_b:.3f}{R}")

    # Stats Bayésiennes
    print(f"\n{B}  📊 Stats Bayésiennes ({len(ALL_MATCHES)} matchs){R}")
    ci_a = st_a['p_shot_ci']; ci_b = st_b['p_shot_ci']
    print(f"  {team_a:<22} WR:{G}{st_a['win_rate']*100:.0f}%{R}  "
          f"p_Bayes:{C}{st_a['p_shot']:.3f}{R} [{ci_a[0]:.3f}-{ci_a[1]:.3f}]  "
          f"N:{st_a['games']}  Streak:{streak_str(s_len_a)}")
    print(f"  {team_b:<22} WR:{RE}{st_b['win_rate']*100:.0f}%{R}  "
          f"p_Bayes:{C}{st_b['p_shot']:.3f}{R} [{ci_b[0]:.3f}-{ci_b[1]:.3f}]  "
          f"N:{st_b['games']}  Streak:{streak_str(s_len_b)}")

    # H2H
    if total_h2h > 0:
        print(f"\n{B}  🔄 H2H{R}: {team_a} {G}{h['W']}{R}W–{RE}{h['L']}{R}L "
              f"({total_h2h} matchs)"
              + (f" → {p_h2h_a*100:.0f}% faveur A" if p_h2h_a else
                 " [< 4 matchs → non utilisé]"))

    # Runs test
    for team_lbl, rt in [(team_a, rt_a), (team_b, rt_b)]:
        if rt:
            color = Y if not rt["is_random"] else GR
            print(f"  {color}RNG {team_lbl}: {rt['pattern']}  "
                  f"(z={rt['z']}, p={rt['p_value']}){R}")

    # Probabilités
    print(f"\n{B}  🎯 Probabilités de victoire{R}")
    print(f"  {G}{team_a:<26}{R} {bar(p_a*100)} {B}{p_a*100:.1f}%{R}")
    print(f"  {RE}{team_b:<26}{R} {bar(p_b*100)} {B}{p_b*100:.1f}%{R}")
    print(f"  {GR}MC vectorisé (200k): {G}{mc_a*100:.1f}%{R} / {RE}{mc_b*100:.1f}%{R}")

    # Scores
    print(f"\n{B}  📈 Scores probables (Binomial+mort subite){R}")
    for i, (score, prob) in enumerate(top_scores, 1):
        a_s, b_s = score.split(":")
        color = G if int(a_s) > int(b_s) else RE
        medal = ["🥇","🥈","🥉","  4.","  5."][i-1]
        print(f"  {medal} {color}{team_a} {score} {team_b}{R}"
              f"   {bar(prob, 10)} {prob}%")

    print(f"\n  Buts attendus: {G}{team_a}{R} {exp_a:.2f} – {exp_b:.2f} {RE}{team_b}{R}  "
          f"(p_tir: {p_cal_a:.3f} vs {p_cal_b:.3f})")

    # Expected Value
    if ev_a is not None:
        ev_color_a = G if ev_a > 0 else RE
        ev_color_b = G if ev_b > 0 else RE
        print(f"\n{B}  💰 Expected Value{R}")
        print(f"  V1 {team_a}: {ev_color_a}{ev_a:+.4f}{R}  "
              f"V2 {team_b}: {ev_color_b}{ev_b:+.4f}{R}  "
              f"{'✅ valeur positive' if ev_a > 0 or ev_b > 0 else GR+'❌ pari défavorable'+R}")

    # Verdict
    print(f"\n{B}{'═'*64}{R}")
    print(f"  {B}Vainqueur prédit :{R} "
          f"{G if p_a>p_b else RE}{B}{winner}{R}  ({w_prob*100:.1f}%)")
    print(f"  {B}Confiance        :{R} {B}{confidence}{R}")
    print(f"  {B}Modèle           :{R} {C}{mode}{R}")
    print(f"{B}{'═'*64}{R}\n")
    print(f"  {Y}⚠  FC25 RNG — chaque match est indépendant, pas de garantie.{R}\n")

    return {"winner": winner, "prob": round(w_prob*100,1),
            "ev_a": ev_a, "ev_b": ev_b, "confidence": confidence}


# ── Interface CLI ─────────────────────────────────────────────────────────────

def interactive():
    B="\033[1m"; C="\033[96m"; G="\033[92m"; R="\033[0m"; BL="\033[94m"
    print(f"\n{B}{BL}  FC25 PENALTY EXPERT v5.0 — Moteur IA Bayésien{R}")
    print(f"  {C}{len(ALL_MATCHES)} matchs | Bayésien+Calibration+Streak+MC(200k)+EV{R}\n")
    print(f"Équipes: {', '.join(TEAMS)}\n")

    while True:
        try:
            print(f"{B}Équipe A > {R}", end=""); a = input().strip()
            if a.lower() in ("quit","q","exit",""): break
            print(f"{B}Équipe B > {R}", end=""); b = input().strip()
            if not b: continue
            print(f"{B}Cote V1 (Entrée si inconnue) > {R}", end="")
            o1 = input().strip()
            print(f"{B}Cote V2 (Entrée si inconnue) > {R}", end="")
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
    p = argparse.ArgumentParser(description="FC25 Penalty Expert v5.0")
    p.add_argument("--a",    help="Équipe A")
    p.add_argument("--b",    help="Équipe B")
    p.add_argument("--v1",   type=float, help="Cote V1")
    p.add_argument("--v2",   type=float, help="Cote V2")
    p.add_argument("--stats",action="store_true", help="Afficher toutes les stats")
    args = p.parse_args()

    if args.stats:
        stats, _ = build_stats()
        print(f"\n{'='*70}")
        print(f"  STATS FC25 v5.0 — {len(ALL_MATCHES)} matchs | Modèle Bayésien Beta-Binomial")
        print(f"{'='*70}")
        print(f"  {'Équipe':<22} {'WR':>5}  {'p_Bayes':>8}  {'IC90%':>14}  {'N':>4}")
        print(f"  {'-'*65}")
        for t, s in sorted(stats.items(), key=lambda x: -x[1]["win_rate"]):
            ci = s['p_shot_ci']
            print(f"  {t:<22} {s['win_rate']*100:>4.0f}%  "
                  f"{s['p_shot']:>8.4f}  "
                  f"[{ci[0]:.3f}-{ci[1]:.3f}]  {s['games']:>4}")
        print()
        return

    if args.a and args.b:
        a = next((t for t in TEAMS if t.lower().startswith(args.a.lower())), args.a)
        b = next((t for t in TEAMS if t.lower().startswith(args.b.lower())), args.b)
        predict(a, b, args.v1, args.v2)
    else:
        interactive()


if __name__ == "__main__":
    main()
