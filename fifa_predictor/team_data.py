# EA FC 25 — Stats complètes par attribut
# OVR, ATT, MID, DEF, PAC(vitesse), SHO(tir), PAS(passe),
# DRI(dribble), PHY(physique), GK(gardien), STAR(meilleur joueur rating)

TEAM_RATINGS = {
    # ── CLUBS ELITE ──────────────────────────────────────────────────
    "Man City":        {"ovr":86,"att":87,"mid":88,"def":86,"pac":82,"sho":85,"pas":88,"dri":86,"phy":80,"gk":87,"star":91,"star_name":"Haaland","depth":95},
    "Real Madrid":     {"ovr":88,"att":87,"mid":88,"def":87,"pac":84,"sho":86,"pas":87,"dri":88,"phy":82,"gk":88,"star":92,"star_name":"Vinicius Jr","depth":96},
    "Bayern Munich":   {"ovr":87,"att":87,"mid":86,"def":86,"pac":83,"sho":86,"pas":85,"dri":85,"phy":84,"gk":88,"star":90,"star_name":"Kane","depth":94},
    "PSG":             {"ovr":87,"att":90,"mid":85,"def":84,"pac":90,"sho":88,"pas":85,"dri":91,"phy":82,"gk":85,"star":93,"star_name":"Mbappe","depth":93},
    "Liverpool":       {"ovr":86,"att":87,"mid":85,"def":85,"pac":87,"sho":85,"pas":84,"dri":85,"phy":83,"gk":86,"star":91,"star_name":"Salah","depth":92},
    "Arsenal":         {"ovr":85,"att":85,"mid":85,"def":84,"pac":84,"sho":83,"pas":85,"dri":84,"phy":82,"gk":84,"star":89,"star_name":"Saka","depth":90},
    "Chelsea":         {"ovr":84,"att":83,"mid":84,"def":83,"pac":83,"sho":82,"pas":83,"dri":83,"phy":81,"gk":84,"star":88,"star_name":"Palmer","depth":89},
    "Barcelona":       {"ovr":85,"att":86,"mid":85,"def":83,"pac":85,"sho":84,"pas":87,"dri":87,"phy":79,"gk":83,"star":91,"star_name":"Yamal","depth":91},
    "Atletico Madrid": {"ovr":84,"att":82,"mid":83,"def":87,"pac":78,"sho":80,"pas":81,"dri":80,"phy":86,"gk":87,"star":88,"star_name":"Griezmann","depth":88},
    "Inter Milan":     {"ovr":85,"att":84,"mid":83,"def":86,"pac":80,"sho":83,"pas":82,"dri":82,"phy":84,"gk":86,"star":89,"star_name":"Lautaro","depth":89},
    "AC Milan":        {"ovr":83,"att":83,"mid":82,"def":83,"pac":82,"sho":82,"pas":81,"dri":83,"phy":82,"gk":83,"star":87,"star_name":"Leao","depth":86},
    "Juventus":        {"ovr":82,"att":81,"mid":82,"def":83,"pac":78,"sho":80,"pas":82,"dri":80,"phy":83,"gk":84,"star":86,"star_name":"Vlahovic","depth":85},
    "Dortmund":        {"ovr":83,"att":84,"mid":82,"def":81,"pac":87,"sho":83,"pas":82,"dri":84,"phy":80,"gk":81,"star":88,"star_name":"Guirassy","depth":86},
    "Leverkusen":      {"ovr":83,"att":83,"mid":83,"def":82,"pac":83,"sho":82,"pas":84,"dri":83,"phy":81,"gk":82,"star":88,"star_name":"Wirtz","depth":87},
    "Man United":      {"ovr":82,"att":82,"mid":81,"def":81,"pac":82,"sho":80,"pas":80,"dri":82,"phy":82,"gk":83,"star":87,"star_name":"Rashford","depth":84},
    "Tottenham":       {"ovr":82,"att":83,"mid":81,"def":80,"pac":84,"sho":82,"pas":81,"dri":83,"phy":80,"gk":80,"star":87,"star_name":"Son","depth":84},
    "Newcastle":       {"ovr":81,"att":80,"mid":80,"def":82,"pac":80,"sho":79,"pas":79,"dri":79,"phy":82,"gk":82,"star":85,"star_name":"Isak","depth":82},
    "Napoli":          {"ovr":82,"att":83,"mid":81,"def":80,"pac":83,"sho":82,"pas":81,"dri":82,"phy":80,"gk":80,"star":87,"star_name":"Kvaratskhelia","depth":83},
    "Porto":           {"ovr":81,"att":80,"mid":80,"def":81,"pac":82,"sho":79,"pas":79,"dri":80,"phy":80,"gk":81,"star":84,"star_name":"Galeno","depth":80},
    "Benfica":         {"ovr":81,"att":81,"mid":80,"def":80,"pac":82,"sho":80,"pas":79,"dri":81,"phy":79,"gk":80,"star":85,"star_name":"Di Maria","depth":80},
    "Leipzig":         {"ovr":82,"att":82,"mid":81,"def":81,"pac":85,"sho":81,"pas":81,"dri":82,"phy":81,"gk":81,"star":86,"star_name":"Sesko","depth":83},
    "Ajax":            {"ovr":80,"att":80,"mid":80,"def":79,"pac":82,"sho":79,"pas":81,"dri":81,"phy":78,"gk":79,"star":84,"star_name":"Brobbey","depth":79},
    "PSV":             {"ovr":80,"att":81,"mid":79,"def":79,"pac":83,"sho":80,"pas":79,"dri":81,"phy":78,"gk":79,"star":85,"star_name":"Tillman","depth":79},
    "Celtic":          {"ovr":78,"att":78,"mid":77,"def":77,"pac":79,"sho":77,"pas":77,"dri":78,"phy":78,"gk":77,"star":82,"star_name":"Maeda","depth":76},
    "Sevilla":         {"ovr":80,"att":79,"mid":79,"def":81,"pac":79,"sho":78,"pas":79,"dri":79,"phy":80,"gk":81,"star":84,"star_name":"En-Nesyri","depth":79},
    "Roma":            {"ovr":80,"att":80,"mid":79,"def":79,"pac":80,"sho":79,"pas":79,"dri":80,"phy":79,"gk":79,"star":85,"star_name":"Dybala","depth":79},
    # ── ÉQUIPES NATIONALES ───────────────────────────────────────────
    "France":      {"ovr":88,"att":89,"mid":87,"def":87,"pac":90,"sho":87,"pas":86,"dri":88,"phy":85,"gk":88,"star":93,"star_name":"Mbappe","depth":95},
    "Brazil":      {"ovr":87,"att":88,"mid":86,"def":85,"pac":89,"sho":86,"pas":86,"dri":90,"phy":83,"gk":85,"star":92,"star_name":"Vinicius","depth":94},
    "Argentina":   {"ovr":87,"att":89,"mid":85,"def":84,"pac":84,"sho":87,"pas":87,"dri":91,"phy":82,"gk":84,"star":94,"star_name":"Messi","depth":93},
    "England":     {"ovr":86,"att":86,"mid":85,"def":85,"pac":86,"sho":84,"pas":84,"dri":85,"phy":84,"gk":86,"star":89,"star_name":"Bellingham","depth":92},
    "Spain":       {"ovr":86,"att":86,"mid":87,"def":84,"pac":83,"sho":84,"pas":89,"dri":87,"phy":80,"gk":84,"star":90,"star_name":"Yamal","depth":92},
    "Germany":     {"ovr":85,"att":85,"mid":85,"def":84,"pac":83,"sho":84,"pas":85,"dri":83,"phy":83,"gk":85,"star":88,"star_name":"Musiala","depth":90},
    "Portugal":    {"ovr":86,"att":87,"mid":85,"def":83,"pac":83,"sho":87,"pas":84,"dri":86,"phy":82,"gk":83,"star":93,"star_name":"Ronaldo","depth":90},
    "Netherlands": {"ovr":85,"att":85,"mid":84,"def":84,"pac":84,"sho":83,"pas":84,"dri":84,"phy":83,"gk":84,"star":88,"star_name":"Gakpo","depth":88},
    "Belgium":     {"ovr":84,"att":84,"mid":83,"def":83,"pac":83,"sho":83,"pas":83,"dri":83,"phy":82,"gk":83,"star":88,"star_name":"De Bruyne","depth":87},
    "Italy":       {"ovr":84,"att":83,"mid":84,"def":85,"pac":80,"sho":82,"pas":84,"dri":82,"phy":83,"gk":85,"star":87,"star_name":"Barella","depth":87},
    "Croatia":     {"ovr":83,"att":82,"mid":84,"def":82,"pac":80,"sho":80,"pas":85,"dri":82,"phy":81,"gk":82,"star":88,"star_name":"Modric","depth":84},
    "Morocco":     {"ovr":81,"att":80,"mid":80,"def":83,"pac":82,"sho":79,"pas":80,"dri":81,"phy":82,"gk":83,"star":85,"star_name":"Hakimi","depth":82},
    "Senegal":     {"ovr":80,"att":80,"mid":79,"def":80,"pac":84,"sho":79,"pas":78,"dri":80,"phy":83,"gk":80,"star":85,"star_name":"Mane","depth":80},
    "USA":         {"ovr":79,"att":79,"mid":78,"def":78,"pac":83,"sho":77,"pas":78,"dri":79,"phy":81,"gk":78,"star":83,"star_name":"Pulisic","depth":78},
    "Al Nassr":    {"ovr":82,"att":85,"mid":79,"def":79,"pac":78,"sho":92,"pas":78,"dri":82,"phy":83,"gk":79,"star":99,"star_name":"Ronaldo","depth":81},
    "Inter Miami": {"ovr":79,"att":82,"mid":78,"def":76,"pac":80,"sho":80,"pas":78,"dri":82,"phy":78,"gk":76,"star":99,"star_name":"Messi","depth":78},
}


def get_team(name):
    name_lower = name.lower().strip()
    for team, stats in TEAM_RATINGS.items():
        if name_lower == team.lower():
            return team, stats
    for team, stats in TEAM_RATINGS.items():
        if name_lower in team.lower() or team.lower() in name_lower:
            return team, stats
    return None, None


def list_teams():
    return sorted(TEAM_RATINGS.keys())
