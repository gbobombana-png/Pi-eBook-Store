#!/usr/bin/env python3
"""
Calibration Elo — 207 matchs FC25 Penalty réels (matchs #55 à #261)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from elo import update, get_all

# Format: (team_a, score_a, team_b, score_b)
# Équipes FC25 — noms exacts de team_data.py
MATCHES = [
    # ── Matchs #55 → #107 ──────────────────────────────────────────────
    ("Juventus",      3,  "Inter Miami",  4),   # 55
    ("Barcelona",     5,  "Arsenal",      3),   # 56
    ("Bayern Munich", 3,  "Inter Miami",  2),   # 57
    ("Inter Miami",   4,  "Barcelona",    1),   # 58
    ("Arsenal",       7,  "Man City",     6),   # 59
    ("Inter Miami",   4,  "PSG",          5),   # 60
    ("PSG",           5,  "Juventus",     3),   # 61
    ("Barcelona",     6,  "Liverpool",    7),   # 62
    ("Barcelona",     5,  "Arsenal",      3),   # 63
    ("Juventus",      4,  "PSG",          5),   # 64
    ("Juventus",      4,  "PSG",          5),   # 65
    ("Barcelona",     4,  "Al Nassr",     5),   # 66
    ("Barcelona",     3,  "Al Nassr",     4),   # 67
    ("PSG",           7,  "Inter Miami",  6),   # 68
    ("Barcelona",    12,  "Man City",    11),   # 69
    ("Arsenal",       5,  "Real Madrid",  3),   # 70
    ("Arsenal",       2,  "Man City",     4),   # 71
    ("PSG",           5,  "Bayern Munich",3),   # 72
    ("Barcelona",     6,  "Al Nassr",     5),   # 73
    ("Barcelona",     5,  "Al Nassr",     3),   # 74
    ("Barcelona",     4,  "Al Nassr",     3),   # 75
    ("Barcelona",     9,  "Man City",     8),   # 76
    ("Barcelona",     5,  "Al Nassr",     3),   # 77
    ("Barcelona",     4,  "Arsenal",      5),   # 78
    ("Inter Miami",   1,  "Juventus",     3),   # 79
    ("Arsenal",       3,  "Real Madrid",  4),   # 80
    ("Man City",      3,  "Arsenal",      4),   # 81
    ("Barcelona",     7,  "Al Nassr",     6),   # 82
    ("Man City",      2,  "Barcelona",    3),   # 83
    ("PSG",           4,  "Juventus",     2),   # 84
    ("Juventus",      2,  "Liverpool",    3),   # 85
    ("PSG",           5,  "Barcelona",    4),   # 86
    ("Barcelona",     4,  "Al Nassr",     5),   # 87
    ("Real Madrid",   7,  "PSG",          8),   # 88
    ("Barcelona",     4,  "Al Nassr",     3),   # 89
    ("Man City",      6,  "Arsenal",      7),   # 90
    ("Juventus",      6,  "PSG",          5),   # 91
    ("Arsenal",       7,  "Man City",     8),   # 92
    ("Real Madrid",   6,  "Barcelona",    5),   # 93
    ("PSG",           4,  "Inter Miami",  3),   # 94
    ("Juventus",      4,  "Liverpool",    5),   # 95
    ("Barcelona",     5,  "Man City",     3),   # 96
    ("Arsenal",       9,  "Man City",     8),   # 97
    ("Arsenal",       5,  "Real Madrid",  4),   # 98
    ("Arsenal",       5,  "Man City",     3),   # 99
    ("Man City",      5,  "Barcelona",    3),   # 100
    ("Barcelona",     2,  "Al Nassr",     4),   # 101
    ("Real Madrid",   6,  "PSG",          5),   # 102
    ("Juventus",      4,  "Liverpool",    5),   # 103
    ("Juventus",      2,  "Liverpool",    4),   # 104
    ("PSG",           5,  "Inter Miami",  4),   # 105
    ("Barcelona",     4,  "Al Nassr",     5),   # 106
    ("Juventus",      4,  "Liverpool",    3),   # 107
    # ── Matchs #108 → #183 ─────────────────────────────────────────────
    ("PSG",           5,  "Bayern Munich",4),   # 108
    ("Barcelona",     3,  "Al Nassr",     4),   # 109
    ("Barcelona",     3,  "Al Nassr",     1),   # 110
    ("PSG",           5,  "Bayern Munich",3),   # 111
    ("Inter Miami",   4,  "PSG",          1),   # 112
    ("Man City",      4,  "Arsenal",      1),   # 113
    ("Juventus",      4,  "PSG",          5),   # 114
    ("Inter Miami",   5,  "PSG",          3),   # 115
    ("PSG",           4,  "Bayern Munich",2),   # 116
    ("Real Madrid",   3,  "Barcelona",    4),   # 117
    ("Real Madrid",   2,  "Barcelona",    4),   # 118
    ("Liverpool",     3,  "Man City",     4),   # 119
    ("Bayern Munich", 3,  "Inter Miami",  4),   # 120
    ("Bayern Munich", 5,  "Barcelona",    3),   # 121
    ("Barcelona",     4,  "Arsenal",      5),   # 122
    ("Real Madrid",   6,  "Inter Miami",  7),   # 123
    ("PSG",           5,  "Barcelona",    4),   # 124
    ("Juventus",      4,  "Liverpool",    5),   # 125
    ("Barcelona",     4,  "Man City",     5),   # 126
    ("Barcelona",     4,  "Man City",     5),   # 127
    ("Man City",      3,  "Arsenal",      1),   # 128
    ("Arsenal",       2,  "Real Madrid",  3),   # 129
    ("Barcelona",     6,  "Arsenal",      7),   # 130
    ("Barcelona",     5,  "Arsenal",      3),   # 131
    ("Juventus",      4,  "PSG",          5),   # 132
    ("Juventus",      4,  "PSG",          5),   # 133
    ("Juventus",      4,  "PSG",          5),   # 134
    ("Barcelona",     5,  "Arsenal",      3),   # 135
    ("Barcelona",     4,  "Arsenal",      5),   # 136
    ("Real Madrid",   4,  "Inter Miami",  5),   # 137
    ("Real Madrid",   5,  "Barcelona",    3),   # 138
    ("Inter Miami",   3,  "PSG",          2),   # 139
    ("Barcelona",     5,  "Liverpool",    4),   # 140
    ("Barcelona",     7,  "Al Nassr",     8),   # 141
    ("Juventus",      6,  "PSG",          7),   # 142
    ("Liverpool",     8,  "Man City",     7),   # 143
    ("Barcelona",     4,  "Al Nassr",     1),   # 144
    ("Barcelona",     8,  "Al Nassr",     7),   # 145
    ("Juventus",      3,  "PSG",          4),   # 146
    ("PSG",           2,  "Juventus",     3),   # 147
    ("Inter Miami",   7,  "Real Madrid",  6),   # 148
    ("Bayern Munich", 4,  "Inter Miami",  1),   # 149
    ("Barcelona",     4,  "Arsenal",      5),   # 150
    ("PSG",           5,  "Liverpool",    6),   # 151
    ("PSG",           2,  "Arsenal",      3),   # 152
    ("PSG",           4,  "Inter Miami",  2),   # 153
    ("Barcelona",     7,  "Man City",     8),   # 154
    ("Barcelona",     3,  "Man City",     4),   # 155
    ("Juventus",      4,  "PSG",          5),   # 156
    ("Arsenal",       7,  "Real Madrid",  6),   # 157
    ("Barcelona",     4,  "Al Nassr",     3),   # 158
    ("PSG",           4,  "Bayern Munich",2),   # 159
    ("PSG",           3,  "Inter Miami",  0),   # 160
    ("Barcelona",     5,  "Al Nassr",     4),   # 161
    ("PSG",           4,  "Bayern Munich",5),   # 162
    ("Real Madrid",   6,  "Barcelona",    5),   # 163
    ("Real Madrid",   4,  "Liverpool",    3),   # 164
    ("Real Madrid",   4,  "Barcelona",    2),   # 165
    ("Liverpool",     4,  "Man City",     5),   # 166
    ("Inter Miami",   4,  "Barcelona",    5),   # 167
    ("Real Madrid",   1,  "PSG",          3),   # 168
    ("Real Madrid",   5,  "Inter Miami",  3),   # 169
    ("Inter Miami",   4,  "Barcelona",    5),   # 170
    ("Man City",      8,  "Barcelona",    7),   # 171
    ("Juventus",      5,  "Inter Miami",  4),   # 172
    ("PSG",           6,  "Inter Miami",  5),   # 173
    ("Juventus",      4,  "Liverpool",    3),   # 174
    ("Real Madrid",   5,  "Liverpool",    3),   # 175
    ("PSG",           2,  "Juventus",     4),   # 176
    ("Barcelona",     4,  "Al Nassr",     2),   # 177
    ("Real Madrid",   0,  "Barcelona",    2),   # 178
    ("PSG",           3,  "Juventus",     4),   # 179
    ("Barcelona",     5,  "Man City",     4),   # 180
    ("Barcelona",     4,  "Al Nassr",     3),   # 181
    ("Barcelona",     4,  "Al Nassr",     3),   # 182
    ("Juventus",     10,  "Inter Miami", 11),   # 183
    # ── Matchs #184 → #241 ─────────────────────────────────────────────
    ("Barcelona",     2,  "Al Nassr",     4),   # 184
    ("Barcelona",     6,  "Arsenal",      5),   # 185
    ("PSG",           4,  "Bayern Munich",3),   # 186
    ("Barcelona",     5,  "Arsenal",      6),   # 187
    ("Barcelona",     3,  "Liverpool",    0),   # 188
    ("Barcelona",     4,  "Arsenal",      5),   # 189
    ("Barcelona",     2,  "Liverpool",    4),   # 190
    ("PSG",           4,  "Juventus",     5),   # 191
    ("PSG",           4,  "Barcelona",    5),   # 192
    ("Juventus",      6,  "PSG",          5),   # 193
    ("Barcelona",     5,  "Liverpool",    3),   # 194
    ("Juventus",      4,  "PSG",          5),   # 195
    ("Barcelona",     7,  "Liverpool",    6),   # 196
    ("Juventus",      5,  "PSG",          6),   # 197
    ("Real Madrid",   4,  "Barcelona",    5),   # 198
    ("Juventus",      4,  "PSG",          2),   # 199
    ("Juventus",      3,  "PSG",          4),   # 200
    ("PSG",           5,  "Inter Miami",  6),   # 201
    ("PSG",           2,  "Bayern Munich",3),   # 202
    ("Arsenal",       7,  "Real Madrid",  6),   # 203
    ("Juventus",      4,  "PSG",          5),   # 204
    ("Inter Miami",   2,  "Barcelona",    4),   # 205
    ("Real Madrid",   3,  "Barcelona",    4),   # 206
    ("Barcelona",     5,  "Arsenal",      3),   # 207
    ("Barcelona",     4,  "Man City",     5),   # 208
    ("Barcelona",     3,  "Arsenal",      4),   # 209
    ("Arsenal",       3,  "Real Madrid",  4),   # 210
    ("PSG",           4,  "Inter Miami",  3),   # 211
    ("Barcelona",     5,  "Al Nassr",     3),   # 212
    ("Barcelona",     7,  "Man City",     8),   # 213
    ("Liverpool",     0,  "Man City",     3),   # 214
    ("Barcelona",     7,  "Liverpool",    6),   # 215
    ("Barcelona",     4,  "Arsenal",      2),   # 216
    ("Barcelona",     2,  "Man City",     3),   # 217
    ("Real Madrid",   4,  "Barcelona",    2),   # 218
    ("Real Madrid",   5,  "Inter Miami",  4),   # 219
    ("Real Madrid",   4,  "Barcelona",    3),   # 220
    ("Real Madrid",   5,  "Inter Miami",  6),   # 221
    ("Bayern Munich", 4,  "Inter Miami",  5),   # 222
    ("Juventus",      5,  "PSG",          4),   # 223
    ("Barcelona",     6,  "Man City",     5),   # 224
    ("Barcelona",     3,  "Al Nassr",     4),   # 225
    ("PSG",           5,  "Inter Miami",  4),   # 226
    ("PSG",           4,  "Juventus",     2),   # 227
    ("Real Madrid",   4,  "Bayern Munich",2),   # 228
    ("Juventus",      9,  "Liverpool",   10),   # 229
    ("Arsenal",       9,  "Man City",    10),   # 230
    ("Real Madrid",   4,  "Bayern Munich",5),   # 231
    ("PSG",           4,  "Barcelona",    1),   # 232
    ("Juventus",      5,  "Bayern Munich",3),   # 233
    ("Inter Miami",   4,  "Juventus",     3),   # 234
    ("Arsenal",      10,  "Man City",    11),   # 235
    ("Man City",      5,  "Juventus",     6),   # 236
    ("Arsenal",       3,  "Real Madrid",  4),   # 237
    ("Inter Miami",   8,  "Juventus",     7),   # 238
    ("Barcelona",     4,  "Al Nassr",     3),   # 239
    ("Real Madrid",   3,  "Inter Miami",  4),   # 240
    ("Bayern Munich",13,  "Barcelona",   14),   # 241
    # ── Matchs #242 → #261 ─────────────────────────────────────────────
    ("Inter Miami",   4,  "PSG",          5),   # 242
    ("Barcelona",     2,  "Arsenal",      4),   # 243
    ("Juventus",      5,  "PSG",          6),   # 244
    ("Juventus",      4,  "Inter Miami",  3),   # 245
    ("PSG",           2,  "Arsenal",      3),   # 246
    ("PSG",           5,  "Bayern Munich",4),   # 247
    ("Barcelona",     4,  "Man City",     2),   # 248
    ("Barcelona",     1,  "Man City",     3),   # 249
    ("Juventus",      5,  "Bayern Munich",4),   # 250
    ("Liverpool",     3,  "Man City",     4),   # 251
    ("PSG",           6,  "Barcelona",    5),   # 252
    ("Barcelona",     5,  "Al Nassr",     4),   # 253
    ("Juventus",      3,  "Inter Miami",  4),   # 254
    ("Barcelona",     2,  "Al Nassr",     4),   # 255
    ("Barcelona",     3,  "Al Nassr",     4),   # 256
    ("Bayern Munich", 4,  "Inter Miami",  2),   # 257
    ("Barcelona",     5,  "Man City",     3),   # 258
    ("Barcelona",     4,  "Liverpool",    2),   # 259
    ("Barcelona",     5,  "Man City",     6),   # 260
    ("PSG",           4,  "Juventus",     5),   # 261
]


def main():
    print(f"Calibration Elo — {len(MATCHES)} matchs FC25 Penalty")
    print("=" * 55)

    for i, (a, sa, b, sb) in enumerate(MATCHES, start=55):
        update(a, sa, b, sb)

    ratings = get_all()
    print(f"\nClassement Elo final ({len(ratings)} équipes):")
    print("-" * 40)
    for team, elo in sorted(ratings.items(), key=lambda x: -x[1]):
        bar = "█" * int((elo - 1400) / 10)
        print(f"  {elo:>7.1f}  {team:<20} {bar}")

    print("\nCalibration terminée. elo_ratings.json mis à jour.")


if __name__ == "__main__":
    main()
