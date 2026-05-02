import json
from pathlib import Path
import sys
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from Semantic_distance.semantic_chooser_enum import SemanticChooserStrategy
from Semantic_distance.strategies import select_best_themes

if __name__ == "__main__":

    DATA_DIR = BASE_DIR / "Semantic_distance" / "data"
    DF_PATH = DATA_DIR / "mapped" / "combined_selected_themes_preprocessed.csv"

    df = pd.read_csv(DF_PATH)

    similarity_threshold = 0.55
    df_filtered = df[df["similarity"] > similarity_threshold] # define el umbral de similitud

    df_sorted = df_filtered.sort_values(by="similarity", ascending=False)
    top_themes = df_sorted.drop_duplicates(subset=["group", "keyword"], keep="first")

    result_dict = (
        top_themes.groupby("group")
        .apply(lambda g: dict(zip(g["keyword"], g["theme"])))
        .to_dict()
    )
    themes_only_dict = {
        group: list(set(inner_dict.values())) for group, inner_dict in result_dict.items()
    }

    output_path = BASE_DIR / "keywords_dicts" / "themes_by_group_max_similarity.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(themes_only_dict, f, indent=2)
