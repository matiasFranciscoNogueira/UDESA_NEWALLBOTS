from pathlib import Path
import pandas as pd


if __name__ == "__main__":


    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "Semantic_distance" / "data" / "mapped"
    DF_PATH = DATA_DIR / "combined_selected_themes_preprocessed.csv"

    df = pd.read_csv(DF_PATH)

    theme_avg_similarity = df.groupby("theme")["similarity"].mean().rename("theme_avg_similarity")
    df_with_avg = df.merge(theme_avg_similarity, on="theme")
    df_with_avg["similarity_diff"] = df_with_avg["similarity"] - df_with_avg["theme_avg_similarity"]

    model_summary = df_with_avg.groupby("model").agg(mean_similarity=("similarity", "mean"), mean_above_theme_avg=("similarity_diff", "mean"), proportion_above_theme_avg=("similarity_diff", lambda x: (x > 0).mean()), count=("similarity", "count")).reset_index()

    model_summary.to_csv(DATA_DIR / "model_summary.csv", index=False)

