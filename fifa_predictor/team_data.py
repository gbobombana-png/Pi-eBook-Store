# Ratings EA FC 25 officiels (Overall, Attack, Midfield, Defense)
# Source: EA Sports official ratings
TEAM_RATINGS = {
    # Elite
    "Man City":        {"ovr": 88, "att": 88, "mid": 88, "def": 87},
    "Real Madrid":     {"ovr": 88, "att": 87, "mid": 88, "def": 87},
    "Bayern Munich":   {"ovr": 87, "att": 87, "mid": 86, "def": 86},
    "PSG":             {"ovr": 87, "att": 90, "mid": 85, "def": 84},
    "Liverpool":       {"ovr": 86, "att": 87, "mid": 85, "def": 85},
    "Arsenal":         {"ovr": 85, "att": 85, "mid": 85, "def": 84},
    "Chelsea":         {"ovr": 84, "att": 83, "mid": 84, "def": 83},
    "Barcelona":       {"ovr": 85, "att": 86, "mid": 85, "def": 83},
    "Atletico Madrid": {"ovr": 84, "att": 82, "mid": 83, "def": 87},
    "Inter Milan":     {"ovr": 85, "att": 84, "mid": 83, "def": 86},
    "AC Milan":        {"ovr": 83, "att": 83, "mid": 82, "def": 83},
    "Juventus":        {"ovr": 82, "att": 81, "mid": 82, "def": 83},
    "Dortmund":        {"ovr": 83, "att": 84, "mid": 82, "def": 81},
    "Man United":      {"ovr": 82, "att": 82, "mid": 81, "def": 81},
    "Tottenham":       {"ovr": 82, "att": 83, "mid": 81, "def": 80},
    "Newcastle":       {"ovr": 81, "att": 80, "mid": 80, "def": 82},
    "Aston Villa":     {"ovr": 81, "att": 81, "mid": 80, "def": 80},
    "Napoli":          {"ovr": 82, "att": 83, "mid": 81, "def": 80},
    "Porto":           {"ovr": 81, "att": 80, "mid": 80, "def": 81},
    "Benfica":         {"ovr": 81, "att": 81, "mid": 80, "def": 80},
    "Sevilla":         {"ovr": 80, "att": 79, "mid": 79, "def": 81},
    "Roma":            {"ovr": 80, "att": 80, "mid": 79, "def": 79},
    "Leverkusen":      {"ovr": 83, "att": 83, "mid": 83, "def": 82},
    "Leipzig":         {"ovr": 82, "att": 82, "mid": 81, "def": 81},
    "Ajax":            {"ovr": 80, "att": 80, "mid": 80, "def": 79},
    "PSV":             {"ovr": 80, "att": 81, "mid": 79, "def": 79},
    "Celtic":          {"ovr": 78, "att": 78, "mid": 77, "def": 77},
    "Rangers":         {"ovr": 77, "att": 76, "mid": 76, "def": 77},
    # Nationales
    "France":          {"ovr": 88, "att": 89, "mid": 87, "def": 87},
    "Brazil":          {"ovr": 87, "att": 88, "mid": 86, "def": 85},
    "England":         {"ovr": 86, "att": 86, "mid": 85, "def": 85},
    "Spain":           {"ovr": 86, "att": 86, "mid": 87, "def": 84},
    "Germany":         {"ovr": 85, "att": 85, "mid": 85, "def": 84},
    "Argentina":       {"ovr": 87, "att": 89, "mid": 85, "def": 84},
    "Portugal":        {"ovr": 86, "att": 87, "mid": 85, "def": 83},
    "Netherlands":     {"ovr": 85, "att": 85, "mid": 84, "def": 84},
    "Belgium":         {"ovr": 84, "att": 84, "mid": 83, "def": 83},
    "Italy":           {"ovr": 84, "att": 83, "mid": 84, "def": 85},
    "Croatia":         {"ovr": 83, "att": 82, "mid": 84, "def": 82},
    "Morocco":         {"ovr": 81, "att": 80, "mid": 80, "def": 83},
    "Senegal":         {"ovr": 80, "att": 80, "mid": 79, "def": 80},
    "USA":             {"ovr": 79, "att": 79, "mid": 78, "def": 78},
    "Mexico":          {"ovr": 79, "att": 79, "mid": 78, "def": 78},
    "Japan":           {"ovr": 79, "att": 78, "mid": 79, "def": 79},
}


def get_team(name):
    """Cherche une équipe (insensible à la casse et partielle)"""
    name_lower = name.lower()
    for team, stats in TEAM_RATINGS.items():
        if name_lower in team.lower() or team.lower() in name_lower:
            return team, stats
    return None, None


def list_teams():
    return sorted(TEAM_RATINGS.keys())
