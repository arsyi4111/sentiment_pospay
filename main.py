import json
from src.extract import fetch_reviews
from src.transform import transform_reviews
from src.enrich import analyze_batch
from src.store import save_data
import pandas as pd
import math

def enrich_dataframe(df, batch_size):
    results = []

    texts = df["text_clean"].tolist()
    total_batches = math.ceil(len(texts) / batch_size)

    for i in range(total_batches):
        batch = texts[i * batch_size:(i + 1) * batch_size]

        print(f"Processing batch {i+1}/{total_batches}")

        batch_result = analyze_batch(batch)
        results.extend(batch_result)

    return results

def run_pipeline():
    with open("config/config.json") as f:
        config = json.load(f)

    raw_reviews = fetch_reviews(config)
    df = transform_reviews(raw_reviews, config)

    if config["ai_enabled"]:
        ai_results = enrich_dataframe(df, config["batch_size"])

        df["sentiment"] = [r["sentiment"] for r in ai_results]
        df["issues"] = [r["issues"] for r in ai_results]
        df["summary"] = [r["summary"] for r in ai_results]

    save_data(df, "data/processed/reviews.csv")
    raw_df = pd.DataFrame(raw_reviews)
    save_data(raw_df, "data/raw/reviews_raw.csv")

    print("Pipeline completed.")

if __name__ == "__main__":
    run_pipeline()