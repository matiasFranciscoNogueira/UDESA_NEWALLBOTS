import json
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent


themes_df = pd.read_csv(BASE_DIR.parent / "data" / "GDELT THEMES LIST.csv")
themes_df['THEME_LOWER'] = themes_df['THEME'].str.lower()

kw_file = "key_words_paper_updated.json"
kw_path = BASE_DIR.parent / "src" / kw_file
with open(kw_path, 'r', encoding='utf-8') as f:
    kw_dict = json.load(f)

def find_matches(keywords):
    matches = {}
    for word in keywords:
        results = themes_df[themes_df['THEME_LOWER'].str.contains(word.lower(), na=False)]
        matches[word] = results['THEME'].tolist()
    return matches

matches_e = find_matches(kw_dict["E"])
matches_p = find_matches(kw_dict["P"])
matches_u = find_matches(kw_dict["U"])

mapping_results = {
    "E": matches_e,
    "P": matches_p,
    "U": matches_u
}


kw_mapped = {}

for group, word_map in mapping_results.items():
    group_keywords = []
    for word, theme_list in word_map.items():
        if theme_list:
            group_keywords.extend(theme_list)

    kw_mapped[group] = list(set(group_keywords))

print(kw_mapped)
