import sys
import pandas as pd
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

if __name__ == "__main__":

    DATA_DIR = BASE_DIR / "Semantic_distance" / "data" / "mapped"
    CSV_PATH = DATA_DIR / "combined_selected_themes_preprocessed.csv"

    df = pd.read_csv(CSV_PATH)

    model_name = "all-MiniLM-L6-v2"
    filtered_df = df[df['model'] == model_name]

    themes_by_group = (filtered_df.groupby('group')['theme'].apply(lambda x: sorted(set(x))).to_dict())

    output_path = BASE_DIR / "keywords_dicts" / f"themes_by_group_{model_name}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(themes_by_group, f, indent=2)