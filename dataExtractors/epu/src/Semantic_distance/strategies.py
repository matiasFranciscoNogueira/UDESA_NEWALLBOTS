import pandas as pd


def select_best_themes(df: pd.DataFrame, strategy: str = "mean_similarity", top_n: int = 1, min_similarity: float = 0.55, fill_if_missing: bool = True) -> pd.DataFrame:
    
    assert {'keyword', 'theme', 'similarity', 'model', 'match_rank'}.issubset(df.columns)

    if strategy == "best_per_model":
        result = best_per_model_strategy(df, top_n, min_similarity, fill_if_missing)
    elif strategy == "mean_similarity":
        result = mean_similarity_strategy(df, top_n, min_similarity, fill_if_missing)
    elif strategy == "consensus":
        result = consensus_strategy(df, top_n, min_similarity, fill_if_missing)
    else:
        raise ValueError("Estrategia no reconocida")

    concated_df = pd.concat(result, ignore_index=True)
    sorted_df = __sort_by_group(concated_df)
    return sorted_df

def best_per_model_strategy(df: pd.DataFrame, top_n: int, min_similarity: float, fill_if_missing: bool) -> pd.DataFrame:
    result_frames = []
    grouped = df.groupby(['keyword', 'model'])
    for _, group in grouped:
        high_sim = group[group['similarity'] >= min_similarity].nsmallest(top_n, 'match_rank')
        high_sim = high_sim.copy()
        high_sim['filled'] = False

        if fill_if_missing and len(high_sim) < top_n:
            remainder = group[~group.index.isin(high_sim.index)].nlargest(top_n - len(high_sim), 'similarity')
            remainder = remainder.copy()
            remainder['filled'] = True
            high_sim = pd.concat([high_sim, remainder])

        result_frames.append(high_sim)

    return result_frames

def mean_similarity_strategy(df: pd.DataFrame, top_n: int, min_similarity: float, fill_if_missing: bool) -> pd.DataFrame:
    result_frames = []

    keyword_groups = df[['keyword', 'group']].drop_duplicates().set_index('keyword')

    grouped = (df.groupby(["keyword", "theme"]).agg(mean_similarity=('similarity', 'mean'), count=('model', 'count')).reset_index())

    grouped['group'] = grouped['keyword'].map(keyword_groups['group'])

    for _, group_df in grouped.groupby("keyword"):
        high_sim = group_df[group_df["mean_similarity"] >= min_similarity].nlargest(top_n, "mean_similarity").copy()
        high_sim['filled'] = False

        if fill_if_missing and len(high_sim) < top_n:
            remainder = group_df[~group_df.index.isin(high_sim.index)].nlargest(top_n - len(high_sim), "mean_similarity").copy()
            remainder['filled'] = True
            high_sim = pd.concat([high_sim, remainder])

        high_sim['similarity'] = high_sim['mean_similarity']
        high_sim['model'] = 'Mean'
        high_sim['match_rank'] = -1
        result_frames.append(high_sim[['group', 'keyword', 'theme', 'similarity', 'model', 'match_rank', 'filled']])

    return result_frames


def consensus_strategy(df: pd.DataFrame, top_n: int, min_similarity: float, fill_if_missing: bool) -> pd.DataFrame:
    result_frames = []

    keyword_groups = df[['keyword', 'group']].drop_duplicates().set_index('keyword')

    grouped = (df.groupby(["keyword", "theme"]).agg(models_count=('model', 'nunique'), mean_similarity=('similarity', 'mean')).reset_index())

    grouped['group'] = grouped['keyword'].map(keyword_groups['group'])

    for _, group_df in grouped.groupby("keyword"):
        high_sim = group_df[group_df["mean_similarity"] >= min_similarity].nlargest(top_n, ["models_count", "mean_similarity"]).copy()
        high_sim['filled'] = False

        if fill_if_missing and len(high_sim) < top_n:
            remainder = group_df[~group_df.index.isin(high_sim.index)].nlargest(top_n - len(high_sim), ["models_count", "mean_similarity"]).copy()
            remainder['filled'] = True
            high_sim = pd.concat([high_sim, remainder])

        high_sim['similarity'] = high_sim['mean_similarity']
        high_sim['model'] = 'Consensus'
        high_sim['match_rank'] = -1
        result_frames.append(high_sim[['group', 'keyword', 'theme', 'similarity', 'model', 'match_rank', 'filled']])

    return result_frames


def __sort_by_group(df: pd.DataFrame) -> pd.DataFrame:
    group_order = {"E": 0, "P": 1, "U": 2}
    df['group_sort'] = df['group'].map(group_order)
    df.sort_values(by=['group_sort', 'keyword', 'match_rank'], inplace=True)
    df.drop(columns='group_sort', inplace=True)
    return df