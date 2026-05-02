from pathlib import Path
import sys
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from Semantic_distance.semantic_chooser_enum import SemanticChooserStrategy
from Semantic_distance.strategies import select_best_themes

if __name__ == "__main__":

    DATA_DIR = BASE_DIR / "Semantic_distance" / "data"
    DF_PATH = DATA_DIR / "keyword_theme_matches_all_models.csv"

    df = pd.read_csv(DF_PATH)

    strategy_results = []
    for strategy in SemanticChooserStrategy:
        print(f"Strategy: {strategy}")
        selected_themes = select_best_themes(df, strategy=strategy.value, top_n=1, min_similarity=0.45, fill_if_missing= False)
        selected_themes.to_csv(DATA_DIR / "mapped" / f"selected_themes_{strategy.value}.csv", index=False)
        strategy_results.append(selected_themes)

    combined_results = pd.concat(strategy_results, ignore_index=True)
    combined_results.to_csv(DATA_DIR / "mapped" / "combined_selected_themes.csv", index=False)

    
