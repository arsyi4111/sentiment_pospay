import pandas as pd

def transform_reviews(raw_reviews, config):
    df = pd.DataFrame(raw_reviews)

    df = df.rename(columns={
        "reviewId": "review_id",
        "content": "text",
        "score": "rating",
        "at": "timestamp"
    })

    df["text_clean"] = df["text"].str.lower()
    df["review_date"] = pd.to_datetime(df["timestamp"]).dt.date

    # 🔥 DATE FILTER (from config)
    if config.get("start_date") and config.get("end_date"):
        start = pd.to_datetime(config["start_date"]).date()
        end = pd.to_datetime(config["end_date"]).date()

        df = df[(df["review_date"] >= start) & (df["review_date"] <= end)]

    return df[["review_id", "text", "text_clean", "rating", "review_date"]]