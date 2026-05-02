from pathlib import Path
import pandas as pd
import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

if __name__ == "__main__":

    BASE_DIR = Path(__file__).resolve().parent.parent
    KEY_PATH = BASE_DIR.parent / "src"/ "keywords_dicts" / "key_words_paper_ghirelli.json"
    THEM_PATH = BASE_DIR.parent / "data" / "GDELT THEMES LIST.csv"

    with open(KEY_PATH, 'r', encoding='utf-8') as f:
        kw = json.load(f)

    themes_df = pd.read_csv(THEM_PATH, encoding='utf-8')

    model_names = ['all-MiniLM-L6-v2', 'all-mpnet-base-v2', 'sentence-transformers/LaBSE']
    theme_texts = themes_df['THEME'].tolist()
    
    theme_texts = [theme.replace('_', ' ') for theme in theme_texts]

    all_results = []

    for model_name in model_names:
        print(f"Processing model: {model_name}")
        model = SentenceTransformer(model_name)

        theme_embeddings = model.encode(theme_texts, normalize_embeddings=True)

        for label, keywords in kw.items():
            for word in keywords:
                word_embedding = model.encode([word], normalize_embeddings=True)
                sims = cosine_similarity(word_embedding, theme_embeddings)[0]
                top_indices = sims.argsort()[-3:][::-1]  # Top 3 matches
                for rank, idx in enumerate(top_indices, 1):
                    current_model = {
                        'model': model_name,
                        'group': label,
                        'keyword': word,
                        'match_rank': rank,
                        'theme': theme_texts[idx],
                        'similarity': round(float(sims[idx]), 4)
                    }
                    all_results.append(current_model)

        try:
            model_results = [r for r in all_results if r['model'] == model_name]
            current_df = pd.DataFrame(model_results) # guardo en cada iteración por si se interrumpe
            current_df.to_csv(BASE_DIR / "Semantic_distance" / "data" / f"keyword_theme_preprocessed_matches_{model_name.replace('/', '_').replace(" ","-")}.csv", index=False)
        except Exception as e:
            print(f"Error saving results for {model_name}: {e}")

            
    try:        
        all_results_df = pd.DataFrame(all_results) #guardo todo en all models
        all_results_df.to_csv(BASE_DIR / "Semantic_distance" / "data" / "keyword_theme_preprocessed_matches_all_models.csv", index=False)
    except Exception as e:
        print(f"Error saving all results: {e}")