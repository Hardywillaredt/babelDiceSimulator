import random
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict
from itertools import product

# --- Dice and Group Definitions ---
dice_faces = {
    1: ["MV:2", "MV:2", "MV:1", "MV:1", "MV:1", "S:0.5"],
    2: ["S:2", "S:1", "S:1", "S:1", "MV:1", "MV:1"],
    3: ["M:2", "M:1", "M:1", "S:1", "S:1", "MV:0.5"],
    4: ["R:2", "R:2", "R:1", "S:0.5", "S:0.5", "MV:0.5"],
    5: ["R:2", "R:1", "HX:2", "M:2", "M:2", "HX:1"],
    6: ["NG:1", "NG:2", "HX:2", "HX:2", "RE:2", "RE:2"],
    7: ["NG:2", "NG:2", "MP:2", "MP:2", "RE:2", "HX:3"],
}

scrabble_scores = {
    "A": 1, "E": 1, "I": 1, "O": 1, "U": 1,
    "L": 2, "N": 2, "S": 2, "T": 2, "R": 2,
    "B": 3, "C": 3, "M": 3, "P": 3,
    "D": 4, "G": 4, "V": 4, "Y": 4,
    "F": 5, "H": 5, "W": 5,
    "J": 6, "X": 6, "K": 6,
    "Q": 7, "Z": 7
}

removal_priority = [1, 4, 2, 3, 5, 6, 7]
repair_priority = [7, 6, 5, 3, 2, 4, 1]
words = ["KING", "FIRE", "KNIGHT", "ARCHER", "WIZARD", "BLADE", "MAGIC", "HEX", "JINX", "QUEST"]

def get_group_counts(word):
    group_counts = Counter()
    for letter in word:
        group = scrabble_scores[letter.upper()]
        group_counts[group] += 1
    return group_counts

# Battle logic functions omitted for brevity (same as before)
# ... (include roll_die, parse_face, categorize_rolls, resolve_damage, remove_dice, repair_dice, simulate_battle)
def roll_die(letter):
    return random.choice(dice_faces[scrabble_scores[letter]])

def parse_face(face):
    typ, val = face.split(":")
    return typ, float(val)

def categorize_rolls(rolls):
    count = Counter()
    for face in rolls:
        typ, val = parse_face(face)
        if typ == "HX":
            count[f"D{int(val)}"] += 1
        elif typ in ["R", "M"]:
            count[f"D{int(val)}"] += 1
        elif typ == "S":
            count[f"S{val}"] += 1
        elif typ in ["NG", "MP", "RE"]:
            count[typ] += int(val)
    return count

def resolve_damage(count_self, count_enemy):
    negate = count_self["NG"]
    for tier in ["D3", "D2", "D1"]:
        while negate > 0 and count_enemy[tier] > 0:
            dmg = count_enemy["D3"] * 3 + count_enemy["D2"] * 2 + count_enemy["D1"]
            shield = int(count_self["S2"] * 2 + count_self["S1"] + count_self["S0.5"] * 0.5)
            if dmg <= shield: break
            count_enemy[tier] -= 1
            negate -= 1
    for tier in ["S2", "S1", "S0.5"]:
        while negate > 0 and count_enemy[tier] > 0:
            count_enemy[tier] -= 1
            negate -= 1

    multiply = count_self["MP"]
    for tier in ["S2", "S1", "S0.5"]:
        while multiply > 0 and count_self[tier] > 0:
            dmg = count_enemy["D3"] * 3 + count_enemy["D2"] * 2 + count_enemy["D1"]
            shield = int(count_self["S2"] * 2 + count_self["S1"] + count_self["S0.5"] * 0.5)
            if shield >= dmg: break
            count_self[tier] += 1
            multiply -= 1
    for tier in ["D3", "D2", "D1"]:
        while multiply > 0 and count_self[tier] > 0:
            count_self[tier] += 1
            multiply -= 1

    dmg = count_enemy["D3"] * 3 + count_enemy["D2"] * 2 + count_enemy["D1"]
    shield = int(count_self["S2"] * 2 + count_self["S1"] + count_self["S0.5"] * 0.5)
    return max(0, dmg - shield)

def remove_dice(pool, damage):
    removed = []
    for _ in range(int(damage)):
        if not pool: break
        pool.sort(key=lambda d: removal_priority.index(scrabble_scores[d]))
        removed.append(pool.pop(0))
    return removed

def repair_dice(damaged, amount):
    damaged.sort(key=lambda d: repair_priority.index(scrabble_scores[d]))
    return [damaged.pop(0) for _ in range(min(amount, len(damaged)))]

def simulate_battle(word1, word2):
    pool1 = list(word1)
    pool2 = list(word2)
    damaged1, damaged2 = [], []
    rounds = 0

    rolls1 = [roll_die(d) for d in pool1]
    rolls2 = [roll_die(d) for d in pool2]
    count1 = categorize_rolls(rolls1)
    count2 = categorize_rolls(rolls2)
    dmg1 = resolve_damage(count1.copy(), count2.copy())
    dmg2 = resolve_damage(count2.copy(), count1.copy())
    damaged1 += remove_dice(pool1, dmg1)
    damaged2 += remove_dice(pool2, dmg2)

    while pool1 and pool2:
        rounds += 1
        rolls1 = [roll_die(d) for d in pool1]
        rolls2 = [roll_die(d) for d in pool2]
        count1 = categorize_rolls(rolls1)
        count2 = categorize_rolls(rolls2)
        dmg1 = resolve_damage(count1.copy(), count2.copy())
        dmg2 = resolve_damage(count2.copy(), count1.copy())

        new_damaged1 = remove_dice(pool1, dmg1)
        new_damaged2 = remove_dice(pool2, dmg2)

        repaired1 = repair_dice(damaged1, count1["RE"])
        repaired2 = repair_dice(damaged2, count2["RE"])
        pool1 += repaired1
        pool2 += repaired2

        damaged1 = [d for d in damaged1 if d not in repaired1]
        damaged2 = [d for d in damaged2 if d not in repaired2]
        damaged1 += new_damaged1
        damaged2 += new_damaged2

    winner = word1 if pool1 else word2 if pool2 else "Draw"
    return winner, rounds, len(damaged1), len(damaged2)


# Run battles and collect stats
results = []
group_stats = defaultdict(lambda: {"wins": 0, "appearances": 0, "rounds": 0, "damage": 0})

for word1, word2 in product(words, words):
    if word1 == word2: continue
    group1 = get_group_counts(word1)
    group2 = get_group_counts(word2)
    for _ in range(10):
        winner, rounds, dmg1, dmg2 = simulate_battle(word1, word2)
        results.append({
            "Word1": word1, "Word2": word2, "Winner": winner,
            "Rounds": rounds, "Damage_Word1": dmg1, "Damage_Word2": dmg2
        })
        for g in group1:
            group_stats[g]["appearances"] += group1[g]
            group_stats[g]["rounds"] += rounds
            group_stats[g]["damage"] += dmg1
            if winner == word1:
                group_stats[g]["wins"] += group1[g]
        for g in group2:
            group_stats[g]["appearances"] += group2[g]
            group_stats[g]["rounds"] += rounds
            group_stats[g]["damage"] += dmg2
            if winner == word2:
                group_stats[g]["wins"] += group2[g]

# Summarize group performance
group_summary = pd.DataFrame([
    {
        "Group": g,
        "Wins": v["wins"],
        "Appearances": v["appearances"],
        "Win Rate": v["wins"] / v["appearances"] if v["appearances"] else 0,
        "Avg Rounds": v["rounds"] / v["appearances"] if v["appearances"] else 0,
        "Avg Damage Taken": v["damage"] / v["appearances"] if v["appearances"] else 0,
    }
    for g, v in sorted(group_stats.items())
])

print("\n=== Group Performance Summary ===")
print(group_summary)

# Build win/damage/round matrices
wins_matrix = pd.DataFrame(0, index=words, columns=words)
damage_matrix = pd.DataFrame(0.0, index=words, columns=words)
rounds_matrix = pd.DataFrame(0.0, index=words, columns=words)
counts = pd.DataFrame(0, index=words, columns=words)

for row in results:
    w1, w2 = row["Word1"], row["Word2"]
    if row["Winner"] == w1:
        wins_matrix.loc[w1, w2] += 1
    elif row["Winner"] == w2:
        wins_matrix.loc[w2, w1] += 1
    damage_matrix.loc[w1, w2] += row["Damage_Word1"]
    damage_matrix.loc[w2, w1] += row["Damage_Word2"]
    rounds_matrix.loc[w1, w2] += row["Rounds"]
    counts.loc[w1, w2] += 1
    counts.loc[w2, w1] += 1

# Normalize for averages
damage_avg = damage_matrix / counts.replace(0, 1)
rounds_avg = rounds_matrix / counts.replace(0, 1)

for w in words:
    damage_avg.loc[w, w] = None
    rounds_avg.loc[w, w] = None

# Plot heatmaps
def plot_heatmap(data, title, cmap, label):
    plt.figure(figsize=(10, 8))
    sns.heatmap(data, annot=True, fmt=".1f", cmap=cmap, cbar_kws={"label": label})
    plt.title(title)
    plt.xlabel("Opponent")
    plt.ylabel("Word")
    plt.tight_layout()
    plt.show()

plot_heatmap(wins_matrix, "Wins per Matchup", "YlGn", "Wins")
plot_heatmap(damage_avg, "Avg Damage Taken per Matchup", "OrRd", "Avg Damage")
plot_heatmap(rounds_avg, "Avg Rounds per Matchup", "YlGnBu", "Avg Rounds")
