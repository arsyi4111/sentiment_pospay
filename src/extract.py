from google_play_scraper import reviews, Sort

def fetch_reviews(config):
    result, _ = reviews(
        config["app_id"],
        lang=config["language"],
        country=config["country"],
        sort=Sort.NEWEST,
        count=config["max_reviews"]
    )
    return result